"""Prepared cell bindings for independent tests, never a calculation engine.

Only saved values are copied; formulas and VBA are never evaluated here.
Additional cases require explicit Excel recalculation and a fresh export.
"""
import argparse
import json
import re
import tempfile
from pathlib import Path
from decimal import Decimal
from ontology.tbox import Policy, Tariff, ProjectionYear, Result, CalculationCase, TBOX_VERSION
from tools.evidence import SourcePackage, within
from tools.export import export_workbook, sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
POLICY_CELLS = dict(entry_age='B4', sex='B5', term='B6', premium_term='B7', sum_insured='B8', payment_frequency='B9')
TARIFF_CELLS = dict(interest_rate='E4', mortality_table='E5', acquisition_cost_rate='E6', premium_cost_rate='E7',
                   admin_rate_paying='E8', admin_rate_after_payment='E9', admin_rate_paid_up='E10',
                   annual_policy_fee='E11', flex_min_age='H4', flex_years='H5')
SCALAR_CELLS = dict(gross_premium_factor='K5', gross_annual_premium='K6', modal_premium='K7', reserve_premium_factor='K9')
TRAJECTORY_COLUMNS = dict(year='A', benefit_pv='B', annuity_pv_term='C', annuity_pv_premium_term='D',
                          reserve_factor='E', reserve='F', paid_up_reserve_factor='G', minimum_surrender_reserve='H',
                          flexible_phase='I', surrender_deduction='J', surrender_value='K', paid_up_sum_insured='L')


def integer(value):
    number = Decimal(value)
    if not number.is_finite() or number != number.to_integral_value():
        raise ValueError('Expected an integer saved value.')
    return int(number)


def case_from_export(package):
    cells = package.cells('Calculation')
    def value(address):
        v = cells[address]['Value']
        if not v or v.startswith('#'):
            raise ValueError(f'Missing or error cache at Calculation!{address}')
        return v
    def fields(model, mapping):
        if set(model.model_fields) != set(mapping):
            raise ValueError('Reference cell map differs from the domain contract.')
        return {key: integer(value(address)) if (model.model_fields[key].annotation is int or key=='payment_frequency')
                else value(address) for key,address in mapping.items()}
    policy = Policy(**fields(Policy, POLICY_CELLS))
    tariff = Tariff(**fields(Tariff, TARIFF_CELLS))
    if not 0 < policy.term <= 50:
        raise ValueError('This workbook exports at most 50 policy years.')
    points = [ProjectionYear(**fields(ProjectionYear, {key:f'{col}{year+16}' for key,col in TRAJECTORY_COLUMNS.items()}))
              for year in range(policy.term+1)]
    if [p.year for p in points] != list(range(policy.term+1)):
        raise ValueError('Unexpected saved trajectory time axis.')
    tables = package.cells('MortalityTables')
    mortality = []
    for column in 'BCDE':
        table_id, sex = tables[column+'3']['Value'].rsplit('_',1)
        for row in range(4,128):
            age = integer(tables[f'A{row}']['Value'])
            if age != row-4:
                raise ValueError('Unexpected mortality age axis.')
            mortality.append(dict(table_id=table_id, sex=sex, age=age, probability=tables[f'{column}{row}']['Value']))
    if set(Result.model_fields) != set(SCALAR_CELLS)|{'trajectory'}:
        raise ValueError('Incomplete scalar map.')
    return CalculationCase(policy=policy, assumptions={'tariff':tariff, 'mortality':mortality},
                           result=Result(**{key:value(address) for key,address in SCALAR_CELLS.items()}, trajectory=points))


class ReferenceRunMissing(FileNotFoundError):
    """Reference preparation has not been run in this workshop run."""


def configuration(project):
    return json.loads((Path(project)/'seminar.json').read_text())


def workbooks(project=ROOT):
    project = Path(project).resolve()
    directory = within(project, configuration(project)['reference_workbooks'])
    found = {}
    for path in sorted(directory.glob('*.xlsm')):
        if not re.fullmatch(r'KLV-[0-9]{3,}', path.stem):
            raise ValueError(f'Reference filename must be KLV-<at least three digits>.xlsm: {path.name}')
        within(project, path.relative_to(project))
        found[path.stem] = path
    return found


def build_reference(case_id, source, manifest):
    package = SourcePackage(manifest)
    source_hash = sha256(source)
    if source_hash != package.manifest['source']['sha256']:
        raise ValueError(f'Workbook differs from exported source: {case_id}')
    return {'schema_version':'endowment.reference.v1', 'id':case_id, 'tbox_version':TBOX_VERSION,
            'origin':'Saved Excel cache; not recalculated by the seminar tools.',
            'source_sha256':source_hash, 'manifest_sha256':sha256(manifest),
            'case':case_from_export(package).model_dump(mode='json')}


