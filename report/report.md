# Google Local Review Analysis and Business Strategy

## Introduction and scope

This report evaluates the supplied Google Local Users, Places and Reviews datasets and presents a reproducible method for preparing, querying and analysing them. The analysis finds predominantly positive review language, but the coverage of individual businesses is too sparse to support dependable business rankings. Missing place records also restrict the connection between reviews and named businesses. These limitations shape the proposed business strategy and the safeguards recommended for future advertising data collection.

The implementation uses Python and pandas for structured processing, NLTK for tokenization and sentiment analysis, and pyspellchecker for controlled spelling suggestions. The accompanying notebook contains executed results. CSV outputs provide machine-readable answers, while Figures 1 to 5 capture the actual results in a browser. Source data remains unchanged. Separate local files contain cleaned tables and detailed review scores, so each result can be traced back to its input without replacing the original evidence.

The supplied files contain 21,858 users, 22,476 places and 21,767 reviews. These observed totals differ from the supporting material, which describes 21,848 users, 22,484 places and 22,272 reviews [1]. The report uses the actual supplied files rather than adjusting records to match the documentation. Conclusions therefore concern this extract of the Google Local dataset, rather than the entire Google Maps service or its present customer population.

## Task 1 Data preparation

### Structuring and validating all three files

Although the filenames end in CSV, their fields are separated by tabs. pandas read_csv therefore uses a tab separator. Selecting the correct delimiter produces seven columns in Places, seven in Reviews and six in Users. Renaming a file alone does not structure its contents; the parser interprets delimiters, quoted fields and missing values. All columns initially load as strings, preserving the long Google identifiers without rounding or scientific notation. pandas supports explicit types and missing-value settings for this purpose [2].

Whitespace is stripped from field boundaries and explicit markers, including empty strings and the literal None, become missing values. This matters because the first supplied review contains None in reviewText. It must represent absent text rather than a word submitted for sentiment classification. Optional fields remain missing where no evidence supports a replacement. Missing job titles, prices and opening hours are not inferred from neighbouring records or filled with invented averages.

Each table is checked for exact duplicate rows. None are found. Users and Places also pass checks for complete, unique primary keys. Review foreign keys are complete, and all ratings convert to numeric values within one to five. Closed flags are validated against True and False before conversion to a nullable Boolean type. Dates are parsed using the observed month, day and year format. There are 29 missing review dates and no additional non-missing dates that fail parsing.

Checking relationships reveals 14,622 reviews whose place identifier is absent from Places. Every review user identifier matches Users. Missing place relationships are reported rather than silently removed through an inner join. The place identifier still supports a valid count even when the business name is unavailable. Resolving missing names would require additional source data; guessing names from review language would create unsupported records and could attach comments to the wrong business.

### Missing values and appropriate analysis populations

There are 4,061 reviews without text, leaving 17,706 text reviews. Deleting those records from the main Reviews table would undercount business activity. The implementation therefore retains the full 21,767 records for review-count questions and creates a separate text subset for phrase extraction and sentiment analysis. A missing comment does not imply neutral sentiment. Such records remain outside the text classifier and are disclosed alongside its denominator.

Places has 15,784 missing prices, 7,876 missing opening-hours fields and 1,365 missing phone numbers. Users has 3,906 missing jobs, 6,515 missing current locations, 13,380 missing previous locations and 6,266 missing education fields. Reviews also has 211 missing categories. Removing every incomplete row would discard useful identifiers and ratings simply because unrelated profile details are unavailable. Column-specific treatment preserves valid answers while making the missingness visible in the quality audit.

For future updates, the validation checks act as stopping conditions for invalid primary keys, ratings or closed flags. They do not silently coerce incorrect values into acceptable categories. Optional missing fields remain distinguishable from invalid observations. The generated quality tables record dataset sizes, missing cells and duplicates, while source hashes identify the exact input files. Figure 1 shows this audit and the separation between the complete review population and the text-analysis subset.

### Spelling correction and contraction expansion

Text preparation creates separate normalized, expanded and corrected columns. Unicode normalization standardizes equivalent character representations, and curly apostrophes are converted for contraction matching. A dictionary handles irregular forms such as cannot and will not, while regular-expression rules expand common endings such as not, are and have. Matching ignores case and uses word boundaries. Possessive apostrophes are not removed indiscriminately, because this could change business names or the meaning of ordinary noun phrases.

