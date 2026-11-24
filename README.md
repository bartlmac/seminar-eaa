# From Excel to Python: a three-hour endowment insurance workshop

Port the supplied **endowment life insurance calculator (KLV)** to Python with an
AI coding assistant. Work in English throughout: discussion, evidence, decisions,
code, tests, reports and the final interface.

The only source workbook is [`sources/Tariff_Calculator.xlsm`](sources/Tariff_Calculator.xlsm).
The starting kit contains a domain contract, local export/check tools,
tutor-provided reference workbooks and focused skills. It deliberately contains no
completed extraction, specification, Python calculation engine or GUI.

The aim is a small, traceable application: a direct Python API, a Streamlit
interface and a complete yearly CSV export. Keep the calculation separate from
the interface. A single `calculator/engine.py` is sufficient; no product routing,
web service or elaborate framework is needed.

## Before the workshop

Follow the [Windows/WSL and Linux setup guide](SETUP.md) for VS Code, Python 3.11,
the virtual environment, dependencies and Codex or Claude Code sign-in.

The tutor prepares Linux, CPython 3.11, the coding assistant and the environment.
Installation time is outside the three-hour teaching slot. No Excel installation
is needed to export supplied workbooks and read their saved results. Producing
new Excel expectations requires Excel with working VBA, recalculation and saving.

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt -r requirements-gui.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps .
.venv/bin/python -m pytest tests/foundation -q
```

The assistant starts by reading this file, `AGENTS.md` and `seminar.json`.
Do not run the entire workshop from a request for one step. Participants can
request and complete each step themselves and make the business decisions needed
for the next one. In the video seminar, the tutor calls the next step when
everyone is ready.

## Workshop schedule — 180 minutes

| Step | Time | Example request and result |
|---|---:|---|
| 1. Export Excel | 10 min | “Export the supplied workbook as text and inspect the manifest.” Result: `derived/excel/`. |
| 2. Extract domain knowledge | 30 min | “Use $extract-knowledge for the exported workbook.” Result: evidenced `derived/knowledge.json` and its HTML reading copy. |
| 3. Specify the port | 25 min | “Use $specify-port to describe all calculation paths and flag decisions for participants to make.” Result: `specification/calculation.md`, including decisions and test needs. |
| 4. Prepare reference cases | 10 min | “Export the current reference workbooks and generate reference data for this run; explain provenance and tolerances.” Result: `derived/references/`. |
| 5. Implement the engine | 45 min | “Use $implement-calculator to implement the approved specification, direct API and standalone package.” Result: `calculator/`, targeted API checks. |
| 6. Test results | 25 min | “Use $test-calculator to compare the current reference cases and add independent boundary and error tests.” Result: honest findings under `test_reports/`. |
| 7. Add the interface and deliver | 25 min | “Use $developing-with-streamlit to add a simple English interface, full CSV download and verify standalone delivery.” Result: working GUI and isolated delivery check. |
| 8. Reflect | 10 min | “Explain what was demonstrated, what differs from Excel and what remains untested.” |

These are timeboxes, not a guarantee of full actuarial correctness. Discuss
blockers as soon as they appear. Prefer a compact calculation specification and
few informative tests over extra architecture or repeated reports. Record any
unfinished scope explicitly; do not silently drop outputs or boundary checks to
meet the clock. Optional numerical investigations and additional Excel scenarios
can follow after the workshop.

## Commands

Run commands from the project root. Tools are local and deterministic; they do
not contact a model provider or execute VBA.

```sh
# Step 1: the output directory must be empty
.venv/bin/python -m tools export --input sources/Tariff_Calculator.xlsm --out-dir derived/excel --strict

# Step 2: check the extraction, then create its offline reading copy
.venv/bin/python -m tools check
.venv/bin/python -m tools report

# Step 4: export all current reference workbooks and copy their saved results
.venv/bin/python -m tests.reference

# Any time: inspect the command options
.venv/bin/python -m tools --help

# Step 6: all saved scalar and trajectory values; -s shows verbose output
.venv/bin/python -m pytest tests/calculator/test_excel.py -q -s --excel-verbose

