"""Reproducible Google Local assignment analysis. Run: python analysis.py."""
from pathlib import Path
from collections import Counter
from functools import lru_cache
import hashlib
import json
import re
import time
import unicodedata
import os
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent / '.cache' / 'matplotlib'))
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import TreebankWordTokenizer
from spellchecker import SpellChecker
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
DATA = ROOT / 'data' / 'processed'
NLTK_DATA = ROOT / '.cache' / 'nltk_data'
nltk.data.path.insert(0, str(NLTK_DATA))
MISSING = ['', 'None', 'null', 'NULL', 'NaN', 'nan', 'N/A']
ORDER = ['Positive', 'Neutral', 'Negative']
TOKENIZER = TreebankWordTokenizer()
CONTRACTIONS = {"won't": 'will not', "can't": 'cannot', "shan't": 'shall not',
 "ain't": 'is not', "let's": 'let us', "i'm": 'I am', "it's": 'it is',
 "that's": 'that is', "what's": 'what is', "there's": 'there is',
 "he's": 'he is', "she's": 'she is'}
# Reviewed English typos only. Unrestricted dictionary correction corrupted foreign
# words and business vocabulary (e.g. wifi -> wife); retain all other candidates.
APPROVED_TYPOS = {'recomend':'recommend', 'definately':'definitely',
 'recieved':'received', 'recieve':'receive', 'awsome':'awesome',
 'pleasent':'pleasant', 'experiance':'experience', 'resturant':'restaurant',
 'thier':'their'}

def expand_contractions(text):
    text = text.replace('\u2019', "'").replace('\u2018', "'")
    for short, full in CONTRACTIONS.items():
        text = re.sub(r'\b' + re.escape(short) + r'\b', full, text, flags=re.I)
    for suffix, full in [("n't", ' not'), ("'re", ' are'), ("'ve", ' have'),
                         ("'ll", ' will'), ("'d", ' would')]:
        text = re.sub(re.escape(suffix) + r'\b', full, text, flags=re.I)
    return text

def sentiment_label(score):
    return 'Positive' if score >= .05 else 'Negative' if score <= -.05 else 'Neutral'

def load_table(filename):
    frame = pd.read_csv(ROOT / filename, sep='\t', dtype='string',
                        keep_default_na=False, na_values=MISSING)
    for col in frame:
        frame[col] = frame[col].str.strip().replace('', pd.NA)
    return frame

def save_csv(frame, name, private=False):
    folder = OUT / 'private' if private else OUT
    folder.mkdir(parents=True, exist_ok=True)
    frame.to_csv(folder / (name + '.csv'), index=False)

