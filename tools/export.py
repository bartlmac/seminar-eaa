"""Deterministic OOXML text export; no Excel calculation or provider calls."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

import openpyxl
from oletools.olevba import VBA_Parser


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def safe_name(value):
    name = re.sub(r'[^\w.-]', '_', value).strip('.')
    return name or 'artifact'


def text(value):
    if value is None:
        return ''
    if hasattr(value, 'text'):
        return value.text or ''
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError('Non-finite cached cell value.')
        if value.is_integer():
            return str(int(value))
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


def export_workbook(source, output, *, strict=False):
    source, output = Path(source), Path(output)
    if source.suffix.lower() not in ('.xlsm', '.xlsx'):
        raise ValueError('Expected an .xlsm or .xlsx workbook.')
    # Fresh directories avoid stale artifacts and unintended overwrites.
    if output.is_symlink() or (output.exists() and any(output.iterdir())):
        raise ValueError('Export directory must be empty and must not be a symlink.')
    source_hash = sha256(source)
    output.mkdir(parents=True, exist_ok=True)
    formulas = openpyxl.load_workbook(source, data_only=False, read_only=False)
    values = openpyxl.load_workbook(source, data_only=True, read_only=False)
    warnings, sheets, files, names = [], [], [], []
    used = set()
    def filename(label, suffix):
        stem = safe_name(label)
        candidate, index = stem+suffix, 1
        while candidate.casefold() in used:
            index += 1
            candidate = f'{stem}_{index}{suffix}'
        used.add(candidate.casefold())
        return candidate
    try:
        for sheet in formulas.worksheets:
            target = filename(sheet.title, '.csv')
            count = 0
            with (output/target).open('w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['Sheet', 'Address', 'Formula', 'Value'])
                for row in sheet:
                    for cell in row:
                        cached = values[sheet.title][cell.coordinate].value
                        if cell.value is None and cached is None:
                            continue
                        is_formula = cell.data_type == 'f'
                        if is_formula:
                            count += 1
                            if cached is None:
                                warnings.append(f'Missing cached value: {sheet.title}!{cell.coordinate}; recalculate and save in Excel if expected values are needed.')
                        writer.writerow([sheet.title, cell.coordinate, text(cell.value) if is_formula else '', text(cached)])
            files.append(target)
            sheets.append({'name': sheet.title, 'file': target, 'formula_count': count,
                           'state': sheet.sheet_state,
                           'validations': [{'range':str(v.sqref), 'type':v.type, 'formula1':v.formula1,
                                            'formula2':v.formula2, 'allow_blank':v.allow_blank}
                                           for v in sheet.data_validations.dataValidation],
                           'tables': [t.ref for t in sheet.tables.values()]})
            for name, value in sheet.defined_names.items():
                names.append({'name': name, 'scope': sheet.title, 'definition': value.attr_text})
        names.extend({'name':name, 'scope':'Workbook', 'definition':value.attr_text}
                     for name,value in formulas.defined_names.items())
        write_json(output/'names.json', names)
        files.append('names.json')
    finally:
        formulas.close()
        values.close()
    # Preserve original OOXML structures (including unsupported chart properties).
    with ZipFile(source) as archive:
        parts = sorted(archive.namelist())
        structure_parts = [p for p in parts if re.fullmatch(r'xl/(workbook.xml|worksheets/sheet\d+.xml|tables/table\d+.xml)', p)]
        structure = {p:archive.read(p).decode('utf-8') for p in structure_parts}
        # Names, tables, validation definitions and formulas remain available as text.
        write_json(output/'structure.json', {'parts':structure, 'sheets':sheets})
        chart_parts = [p for p in parts if (p.startswith('xl/charts/') or p.startswith('xl/drawings/')) and (p.endswith('.xml') or p.endswith('.rels'))]
        write_json(output/'charts.json', {'parts':{p:archive.read(p).decode('utf-8') for p in chart_parts},
                  'limitations':['Raw chart and drawing definitions; no rendering or formula evaluation.']})
        files += ['structure.json', 'charts.json']
        externals = [p for p in parts if p.startswith('xl/externalLinks/') and p.endswith('.xml')]
        if externals:
            warnings.append('External workbook links are preserved in source only; external targets are never loaded.')
        has_vba = 'xl/vbaProject.bin' in parts
    if has_vba:
        parser = VBA_Parser(str(source))
        try:
            for _, _, module, code in parser.extract_macros():
                if not code.strip():
                    continue
                target = 'vba/'+filename(str(module), '.txt')
                (output/'vba').mkdir(exist_ok=True)
                (output/target).write_text(code, encoding='utf-8')
                files.append(target)
        finally:
            parser.close()
    if sha256(source) != source_hash:
        raise ValueError('Source workbook changed during export.')
    manifest = {'schema_version':'endowment.export.v1',
                'source':{'file':source.name, 'sha256':source_hash, 'bytes':source.stat().st_size},
                'sheets':sheets, 'artifacts':[{'file':p, 'sha256':sha256(output/p), 'bytes':(output/p).stat().st_size}
                                           for p in sorted(files)],
                'warnings':warnings,
                'limitations':['Cached values are saved source values, not recalculated results.',
                               'VBA text is exported but never executed.']}
    write_json(output/'manifest.json', manifest)
    if strict and warnings:
        raise ValueError('Strict export failed; inspect warnings in manifest.json.')
    return manifest