Contractions are expanded in 5,251 reviews. This produces a more consistent representation for phrase counting, where equivalent forms should contribute to the same phrase. Ambiguous forms remain a limitation: an ending such as apostrophe d can mean had or would, depending on context. The implementation uses would for this suffix and documents the simplifying assumption. A linguistic parser could resolve some cases, but would add model dependencies and still require assessment on the languages present.

An initial spelling audit showed why automatic correction needs restraint. Dictionary suggestions included changing wifi to wife, tech to teach and several foreign words into unrelated English words. Such changes would damage the evidence. The final implementation applies only a reviewed list of clear English typos when pyspellchecker agrees with the approved replacement. Examples include recomend to recommend, definately to definitely and recieved to received. Other words remain unchanged, including names, technical vocabulary and regional spelling variants.

This approach performs real corrections while accepting that some errors remain. It is preferable to claiming that every unfamiliar word is incorrect. Figure 2 lists applied replacements and their frequencies. Cached suggestions avoid repeating dictionary work for recurring tokens. The correction log supports inspection and later extension of the approved list. Original text is retained throughout, allowing a reviewer to compare transformations and allowing sentiment analysis to avoid any meaning changes introduced during correction.

### Tokenization storage and reproducibility

NLTK TreebankWordTokenizer splits corrected reviews into word and punctuation tokens without requiring a downloaded sentence model. This is sufficient for the requested word tokenization. Tokens are stored with the raw and transformed review text in a local JSON Lines file. Sentence segmentation is unnecessary for the requested queries. Phrase extraction uses its own documented word sequence, because punctuation tokens should not count as words in a three-word phrase.

The structured Places, Users and Reviews tables are exported locally as CSV files. These formats are portable and sufficient for an extract of approximately twenty thousand records per table. In-memory grouping avoids unnecessary infrastructure at this scale. The pipeline reads each input once, retains identifiers for joining and produces separate outputs for each question. Derived files containing personal details are excluded from version control; aggregate results and reproducible code remain available for review.

The implementation is an end-to-end batch process rather than a production database service. A larger deployment would need indexed persistent storage, incremental ingestion, access controls and scheduled quality checks. Performance should be measured on that deployment rather than inferred from this small extract. The current program records elapsed runtime, validates output totals and preserves source hashes. These controls establish reproducibility without claiming that a pandas process alone solves every future big-data requirement.

Correctness is checked through independent reconciliation rather than visual appearance alone. Tests recompute place frequencies directly from the original Reviews file and compare every qualifying identifier with the generated answer. They also confirm that all maximum-count ties survive the name lookup. Sentiment totals must equal the text population, and operating plus closed plus unknown statuses must equal the Places population. Boundary tests cover the exact sentiment thresholds and contraction handling, where small comparison errors could otherwise change classifications.

## Task 2 Data processing results

### Places with more than three reviews

Reviews are grouped by gPlusPlaceId and group sizes provide review counts. Filtering for counts strictly greater than three returns four places, each with four reviews. The identifiers are 100515652515321866651, 102250986789579477120, 103029351909058756043 and 105590614995402411627. The output includes every qualifying identifier, even where its corresponding Places record is unavailable. Counting precedes any name lookup, preventing incomplete Places coverage from changing the answer.

The strict comparison matters because the task asks for more than three rather than at least three. Group size also counts records independently of optional columns, whereas counting non-missing reviewText would measure only written comments. The original approach dropped missing text too early and returned only three qualifying places. Keeping the full review population corrects that result. Figure 3 presents the corrected table and the related place-status and maximum-review queries.

### Operating and permanently closed places

The Places table contains 21,720 operating places and 756 permanently closed places. There are no unknown closed flags, and the totals reconcile to 22,476. Closed places therefore represent approximately 3.36 percent of this supplied Places extract. Boolean value counting directly answers the question and avoids interpreting missing information as an operating business. An explicit unknown category is retained in the output structure so future extracts can disclose incomplete flags.

These figures describe the recorded status in the dataset. They do not establish when a business closed or whether its status remains current. A closure trend would require dated status observations or additional business records. Reviews should not be used to infer closure simply because comments stop appearing: infrequent participation, incomplete extraction and other missing data could produce the same pattern. The status result should consequently be reported as a snapshot count.

