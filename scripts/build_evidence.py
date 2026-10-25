"""Generate an executed notebook and browser evidence pages from real outputs."""
from pathlib import Path
import os
import sys
import argparse
import json
import html
import pandas as pd
import nbformat as nbf
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--pages-only',action='store_true',help='Refresh HTML from existing outputs without rerunning the notebook')
args=parser.parse_args()
OUT=ROOT/'outputs'
EVIDENCE=ROOT/'evidence'
EVIDENCE.mkdir(exist_ok=True)
for key, folder in [('IPYTHONDIR','ipython'),('JUPYTER_CONFIG_DIR','jupyter'),('JUPYTER_DATA_DIR','jupyter_data'),('JUPYTER_RUNTIME_DIR','jupyter_runtime')]:
    os.environ[key]=str(ROOT/'.cache'/folder)
    Path(os.environ[key]).mkdir(parents=True,exist_ok=True)

def table(name):
    return pd.read_csv(OUT/(name+'.csv'),dtype=str).fillna('Unavailable in supplied Places').to_html(index=False,escape=True,border=0)

summary=json.loads((OUT/'summary.json').read_text())
missing=pd.read_csv(OUT/'missing_values.csv')
missing=missing.loc[missing.missing>0]
it=pd.read_csv(OUT/'private/task2d_it_specialists.csv',dtype=str).fillna('Unknown')
it['gPlusUserId']=it.gPlusUserId.str[:4]+'...'+it.gPlusUserId.str[-4:]
it=it[['gPlusUserId','jobs']]
cleaned=pd.read_json(ROOT/'data/processed/review_text.jsonl',lines=True,dtype={'gPlusPlaceId':str,'gPlusUserId':str})
examples=cleaned.loc[(cleaned.normalizedText.str.len()<90)&(cleaned.normalizedText!=cleaned.expandedText)].head(2)
example_rows=[]
for _,example in examples.iterrows():
    example_rows.extend([{'stage':'Original text','value':example.normalizedText},
                         {'stage':'Expanded text','value':example.expandedText},
                         {'stage':'Word tokens','value':str(example.tokens)}])
example_html=pd.DataFrame(example_rows).to_html(index=False,border=0)
pages=[
 ('01_data_quality','Task 1 Data preparation', '<p>All valid review records are retained for counting. Missing text is excluded only from text analysis.</p>'+table('data_quality')+f'<p>Text reviews: {summary["reviews_with_text"]:,} | Missing text: {summary["reviews_without_text"]:,}<br>Contractions expanded in {summary["expanded_reviews"]:,} reviews | Spell replacements: {summary["spelling_replacements"]:,}<br>Review references absent from Places: {summary["reviews_without_place"]:,}</p><h2>Columns with missing values</h2>'+missing.to_html(index=False,border=0)),
 ('02_preprocessing','Task 1 Cleaning evidence','<p>Actual spelling replacements from the full run. Corrections are stored separately; VADER uses original text.</p>'+pd.read_csv(OUT/'spelling_changes.csv').head(16).to_html(index=False,border=0)+'<h2>Actual contraction and tokenization examples</h2>'+example_html+'<p>Tokenizer: TreebankWordTokenizer. Full transformed text retained locally.</p>'),
 ('03_queries','Task 2 Places and users','<h2>Places with more than three reviews</h2>'+table('task2a_places_over_three')+'<h2>Operating and closed places</h2>'+table('task2b_place_status')+'<h2>IT Specialist users</h2><p>Five matching users. Identifiers abbreviated in this screenshot.</p>'+it.to_html(index=False,border=0)+'<h2>Most reviewed places including all ties</h2>'+table('task2e_most_reviewed')),
 ('04_phrases','Task 2 Twenty most frequent phrases',f'<p>Rating 5 only | {summary["five_star_text_reviews"]:,} reviews with text | Three consecutive words | Lowercase, expanded contractions and conservative spelling correction</p>'+table('task2c_top_twenty_phrases')),
 ('05_sentiment','Task 3 Sentiment analysis',f'<p>VADER applied to {summary["reviews_with_text"]:,} original review texts.<br>Positive compound >= 0.05 | Negative compound <= -0.05 | Neutral between thresholds</p>'+table('task3_sentiment')+'<img width="850" src="../outputs/sentiment_distribution.png"><h2>Rating baseline compared with VADER</h2><p>Rows: rating sentiment. Columns: VADER sentiment. Agreement is a proxy, not verified accuracy.</p>'+pd.read_csv(OUT/'task3_rating_comparison.csv').to_html(index=False,border=0)+f'<p>Agreement: {summary["rating_agreement_percent"]}%</p>')]
