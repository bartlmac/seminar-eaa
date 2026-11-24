"""The single maintained domain contract for the endowment calculator.

Generate JSON Schema and the field catalogue with ``python -m tools schema``.
This module defines data and target boundaries, never calculation rules.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

TBOX_VERSION = '1.0.0'


class DomainModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


def quantity(label, unit, role, description=None, **constraints):
    return Field(title=label, description=description or label,
                 json_schema_extra={'unit': unit, 'role': role}, **constraints)


class Policy(DomainModel):
    entry_age: StrictInt = quantity('Entry age', 'years', 'input', ge=0)
    sex: Literal['M', 'F'] = quantity('Sex for mortality table selection', 'category', 'input')
    term: StrictInt = quantity('Policy term', 'years', 'input', gt=0)
    premium_term: StrictInt = quantity('Premium payment term', 'years', 'input', gt=0)
    sum_insured: float = quantity('Sum insured', 'EUR', 'input', ge=0)
    payment_frequency: Literal[1, 2, 4, 12] = quantity('Payments per year', 'payments/year', 'input')

    @field_validator('payment_frequency', mode='before')
    @classmethod
    def integer_frequency(cls, value):
        if type(value) is not int:
            raise ValueError('Payment frequency must be an integer.')
        return value

    @model_validator(mode='after')
    def valid_term(self):
        if self.premium_term > self.term:
            raise ValueError('Premium payment term must not exceed policy term.')
        return self


class Tariff(DomainModel):
    interest_rate: float = quantity('Annual valuation interest rate', 'fraction/year', 'parameter')
    mortality_table: str = quantity('Mortality table identifier', 'identifier', 'parameter', min_length=1)
    acquisition_cost_rate: float = quantity('Acquisition cost rate', 'fraction', 'parameter',
        'Rate applied to the premium total defined by the source formula.')
    premium_cost_rate: float = quantity('Premium related cost rate', 'fraction', 'parameter')
    admin_rate_paying: float = quantity('Administration rate during premium payment', 'fraction/year', 'parameter')
    admin_rate_after_payment: float = quantity('Administration rate after premium payment', 'fraction/year', 'parameter')
    admin_rate_paid_up: float = quantity('Administration rate for paid-up valuation', 'fraction/year', 'parameter',
        'Separate paid-up valuation; not the scheduled end of premium payment.')
    annual_policy_fee: float = quantity('Annual policy fee', 'EUR/year', 'parameter', ge=0)
    flex_min_age: StrictInt = quantity('Minimum age for flexible phase', 'years', 'parameter', ge=0)
    flex_years: StrictInt = quantity('Length of flexible final phase', 'years', 'parameter', ge=0)


class MortalityRow(DomainModel):
    table_id: str = quantity('Table identifier', 'identifier', 'table_input', min_length=1)
    sex: Literal['M', 'F'] = quantity('Sex', 'category', 'table_input')
    age: StrictInt = quantity('Table age', 'years', 'table_input', ge=0)
    probability: float = quantity('Annual mortality probability', 'probability', 'table_input', ge=0, le=1)


class Assumptions(DomainModel):
    tariff: Tariff
    mortality: list[MortalityRow] = Field(min_length=1)


class ProjectionYear(DomainModel):
    year: StrictInt = quantity('Elapsed policy years', 'years', 'trajectory_output', ge=0)
    benefit_pv: float = quantity('Benefit present value including survival benefit', 'dimensionless', 'trajectory_output')
    annuity_pv_term: float = quantity('Annuity due present value over remaining policy term', 'dimensionless', 'trajectory_output')
    annuity_pv_premium_term: float = quantity('Annuity due present value over remaining payment term', 'dimensionless', 'trajectory_output')
    reserve_factor: float = quantity('Premium paying reserve per unit sum insured', 'dimensionless', 'trajectory_output')
    reserve: float = quantity('Premium paying reserve', 'EUR', 'trajectory_output')
    paid_up_reserve_factor: float = quantity('Paid-up reserve factor', 'dimensionless', 'trajectory_output')
    minimum_surrender_reserve: float = quantity('Reserve for minimum surrender value before deduction', 'EUR', 'trajectory_output')
    flexible_phase: StrictInt = quantity('Flexible phase indicator', 'indicator', 'trajectory_output', ge=0, le=1)
    surrender_deduction: float = quantity('Surrender deduction', 'EUR', 'trajectory_output')
    surrender_value: float = quantity('Surrender value', 'EUR', 'trajectory_output')
    paid_up_sum_insured: float = quantity('Paid-up sum insured', 'EUR', 'trajectory_output')


class Result(DomainModel):
    gross_premium_factor: float = quantity('Gross premium factor', 'dimensionless', 'scalar_output')
    reserve_premium_factor: float = quantity('Reserve premium factor', 'dimensionless', 'scalar_output')
    gross_annual_premium: float = quantity('Gross annual premium excluding policy fee and modal surcharge', 'EUR/year', 'scalar_output')
    modal_premium: float = quantity('Premium per payment including policy fee and surcharge', 'EUR/payment', 'scalar_output')
    trajectory: list[ProjectionYear] = Field(min_length=1)


class CalculationCase(DomainModel):
    policy: Policy
    assumptions: Assumptions
    result: Result | None = None

    @model_validator(mode='after')
    def flex_within_term(self):
        if self.assumptions.tariff.flex_years > self.policy.term:
            raise ValueError('Flexible phase length must not exceed policy term.')
        return self


FIELD_GROUPS = (Policy, Tariff, MortalityRow, ProjectionYear, Result)


def required_coverage():
    return {(name, field.json_schema_extra['role']) for model in FIELD_GROUPS
            for name, field in model.model_fields.items() if isinstance(field.json_schema_extra, dict)}


def artifacts():
    schema = CalculationCase.model_json_schema()
    schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    schema['$id'] = 'urn:endowment-seminar:tbox:' + TBOX_VERSION
    schema['x-tbox-version'] = TBOX_VERSION
    schema['x-model-rules'] = ['premium_term <= term', 'flex_years <= term',
                              'All floating point values must be finite.']
    lines = ['# Domain field catalogue', '',
             'Generated from `ontology/tbox.py`; edit that Python source only.', '',
             'See the [ontology guide](README.md#reading-the-field-catalogue) for column datatypes, role meanings and constraint notation.', '',
             'Target constraints are part of the data contract. Additional source rules and numerical decisions belong in the current specification.', '']
    for model in FIELD_GROUPS:
        lines += ['## ' + model.__name__, '', '| Field | Meaning | Unit | Role | Constraints |',
                  '|---|---|---|---|---|']
        properties = model.model_json_schema()['properties']
        for name, field in model.model_fields.items():
            prop = properties[name]
            if 'role' not in prop:
                continue
            constraints = {k:v for k,v in prop.items() if k in ('enum','minimum','maximum','exclusiveMinimum','exclusiveMaximum')}
            lines += [f"| `{name}` | {field.description} | {prop['unit']} | {prop['role']} | {json.dumps(constraints)} |"]
        lines += ['']
    return {'tbox.json': json.dumps(schema, indent=2, ensure_ascii=False)+'\n',
            'fields.md': '\n'.join(lines)+'\n'}
