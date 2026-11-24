# Domain contract

`tbox.py` is the maintained model for policy, tariff, mortality assumptions and
complete results. It defines the target boundaries, not calculation algorithms.
`knowledge.py` defines evidence-backed extraction separately from a calculation
case. Source findings can differ from target constraints; document both honestly.

Read [fields.md](fields.md) for field meanings and [tbox.json](tbox.json) for
the generated calculation schema. [extraction.schema.json](extraction.schema.json)
is generated from `KnowledgeExtract` in [knowledge.py](knowledge.py).

## Reading the field catalogue

Each row describes one field. The columns contain metadata, not the field's
actual calculation value:

| Column | Meaning and datatype |
|---|---|
| Field | A string naming the Python attribute, such as `entry_age`. |
| Meaning | A free-text English description. |
| Unit | A string describing the unit or value category, such as `EUR`, `years`, `fraction/year` or `identifier`. It does not determine the datatype or perform unit conversion. |
| Role | A string identifying how the field participates in the calculation; see below. |
| Constraints | A JSON object showing selected restrictions on the field's value; see below. |

The value datatype is defined by the annotation in [tbox.py](tbox.py) and the
generated JSON Schema. For example, `entry_age` is a strict integer,
`sum_insured` is a finite floating point number, and `sex` is a string restricted
to `M` or `F`. A role or unit is not a substitute for that datatype.

## Roles

These five roles are workshop conventions:

| Role | Meaning | Example |
|---|---|---|
| `input` | A policy-specific value supplied for a calculation. | `Policy.sum_insured` |
| `parameter` | A tariff assumption controlling the calculation. Parameters can also be edited; the role does not make them constants. | `Tariff.interest_rate` |
| `table_input` | A field in a lookup-table row, including identifying keys and the value looked up. | `MortalityRow.table_id`, `age` and `probability` |
| `scalar_output` | One result value for the policy. | `Result.gross_annual_premium` |
| `trajectory_output` | A value recorded at each projection year, including the year index. | `ProjectionYear.reserve` and `year` |

The assignments are maintained in `tbox.py`. `Mapping.role` in `knowledge.py`
restricts extraction mappings to these five strings. The `quantity()` helper
stores role and unit metadata without separately validating their vocabulary.

## Constraints

The catalogue uses JSON Schema names. The Python model expresses the same
restrictions through Pydantic field arguments or `Literal` annotations:

| Catalogue constraint | Meaning | Python definition | Example |
|---|---|---|---|
| `minimum` | Greater than or equal to the bound. | `ge=...` | `{"minimum": 0}` allows zero. |
| `maximum` | Less than or equal to the bound. | `le=...` | `{"maximum": 1}` allows one. |
| `exclusiveMinimum` | Strictly greater than the bound. | `gt=...` | `{"exclusiveMinimum": 0}` excludes zero. |
| `exclusiveMaximum` | Strictly less than the bound. Currently unused, but supported by the catalogue generator. | `lt=...` | `{"exclusiveMaximum": 1}` excludes one. |
| `enum` | Exactly one of the listed values. | `Literal[...]` | `{"enum": [1, 2, 4, 12]}` lists the allowed payment frequencies. |

Restrictions apply together with the datatype. `term` is a strict integer with
`exclusiveMinimum: 0`, so its allowed values are 1, 2, 3, and so on. Mortality
`probability` is a finite float with `minimum: 0` and `maximum: 1`, so it may take
any representable value in that inclusive interval.

An empty object `{}` means **no bounds or enumeration are displayed**, not that
all values are valid. The catalogue currently displays only the five constraint
keywords above. Other rules remain in the model and, where expressible, its
generated schema:

- `min_length=1` becomes `minLength: 1` for identifiers and `minItems: 1` for
  required nonempty lists.
- All floating point values must be finite: NaN and positive/negative infinity
  are rejected by `DomainModel`.
- Strict integer fields reject fractional values and booleans. Payment frequency
  additionally requires an actual integer, rather than `1.0` or `True`.
- Model validators enforce `premium_term <= term` and `flex_years <= term`.
  These cross-field rules are also listed in the schema's `x-model-rules`
  annotation; that annotation describes the rules, while the Python validators
  enforce them.
- Unknown fields are rejected by `DomainModel`.

These are target-system constraints. Whether Excel applies the same restrictions
must be established separately from the current source export.

## Maintaining the contract

Only for an authorized equipment change:

```sh
.venv/bin/python -m tools schema
.venv/bin/python -m pytest tests/foundation -q
```

Local helper quantities are allowed in formulas and implementation. They do not
require additional domain fields or a T-Box extension.