for stem,title,body in pages:
    document='<!doctype html><html><head><meta charset="utf-8"><style>body{font:17px Arial,sans-serif;color:#182434;background:#fff;margin:42px;max-width:1100px}h1{font-size:29px;margin:0 0 12px}h2{font-size:21px;margin:26px 0 10px}p{line-height:1.6;color:#34465b}table{border-collapse:collapse;width:100%;font-size:15px}th,td{padding:9px 12px;border:1px solid #d9dfe6;text-align:left}th{background:#eaf0f5}tr:nth-child(even){background:#f7f9fb}footer{font-size:13px;color:#566479;margin-top:24px}</style></head><body><h1>'+title+'</h1>'+body+'<footer>Google Local Research Team | Evidence generated from outputs of analysis.py | Source files unchanged</footer></body></html>'
    (EVIDENCE/(stem+'.html')).write_text(document,encoding='utf-8')
    document=document.replace('margin:42px;max-width:1100px','margin:24px;max-width:860px').replace('font-size:15px','font-size:17px').replace('padding:9px 12px','padding:7px 10px')
    (EVIDENCE/(stem+'.html')).write_text(document,encoding='utf-8')

if args.pages_only:
    print('Evidence pages refreshed from existing analysis outputs')
    raise SystemExit(0)

