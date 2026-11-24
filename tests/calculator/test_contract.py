"""Public API shape, validated data and isolated calls; no private implementation tests."""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT/'calculator/api.py').is_file():
    pytest.skip('Seminar start: calculator API has not been implemented.', allow_module_level=True)

from calculator.api import calculate, CalculationError
from calculator import models
from ontology import tbox


def test_runtime_models_match_prepared_contract():
    for name in ('Policy','Tariff','MortalityRow','Assumptions','ProjectionYear','Result','CalculationCase'):
        assert getattr(models,name).model_json_schema() == getattr(tbox,name).model_json_schema()


def test_repeat_calls_do_not_share_state_or_mutate_inputs(reference_case):
    case = reference_case
    policy = models.Policy.model_validate_json(case.policy.model_dump_json())
    assumptions = models.Assumptions.model_validate_json(case.assumptions.model_dump_json())
    before = (policy.model_dump(), assumptions.model_dump())
    first = calculate(policy, assumptions)
    second = calculate(policy, assumptions)
    assert first == second
    assert first is not second and first.trajectory is not second.trajectory
    assert first.trajectory[0] is not second.trajectory[0]
    assert (policy.model_dump(), assumptions.model_dump()) == before


def test_api_revalidates_mutated_policy(reference_case):
    case = reference_case
    policy = models.Policy.model_validate_json(case.policy.model_dump_json())
    assumptions = models.Assumptions.model_validate_json(case.assumptions.model_dump_json())
    policy.premium_term = policy.term+1
    with pytest.raises(CalculationError):
        calculate(policy, assumptions)
