"""Compare all current reference scalars and every year/field with independent saved caches."""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT/'calculator/api.py').is_file():
    pytest.skip('Seminar start: calculator/api.py has not been implemented.', allow_module_level=True)

from calculator.api import calculate
from calculator.models import Policy, Assumptions, Result, ProjectionYear
from tests.reference import SCALAR_CELLS, TRAJECTORY_COLUMNS
from tests.comparison_output import comparison_table


def test_complete_excel_reference(request, excel_case):
    case = excel_case
    actual = calculate(Policy.model_validate_json(case.policy.model_dump_json()),
                       Assumptions.model_validate_json(case.assumptions.model_dump_json()))
    expected = case.result
    assert set(type(actual).model_fields) == set(Result.model_fields) == set(SCALAR_CELLS)|{'trajectory'}
    assert set(ProjectionYear.model_fields) == set(TRAJECTORY_COLUMNS)
    assert len(actual.trajectory) == len(expected.trajectory) == case.policy.term+1
    comparisons = [(name, 'Calculation!'+address, getattr(expected,name), getattr(actual,name), Result.model_fields[name])
                   for name,address in SCALAR_CELLS.items()]
    for year,point in enumerate(actual.trajectory):
        assert set(type(point).model_fields) == set(TRAJECTORY_COLUMNS)
        comparisons.extend((f'trajectory[{year}].{name}', f'Calculation!{column}{year+16}',
                            getattr(expected.trajectory[year],name), getattr(point,name), ProjectionYear.model_fields[name])
                           for name,column in TRAJECTORY_COLUMNS.items())
    table, failures = comparison_table(comparisons)
    if request.config.getoption('--excel-verbose'):
        print(f'\nReference case: {request.node.callspec.id}')
        print(table)
    assert not failures, '\n'+failures