### Twenty most frequent three word phrases

The phrase query uses the 11,114 five-star reviews with text. Corrected, expanded text is converted to lowercase and divided into word sequences. A sliding window produces every sequence of three consecutive words within each review. Counter aggregates occurrences, and sorting by descending frequency with alphabetical tie-breaking gives a reproducible top twenty. Windows never cross from one review into another. Figure 4 contains all twenty phrases and their computed frequencies.

Lowercasing combines variants that differ only by capitalization. Stopwords remain because removing them would change the question from consecutive words in reviews to consecutive retained keywords. The leading expressions include i have been, i highly recommend and one of the. These communicate recurring language patterns, but they do not all identify actionable business attributes. High frequency alone does not establish that a phrase explains customer satisfaction or distinguishes one business from another.

The word extraction rule treats punctuation as a separator and retains internal apostrophes. Consequently, a three-word window can span a punctuation boundary inside a review. This operational definition is stated so another analyst can reproduce the result or choose a sentence-bounded alternative. Spelling choices and contraction expansion also affect counts. The exported phrase table is therefore interpreted alongside the preprocessing rules rather than compared uncritically with counts from differently normalized text.

### IT Specialist subset

Exact filtering of the jobs column for IT Specialist returns five users. Missing jobs do not match, and unrelated roles containing similar words are excluded. This follows the task's explicit equality condition rather than expanding the population to developers, technicians or other information-technology occupations. The full subset is saved locally with the original user attributes. The public screenshot abbreviates identifiers and omits names because those details are unnecessary to demonstrate the filtering result.

Five users provide too little evidence for general claims about professional preferences. Their profiles may also be self-reported or outdated. Any later comparison of their reviews with other occupations would require a clear research question, checks for repeated users and appropriate protection of personal information. The present task establishes the requested subset without attributing collective behaviour to an occupation from such a small and potentially unrepresentative sample.

### Places receiving the largest number of reviews

The maximum review count is four, shared by the same four identifiers returned in the first query. A left merge adds available business names after counting. Identifier 102250986789579477120 matches Scott Clark Honda; names for the other three identifiers are unavailable in the supplied Places file. The output retains all ties and explicitly marks unavailable names. Reporting Scott Clark Honda as the sole winner would conceal both the tie and the incomplete lookup coverage.

The merge validates the uniqueness of place records so a duplicated lookup cannot multiply review counts. This ordering separates two different questions: which identifiers have the most reviews, and which names can be recovered from Places. The result supports a correct maximum-count answer while making the data limitation explicit. It does not show that these businesses are the most popular outside the extract, since review counts are exceptionally low and collection coverage is incomplete.

## Task 3 Sentiment analysis and evaluation

### Method and observed sentiment distribution

NLTK SentimentIntensityAnalyzer applies VADER to the 17,706 reviews containing text. It receives the original text after Unicode normalization, preserving capitalization, punctuation and negation. VADER produces a compound score summarizing polarity. Scores of at least 0.05 are classified as positive, scores of at most minus 0.05 as negative, and values between these thresholds as neutral. These are the conventional thresholds documented by the VADER project [3].

The result is 13,498 positive reviews, 1,995 neutral reviews and 2,213 negative reviews. Their shares are 76.23 percent, 11.27 percent and 12.50 percent respectively. Counts sum to the text-analysis population, and Figure 5 shows both the table and the distribution chart. The 4,061 missing-text records receive no text sentiment label. This denominator distinguishes the prevalence of positive language among written comments from the distribution of ratings across every review.

VADER is selected because it requires no model training and its scores are inspectable. NLTK examples demonstrate its treatment of emphasis, negation and emoticons [4]. Preserving these signals is important: aggressive lowercasing, punctuation removal or token deletion before scoring would discard information the model uses. Corrected text remains useful for the preprocessing requirement and phrase query, while the sentiment branch retains the more faithful original wording.

### Comparison with a rating baseline

A separate baseline maps four- and five-star ratings to positive, three stars to neutral and one or two stars to negative. This does not replace the text classifier. Comparing both labels on the same 17,706 text reviews gives 77.93 percent agreement. Ratings provide a convenient consistency check, but they are an imperfect proxy for what a comment says. A mixed review may praise staff while giving a low overall rating because of price or delays.