def main():
    started = time.perf_counter()
    OUT.mkdir(exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        nltk.download('vader_lexicon', download_dir=str(NLTK_DATA), raise_on_error=True)
    places, reviews, users = (load_table(f) for f in ['Place.csv', 'reviews.csv', 'users.csv'])
    frames = {'Places': places, 'Reviews': reviews, 'Users': users}
    audit = []
    for name, df in frames.items():
        audit.append({'dataset': name, 'rows': len(df), 'columns': len(df.columns),
                      'exact_duplicates': int(df.duplicated().sum()),
                      'missing_cells': int(df.isna().sum().sum())})
    save_csv(pd.DataFrame(audit), 'data_quality')
    missing = pd.concat([pd.DataFrame({'dataset': name, 'column': df.columns,
                      'missing': df.isna().sum().values}) for name, df in frames.items()])
    save_csv(missing, 'missing_values')
    for df, key in [(places, 'gPlusPlaceId'), (users, 'gPlusUserId')]:
        if df[key].isna().any() or df[key].duplicated().any():
            raise ValueError(f'Invalid primary key: {key}; resolve before analysis')
    for col in ['gPlusPlaceId', 'gPlusUserId']:
        if reviews[col].isna().any():
            raise ValueError(f'Missing review foreign key: {col}')
    reviews['rating'] = pd.to_numeric(reviews['rating'], errors='raise')
    if not reviews['rating'].isin([1, 2, 3, 4, 5]).all():
        raise ValueError('Invalid rating')
    unknown_closed = places['closed'].dropna()[~places['closed'].dropna().isin(['True','False'])]
    if len(unknown_closed):
        raise ValueError('Unknown closed flag')
    places['closed'] = places['closed'].map({'True': True, 'False': False}).astype('boolean')
    reviews['reviewDate'] = pd.to_datetime(reviews['reviewTime'], format='%b %d, %Y', errors='coerce')
    links = {'reviews_without_place': int((~reviews.gPlusPlaceId.isin(places.gPlusPlaceId)).sum()),
             'reviews_without_user': int((~reviews.gPlusUserId.isin(users.gPlusUserId)).sum()),
             'invalid_dates': int((reviews.reviewTime.notna() & reviews.reviewDate.isna()).sum())}
    # Preserve raw text for VADER: punctuation, case and negation carry meaning.
    text = reviews.loc[reviews.reviewText.notna()].copy()
    text['normalizedText'] = text.reviewText.map(lambda s: unicodedata.normalize('NFKC', s))
    spell = SpellChecker(distance=1)
    changes = Counter()
    @lru_cache(maxsize=None)
    def correction(word):
        # Conservative English correction: preserve names, acronyms and short tokens.
        if not word.isascii() or not word.islower() or len(word) < 4 or word in spell:
            return word
        if word not in APPROVED_TYPOS:
            return word
        candidate = spell.correction(word)
        return candidate if candidate == APPROVED_TYPOS[word] else word
    def correct_text(value):
        def replace(match):
            word = match.group()
            fixed = correction(word)
            if fixed != word:
                changes[(word, fixed)] += 1
            return fixed
        return re.sub(r"\b[A-Za-z]+(?:'[A-Za-z]+)?\b", replace, value)
    text['expandedText'] = text.normalizedText.map(expand_contractions)
    print(f'Cleaning {len(text):,} text reviews', flush=True)
    text['correctedText'] = text.expandedText.map(correct_text)
    text['tokens'] = text.correctedText.map(TOKENIZER.tokenize)
    examples = text.loc[text.normalizedText != text.correctedText,
                        ['normalizedText', 'expandedText', 'correctedText', 'tokens']].head(12)
    save_csv(examples, 'preprocessing_examples', private=True)
    save_csv(pd.DataFrame([{'original': a, 'replacement': b, 'occurrences': n}
                          for (a,b),n in changes.most_common()]), 'spelling_changes')
    counts = reviews.groupby('gPlusPlaceId').size().rename('review_count').reset_index()
    over3 = counts.loc[counts.review_count > 3].sort_values(['review_count','gPlusPlaceId'], ascending=[False,True])
    save_csv(over3, 'task2a_places_over_three')
    closed = places.closed.value_counts(dropna=False).reindex([False,True,pd.NA], fill_value=0)
    status = pd.DataFrame({'status': ['Operating','Closed','Unknown'], 'places': closed.values})
    save_csv(status, 'task2b_place_status')
    # No stopword removal: the task explicitly requests consecutive three-word phrases.
    trigrams = Counter()
    for value in text.loc[text.rating == 5, 'correctedText']:
        words = re.findall(r"[^\W\d_]+(?:'[^\W\d_]+)?", value.lower(), flags=re.UNICODE)
        trigrams.update(' '.join(words[i:i+3]) for i in range(len(words)-2))
    phrases = pd.DataFrame(sorted(trigrams.items(), key=lambda x: (-x[1], x[0]))[:20], columns=['phrase','frequency'])
    save_csv(phrases, 'task2c_top_twenty_phrases')
    specialists = users.loc[users.jobs == 'IT Specialist'].copy()
    save_csv(specialists, 'task2d_it_specialists', private=True)
    winners = counts.loc[counts.review_count == counts.review_count.max()].merge(
        places[['gPlusPlaceId','name']], on='gPlusPlaceId', how='left', validate='one_to_one')
    save_csv(winners, 'task2e_most_reviewed')
    sia = SentimentIntensityAnalyzer()
    print('Scoring original review text with VADER', flush=True)
    text['compound'] = text.normalizedText.map(lambda s: sia.polarity_scores(s)['compound'])
    text['sentiment'] = text.compound.map(sentiment_label)
    text['ratingSentiment'] = text.rating.map(lambda n: 'Positive' if n >= 4 else 'Negative' if n <= 2 else 'Neutral')
    sentiment = text.sentiment.value_counts().reindex(ORDER, fill_value=0).rename_axis('sentiment').reset_index(name='reviews')
    sentiment['percentage'] = (100*sentiment.reviews/len(text)).round(2)
    save_csv(sentiment, 'task3_sentiment')
    comparison = pd.crosstab(text.ratingSentiment, text.sentiment).reindex(index=ORDER, columns=ORDER, fill_value=0)
    comparison.to_csv(OUT / 'task3_rating_comparison.csv')
    by_place = text.groupby(['gPlusPlaceId','sentiment']).size().unstack(fill_value=0).reindex(columns=ORDER, fill_value=0)
    by_place['text_reviews'] = by_place.sum(axis=1)
    by_place.reset_index().to_csv(OUT / 'private' / 'sentiment_by_place.csv', index=False)
    # Export useful structured local artifacts, excluded from Git to avoid redundant personal data.
    places.to_csv(DATA/'places.csv', index=False)
    users.to_csv(DATA/'users.csv', index=False)
    reviews.to_csv(DATA/'reviews.csv', index=False)
    text.to_json(DATA/'review_text.jsonl', orient='records', lines=True, force_ascii=False, date_format='iso')
    text[['gPlusPlaceId','rating','compound','sentiment']].to_csv(OUT/'private'/'scored_reviews.csv', index=False)
    summary = {'datasets': audit, **links, 'reviews_with_text': len(text),
       'reviews_without_text': len(reviews)-len(text), 'it_specialists': len(specialists),
       'places_over_three': len(over3), 'five_star_text_reviews': int((text.rating==5).sum()),
       'spelling_replacements': sum(changes.values()), 'distinct_spelling_changes': len(changes),
       'expanded_reviews': int((text.normalizedText != text.expandedText).sum()),
       'rating_agreement_percent': round(100*(text.sentiment==text.ratingSentiment).mean(),2),
       'places_with_at_least_ten_text_reviews': int((by_place.text_reviews>=10).sum()),
       'runtime_seconds': round(time.perf_counter()-started,2),
       'source_sha256': {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['Place.csv','reviews.csv','users.csv']}}
    (OUT/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    plt.rcParams.update({'font.size': 11, 'axes.spines.top':False, 'axes.spines.right':False})
    fig, ax = plt.subplots(figsize=(8,4))
    bars = ax.bar(sentiment.sentiment, sentiment.reviews, color=['#287c62','#8792a2','#b44a4a'])
    ax.bar_label(bars, padding=3, fmt='%.0f')
    ax.set(ylabel='Reviews with text', title=f'VADER sentiment across {len(text):,} reviews', ylim=(0,sentiment.reviews.max()*1.18))
    fig.tight_layout(); fig.savefig(OUT/'sentiment_distribution.png', dpi=180); plt.close(fig)
    assert counts.review_count.sum() == len(reviews)
    assert status.places.sum() == len(places)
    assert sentiment.reviews.sum() == len(text)
    assert (over3.review_count > 3).all()
    assert len(phrases) == 20
    print(json.dumps(summary, indent=2))
    print('\nMost reviewed places\n', winners.to_string(index=False))
    print('\nSentiment\n', sentiment.to_string(index=False))
    return summary

if __name__ == '__main__':
    main()
