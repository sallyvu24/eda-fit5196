# Group005 A1 historical data

Parse the JSON and XML with structured parsers, reconcile source overlap using
stable entity keys, and create the six tables in `public_data_dictionary.csv`.
Raw dates, booleans, currency and names use the published alternatives shown by
the files.

Regex is assessed only in bounded narrative fields. Remove HTML tags, the
markers `[SYSTEM]`, `[CATALOGUE]` and `[VERIFIED_PURCHASE]`, URLs and repeated
whitespace. Extract order references
matching `[HC]ORD` plus six digits, product SKUs matching `SKU-` plus letters or
digits, and promotional codes matching `B[1-5]SAVE-` plus two digits.

Preserve the lower-case multilingual review in `review_body_clean`. Create
`review_body_latin_analysis` separately by retaining Latin-script letters,
including European diacritics. Remove emoji from both cleaned outputs and use
the literal `NaN` for prescribed missing values.

Do not infer clean row counts from this README. Validate primary keys, foreign
keys, arithmetic, source coverage and temporal relationships in your own work.
