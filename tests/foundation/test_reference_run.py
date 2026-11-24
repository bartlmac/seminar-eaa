"""Reference lifecycle checks; all exports are confined to temporary directories."""
import json
import shutil
from pathlib import Path
import pytest
import openpyxl
from tests.reference import (ROOT, ReferenceRunMissing, export_references, load_references,
                             POLICY_CELLS, TARIFF_CELLS, SCALAR_CELLS, TRAJECTORY_COLUMNS)
from tools.export import write_json


def synthetic_workbook(path):
    # Literal synthetic values test the reference pipeline, not tariff arithmetic.
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = 'Calculation'
    policy = dict(entry_age=40,sex='M',term=1,premium_term=1,sum_insured=1000,payment_frequency=1)
    tariff = dict(interest_rate=0,mortality_table='DAV1994_T',acquisition_cost_rate=0,premium_cost_rate=0,
                  admin_rate_paying=0,admin_rate_after_payment=0,admin_rate_paid_up=0,annual_policy_fee=0,flex_min_age=60,flex_years=0)
    for mapping,values in ((POLICY_CELLS,policy),(TARIFF_CELLS,tariff)):
        for field,cell in mapping.items():
            sheet[cell] = values[field]
    for cell in SCALAR_CELLS.values():
        sheet[cell] = 0
    for year in range(2):
        for field,column in TRAJECTORY_COLUMNS.items():
            sheet[f'{column}{year+16}'] = year if field=='year' else 0
    tables = wb.create_sheet('MortalityTables')
    for col,key in zip('BCDE',['DAV1994_T_M','DAV1994_T_F','DAV2008_T_M','DAV2008_T_F']):
        tables[f'{col}3'] = key
        for age in range(124):
            tables[f'A{age+4}'] = age
            tables[f'{col}{age+4}'] = 0.01
    wb.save(path)
    wb.close()


@pytest.fixture
def project(tmp_path):
    directory = tmp_path/'tests/reference_workbooks'
    directory.mkdir(parents=True)
    for name in ('KLV-001.xlsm','KLV-002.xlsm'):
        synthetic_workbook(directory/name)
    write_json(tmp_path/'seminar.json',dict(reference_workbooks='tests/reference_workbooks',reference_run='derived/references'))
    return tmp_path


def test_missing_run_is_explicit_and_read_only(project):
    with pytest.raises(ReferenceRunMissing,match='step 4'):
        load_references(project)
    assert not (project/'derived').exists()


def test_complete_snapshot_of_all_provided_cases(tmp_path):
    directory = tmp_path/'tests/reference_workbooks'
    directory.mkdir(parents=True)
    originals = sorted((ROOT/'tests/reference_workbooks').glob('KLV-*.xlsm'))
    if not originals:
        pytest.skip('No tutor reference workbooks supplied.')
    for path in originals:
        shutil.copy2(path,directory/path.name)
    write_json(tmp_path/'seminar.json',dict(reference_workbooks='tests/reference_workbooks',reference_run='derived/references'))
    summary = export_references(tmp_path)
    cases = load_references(tmp_path)
    assert list(cases) == summary['cases'] == [p.stem for p in originals]
    for case in cases.values():
        assert case.result is not None
        assert [p.year for p in case.result.trajectory] == list(range(case.policy.term+1))
    with pytest.raises(ValueError,match='must be empty'):
        export_references(tmp_path)


def test_added_and_removed_workbooks_require_rebuild(project):
    export_references(project)
    directory = project/'tests/reference_workbooks'
    shutil.copy2(directory/'KLV-001.xlsm',directory/'KLV-011.xlsm')
    with pytest.raises(ValueError,match='workbook set changed'):
        load_references(project)
    (directory/'KLV-011.xlsm').unlink()
    (directory/'KLV-002.xlsm').unlink()
    with pytest.raises(ValueError,match='workbook set changed'):
        load_references(project)
    shutil.rmtree(project/'derived/references')
    export_references(project)
    assert list(load_references(project)) == ['KLV-001']


def test_changed_workbook_requires_rebuild(project):
    export_references(project)
    path = project/'tests/reference_workbooks/KLV-001.xlsm'
    # A harmless trailing byte still changes source identity and must be detected.
    path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises(ValueError,match='differs from exported source'):
        load_references(project)


def test_tampered_reference_and_partial_run_are_errors(project):
    export_references(project)
    data = project/'derived/references/data/KLV-001.json'
    data.write_text(data.read_text()+' ')
    with pytest.raises(ValueError,match='integrity mismatch'):
        load_references(project)
    (project/'derived/references/index.json').unlink()
    with pytest.raises(FileNotFoundError) as caught:
        load_references(project)
    assert not isinstance(caught.value,ReferenceRunMissing)


def test_failed_generation_leaves_no_partial_snapshot(project):
    (project/'tests/reference_workbooks/KLV-002.xlsm').write_bytes(b'not an Excel file')
    with pytest.raises(Exception):
        export_references(project)
    assert not (project/'derived/references').exists()
    assert not list((project/'derived').glob('.reference-stage-*'))
