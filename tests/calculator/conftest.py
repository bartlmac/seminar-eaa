"""Run references are prepared explicitly, never as a side effect of testing."""
import pytest
from tests.reference import workbooks, load_references, ReferenceRunMissing


@pytest.fixture(scope='module')
def reference_cases():
    try:
        return load_references()
    except ReferenceRunMissing as exc:
        pytest.skip(str(exc))


@pytest.fixture(params=list(workbooks()) or [None])
def excel_case(request, reference_cases):
    return reference_cases[request.param]


@pytest.fixture
def reference_case(reference_cases):
    return next(iter(reference_cases.values()))
