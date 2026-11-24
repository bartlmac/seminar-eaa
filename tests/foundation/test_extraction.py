"""End-to-end tool checks using synthetic evidence, not an extraction solution."""
import json
import openpyxl
import pytest
from pydantic import ValidationError
from tools.export import export_workbook, write_json
from tools.evidence import validate_extract
from tools.cli import generate_schemas, main
from ontology.tbox import required_coverage, TBOX_VERSION
from ontology.knowledge import KnowledgeExtract
from tools.report import create_report


@pytest.fixture
def exercise(tmp_path):
    source = tmp_path/'source.xlsx'
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Example'
    ws['A1'],ws['A2'],ws['B1'],ws['B2'] = 1,2,'=A1*2','=A2*2'
    wb.save(source)
    wb.close()
    manifest = export_workbook(source,tmp_path/'derived/excel')
    generate_schemas(tmp_path)
    config = dict(source='source.xlsx',manifest='derived/excel/manifest.json',extract='derived/knowledge.json',
                  report='derived/knowledge.html',tbox='ontology/tbox.json',extraction_schema='ontology/extraction.schema.json',tbox_version=TBOX_VERSION)
    write_json(tmp_path/'seminar.json',config)
    file = 'derived/excel/'+manifest['sheets'][0]['file']
    proof = dict(file=file,location='Example!A1')
    extract = dict(schema_version='endowment.knowledge.v1',tbox_version=TBOX_VERSION,
                   source_file='source.xlsx',source_sha256=manifest['source']['sha256'],
                   mappings=[dict(quantity=name,role=role,evidence=[proof]) for name,role in sorted(required_coverage())],
                   rules=[dict(id='R1',description='Synthetic test rule.',affects=['term'],evidence=[proof],confidence='direct_evidence')],
                   datasets=[dict(id='D1',description='Synthetic data, no business content.',evidence=[proof])],
                   formulas=[dict(id='F1',target='helper',latex=r'y=2x',symbols=[dict(symbol='x',meaning='Test value',reference='Example!A1')],
                                  worksheet_formulas=[dict(source_formula='=A1*2',evidence=dict(file=file,location='Example!B1'),applies_to='Example!B1:B2')],
                                  evidence=[proof],conditions='For the two synthetic rows.',timing='Row order.',status='documented')],
                   open_questions=[],limitations=['Synthetic artifact for tool checks only.'])
    write_json(tmp_path/config['extract'],extract)
    return tmp_path,config,extract


def test_valid_extract_and_report(exercise):
    root,config,data = exercise
    extract,summary = validate_extract(root,config)
    assert summary['coverage']=='complete' and summary['formulas']==1
    assert extract.formulas[0].worksheet_formulas[0].applies_to=='Example!B1:B2'
    data['limitations'] = ['<script>alert("x")</script>']
    write_json(root/config['extract'],data)
    report = create_report(root,config)
    text = (root/report['report']).read_text()
    assert '<html lang="en">' in text
    assert '&lt;script&gt;' in text and '<script>alert' not in text
    assert 'y=2x' in text


def test_formula_family_mismatch(exercise):
    root,config,data = exercise
    # The original formula is genuine, but this false family includes A1.
    data['formulas'][0]['worksheet_formulas'][0]['applies_to'] = 'Example!A1:B2'
    write_json(root/config['extract'],data)
    with pytest.raises(ValueError, match='Formula family'):
        validate_extract(root,config)


def test_original_formula_mismatch(exercise):
    root,config,data = exercise
    data['formulas'][0]['worksheet_formulas'][0]['source_formula'] = '=A1*3'
    write_json(root/config['extract'],data)
    with pytest.raises(ValueError, match='Source formula'):
        validate_extract(root,config)


def test_missing_domain_mapping_and_stale_report(exercise,capsys):
    root,config,data = exercise
    create_report(root,config)
    data['mappings'].pop()
    write_json(root/config['extract'],data)
    assert main(['--project',str(root),'report']) == 1
    outcome = json.loads(capsys.readouterr().out)
    assert 'Coverage mismatch' in outcome['error']
    assert outcome['previous_report_remains'] is True


