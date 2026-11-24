# Domain field catalogue

Generated from `ontology/tbox.py`; edit that Python source only.

See the [ontology guide](README.md#reading-the-field-catalogue) for column datatypes, role meanings and constraint notation.

Target constraints are part of the data contract. Additional source rules and numerical decisions belong in the current specification.

## Policy

| Field | Meaning | Unit | Role | Constraints |
|---|---|---|---|---|
| `entry_age` | Entry age | years | input | {"minimum": 0} |
| `sex` | Sex for mortality table selection | category | input | {"enum": ["M", "F"]} |
| `term` | Policy term | years | input | {"exclusiveMinimum": 0} |
| `premium_term` | Premium payment term | years | input | {"exclusiveMinimum": 0} |
| `sum_insured` | Sum insured | EUR | input | {"minimum": 0} |
| `payment_frequency` | Payments per year | payments/year | input | {"enum": [1, 2, 4, 12]} |

## Tariff

| Field | Meaning | Unit | Role | Constraints |
|---|---|---|---|---|
| `interest_rate` | Annual valuation interest rate | fraction/year | parameter | {} |
| `mortality_table` | Mortality table identifier | identifier | parameter | {} |
| `acquisition_cost_rate` | Rate applied to the premium total defined by the source formula. | fraction | parameter | {} |
| `premium_cost_rate` | Premium related cost rate | fraction | parameter | {} |
| `admin_rate_paying` | Administration rate during premium payment | fraction/year | parameter | {} |
| `admin_rate_after_payment` | Administration rate after premium payment | fraction/year | parameter | {} |
| `admin_rate_paid_up` | Separate paid-up valuation; not the scheduled end of premium payment. | fraction/year | parameter | {} |
| `annual_policy_fee` | Annual policy fee | EUR/year | parameter | {"minimum": 0} |
| `flex_min_age` | Minimum age for flexible phase | years | parameter | {"minimum": 0} |
| `flex_years` | Length of flexible final phase | years | parameter | {"minimum": 0} |

## MortalityRow

| Field | Meaning | Unit | Role | Constraints |
|---|---|---|---|---|
| `table_id` | Table identifier | identifier | table_input | {} |
| `sex` | Sex | category | table_input | {"enum": ["M", "F"]} |
| `age` | Table age | years | table_input | {"minimum": 0} |
| `probability` | Annual mortality probability | probability | table_input | {"maximum": 1, "minimum": 0} |

## ProjectionYear

| Field | Meaning | Unit | Role | Constraints |
|---|---|---|---|---|
| `year` | Elapsed policy years | years | trajectory_output | {"minimum": 0} |
| `benefit_pv` | Benefit present value including survival benefit | dimensionless | trajectory_output | {} |
| `annuity_pv_term` | Annuity due present value over remaining policy term | dimensionless | trajectory_output | {} |
| `annuity_pv_premium_term` | Annuity due present value over remaining payment term | dimensionless | trajectory_output | {} |
| `reserve_factor` | Premium paying reserve per unit sum insured | dimensionless | trajectory_output | {} |
| `reserve` | Premium paying reserve | EUR | trajectory_output | {} |
| `paid_up_reserve_factor` | Paid-up reserve factor | dimensionless | trajectory_output | {} |
| `minimum_surrender_reserve` | Reserve for minimum surrender value before deduction | EUR | trajectory_output | {} |
| `flexible_phase` | Flexible phase indicator | indicator | trajectory_output | {"maximum": 1, "minimum": 0} |
| `surrender_deduction` | Surrender deduction | EUR | trajectory_output | {} |
| `surrender_value` | Surrender value | EUR | trajectory_output | {} |
| `paid_up_sum_insured` | Paid-up sum insured | EUR | trajectory_output | {} |

## Result

| Field | Meaning | Unit | Role | Constraints |
|---|---|---|---|---|
| `gross_premium_factor` | Gross premium factor | dimensionless | scalar_output | {} |
| `reserve_premium_factor` | Reserve premium factor | dimensionless | scalar_output | {} |
| `gross_annual_premium` | Gross annual premium excluding policy fee and modal surcharge | EUR/year | scalar_output | {} |
| `modal_premium` | Premium per payment including policy fee and surcharge | EUR/payment | scalar_output | {} |

