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
for title,name in [('Task 2a Places with more than three reviews','task2a_places_over_three'),('Task 2b Closed and operating places','task2b_place_status'),('Task 2c Top twenty phrases','task2c_top_twenty_phrases'),('Task 2e Most reviewed places and ties','task2e_most_reviewed'),('Task 3 Sentiment counts','task3_sentiment'),('Task 3 Rating comparison','task3_rating_comparison')]:
    cells.extend([nbf.v4.new_markdown_cell('## '+title),nbf.v4.new_code_cell(f'display(pd.read_csv(OUT/"{name}.csv", dtype=str))')])
cells.extend([nbf.v4.new_markdown_cell('## Task 2d IT Specialist subset\nThe full subset is saved locally. This public notebook abbreviates identifiers and omits names.'),nbf.v4.new_code_cell('specialists = pd.read_csv(OUT/"private/task2d_it_specialists.csv", dtype=str)\nview = specialists[["gPlusUserId", "jobs"]].copy()\nview["gPlusUserId"] = view.gPlusUserId.str[:4] + "..." + view.gPlusUserId.str[-4:]\ndisplay(view)'),nbf.v4.new_code_cell('from IPython.display import Image, display\ndisplay(Image(filename=str(OUT/"sentiment_distribution.png")))')])
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
