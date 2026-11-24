"""Readable, self-contained offline report; validation precedes any output write."""
from collections import defaultdict
from html import escape
from pathlib import Path
import re
from openpyxl.formula.translate import Translator
from tools.evidence import validate_extract, SourcePackage, parse_location


def text(value):
    return escape(str(value), quote=True)


def table(headers, rows):
    return ('<div class="scroll"><table><thead><tr>' + ''.join('<th scope="col">'+text(h)+'</th>' for h in headers)
            + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+cell+'</td>' for cell in row)+'</tr>' for row in rows)
            + '</tbody></table></div>')


def details(label, content):
    return '<details><summary>'+text(label)+'</summary>'+content+'</details>'


def evidence(items):
    unique = dict.fromkeys((e.file, e.location) for e in items)
    return '<ul>'+''.join('<li><code>'+text(loc)+'</code> — '+text(file)+'</li>' for file, loc in unique)+'</ul>'


def worksheet_families(records):
    """Merge adjacent ranges only when Excel relative translation agrees."""
    entries = []
    for f in records:
        for w in f.worksheet_formulas:
            sheet, start, end, bounds = parse_location(w.applies_to or w.evidence.location)
            entries.append((w.evidence.file, sheet, start, end, bounds, w.source_formula))
    entries = sorted(set(entries), key=lambda e: (e[0], e[1], e[4][0], e[4][1]))
    families = []
    for file, sheet, start, end, bounds, formula in entries:
        c1,r1,c2,r2 = bounds
        if families:
            last = families[-1]
            lc1,lr1,lc2,lr2 = last['bounds']
            adjacent = (c1 == c2 == lc1 == lc2 and r1 == lr2 + 1)
            adjacent |= (r1 == r2 == lr1 == lr2 and c1 == lc2 + 1)
            if (file, sheet) == (last['file'], last['sheet']) and adjacent:
                if Translator(last['formula'], origin=last['start']).translate_formula(start) == formula:
                    last.update(end=end, bounds=(lc1,lr1,c2,r2))
                    continue
        families.append(dict(file=file,sheet=sheet,start=start,end=end,bounds=bounds,formula=formula))
    return families


def vba_catalog(package):
    """Use declarations in registered text artifacts, not guessed symbol meanings."""
    catalog = {}
    for path, raw in package.files.items():
        if not path.name.endswith('.txt'):
            continue
        for line, source in enumerate(raw.decode('utf-8-sig').splitlines(), 1):
            match = re.match(r'\s*(?:(?:Public|Private)\s+)?Function\s+(\w+)\s*\(', source, re.I)
            if match:
                catalog[match[1].lower()] = (match[1], path.name, line)
    return catalog


def calls_for(records, catalog):
    names = {name.lower() for f in records for w in f.worksheet_formulas
             for name in re.findall(r'([A-Za-z_][A-Za-z_0-9.]*)\s*\(', w.source_formula)}
    return [catalog[name] for name in sorted(names & catalog.keys())]


# Tokenize notation, not prose or LaTeX layout commands. Positions allow coloring
# the original expression without rewriting its mathematics or extraction data.
GREEK = set('alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi pi rho sigma tau upsilon phi chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega'.split())


def latex_tokens(source):
    pattern = (r'\\(?:begin|end|text|mathrm|operatorname)\s*\{[^{}]*\}'
               r'|\\[A-Za-z]+|[A-Za-z0-9]|[_^(),+\-=;/<>]')
    result = []
    for match in re.finditer(pattern, source):
        token = match.group()
        if token.startswith('\\'):
            if token[1:] not in GREEK:
                continue
            token = token[1:]
        result.append((token, match.start(), match.end()))
    return result