# Step 7, after implementation
.venv/bin/python -m streamlit run calculator/gui/app.py
```

Commands return JSON and exit with 0 for success, 1 for processing failure or 2
for invalid arguments. Missing exercise artifacts are errors for `check` and
`report`. If report validation fails, an older report may remain; the command
reports this and the assistant must flag it as stale.

The export contains cell CSVs (`Sheet;Address;Formula;Value`), defined names,
VBA text, workbook structure, chart/drawing definitions and a SHA-256 manifest.
Source formulas and identifiers remain verbatim. Values are the **saved Excel
cache**, not fresh calculations. The exporter never modifies the workbook.
Use the text artifacts for all agentic domain analysis, not the binary workbook.
The supplied workbook has no charts; its empty chart export is still recorded.

## Evidence and handover

The maintained T-Box is [`ontology/tbox.py`](ontology/tbox.py). Its
[field catalogue](ontology/fields.md), JSON Schema and
[extraction schema](ontology/extraction.schema.json) are prepared equipment.
Only an explicitly requested equipment change may alter them. When authorized,
regenerate them with `.venv/bin/python -m tools schema`; do not edit generated
schemas independently.

Extraction maps every required `(quantity, role)` pair to exact source locations.
Include source formulas, LaTeX, symbols, conditions, timing, helper calculations,
VBA evidence, table bindings and open questions. Table values stay in the export.
Formula families may use one template and a range; every cell is checked by
relative formula translation. Treat initial, final and exceptional rows separately.

`tools check` validates schema, source/artifact hashes, field coverage, evidence
locations, original formulas and declared families. Named/VBA locations are
reported for manual review. It does **not** prove that LaTeX, VBA interpretation or
business conclusions are correct. The HTML report is a compact offline reading
copy with open questions first, grouped formulas, expandable evidence and rendered
LaTeX. Adjacent progression ranges with matching relative formulas are shown as
one worksheet family; differing conditions and timing remain available separately.
Mathematical notation is distinguished from literal VBA calls, whose exported
declarations are listed alongside each formula group. Each formula shows only
its own symbols, with explicit quantity/helper/VBA links. A single formula key
uses blue for known quantities, red for “Calculated using VBA” and green for
mathematical helpers/local notation; categories are also named in the symbol table.
Conditions and timing follow structural formulas (for example `j < t`), never
phase boundaries inferred from saved example inputs. The single HTML file bundles KaTeX (license included) and works offline
in a current Firefox, Edge or Chrome browser using native MathML. JavaScript
enables rendering; original LaTeX remains available in expandable details.
Review it together during the seminar.

Before implementation, trace each of the four scalar outputs and all twelve
trajectory fields back through formulas, VBA and tables. Specify order, loops,
lookup keys, rounding, zero denominators, missing data, time axis and errors.
Keep source findings, proposed target behavior and participant decisions distinct.
Resolve material business questions in the current specification. No decisions
or solutions from an earlier run are valid inputs.

## Target application contract

Step 5 provides the following public interface:

```python
from calculator.api import calculate, CalculationError
from calculator.models import Policy, Assumptions, Result

