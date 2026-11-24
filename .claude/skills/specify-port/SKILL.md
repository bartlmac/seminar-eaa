---
name: specify-port
description: Specify the single endowment calculator from the validated extract and current text export; identify participant decisions without implementing it.
---

# Specify the port

Read README.md, seminar.json, the current extract, its referenced text artifacts
and ontology/tbox.py. Confirm the extract with `python -m tools check`, or reuse
a valid same-run check. Do not use binary Excel or an earlier solution.

Write one compact `specification/calculation.md`:

1. Identify the source hash, extract and model version.
2. Trace every scalar and trajectory field through worksheet formulas, defined
   names, VBA helpers and tables. Give stable rule IDs, exact source evidence,
   computation order, loops, keys, timing and output bindings.
3. Describe initialization, premium cessation, maturity, flex conditions,
   zero denominators, rounding and missing data. Trace VBA bodies, not just calls.
4. Separate source findings, proposed target choices and current participant decisions.
   For material unresolved choices present alternatives and consequences; obtain
   the participants’ decisions before dependent implementation. Do not assume an old rule.
5. Plan a small `calculator/` with models, engine, API, own data and separate GUI.
   Use `calculate(policy, assumptions)` and `CalculationError`. Plan reproducible
   data transfer and isolated delivery according to README.
6. Map each output/rule to an independent test or an explicit missing proof.
   Reference workbooks are prepared in step 4 for the current run; their inputs
   and count may change. A finite reference set does not cover all parameters.

Mark incomplete/blocking paths. Keep decisions in this specification, without
rewriting prepared equipment or implementing code. No extra architecture document
is required unless it makes the calculation easier to review.