def symbol_occurrences(latex, symbols):
    tokens = latex_tokens(latex)
    values = [t[0] for t in tokens]
    candidates = []
    for symbol in symbols:
        name = symbol.symbol
        function = '(' in name and name.endswith(')')
        head = name.split('(',1)[0] if function else name
        wanted = [t[0] for t in latex_tokens(head)]
        if not wanted:
            continue
        for i in range(len(tokens)-len(wanted)+1):
            stop = i+len(wanted)
            if values[i:stop] != wanted:
                continue
            following = values[stop] if stop < len(values) else None
            if function and (following != '(' or (i and values[i-1] in ('_', '^'))):
                continue
            if not function and following == '_':
                continue
            # An index letter is explained separately as well as in its parent quantity.
            start, end = tokens[i][1], tokens[stop-1][2]
            # Closing braces of a subscript belong inside its color wrapper.
            balance = latex[start:end].count('{')-latex[start:end].count('}')
            while balance > 0 and end < len(latex) and latex[end] == '}':
                end += 1
                balance -= 1
            candidates.append((start,end,symbol))
    # Longer declarations (G_f, a^n_j) take priority over their scalar prefixes.
    selected = []
    for start,end,symbol in sorted(candidates,key=lambda v: (-(v[1]-v[0]),v[0], '(' not in v[2].symbol)):
        if not any(start < b and end > a for a,b,_ in selected):
            selected.append((start,end,symbol))
    return sorted(selected,key=lambda v:v[0])


def notation(latex, records, catalog, quantities):
    declared = {}
    for f in records:
        for symbol in f.symbols:
            declared[(symbol.symbol,symbol.meaning,symbol.reference)] = symbol
    occurrences = symbol_occurrences(latex, declared.values())
    used = dict.fromkeys((s.symbol,s.meaning,s.reference) for _,_,s in occurrences)
    def kind(reference):
        names = re.findall(r'[A-Za-z_][A-Za-z_0-9]*', reference)
        implementations = [catalog[n.lower()][0] for n in names if n.lower() in catalog]
        if reference in quantities:
            return 'quantity', 'Known quantity', reference
        if implementations:
            return 'vba', 'Calculated using VBA', ', '.join(dict.fromkeys(implementations))+' — '+reference
        return 'helper', 'Mathematical helper / local notation', reference
    rows = []
    for symbol,meaning,reference in used:
        color,label,link = kind(reference)
        rows.append(['<span class="notation '+color+'">'+text(symbol)+'</span>',text(label),text(meaning),text(link)])
    annotated = latex
    for start,end,symbol in reversed(occurrences):
        color = {'quantity':'#003f9e','vba':'#b00020','helper':'#006b3c'}[kind(symbol.reference)[0]]
        annotated = annotated[:start]+r'{\textcolor{'+color+'}{'+annotated[start:end]+'}}'+annotated[end:]
    return annotated, rows


STYLE = '''
:root{color-scheme:light;--ink:#193041;--line:#d6dfe5;--paper:#f4f7fa}
body{font:16px/1.6 system-ui,sans-serif;color:var(--ink);max-width:1100px;margin:32px auto;padding:0 24px}
h1,h2,h3{line-height:1.25}h2{margin-top:2.5rem;border-bottom:2px solid var(--line);padding-bottom:10px}
a{color:#075aa0}nav{display:flex;gap:16px;flex-wrap:wrap}article{border:1px solid var(--line);border-radius:8px;padding:18px;margin:16px 0}
p{margin:8px 0}summary{cursor:pointer;color:#075aa0;font-weight:600;padding:8px 0}
.scroll,.math{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid var(--line)}th{background:var(--paper)}
code,pre{font-size:.85rem;overflow-wrap:anywhere}pre{white-space:pre-wrap;background:var(--paper);padding:12px}
.math{padding:18px 4px;font-size:1.2rem;background:var(--paper)}.badge{font-size:.8rem;background:#edf2f7;padding:3px 8px;border-radius:8px}
.notation{font-weight:600}.quantity{color:#003f9e}.vba{color:#b00020}.helper{color:#006b3c}
.warning{border-left:4px solid #b26a00;padding-left:12px}.math-error{color:#a12517}li{margin:6px 0}
@media print{details{display:block}nav,button{display:none}article{break-inside:avoid}body{max-width:none}}
'''

