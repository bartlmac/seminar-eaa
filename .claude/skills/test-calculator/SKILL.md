---
name: test-calculator
description: Test endowment calculator results through the public API using saved Excel expectations and independent hand-derived boundary and error cases.
---

# Test the calculator

Read README.md, tests/README.md, the current specification and public API.
Review same-run evidence first; a step change alone does not require repetition.
Use text exports for source questions. Do not implement missing production code
in a pure test task.

Compare all cases in the current `derived/references/` snapshot when no valid
matching proof exists. Step 4 explicitly exports current `KLV-*.xlsm` workbooks
with `python -m tests.reference`. Missing preparation must be reported; tests
never generate or refresh references as a side effect. Changed, added or removed
workbooks invalidate the snapshot and dependent proofs. The tutor may revise
references, then explicitly clear/rebuild the snapshot with fresh provenance. Add missing specification tests under `test_reports/run_tests/` using
`calculate(policy, assumptions)`, not private calculation helpers or GUI output.

Cover relevant premium/maturity/flex transitions, zero sum insured, table access,
invalid requests, finite results and repeated independent calls. Hand-derived
expectations must explain their assumptions and derivation. New Excel cases need
working VBA, recalculation, saving and export; tools never recalculate Excel.

Keep independent expectations and absolute tolerances unchanged. Compare every
scalar and trajectory field at the correct year, including shape and indices.
NaN/infinity and missing values fail. Diagnose the first mismatch with expected,
actual, absolute difference, tolerance, rule and source. Never mark a known
mismatch passed or replace its expectation with the target's output.

Write a short report under `test_reports/` identifying state, commands, new and
reused proofs, skips, failures, coverage and limitations. A single cache case is
not general correctness or business approval. At final delivery verify only an
isolated copy of `calculator/` from its own install/start instructions, with
independent expectations in an external driver. Keep numerical results,
installation and GUI evidence separate.
