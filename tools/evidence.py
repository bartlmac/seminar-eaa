"""Validate artifact integrity, evidence locations and relative formula families."""
import csv
import json
import re
from pathlib import Path
from openpyxl.formula.translate import Translator
from openpyxl.utils.cell import range_boundaries, get_column_letter
from ontology.knowledge import KnowledgeExtract
from ontology.tbox import required_coverage, artifacts, TBOX_VERSION
from tools.export import sha256


def within(base, relative):
    path = (base/relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(base.resolve()):
        raise ValueError('Artifact path must remain inside its declared directory.')
    return path


class SourcePackage:
    def __init__(self, manifest_path):
        self.path = Path(manifest_path)
        self.base = self.path.parent
        self.manifest = json.loads(self.path.read_text())
        if self.manifest['schema_version'] != 'endowment.export.v1':
            raise ValueError('Unsupported export format.')
        self.files = {}
        for item in self.manifest['artifacts']:
            path = within(self.base, item['file'])
            if path in self.files:
                raise ValueError('Duplicate manifest artifact.')
            raw = path.read_bytes()
            from hashlib import sha256 as digest
            if digest(raw).hexdigest() != item['sha256'] or len(raw) != item['bytes']:
                raise ValueError(f'Artifact integrity mismatch: {item["file"]}')
            self.files[path] = raw
        self.sheets = {}
        for sheet in self.manifest['sheets']:
            path = within(self.base, sheet['file'])
            if sheet['name'] in self.sheets or path not in self.files:
                raise ValueError('Invalid sheet binding.')
            import io
            reader = csv.DictReader(io.StringIO(self.files[path].decode('utf-8-sig')), delimiter=';')
            if reader.fieldnames != ['Sheet','Address','Formula','Value']:
                raise ValueError('Invalid cell CSV header.')
            cells = {}
            for row in reader:
                if row['Sheet'] != sheet['name'] or row['Address'] in cells:
                    raise ValueError('Invalid or duplicate cell binding.')
                cells[row['Address']] = row
            self.sheets[sheet['name']] = (path, cells)

    def cells(self, name):
        return self.sheets[name][1]


def parse_location(value):
    match = re.fullmatch(r"(?:'((?:[^']|'')+)'|([^!]+))!\$?([A-Z]+)\$?([1-9][0-9]*)(?::\$?([A-Z]+)\$?([1-9][0-9]*))?", value)
    if not match:
        raise ValueError('Expected Sheet!Cell or Sheet!Range.')
    sheet = (match[1] or match[2]).replace("''", "'")
    first = match[3]+match[4]
    last = (match[5]+match[6]) if match[5] else first
    c1,r1,c2,r2 = range_boundaries(first+':'+last)
    if c1>c2 or r1>r2 or c2>16384 or r2>1048576:
        raise ValueError('Invalid cell range.')
    return sheet, first, last, (c1,r1,c2,r2)


def validate_extract(project, config):
    project = Path(project).resolve()
    if config['tbox_version'] != TBOX_VERSION:
        raise ValueError('Configured T-Box version differs from the maintained model.')
    if json.loads(within(project, config['tbox']).read_text()) != json.loads(artifacts()['tbox.json']):
        raise ValueError('Generated T-Box schema is stale or modified.')
    if json.loads(within(project, config['extraction_schema']).read_text()) != KnowledgeExtract.model_json_schema():
        raise ValueError('Generated extraction schema is stale or modified.')
    package = SourcePackage(within(project, config['manifest']))
    source = within(project, config['source'])
    if sha256(source) != package.manifest['source']['sha256']:
        raise ValueError('Workbook differs from exported source.')
    extract = KnowledgeExtract.model_validate_json(within(project, config['extract']).read_bytes())
    if (extract.source_sha256 != package.manifest['source']['sha256'] or
        extract.source_file != source.name):
        raise ValueError('Extract and export refer to different sources.')
    pairs = {(m.quantity, m.role) for m in extract.mappings}
    required = required_coverage()
    if pairs != required:
        raise ValueError(f'Coverage mismatch; missing={sorted(required-pairs)}, unknown={sorted(pairs-required)}')
    quantities = {q for q,_ in required}
    for rule in extract.rules:
        if set(rule.affects) - quantities:
            raise ValueError(f'Unknown rule quantities: {rule.id}')
    symbolic = []
    def proof(evidence):
        path = within(project, evidence.file)
        if path not in package.files:
            raise ValueError(f'Evidence file is not registered: {evidence.file}')
        sheet_files = {p for p,_ in package.sheets.values()}
        if path in sheet_files:
            sheet,_,_,(c1,r1,c2,r2) = parse_location(evidence.location)
            if sheet not in package.sheets or package.sheets[sheet][0] != path:
                raise ValueError('Evidence file and sheet disagree.')
            cells = package.cells(sheet)
            # Sparse ranges may include empty cells; at least one cell must exist.
            if not any(c1<=range_boundaries(a)[0]<=c2 and r1<=range_boundaries(a)[1]<=r2 for a in cells):
                raise ValueError('No exported cells at evidence location.')
        else:
            symbolic.append(evidence.model_dump())
    sheet_files = {p for p,_ in package.sheets.values()}
    for mapping in extract.mappings:
        if within(project, mapping.evidence[0].file) not in sheet_files:
            raise ValueError('A quantity mapping must cite a cell CSV first.')
    for group in (extract.mappings, extract.rules, extract.datasets, extract.open_questions, extract.formulas):
        for item in group:
            for evidence in item.evidence:
                proof(evidence)
    for formula in extract.formulas:
        for worksheet in formula.worksheet_formulas:
            proof(worksheet.evidence)
            sheet,first,last,_ = parse_location(worksheet.evidence.location)
            if first != last:
                raise ValueError('A source formula must cite one cell.')
            if sheet not in package.sheets or within(project, worksheet.evidence.file) != package.sheets[sheet][0]:
                raise ValueError('A worksheet formula must cite its own sheet CSV.')
            cells = package.cells(sheet)
            if cells[first]['Formula'] != worksheet.source_formula:
                raise ValueError('Source formula differs from the export.')
            if worksheet.applies_to:
                family_sheet,start,end,(c1,r1,c2,r2) = parse_location(worksheet.applies_to)
                if family_sheet != sheet or start != first or (c1 != c2 and r1 != r2):
                    raise ValueError('Formula family must start at its template and cover one row or column.')
                translator = Translator(worksheet.source_formula, origin=first)
                for row in range(r1,r2+1):
                    for col in range(c1,c2+1):
                        address = f'{get_column_letter(col)}{row}'
                        if cells.get(address, {}).get('Formula') != translator.translate_formula(address):
                            raise ValueError(f'Formula family mismatch: {sheet}!{address}')
    return extract, {'coverage':'complete', 'formulas':len(extract.formulas),
                     'blocking_questions':[q.id for q in extract.open_questions if q.blocks_porting],
                     'symbolic_evidence_requires_review':symbolic,
                     'limits':'Integrity and structure checks do not prove mathematical correctness or result equality.'}