SCRIPT = '''
for (const el of document.querySelectorAll('.math')) {
  const source = el.textContent;
  try { katex.render(source, el, {output:'mathml', displayMode:true,
    throwOnError:true, trust:false, strict:'ignore', maxExpand:1000}); }
  catch (err) { el.textContent = 'Formula could not be rendered: ' + source;
    el.classList.add('math-error'); }
}
document.getElementById('expand').addEventListener('click', () => {
  for (const el of document.querySelectorAll('details')) el.open = true;
});
document.getElementById('collapse').addEventListener('click', () => {
  for (const el of document.querySelectorAll('details')) el.open = false;
});
'''


def create_report(project, config):
    extract, summary = validate_extract(project, config)
    vendor = Path(__file__).with_name('vendor')
    renderer = (vendor/'katex.min.js').read_text(encoding='utf-8')
    license_text = (vendor/'KATEX-LICENSE.txt').read_text(encoding='utf-8')
    catalog = vba_catalog(SourcePackage(Path(project)/config['manifest']))
    groups = defaultdict(list)
    for formula in extract.formulas:
        groups[(formula.target, formula.latex)].append(formula)
    body = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>Endowment calculator: evidence report</title><style>'+STYLE+'</style></head><body>',
            '<h1>Endowment calculator: evidence report</h1>',
            '<p>Read the questions first, then the rules and formulas. Expand evidence when reviewing a source claim.</p>',
            '<p class="warning">Integrity and structure validation passed. This does not establish mathematical correctness or equality with Excel. VBA and named evidence require manual review.</p>',
            '<p><strong>'+text(summary['coverage'])+' field coverage</strong> · '+str(len(extract.mappings))+' mappings · '
            +str(len(groups))+' formula groups from '+str(len(extract.formulas))+' records · '
            +str(len(summary['blocking_questions']))+' blocking questions</p>',
            '<nav aria-label="Report sections">'+''.join('<a href="#'+k+'">'+v+'</a>' for k,v in [('questions','Questions'),('rules','Rules'),('formulas','Formulas'),('mappings','Field map'),('datasets','Data'),('provenance','Provenance')])+'</nav>',
            '<p><button id="expand" type="button">Expand all details</button> <button id="collapse" type="button">Collapse all details</button></p>',
            '<noscript><p>Enable JavaScript to render formulas. LaTeX source and all evidence remain readable below.</p></noscript>',
            '<h2 id="questions">Questions for tutor review</h2>']
    if not extract.open_questions:
        body.append('<p>No open questions recorded.</p>')
    for q in extract.open_questions:
        body.append('<article><h3>'+text(q.id)+' <span class="badge">'+('Blocks porting' if q.blocks_porting else 'Review')+'</span></h3><p>'+text(q.question)+'</p><p><strong>Impact:</strong> '+text(q.impact)+'</p>'+details('Source evidence',evidence(q.evidence))+'</article>')
    body.append('<h2 id="rules">Source rules and interpretations</h2>')
    for r in extract.rules:
        body.append('<article><h3>'+text(r.id)+'</h3><p>'+text(r.description)+'</p><p class="badge">'+text(r.confidence.replace('_',' '))+' · '+text(', '.join(r.affects))+'</p>'+details('Source evidence',evidence(r.evidence))+'</article>')
    body.append('<h2 id="formulas">Calculation formulas</h2><p>Identical expressions for the same target appear once. Adjacent worksheet ranges are merged only when their relative formulas agree. Mathematical notation below describes quantities and helper functions; literal VBA calls are listed separately in monospace. Full extraction records remain available for audit.</p>')
    rendered_groups = [(target, latex, records, *notation(latex, records, catalog, {m.quantity for m in extract.mappings}))
                       for (target, latex), records in groups.items()]
    labels = [('quantity', 'Blue: known quantity'), ('vba', 'Red: Calculated using VBA'),
              ('helper', 'Green: mathematical helper or local notation')]
    active = {category for _,_,_,_,rows in rendered_groups for row in rows
              for category,_ in labels if 'class="notation '+category+'"' in row[0]}
    if active:
        body.append('<aside aria-label="Formula color key"><p><strong>Formula key:</strong> '
                    + ' · '.join('<span class="notation '+category+'">'+text(label)+'</span>'
                                 for category,label in labels if category in active)
                    + '</p><p>The same key applies throughout this section. The Symbols table also names each category. '
                    + 'A mathematical abbreviation may combine several VBA calls; it is not necessarily a literal call. '
                    + 'Operators and numeric constants retain their usual mathematical meaning.</p></aside>')
    for target, latex, records, annotated, symbol_rows in rendered_groups:
        families = worksheet_families(records)
        family_html = ''.join('<p><strong>Applies to:</strong> <code>'+text(f["sheet"]+'!'+f["start"]+(':'+f["end"] if f["end"] != f["start"] else ''))+'</code></p><pre>'+text(f['formula'])+'</pre>' for f in families)
        calls = calls_for(records, catalog)
        call_html = (table(['VBA function called by worksheet','Declaration in exported VBA'],
                          [['<code>'+text(name)+'(...)</code>',text(file)+':'+str(line)] for name,file,line in calls])
                     if calls else '<p>No direct VBA function call in these worksheet formulas.</p>')
        annotations = table(['Conditions','Timing'], [[text(condition),text(timing)] for condition,timing in dict.fromkeys((f.conditions,f.timing) for f in records)])
        all_evidence = evidence([e for f in records for e in f.evidence])
        record_rows = [[text(f.id),text(f.status),text(', '.join(f.open_questions))] for f in records]
        questions = sorted({q for f in records for q in f.open_questions})
        body.append('<article><h3>'+text(target)+'</h3><div class="math">'+text(annotated)+'</div>'
                    +('<p class="warning">Open questions: '+text(', '.join(questions))+'</p>' if questions else '')
                    +details('LaTeX source','<pre>'+text(latex)+'</pre>')
                    +details('Symbols',table(['Notation in this formula','Kind','Meaning','Quantity or VBA implementation'],symbol_rows))
                    +'<h4>Worksheet formula families</h4>'+family_html
                    +'<h4>VBA calls</h4>'+call_html
                    +details('Conditions and timing',annotations)
                    +details('Source evidence (deduplicated)',all_evidence)
                    +details('Extraction record IDs ('+str(len(records))+')',table(['Record','Status','Questions'],record_rows))+'</article>')
    body.append('<h2 id="mappings">Domain field map</h2>'+details('All '+str(len(extract.mappings))+' field mappings',table(['Field','Role','Source name','Notes and evidence'],[[text(m.quantity),text(m.role),text(m.source_name),text(m.note)+evidence(m.evidence)] for m in extract.mappings])))
    body.append('<h2 id="datasets">Source datasets</h2>')
    for d in extract.datasets:
        body.append('<article><h3>'+text(d.id)+'</h3><p>'+text(d.description)+'</p>'+details('Source evidence',evidence(d.evidence))+'</article>')
    body.append('<h2 id="provenance">Provenance and limits</h2><p>Source: '+text(extract.source_file)+'<br>SHA-256: <code>'+text(extract.source_sha256)+'</code><br>Extract schema: '+text(extract.schema_version)+' · T-Box: '+text(extract.tbox_version)+'</p><ul>'+''.join('<li>'+text(limit)+'</li>' for limit in extract.limitations)+'</ul>')
    body.append(details('Unique VBA and named evidence requiring manual review','<ul>'+''.join('<li>'+text(file)+' — '+text(loc)+'</li>' for file,loc in dict.fromkeys((e['file'],e['location']) for e in summary['symbolic_evidence_requires_review']))+'</ul>'))
    body.append(details('Offline formula renderer and license','<p>KaTeX 0.16.22, bundled from https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.js. MathML output uses the browser’s native math layout; no network or external fonts are required. Use a current Firefox, Edge or Chrome browser.</p><pre>'+text(license_text)+'</pre>'))
    # The trusted vendored script is embedded, while every extracted string above is escaped.
    body += ['<script>'+renderer.replace('</script',r'<\/script')+'</script>', '<script>'+SCRIPT+'</script></body></html>']
    target = Path(project)/config['report']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join(body), encoding='utf-8')
    return {'report':config['report'], 'validation':summary}
