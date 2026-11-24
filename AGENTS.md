# Workshop working rules

Read `README.md` and `seminar.json` first. This is a three-hour English workshop
porting the single workbook `sources/Tariff_Calculator.xlsm`.

- Use English in all new conversation, documentation, identifiers and UI text.
- Follow the README workflow and execute only the requested step. Participants
  may request steps themselves; the tutor coordinates the group during the video seminar.
  Do not pre-build the solution while preparing, exporting or specifying.
- Domain analysis reads registered text exports only. The deterministic exporter
  may read the binary workbook. Never execute VBA or claim an export recalculated Excel.
- Use the local skills `extract-knowledge`, `specify-port`, `implement-calculator`,
  `test-calculator` and, for GUI work, `developing-with-streamlit`.
- Keep one direct API `calculate(policy, assumptions)` and separate engine/GUI.
  Use the prepared T-Box from `ontology/tbox.py`; no business-model extensions
  without a specific equipment-change request. Generate schemas from Python.
- Announce planned writes/deletions before editing and report actual scope.
  Step outputs go to `derived/`, `specification/`, `calculator/` or `test_reports/`.
  Prepared sources, tools, ontology, tests, skills and root files need a specific
  equipment-change request. Do not infer write access from readable inputs.
- Store source-backed findings, unresolved questions and current participant decisions
  separately. Put decisions in `specification/`, never in prepared equipment.
  Earlier runs, archived solutions and previous conversation are not evidence.
- Finish extraction with `python -m tools report`; report validation errors and
  any older report that remains. Structural checks do not prove business correctness.
- Reference workbooks under `tests/reference_workbooks/` are permanent equipment,
  not fallback knowledge extracts. The tutor may revise/remove/add cases during
  the seminar. Step 4 explicitly generates `derived/references/`; tests never
  generate or refresh reference data. Revisions need Excel recalculation, saving
  and a fresh reference snapshot. Reject stale snapshots; preserve tolerances and
  never replace expectations with target calculator output.
- The delivered `calculator/` must contain its own models, complete required data,
  package definition and start instructions. No runtime seminar imports/files,
  symlinks, external repository dependencies or model/provider calls in tools.
  At final delivery prove installation with only an isolated copy of `calculator/`.
- Run targeted checks for changes; reuse valid same-run evidence. Missing API/GUI
  yields an explained skip, broken existing code fails. Run the complete suite
  before a requested commit, including `test_reports/run_tests/` if present.
  Tests write only to temporary directories. Do not push without a request.
- Reset only on explicit instruction: clear run artifacts in `derived/`,
  `specification/`, `test_reports/` and `calculator/`, keep their directories and
  all prepared equipment. Reset does not start the next workflow step.