# calculate(policy: Policy, assumptions: Assumptions) -> Result
```

Copy the maintained domain models into `calculator/models.py` with documented
origin and matching schemas; do not create a second independently maintained
business model. The API validates the complete request, including mutated model
instances, and raises `CalculationError` for invalid or undefined calculations.
Return all four scalars and every specified yearly state. Calls must not mutate
inputs or share mutable calculation state.

The target constraints include positive integer terms, `premium_term <= term`,
`flex_years <= term`, nonnegative sum insured **including zero**, M/F table
selection, payment frequencies 1/2/4/12, mortality probabilities in [0,1] and
finite floating point values. Additional calculation rules are determined from
the current source and specification, not from the old exercise or example data.

Deliver complete required mortality data as CSV and tariff/start inputs as JSON.
Generate these from the validated current text export, not from expected output
values. Record provenance and check delivered data integrity when loading it.
The application uses only its own files and documented third-party dependencies;
no runtime imports, symlinks or file access to `ontology/`, `tools/`, `tests/`,
`derived/`, `specification/` or another repository. The core must work without
Streamlit or pandas. Add a package definition, dependency files and its own
installation/start README under `calculator/`.

Step 7 adds a small native Streamlit page: editable policy and tariff values,
**Calculate**, four metrics, the full yearly table and **Download CSV**.
Use explicit submission, English errors without tracebacks, and reject invalid
inputs visibly. New input values must not leave an old result or download looking
current. Monetary display has two decimal places, other decimal output seven;
indices are integers. API values and CSV retain their full precision. Categories
use selection widgets. Use increment/decrement controls only for integer fields
such as years. Enter decimal rates and euro amounts directly in text fields,
without step controls; validate their numeric content through the API.
An advanced mortality-table editor and custom styling are outside the timebox.

At delivery, copy **only `calculator/`** into a temporary directory, install it in
a separate environment from its own instructions and test the API and GUI there.
Keep independent expectations in the external test driver. A whole-project install
is not an isolation proof. Document the result under `test_reports/`; a successful
installation and a successful numerical comparison are separate claims.

## Tests and reference limits

See [`tests/README.md`](tests/README.md). Permanent Excel workbooks live under
`tests/reference_workbooks/`. The tutor may revise, remove or add `KLV-*.xlsm`
cases before reference preparation, including during the seminar. There is no
fixed case count or hard-coded requirement to keep the original baseline inputs.
Recalculate changed workbooks in Excel with functioning VBA and save the results.

In step 4, `python -m tests.reference` exports all current workbooks and copies
saved inputs, assumptions and expected results into `derived/references/`.
This is a run step, not prepared output or an automatic test side effect.
All four scalars and all twelve fields for years 0 through each case's policy
term are compared. Source hashes, export integrity and the current workbook
inventory are checked independently of the target calculator.

Changed workbooks, added/removed cases or corrupted artifacts invalidate the
snapshot and dependent results. Explicitly clear only `derived/references/` and
repeat step 4 to rebuild it. Existing snapshots are never silently overwritten.
A failed generation publishes no partial snapshot. Tests explain a missing run;
a present but stale or damaged run fails validation. A fresh workshop/reset has
no generated reference exports or reference JSON data.

Use independent hand-derived cases and the specified error behavior to cover
zero sum insured, premium cessation, maturity, flex limits, missing table keys,
invalid inputs and repeated calls. Explain assumptions behind each expectation.
Additional Excel cases need recalculation with functioning VBA, a fresh export
and documented provenance. Never manufacture expectations using the target code,
relax tolerances to hide differences or replace expected values with target output. Tutor revisions to the Excel
references instead require a fresh export and new independent provenance.

Run tests affected by a change; reuse valid evidence from the same workshop run.
A step change or writing a report is not a reason to repeat everything. Explicitly
requested test runs still run. Missing API/GUI modules produce explained skips;
errors in existing implementations must fail. Before a requested commit run the
complete suite, including any current `test_reports/run_tests/`. No push without
an explicit request. Tests write only to temporary directories.

## Working areas and restart

| Directory | Purpose |
|---|---|
| `sources/` | The English Excel source |
| `ontology/` | Prepared domain and extraction contracts |
| `tools/` | Prepared export, evidence validation and report tools |
| `.agents/skills/`, `.claude/skills/` | Matching English workflow skills |
| `tests/` | Prepared test code and permanent reference workbooks |
| `derived/` | Current source export, knowledge extract, reading copy and reference snapshot |
| `specification/` | Current calculation specification and participant decisions |
| `calculator/` | Application created during the workshop |
| `test_reports/` | Current evidence and `run_tests/` |

A requested step authorizes its output directory; announce planned writes and
report actual changes. Prepared equipment and root configuration need a specific
equipment-change request. A reference being readable does not permit overwriting
it. No fallback solutions or hidden dependencies on the longer seminar.

A restart requires an explicit request. Clear `derived/`, `specification/`,
`test_reports/` and all generated contents of `calculator/`, preserving their
directories. Keep all prepared equipment, reference workbooks and environment files.
Generated reference exports and data under `derived/references/` are cleared.
A reset ends there; request the next step separately.