The comparison table makes disagreement visible. Among rating-positive reviews, VADER identifies 12,064 positive, 1,373 neutral and 490 negative texts. Among rating-negative reviews, it identifies 1,421 negative, 760 positive and 308 neutral texts. Three-star reviews produce 674 positive, 314 neutral and 302 negative classifications. These patterns justify reviewing disagreement cases before business action. Agreement must not be presented as measured predictive accuracy because no independent human-labelled reference set was created.

Neutral VADER output also needs careful interpretation. It can describe factual language or an absence of recognized sentiment words, rather than a customer's deliberately balanced opinion. Non-English reviews occur in the data, and an English-oriented lexicon may miss their meaning. Sarcasm, domain-specific language, spelling errors and multiple experiences within one review remain limitations. The numerical distribution is therefore a model result for this extract, with uncertainty that cannot be reduced to a validated accuracy claim.

### Systematic comparison with alternative techniques

Rating rules have minimal computational cost and clear explanations, but measure the selected star category rather than textual sentiment. They remain useful where text is missing and as a baseline, provided those outputs are labelled separately. VADER adds language-based evidence without requiring a labelled training corpus. Its limitations are lexicon coverage, context and language support. The choice suits an initial reproducible analysis, while retaining review-level scores for checking borderline cases.

A supervised Naive Bayes classifier could learn associations between tokens and sentiment from labelled reviews. A linear support-vector machine using term-frequency features offers another conventional approach. Both would require a labelled training set, a held-out evaluation and controls against leakage from repeated users or highly similar texts. Their potential advantage is adaptation to business-review vocabulary. Neither should be described as superior on this dataset without conducting a fair comparison on the same independent test population.

A transformer-based classifier could represent broader linguistic context and use an appropriate multilingual model. It would add model-download, inference and version-management requirements, and could still misinterpret sarcasm or domain-specific phrasing. A future evaluation should compare macro F1 and class-level precision and recall, alongside inference time and disagreement examples. Human annotation should include ambiguous cases and language categories so apparent improvements are not driven only by the majority positive class.

An annotation exercise should select reviews across rating categories, model labels and languages rather than sampling only common positive examples. Two reviewers could label each selected text independently and discuss disagreements using a written definition of sentiment. A held-out portion should remain untouched while thresholds or preprocessing rules are adjusted. Reporting reviewer agreement would expose uncertainty in the reference labels themselves. This proposed procedure would permit a meaningful accuracy estimate; the current comparison with star ratings provides only an initial diagnostic.

## Task 4 Business strategy and responsible data collection

### Using the findings to improve business operations

Location owners should treat the sentiment distribution as an initial screening measure. The 12.50 percent negative share warrants inspection, but the dataset does not establish which operational problem caused those comments. Review text should first be grouped into observable issues such as waiting time, staff interaction or product quality through manual checking or a separately evaluated topic method. The phrase ranking provides starting points for reading, rather than proof that a particular improvement will increase satisfaction.

Business-level decisions need a stronger evidence base. No place reaches ten text reviews, so an alert threshold of ten would currently exclude every location. Owners should collect a longer observation period and display review counts beside sentiment percentages. A single negative review among a few comments should prompt a response and investigation, without being treated as a stable estimate of business quality. Missing business names must also be resolved before assigning results to operating teams.

A practical pilot would appoint a manager to review a sample of negative and disagreement cases weekly. Verified complaints could become a short improvement register with an owner, action date and outcome measure. For a confirmed waiting-time problem, the action might be a staffing adjustment, with waiting times and subsequent feedback monitored. This is a proposed example, not a complaint pattern established by the current aggregate analysis. Staff should retain responsibility for interpreting comments and deciding proportionate responses.

Changes should be assessed against a baseline period with adequate review volume. Useful measures include complaint recurrence, response time and sentiment distribution, supported by operational records. Changes in customer mix, seasonality or review volume can affect those measures, so a sentiment increase alone does not demonstrate causation. Where feasible, compare similar periods or pilot the change at comparable locations. Report uncertain outcomes honestly and retain examples that explain why a numerical measure changed.