def export_references(project=ROOT):
    """Explicit run step: publish a complete snapshot, never overwrite a previous one."""
    project = Path(project).resolve()
    config = configuration(project)
    sources = workbooks(project)
    if not sources:
        raise ValueError('No reference workbooks found; add KLV-001.xlsm etc. first.')
    raw_output = project/config['reference_run']
    output = within(project, config['reference_run'])
    workbook_directory = within(project, config['reference_workbooks'])
    if output == project or output == workbook_directory or output in workbook_directory.parents or workbook_directory in output.parents:
        raise ValueError('Reference output must be separate from permanent workbooks.')
    if raw_output.is_symlink() or (output.exists() and (not output.is_dir() or any(output.iterdir()))):
        raise ValueError('Reference run directory must be empty. Explicitly clear the previous snapshot before rebuilding.')
    output.parent.mkdir(parents=True, exist_ok=True)
    # A failed export must not leave a usable-looking partial reference set.
    with tempfile.TemporaryDirectory(prefix='.reference-stage-', dir=output.parent) as staging:
        stage = Path(staging)
        records = []
        for case_id, source in sources.items():
            manifest = stage/'exports'/case_id/'manifest.json'
            export_workbook(source, manifest.parent, strict=True)
            reference = build_reference(case_id, source, manifest)
            target = stage/'data'/f'{case_id}.json'
            target.parent.mkdir(exist_ok=True)
            write_json(target, reference)
            records.append({'id':case_id, 'workbook':source.relative_to(project).as_posix(),
                            'reference':target.relative_to(stage).as_posix(), 'sha256':sha256(target)})
        # Detect additions/removals and edits during generation as well.
        if workbooks(project) != sources or any(sha256(sources[r['id']]) != json.loads((stage/r['reference']).read_text())['source_sha256'] for r in records):
            raise ValueError('Reference workbooks changed during generation; no snapshot published.')
        write_json(stage/'index.json', {'schema_version':'endowment.references.v1',
                                      'tbox_version':TBOX_VERSION, 'cases':records})
        if output.exists():
            output.rmdir()  # Only an empty directory is allowed.
        stage.rename(output)
    return {'directory':config['reference_run'], 'cases':list(sources),
            'limits':'Saved Excel results only; no recalculation and no comparison with the target calculator.'}


def load_references(project=ROOT):
    """Validate the whole snapshot against the current workbook set; never regenerate it."""
    project = Path(project).resolve()
    config = configuration(project)
    output = within(project, config['reference_run'])
    if not output.exists() or (output.is_dir() and not any(output.iterdir())):
        raise ReferenceRunMissing('Reference preparation has not run: execute python -m tests.reference in step 4.')
    index = json.loads((output/'index.json').read_text())
    if index['schema_version'] != 'endowment.references.v1' or index['tbox_version'] != TBOX_VERSION:
        raise ValueError('Reference snapshot format or T-Box version mismatch.')
    sources = workbooks(project)
    ids = [r['id'] for r in index['cases']]
    if not ids or len(ids) != len(set(ids)) or set(ids) != set(sources):
        raise ValueError('Reference workbook set changed or index is invalid; explicitly rebuild the snapshot.')
    cases = {}
    for record in index['cases']:
        case_id = record['id']
        if within(project, record['workbook']) != sources[case_id]:
            raise ValueError('Reference workbook path mismatch.')
        path = within(output, record['reference'])
        if sha256(path) != record['sha256']:
            raise ValueError(f'Reference data integrity mismatch: {case_id}')
        saved = json.loads(path.read_text())
        expected = build_reference(case_id, sources[case_id], output/'exports'/case_id/'manifest.json')
        if saved != expected:
            raise ValueError(f'Reference data or source binding mismatch: {case_id}')
        cases[case_id] = CalculationCase.model_validate(saved['case'])
    return cases


def main(argv=None):
    parser = argparse.ArgumentParser(description='Export all current reference workbooks and copy their saved results into this run.')
    parser.add_argument('--project', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        summary = export_references(args.project)
        result, code = {'status':'passed', 'summary':summary}, 0
    except Exception as exc:
        result, code = {'status':'failed', 'error':f'{type(exc).__name__}: {exc}'}, 1
    print(json.dumps(result))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