def test_outside_evidence_rejected(exercise):
    root,config,data = exercise
    data['rules'][0]['evidence'][0]['file'] = '../outside.txt'
    write_json(root/config['extract'],data)
    with pytest.raises(ValueError, match='inside'):
        validate_extract(root,config)


def test_changed_source_and_schema_rejected(exercise):
    root,config,data = exercise
    source = root/config['source']
    source.write_bytes(source.read_bytes()+b'changed')
    with pytest.raises(ValueError, match='Workbook differs'):
        validate_extract(root,config)
    write_json(root/config['tbox'],{})
    with pytest.raises(ValueError, match='schema is stale'):
        validate_extract(root,config)


def test_incomplete_formula_requires_known_question(exercise):
    _,_,data = exercise
    data['formulas'][0]['status'] = 'incomplete'
    with pytest.raises(ValidationError,match='needs an open question'):
        KnowledgeExtract.model_validate(data)
    data['formulas'][0]['open_questions'] = ['not-known']
    with pytest.raises(ValidationError,match='unknown open question'):
        KnowledgeExtract.model_validate(data)


def test_formula_must_cite_its_cell_csv(exercise):
    root,config,data = exercise
    data['formulas'][0]['worksheet_formulas'][0]['evidence']['file'] = 'derived/excel/names.json'
    write_json(root/config['extract'],data)
    with pytest.raises(ValueError,match='own sheet CSV'):
        validate_extract(root,config)


def test_readable_report_groups_without_losing_evidence(exercise):
    from copy import deepcopy
    root,config,data = exercise
    repeated = deepcopy(data['formulas'][0])
    repeated.update(id='F2',timing='Distinct later timing.',conditions='Distinct later condition.')
    repeated['worksheet_formulas'] = [dict(source_formula='=A2*2',evidence=dict(file='derived/excel/Example.csv',location='Example!B2'))]
    data['formulas'].append(repeated)
    data['open_questions'] = [dict(id='Q1',question='Review this first.',impact='Unresolved.',blocks_porting=True,evidence=data['rules'][0]['evidence'])]
    write_json(root/config['extract'],data)
    result = create_report(root,config)
    html = (root/result['report']).read_text()
    assert html.count('<div class="math">') == 1
    assert '1 formula groups from 2 records' in html
    for value in ('F1','F2','Distinct later timing.','Distinct later condition.','Example!B2','=A2*2'):
        assert value in html
    assert html.index('Review this first.') < html.index('id="formulas"')
    assert '<details><summary>Symbols</summary>' in html
    assert 'output:\'mathml\'' in html and 'trust:false' in html
    assert '<script src=' not in html and '<link ' not in html
    assert 'KaTeX 0.16.22' in html


def test_report_escapes_formula_and_symbol_markup(exercise):
    root,config,data = exercise
    data['formulas'][0]['latex'] = '</script><img src=x onerror=alert(1)>'
    data['formulas'][0]['symbols'][0]['meaning'] = '<iframe src="bad">'
    write_json(root/config['extract'],data)
    result = create_report(root,config)
    html = (root/result['report']).read_text()
    assert '&lt;/script&gt;&lt;img' in html
    assert '<img src=x' not in html and '<iframe src="bad">' not in html


def test_report_merges_only_adjacent_relative_formulas(exercise):
    from copy import deepcopy
    from tools.report import worksheet_families
    root,config,data = exercise
    first = deepcopy(data['formulas'][0])
    first['worksheet_formulas'][0].pop('applies_to')
    second = deepcopy(first)
    second['id'] = 'F2'
    second['worksheet_formulas'][0].update(source_formula='=A2*2',evidence=dict(file='derived/excel/Example.csv',location='Example!B2'))
    data['formulas'] = [first,second]
    write_json(root/config['extract'],data)
    extract,_ = validate_extract(root,config)
    merged = worksheet_families(extract.formulas)
    assert len(merged) == 1 and merged[0]['start'] == 'B1' and merged[0]['end'] == 'B2'
    result = create_report(root,config)
    html = (root/result['report']).read_text()
    assert '<strong>Applies to:</strong> <code>Example!B1:B2</code>' in html
    assert html.count('<pre>=A1*2</pre>') == 1
    # Matching LaTeX alone must never merge a different worksheet expression.
    extract.formulas[1].worksheet_formulas[0].source_formula = '=A2*3'
    assert len(worksheet_families(extract.formulas)) == 2
    extract.formulas[1].worksheet_formulas[0].source_formula = '=A3*2'
    extract.formulas[1].worksheet_formulas[0].evidence.location = 'Example!B3'
    assert len(worksheet_families(extract.formulas)) == 2


