# Prepared tests and run-specific reference data

## Reference preparation — workshop step 4

Keep Excel workbooks in [`reference_workbooks/`](reference_workbooks/).
The tutor may change or remove existing cases and add new ones during the
seminar. Use `KLV-001.xlsm`, `KLV-002.xlsm`, etc.; the number is not fixed.
Recalculate changed inputs/parameters in Excel with VBA enabled and save.
The tools copy saved values; they never recalculate Excel or execute VBA.

From the project root, explicitly prepare the current set:

```sh
.venv/bin/python -m tests.reference
```

Paths are configured in `seminar.json`. The command discovers all current
`KLV-*.xlsm` files and creates this run's snapshot:

```text
derived/references/
  index.json
  exports/KLV-001/manifest.json   # Plus cell CSVs, VBA and other text artifacts
  data/KLV-001.json              # Inputs, assumptions, saved results and hashes
  ...                           # One export and data file per current case
```

Generation validates all cases before publishing the snapshot. Existing nonempty
snapshots are not overwritten. To rebuild after changing, adding or removing
workbooks, explicitly clear **only `derived/references/`**, then repeat the command.
Previous result proofs depending on those references must be renewed as needed.
A workshop reset clears this snapshot and keeps the workbook originals.

Tests never export or refresh references automatically. Missing preparation gets
an explained skip; stale, incomplete or corrupted snapshots fail. Integrity checks
bind every reference to its workbook, manifest, exported values and T-Box version.
A changed case inventory also invalidates the snapshot. Workbook data, not a fixed
case plan or old baseline values, determines the current reference set.

## Running checks

```sh
# General tools and model constraints work before reference preparation
.venv/bin/python -m pytest tests/foundation -q -rs

# Entire prepared suite
.venv/bin/python -m pytest -q -rs

# All current Excel reference cases after steps 4 and 5
.venv/bin/python -m pytest tests/calculator/test_excel.py -q -s --excel-verbose

# Select a current case by ID
.venv/bin/python -m pytest tests/calculator/test_excel.py -q -s -k KLV-008 --excel-verbose

# Full current run, once participant run tests exist
.venv/bin/python -m pytest tests test_reports/run_tests -q -rs
```

A bare `pytest` selects `tests/`, not participant additions. Missing API/GUI files
produce explained module skips. Errors in existing code fail.

| Area | Purpose |
|---|---|
| `foundation/` | General tools, model constraints, schemas and reference lifecycle/integrity |
| `calculator/` | Public API, runtime model agreement, isolated calls, revalidation and every current Excel case |
| `gui/` | Page smoke test: Calculate, four metrics, table and CSV control |
| `reference_workbooks/` | Permanent tutor-controlled Excel references; preserved on reset |
| `reference.py` | Source-specific cell bindings, explicit export command and read-only reference loader; no tariff arithmetic |
| `tolerances.py` | Absolute tolerances: EUR 1e-8, other floats 1e-10; integers exact |
| `../derived/references/` | Generated exports, expected values and inventory for the current run; cleared on reset |

With `-s --excel-verbose`, each case prints an aligned table with separate year,
field, source cell, Excel value, Python value, absolute difference, tolerance and
status columns. Numeric values retain their round-trip precision; integer
comparisons show `exact` as their tolerance. Failure output uses the same columns.

Each result comparison includes four scalars and all twelve trajectory fields
from year 0 through the policy term. Reference preparation itself verifies saved
values and provenance; it does not prove fresh Excel recalculation or numerical
agreement with the target. Do not replace independent expectations with target
output or change tolerances to hide differences.

Add current-specification hand cases, transitions, errors, package checks, GUI
state/CSV checks and isolated delivery drivers under `test_reports/run_tests/`.
The prepared GUI smoke test does not prove complete binding or CSV accuracy.
Excel reference cases do not establish correctness for all possible inputs.

Tests write only to temporary directories. Lifecycle tests use synthetic
workbooks; an additional integration check exports the currently provided
workbooks into a temporary directory, never into the real run snapshot.
Reuse valid same-run evidence; rerun after relevant changes or explicit requests.
