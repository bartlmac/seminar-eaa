---
name: extract-knowledge
description: Extract source-backed knowledge from the English endowment Excel text export into the prepared T-Box, then validate and report it.
---

# Extract knowledge

Read README.md, seminar.json, ontology/tbox.py and ontology/knowledge.py. Use
only the configured current text export and its manifest; do not read binary
Excel or test references as an extraction answer.

Write `derived/knowledge.json` against `KnowledgeExtract` and the generated
extraction schema. Use English descriptions and verbatim source formulas.

- Map every required `(quantity, role)` pair to exact artifact paths and
  Sheet!Cell/Range evidence. Document table keys and lookups; leave values in
  the export. Do not invent values or expand the T-Box.
- Capture all relevant worksheet outputs and helpers with source formula,
  LaTeX, symbols, conditions and timing. Cite called VBA functions and lines.
  A family template may cover a range only when every relative formula matches.
  Separate initial, final and exceptional rows.
- Give each formula only its own symbols, using valid LaTeX notation. Include
  the left-hand quantity, indexed quantities and helper functions actually
  present; do not copy a global symbol dictionary into every record. Reference
  known quantities by exact T-Box field names. For mathematical helpers, name
  implementing VBA functions in `reference`, or state explicitly that an
  expanded helper combines multiple calls. Do not equate a mathematical
  abbreviation with a literal VBA call without supporting evidence.
- Describe conditions and timing from formulas and VBA control flow: for example
  `j < t`, `j = n`, and `x+j >= flex_min_age`. Never substitute saved example
  inputs to derive phase boundaries or label rows. Distinguish literal formula
  constants (such as five-year recovery) and physically exported row ranges from
  variable policy boundaries. Split families for structural exceptions only.
- Record source behavior, interpretation, uncertainty and blocking questions
  honestly. Formatting is not a rounding rule; example values are not bounds.
- Run `.venv/bin/python -m tools report`. Fix extraction errors within scope.
  Report a failed validation and any older HTML that remains as stale.

Deliver the extract and HTML reading copy, coverage, unresolved questions and
manual review needs. Hash/structure checks do not prove mathematical correctness.
Do not specify target decisions or implement the calculator in this step.