def test_vba_calls_come_from_registered_declarations(exercise):
    from types import SimpleNamespace
    from tools.report import calls_for,vba_catalog
    from ontology.knowledge import Formula
    _,_,data = exercise
    package = SimpleNamespace(files={__import__('pathlib').Path('module.bas.txt'): b'Public Function Act_axn_k(Age As Integer) As Double\nEnd Function\n'})
    catalog = vba_catalog(package)
    formula = Formula.model_validate(data['formulas'][0])
    formula.worksheet_formulas[0].source_formula = '=IF(A1,act_AXN_k(A1),0)'
    assert calls_for([formula],catalog) == [('Act_axn_k','module.bas.txt',1)]
    formula.worksheet_formulas[0].source_formula = '=IF(A1,UnknownHelper(A1),0)'
    assert calls_for([formula],catalog) == []


def test_formula_notation_is_local_and_distinguishes_vba(exercise):
    from tools.report import notation
    from ontology.knowledge import Formula
    _,_,data = exercise
    formula = Formula.model_validate(data['formulas'][0])
    formula.latex = r'U_j=B_j+\gamma a(x,n)'
    formula.symbols = [
        dict(symbol='U_j',meaning='Paid-up factor',reference='paid_up_reserve_factor'),
        dict(symbol='B_j',meaning='Benefit PV',reference='benefit_pv'),
        dict(symbol=r'\gamma',meaning='Cost rate',reference='admin_rate_paid_up'),
        dict(symbol='a(u,h)',meaning='Annual annuity',reference='Act_axn_k with k=1'),
        dict(symbol='x',meaning='Entry age',reference='entry_age'),
        dict(symbol='n',meaning='Term',reference='term'),
        dict(symbol='P',meaning='Unused premium',reference='gross_premium_factor')]
    from ontology.knowledge import Symbol
    formula.symbols = [Symbol.model_validate(s) for s in formula.symbols]
    annotated,rows = notation(formula.latex,[formula],{'act_axn_k':('Act_axn_k','module.txt',12)},
                             {'paid_up_reserve_factor','benefit_pv','admin_rate_paid_up','entry_age','term','gross_premium_factor'})
    legend = str(rows)
    assert 'Unused premium' not in legend
    assert 'Known quantity' in legend and 'Calculated using VBA' in legend
    assert 'Act_axn_k' in legend
    assert r'\textcolor{#003f9e}{U_j}' in annotated
    assert r'\textcolor{#b00020}{a}' in annotated
    assert r'\gamma' in annotated


def test_notation_respects_latex_commands_subscripts_and_powers():
    from ontology.knowledge import Symbol
    from tools.report import notation
    from types import SimpleNamespace
    symbols = [Symbol(symbol=s,meaning=s,reference='local') for s in ('P','p','G','G_f','v','i','x','t','a(u,h)')]
    latex = r'G_f=P+p+v^i+\text{expired}+a(x,t)'
    annotated,rows = notation(latex,[SimpleNamespace(symbols=symbols)],{},set())
    labels = [row[0] for row in rows]
    assert not any('>G</span>' in label for label in labels)
    assert any('>G_f</span>' in label for label in labels)
    assert r'\text{expired}' in annotated
    assert r'^{\textcolor' in annotated
    assert len(rows) == 8


def test_formula_key_appears_once_and_only_for_used_categories(exercise):
    from copy import deepcopy
    root,config,data = exercise
    other = deepcopy(data['formulas'][0])
    other.update(id='F2', target='another_helper', latex='z=2x')
    data['formulas'].append(other)
    write_json(root/config['extract'],data)
    result = create_report(root,config)
    html = (root/result['report']).read_text()
    assert html.count('<strong>Formula key:</strong>') == 1
    assert 'Green: mathematical helper or local notation' in html
    assert 'Red: Calculated using VBA' not in html
    assert 'Blue: known quantity' not in html
    assert 'Notation backed by VBA' not in html
    assert html.index('Formula key:') < html.index('<h3>helper</h3>')