nb=nbf.v4.new_notebook()
nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
cells=[nbf.v4.new_markdown_cell('# Google Local Research Team\nComplete corrected analysis for Tasks 1 to 3. Run all cells from the repository root. Business strategy and ethics are in the report. Raw data is preserved; private derived outputs are excluded from Git.'),
nbf.v4.new_code_cell('from pathlib import Path\nimport pandas as pd\nfrom analysis import main\nsummary = main()\nOUT = Path("outputs")'),
nbf.v4.new_markdown_cell('## Task 1 Data quality and preparation\nIdentifiers are strings. Primary keys, foreign keys, ratings and dates are checked. Missing optional values are retained. Text correction is separate from the raw VADER input.'),
nbf.v4.new_code_cell('display(pd.read_csv(OUT/"data_quality.csv"))\ndisplay(pd.read_csv(OUT/"missing_values.csv"))\ndisplay(pd.read_csv(OUT/"spelling_changes.csv").head(15))')]
cells.extend([
nbf.v4.new_markdown_cell('## Task 1 Text preparation examples'),
nbf.v4.new_code_cell('from pprint import pformat\nfrom analysis import load_table, expand_contractions, TOKENIZER\nplaces = load_table("Place.csv")\nreviews = load_table("reviews.csv")\nusers = load_table("users.csv")\ntext = pd.read_json("data/processed/review_text.jsonl", lines=True,\n                    dtype={"gPlusPlaceId": str, "gPlusUserId": str})\nexamples = text[(text.normalizedText.str.len() < 90) &\n                (text.normalizedText != text.expandedText)].head(2)\nfor value in examples.normalizedText:\n    expanded = expand_contractions(value)\n    print("Original:", value)\n    print("Expanded:", expanded)\n    print("Tokens:", pformat(TOKENIZER.tokenize(expanded), width=100), "\\n")'),
nbf.v4.new_markdown_cell('## Task 2a Places with more than three reviews'),
nbf.v4.new_code_cell('review_counts = reviews.groupby("gPlusPlaceId").size().reset_index(name="review_count")\nmore_than_three = review_counts[review_counts.review_count > 3]\ndisplay(more_than_three.sort_values("gPlusPlaceId"))'),
nbf.v4.new_markdown_cell('## Task 2b Closed and operating places'),
nbf.v4.new_code_cell('status_counts = places["closed"].value_counts(dropna=False)\nprint("Operating:", status_counts.get("False", 0))\nprint("Permanently closed:", status_counts.get("True", 0))\nprint("Total places:", len(places))'),
nbf.v4.new_markdown_cell('## Task 2c Top twenty phrases'),
nbf.v4.new_code_cell('import re\nfrom collections import Counter\ntrigrams = Counter()\nfor value in text.loc[text.rating == 5, "correctedText"]:\n    words = re.findall(r"[^\\W\\d_]+(?:\'[^\\W\\d_]+)?", value.lower())\n    trigrams.update(" ".join(words[i:i+3]) for i in range(len(words)-2))\ntop_twenty = pd.DataFrame(\n    sorted(trigrams.items(), key=lambda item: (-item[1], item[0]))[:20],\n    columns=["phrase", "frequency"])\ndisplay(top_twenty)'),
nbf.v4.new_markdown_cell('## Task 2d IT Specialist subset\nIdentifiers abbreviated for public evidence; the complete subset is saved locally.'),
nbf.v4.new_code_cell('specialists = users[users["jobs"] == "IT Specialist"]\nview = specialists[["gPlusUserId", "jobs"]].copy()\nview["gPlusUserId"] = view.gPlusUserId.str[:4] + "..." + view.gPlusUserId.str[-4:]\nprint("Matching users:", len(specialists))\ndisplay(view)'),
nbf.v4.new_markdown_cell('## Task 2e Most reviewed places and ties'),
nbf.v4.new_code_cell('maximum = review_counts.review_count.max()\nwinners = review_counts[review_counts.review_count == maximum]\nwinners = winners.merge(places[["gPlusPlaceId", "name"]],\n                        on="gPlusPlaceId", how="left", validate="one_to_one")\nwinners["name"] = winners["name"].fillna("Unavailable in supplied Places")\ndisplay(winners)'),
nbf.v4.new_markdown_cell('## Task 3 Sentiment counts'),
nbf.v4.new_code_cell('from nltk.sentiment import SentimentIntensityAnalyzer\nfrom analysis import sentiment_label\nsia = SentimentIntensityAnalyzer()\ntext["compound"] = text.normalizedText.map(lambda value: sia.polarity_scores(value)["compound"])\ntext["sentiment"] = text.compound.map(sentiment_label)\nsentiment_counts = text.sentiment.value_counts().reindex(["Positive", "Neutral", "Negative"])\nprint("Reviews with text:", len(text))\nprint("Reviews excluded because text is missing:", len(reviews) - len(text))\ndisplay(sentiment_counts.rename_axis("sentiment").reset_index(name="reviews"))'),
nbf.v4.new_markdown_cell('## Task 3 Rating comparison'),
nbf.v4.new_code_cell('text["ratingSentiment"] = text.rating.map(\n    lambda value: "Positive" if value >= 4 else "Negative" if value <= 2 else "Neutral")\ndisplay(pd.crosstab(text.ratingSentiment, text.sentiment))\nagreement = (text.ratingSentiment == text.sentiment).mean() * 100\nprint(f"Rating agreement: {agreement:.2f}% (proxy, not verified accuracy)")'),
nbf.v4.new_code_cell('from IPython.display import Image, display\ndisplay(Image(filename=str(OUT/"sentiment_distribution.png")))')])
nb.cells=cells
client=NotebookClient(nb,timeout=300,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpec
km=KernelManager(kernel_name='python3')
km._kernel_spec=KernelSpec(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],display_name='Python 3',language='python')
client.km=km
client.execute()
nbf.write(nb,ROOT/'google_local_analysis.ipynb')
print('Executed notebook and evidence pages created')
