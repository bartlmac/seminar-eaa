---
name: developing-with-streamlit
description: Build, edit and test the workshop's native Streamlit calculator interface after its public Python API is implemented.
---

# Build the Streamlit interface

Follow README.md step 7 and the current specification. Read the local
[API reference](references/api-reference.md), [testing guide](references/testing.md)
and [session state guide](references/session-state.md) as needed. Query the
installed API with `.venv/bin/streamlit docs st.<command>` rather than guessing
widget arguments. The prepared environment has the workshop's pinned version.

Use a single English page at `calculator/gui/app.py`, native widgets and a form
with **Calculate**. Bind all policy/tariff fields to the public API. Keep a clear
validation message, four `st.metric` outputs, the complete yearly dataframe and
`st.download_button` labelled **Download CSV**. No calculation rules in the GUI,
product selector, custom components, CSS, advanced table editor or web framework.

Use increment/decrement (step) controls only for integer fields such as years.
Decimal rates and euro amounts use direct text entry without step controls;
preserve the entered precision and pass numeric validation through the public
models/API on Calculate. Invalid or empty numeric text must show an English
error, never a traceback or stale result. This is a permanent workshop rule.

Keep the last successful request/result explicit. An edited request must not
present old results or CSV as current. Preserve decimal input precision and API
values; display EUR with two decimal places, other decimals with seven and indices
as integers. CSV includes all trajectory fields and full numeric precision.

Run `tests/gui` and add run-dependent checks for data binding, errors, stale
results and full CSV content under `test_reports/run_tests/`. Use `AppTest` for
repeatable widget interactions and also start the real application to verify
startup and a real download; automated page checks alone do not prove delivery.
Complete the README isolated-copy install/start check, including the API, then
report commands and actual results. Do not claim a browser/HTTP check was run
unless it was. Add the target's own install and start instructions.
