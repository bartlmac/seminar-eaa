import json
from pathlib import Path
import pytest
import openpyxl
from tools.export import export_workbook
from tools.evidence import SourcePackage
from tools.cli import main


def test_formula_text_cache_warning_and_integrity(tmp_path):
    source = tmp_path/'sample.xlsx'
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'A worksheet'
    ws['A1'],ws['B1'] = 3,'=A1*2'
    wb.save(source)
    wb.close()
    manifest = export_workbook(source, tmp_path/'export')
    assert len(manifest['warnings']) == 1
    package = SourcePackage(tmp_path/'export/manifest.json')
    assert package.cells('A worksheet')['B1'] == dict(Sheet='A worksheet', Address='B1',Formula='=A1*2',Value='')
    path = tmp_path/'export'/manifest['sheets'][0]['file']
    path.write_text(path.read_text()+'tampered')
    with pytest.raises(ValueError, match='integrity'):
        SourcePackage(tmp_path/'export/manifest.json')


def test_strict_export_and_existing_directory(tmp_path):
    source = tmp_path/'source.xlsx'
    wb = openpyxl.Workbook()
    wb.active['A1'] = '=1+1'
    wb.save(source)
    wb.close()
    with pytest.raises(ValueError, match='Strict export'):
        export_workbook(source,tmp_path/'export',strict=True)
    with pytest.raises(ValueError, match='must be empty'):
        export_workbook(source,tmp_path/'export')
    assert (tmp_path/'export/manifest.json').is_file()


def test_cli_reports_missing_exercise_artifacts_without_writing(tmp_path, capsys):
    (tmp_path/'seminar.json').write_text(json.dumps(dict(manifest='derived/excel/manifest.json')))
    assert main(['--project',str(tmp_path),'check']) == 1
    assert json.loads(capsys.readouterr().out)['status'] == 'failed'
    assert not (tmp_path/'derived').exists()
