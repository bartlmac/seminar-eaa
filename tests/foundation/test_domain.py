"""Model constraints use synthetic inputs, independent of reference-run artifacts."""
import pytest
from pydantic import ValidationError
from ontology.tbox import Policy, Tariff, MortalityRow, CalculationCase, required_coverage

POLICY = dict(entry_age=40, sex='M', term=30, premium_term=20, sum_insured=100000, payment_frequency=12)
TARIFF = dict(interest_rate=0.01, mortality_table='example', acquisition_cost_rate=0,
              premium_cost_rate=0, admin_rate_paying=0, admin_rate_after_payment=0,
              admin_rate_paid_up=0, annual_policy_fee=0, flex_min_age=60, flex_years=5)


@pytest.mark.parametrize('frequency', [1,2,4,12])
def test_payment_categories(frequency):
    assert Policy(**(POLICY|{'payment_frequency':frequency})).payment_frequency == frequency


@pytest.mark.parametrize('change', [dict(entry_age=-1),dict(term=0),dict(premium_term=31),
                                    dict(sum_insured=-1),dict(sum_insured=float('nan')),
                                    dict(sum_insured=float('inf')),dict(payment_frequency=True),
                                    dict(payment_frequency=1.0),dict(payment_frequency=3),dict(term=3.5)])
def test_target_policy_boundaries(change):
    with pytest.raises(ValidationError):
        Policy(**(POLICY|change))


def test_zero_sum_and_flex_boundary():
    case = dict(policy=POLICY|{'sum_insured':0}, assumptions=dict(tariff=TARIFF,
                mortality=[dict(table_id='example',sex='M',age=40,probability=0.01)]))
    assert CalculationCase.model_validate(case).policy.sum_insured == 0
    case['assumptions']['tariff'] = TARIFF|{'flex_years':31}
    with pytest.raises(ValidationError):
        CalculationCase.model_validate(case)


@pytest.mark.parametrize('probability', [-0.01,1.01,float('nan')])
def test_mortality_probability(probability):
    with pytest.raises(ValidationError):
        MortalityRow(table_id='table',sex='M',age=40,probability=probability)


def test_finite_tariff_and_coverage():
    with pytest.raises(ValidationError):
        Tariff(**(TARIFF|{'interest_rate':float('-inf')}))
    assert len(required_coverage()) == 36
