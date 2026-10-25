# Google Local data analysis assignment

Corrected implementation of NCC Education's **Introduction to Data Science and Big Data** assignment, Google Local Research Team, Autumn 2024 to Summer 2025.

## Deliverables

- [Word report](report/Google_Local_Analysis_Report.docx) and [PDF report](report/Google_Local_Analysis_Report.pdf), with evidence screenshots and references.
- [Executed notebook](google_local_analysis.ipynb), covering preparation, all five processing questions, and sentiment analysis.
- [Analysis program](analysis.py), [aggregate CSV results](outputs/), and [browser screenshots](evidence/).
- [Report source](report/report.md), build scripts, dependency versions, and validation tests.

**Before academic submission:** replace `[Enter NCC student number]` in the report using your actual NCC number, review the work and acknowledge assistance under your institution's rules, and attach the required Statement and Confirmation of Own Work. No declaration has been signed on your behalf.

## Main findings

| Measure | Result |
| --- | ---: |
| Supplied users | 21,858 |
| Supplied places | 22,476 |
| Supplied reviews | 21,767 |
| Reviews with text | 17,706 |
| Reviews without text | 4,061 |
| Review references absent from Places | 14,622 |
| Operating / permanently closed places | 21,720 / 756 |
| Places with more than three reviews | 4 |
| Maximum reviews per place | 4, shared by four places |
| IT Specialist users | 5 |
| Positive / neutral / negative text reviews | 13,498 / 1,995 / 2,213 |
| VADER agreement with rating baseline | 77.93% |

Only one of the four tied place identifiers has an available name: **Scott Clark Honda**. The other three are explicitly marked unavailable. Review counts include missing-text reviews. Sentiment percentages use only reviews with text. Rating agreement is a diagnostic, not verified accuracy. The supplied record counts differ from the course dataset description.

## Run the analysis

Python 3.12 was used. The input `.csv` files are actually tab-separated and must remain in the repository root.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python analysis.py
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python scripts/build_evidence.py
```

The first analysis run downloads NLTK's VADER lexicon. Internet access is required for dependency installation and that first download. Later runs reuse `.cache/nltk_data`. The pipeline stops on invalid keys, ratings or Boolean flags and reports unmatched place relationships. Reviewed spelling replacements are applied only when pyspellchecker agrees; unreviewed foreign words and business vocabulary are preserved. The original text is used for VADER. No supervised classifier has been trained.

The pipeline creates cleaned CSV tables and review-text JSON Lines in `data/processed/`, along with the full IT Specialist subset and review-level outputs in `outputs/private/`. These local derived files are intentionally ignored by Git to avoid redundant personal-data copies. The original supplied datasets were already part of this repository and are unchanged. Screenshots and notebook outputs omit user names and abbreviate the IT subset identifiers.

## Rebuild screenshots and report

The screenshot script requires Node.js, Playwright and Chrome. Install Playwright in your preferred tooling environment, or set `PLAYWRIGHT_MODULE` to an existing Playwright module directory.

```powershell
node scripts/capture_evidence.cjs
python scripts/build_report.py --student-number YOUR_NCC_NUMBER
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/export_report.ps1
```

`build_report.py` requires python-docx and Pillow. The Word export script requires Microsoft Word on Windows; it opens only the generated report, read-only, and exports PDF. The report has double-spaced body text and name, student-number and word-count fields in every page header. The word count includes body headings and figure captions, excluding the cover, references and text inside figures.

`scripts/build_evidence.py` regenerates HTML evidence pages and executes the notebook. `scripts/capture_evidence.cjs` captures those actual pages in Chrome. The screenshots are result evidence pages, not images of an IDE or simulated program execution. The notebook separately preserves executed code outputs.

## Corrections from the original submission

- Preserve all valid reviews for counts instead of dropping missing text globally.
- Validate all three datasets and disclose absent place relationships.
- Apply controlled spelling corrections and retain original text.
- Report all maximum-count ties with identifiers, counts and available names.
- Produce the complete top-twenty phrase table and sentiment counts.
- Separate textual sentiment from the star-rating baseline.
- Explain business-level sample limitations and provide a strategy tied to actual findings.
- Replace the old notebook and report; remove the obsolete notebook checkpoint and Word lock file. Original versions remain in Git history.
