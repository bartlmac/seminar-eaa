# Permanent Excel reference workbooks

Store the tutor-controlled Excel files here, using names such as
`KLV-001.xlsm` through `KLV-010.xlsm`. Additional cases such as `KLV-011.xlsm`
are supported; neither the case count nor the input settings are fixed.

The tutor may replace, remove or add workbooks before reference preparation,
including during the seminar. Keep `.xlsm` format, recalculate changed cases in
Excel with VBA enabled and save their result values. Do not adjust independent
references to hide an implementation error.

These originals survive workshop resets. The extraction source remains
`sources/Tariff_Calculator.xlsm`; reference workbooks are for testing.

In workshop step 4 run from the project root:

```sh
.venv/bin/python -m tests.reference
```

This explicitly exports every current case and builds its reference data under
`derived/references/`. Nothing is generated merely by putting workbooks here.
After revising the set, explicitly clear that generated snapshot and repeat
step 4. Tests reject stale snapshots; they do not silently refresh them.
See [the test guide](../README.md) for commands and provenance checks.
