import json
import pytest
from tests.reference import ROOT, load_references, ReferenceRunMissing
from ontology.tbox import artifacts
from ontology.knowledge import KnowledgeExtract


def test_current_reference_provenance_and_completeness():
    try:
        cases = load_references()
    except ReferenceRunMissing as exc:
        pytest.skip(str(exc))
    for case in cases.values():
        assert len(case.assumptions.mortality) == 496
        assert len(case.result.trajectory) == case.policy.term+1
        assert len({(r.table_id,r.sex,r.age) for r in case.assumptions.mortality}) == 496


def test_generated_schemas_and_catalogue_are_current():
    for name,text in artifacts().items():
        assert (ROOT/'ontology'/name).read_text() == text
    assert json.loads((ROOT/'ontology/extraction.schema.json').read_text()) == KnowledgeExtract.model_json_schema()


def test_config_points_to_existing_equipment():
    config = json.loads((ROOT/'seminar.json').read_text())
    for key in ('source','tbox','extraction_schema'):
        assert (ROOT/config[key]).is_file()
