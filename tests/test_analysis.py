"""Check semantic edge cases and independently reconcile generated results."""
import unittest
import json
from pathlib import Path
import pandas as pd
from analysis import expand_contractions, sentiment_label

ROOT = Path(__file__).resolve().parents[1]

class AnalysisTests(unittest.TestCase):
    def test_contractions_and_negation(self):
        self.assertEqual(expand_contractions("I CAN'T say it isn’t good"), 'I cannot say it is not good')
        self.assertEqual(expand_contractions("we're happy; they've arrived"), 'we are happy; they have arrived')

    def test_sentiment_boundaries(self):
        self.assertEqual([sentiment_label(n) for n in [-.05,-.049,0,.049,.05]],
                         ['Negative','Neutral','Neutral','Neutral','Positive'])

    def test_review_counts_include_missing_text_and_ties(self):
        raw = pd.read_csv(ROOT/'reviews.csv', sep='\t', dtype=str, keep_default_na=False)
        expected = raw.gPlusPlaceId.value_counts()
        actual = pd.read_csv(ROOT/'outputs/task2a_places_over_three.csv', dtype={'gPlusPlaceId':str})
        self.assertEqual(dict(zip(actual.gPlusPlaceId,actual.review_count)), expected[expected>3].to_dict())
        winners = pd.read_csv(ROOT/'outputs/task2e_most_reviewed.csv', dtype={'gPlusPlaceId':str})
        self.assertEqual(set(winners.gPlusPlaceId), set(expected[expected==expected.max()].index))
        self.assertEqual(winners.review_count.tolist(), [int(expected.max())]*len(winners))

    def test_population_reconciliation(self):
        summary=json.loads((ROOT/'outputs/summary.json').read_text())
        sentiment=pd.read_csv(ROOT/'outputs/task3_sentiment.csv')
        self.assertEqual(int(sentiment.reviews.sum()),summary['reviews_with_text'])
        self.assertEqual(summary['reviews_with_text']+summary['reviews_without_text'],21767)
        self.assertEqual(int(pd.read_csv(ROOT/'outputs/task2b_place_status.csv').places.sum()),22476)
        table=pd.read_csv(ROOT/'outputs/task3_rating_comparison.csv',index_col=0)
        self.assertEqual(int(table.to_numpy().sum()),summary['reviews_with_text'])

if __name__=='__main__':
    unittest.main()
