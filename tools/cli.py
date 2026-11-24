"""Export the source, validate an extract, or create its offline report."""
import argparse
import json
import sys
from pathlib import Path
from tools.export import export_workbook
from tools.evidence import validate_extract
from tools.report import create_report


def generate_schemas(project):
    from ontology.tbox import artifacts
    from ontology.knowledge import KnowledgeExtract
    files = artifacts()
    files['extraction.schema.json'] = json.dumps(KnowledgeExtract.model_json_schema(), indent=2)+'\n'
    directory = Path(project)/'ontology'
    directory.mkdir(parents=True, exist_ok=True)
    for name,text in files.items():
        (directory/name).write_text(text, encoding='utf-8')
    return {'files':['ontology/'+name for name in files]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest='command', required=True)
    export = commands.add_parser('export', help='Export one Excel workbook into a fresh text directory.')
    export.add_argument('--input', type=Path, required=True)
    export.add_argument('--out-dir', type=Path, required=True)
    export.add_argument('--strict', action='store_true')
    commands.add_parser('schema', help='Regenerate schemas and field catalogue from Python definitions.')
    commands.add_parser('check', help='Check the configured knowledge extract.')
    commands.add_parser('report', help='Validate the extract, then create its HTML reading copy.')
    args = parser.parse_args(argv)
    project = args.project.resolve()
    try:
        if args.command == 'export':
            manifest = export_workbook(project/args.input, project/args.out_dir, strict=args.strict)
            summary = {'manifest':str(args.out_dir/'manifest.json'), 'warnings':manifest['warnings']}
        elif args.command == 'schema':
            summary = generate_schemas(project)
        else:
            config = json.loads((project/'seminar.json').read_text())
            if args.command == 'report':
                summary = create_report(project, config)
            else:
                _,summary = validate_extract(project, config)
        result = {'status':'passed', 'command':args.command, 'summary':summary}
        code = 0
    except Exception as exc:
        result = {'status':'failed', 'command':args.command, 'error':f'{type(exc).__name__}: {exc}'}
        if args.command == 'report':
            report = project/'derived/knowledge.html'
            result['previous_report_remains'] = report.is_file()
        code = 1
    print(json.dumps(result, ensure_ascii=False))
    return code
