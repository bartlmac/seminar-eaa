---
name: implement-calculator
description: Implement the approved single endowment calculator specification as a standalone Python API with its own models and data, without a GUI.
---

# Implement the calculator

Read README.md, the current `specification/calculation.md`, decisions, validated
extract and ontology/tbox.py. Implementation requires resolved material rules.
Report specific gaps; do not invent business decisions while coding.

Write under `calculator/` and add relevant run tests under
`test_reports/run_tests/`:

- `api.py`: `calculate(policy, assumptions) -> Result` and `CalculationError`.
  Validate the complete request again, even for mutated model instances.
- `models.py`: copy the maintained T-Box models with origin and schema agreement.
  Keep the runtime copy independent of seminar imports and data access.
- `engine.py`: all specified calculation paths, scalars and yearly fields.
  A single engine module is enough. No mutable cross-call cache or input mutation.
- Own complete mortality CSV, tariff/start JSON and integrity-aware loader,
  generated reproducibly from the validated current text export. Do not use
  expected outputs as calculation inputs or modify independent reference values.
- Own package/dependency files and installation/start README. The core imports
  no GUI framework and works without GUI dependencies.

Start with a complete specified case and test affected behavior directly. Use
the current run references under `derived/references/` and add meaningful
independent transition/error checks. Reference preparation is explicit step 4,
not an automatic side effect of implementation or tests.
Do not weaken tolerances or hide mismatches. Reuse valid same-run evidence;
report tested scope, failures and outstanding work.

Do not create a GUI before its step. Isolated installation is required at final
delivery, not as an extra mandatory loop during implementation.