Positive feedback can inform service standards and show which experiences customers appreciate after the underlying comments are checked. Businesses should request feedback consistently rather than selecting only satisfied customers or rewarding positive sentiment. Personal replies should avoid disclosing private details. A dashboard should present aggregated counts, dates, missingness and model limitations. Automatic sanctions against employees or targeted offers to identifiable reviewers would be disproportionate to the reliability and coverage of this analysis.

### Ethical risks of expanded advertising collection

Collecting detailed preferences and behaviour would change the sensitivity and purpose of the dataset. Combining review activity with residence, employment and location history could reveal routines or allow sensitive inferences. Publicly visible comments do not remove the need to consider privacy, expectations and a lawful basis for subsequent processing. People may accept publishing a review while objecting to having it combined with other records to predict private interests for advertising.

Where GDPR applies, the programme should define purposes and a lawful basis, minimize collection, limit retention and support transparency and individual rights. Relevant provisions include Articles 5 and 6, information duties in Articles 13 and 14, access and erasure rights, the direct-marketing objection in Article 21, and safeguards in Articles 25, 32 and 35 [5]. These requirements should be assessed for the actual proposed processing; a generic acceptance prompt does not establish compliance for every use.

An ethical design should make optional advertising collection understandable and separately controllable. Explanations should identify the data collected, intended uses, recipients and retention periods in ordinary language. Controls should allow people to change preferences without losing unrelated review functions. If consent is the selected lawful basis, its withdrawal should be practical. The team should record decisions and test whether people understand them, rather than treating a lengthy privacy notice as evidence of informed participation.

Collection should begin with coarse, necessary signals rather than precise movement histories. Sensitive attributes and inferred vulnerabilities should be excluded from advertising profiles unless an independently reviewed justification and appropriate legal conditions exist. Pseudonymous identifiers can reduce routine exposure, but linked behavioural records may remain identifiable. Access to linking information should therefore be restricted, and published research should use aggregated results with thresholds that reduce the chance of exposing a person's activities.

The proposed safeguards include role-based access, encryption during transfer and storage, retention schedules and deletion processes that cover derived profiles. Access logs and incident procedures should support investigation of misuse. Data-sharing partners should receive only fields necessary for an agreed purpose. Before expansion, a privacy impact assessment should examine profiling risks and alternatives, with documented responsibility for remediation. Security testing should include attempts to reconnect supposedly anonymous profiles to identifiable individuals.

Responsibility should be assigned before collection begins. A data owner should approve each requested field and document its operational purpose. A privacy lead should review retention and sharing, while an analytical lead should check whether predictions are sufficiently reliable for the intended use. Regular reviews should remove unused attributes and verify that withdrawal and correction requests propagate to downstream datasets. These operational checks make safeguards measurable rather than leaving them as statements in a policy document.

Fairness checks should examine whether language, geography or occupation produces unequal treatment. This dataset already demonstrates incomplete profile fields and weak business coverage, making confident personal targeting difficult to justify. Review sentiment should not become an unverified label of an individual's personality or economic circumstances. Users need a clear route to challenge mistaken profiles, and advertising decisions should be monitored for harmful exclusions or exploitative targeting of vulnerable groups.

Trust depends on demonstrable limits as well as useful services. A staged rollout should require evidence that collection is necessary, controls work and outcomes can be audited. The team should publish understandable explanations of changes and respond to complaints with corrections where warranted. For this assignment, preserving source records, reporting missing relationships and avoiding unnecessary public copies of personal data follow the same principle: analytical usefulness depends on both accurate evidence and accountable handling of the people represented.

## References

[1] NCC Education, Introduction to Data Science and Big Data, Google Local Research Team assignment brief and Google Local Dataset additional material, Autumn 2024 to Summer 2025, supplied course documents.

[2] pandas development team, pandas.read_csv API documentation, https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html, accessed 25 October 2026.

[3] C. J. Hutto and E. Gilbert, VADER Sentiment Analysis project documentation and classification thresholds, https://github.com/cjhutto/vaderSentiment, accessed 25 October 2026.

[4] NLTK Project, Sample usage for sentiment, https://www.nltk.org/howto/sentiment.html, accessed 25 October 2026.

[5] European Parliament and Council, Regulation EU 2016/679, General Data Protection Regulation, https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng/, accessed 25 October 2026.
