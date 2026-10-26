# fincheck: catching and undoing extraction errors in financial statements with accounting identities

Financial Datasets sells "accurate, auditable financial data for agents" and claims "99.9%+ verified accuracy" across 27,530 stocks (https://www.financialdatasets.ai/). Statements pulled from filings are tied together by identities that must hold: gross profit = revenue - cost of sales, the balance sheet balances, the cash flow adds up and ties to the balance sheet's cash, the four quarters add up to the year. A single wrong number (a thousands-vs-millions slip, a flipped sign, two digits swapped) breaks at least one identity. This prototype checks the identities, then searches for the one-line repair that makes all of them hold again.

## What it does
`fincheck/stmt.py`: a company-year (FY and Q1 to Q4) with income statement, cash flow, FY balance sheet, EPS and shares, and 48 identities (statement chains, A = L + E, cash tie, quarters sum to FY, EPS x shares ~ net income). `fincheck/repair.py`: for the lines inside violated identities, try x1000, /1000, sign flip, adjacent digit swap and copying another line's value; keep repairs after which every identity holds (specific repairs first, then "the value the identity implies" as a last resort). Output: nothing, or the repair(s), or `UNRESOLVED`.

## Results (generated company-years, one planted error each, about 2/7 clean)
Dev: seeds 0-699 (5 error kinds). Held-out: seeds 10000-10699 with two new kinds, `TAG_SWAP` (the values of two expense lines swapped) and `SHARES_UNIT` (shares in thousands vs units); fixed in git before the first run. Baseline: a schema check (all values present and integers, revenue and total assets positive).

| Held-out | n | flagged by identities | repaired to the true value | repair unique | schema check flags |
|---|---|---|---|---|---|
| SCALE (x1000) | 89 | 89 | 89 | 88 | 0 |
| SIGN | 76 | 76 | 76 | 75 | 1 |
| DIGIT_SWAP | 60 | 60 | 60 | 56 | 0 |
| DUPLICATE_ROW | 72 | 72 | 72 | 67 | 0 |
| VALUE_TYPO | 70 | 70 | 70 | 66 | 0 |
| SHARES_UNIT (new) | 86 | 86 | 86 | 63 | 0 |
| TAG_SWAP (new) | 88 | 88 | **0** (all `UNRESOLVED`) | - | 0 |
| clean | 157 | 0 flagged | - | - | 0 |

Dev: 511 planted errors, all flagged, all repaired to the true value (unique for 492), 0 of 183 clean flagged; the schema check flagged 3.
- The identities catch every single-number error here, and a one-line repair restores the exact value in every case except swapped tags, which a single-line repair cannot explain: the checker says `UNRESOLVED` instead of guessing.
- "Unique" is lower than "correct" because some errors have more than one repair that satisfies all identities (an implied value for a line can coincide with a scale or sign fix); the checker returns all of them and a person or a second source decides.

## Read this before believing the table
Synthetic, internally consistent statements where every number sits in some identity, so any single change is detectable. Real filings have line items outside any identity (segment data, KPIs, per-share data with restated shares), taxonomy differences between companies, restatements, and errors that preserve every identity (a number wrong in two places consistently, or a wrong period for a whole statement). Detection by identities is a floor on data quality, not a measure of "99.9% accuracy". Nothing here uses Financial Datasets data or its API.

## Run it (3 commands)
```
pip install pytest
python -m pytest -q tests
python -m fincheck.run
```
Standard library only. 4 tests.

Unofficial prototype by Kushagra Pratap Singh. Not affiliated with Financial Datasets.
