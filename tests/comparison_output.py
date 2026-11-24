"""Aligned console presentation; comparison rules stay in tests.tolerances."""
import re
from tests.tolerances import compare, tolerance


def number(value):
    """Use the shortest round-trip representation without display rounding."""
    return repr(value)


def comparison_table(comparisons):
    """Return the full table and an aligned failure-only table, using shared widths."""
    headers = ('Year', 'Field', 'Source', 'Excel', 'Python', 'Abs. difference', 'Tolerance', 'Status')
    rows, failed = [], []
    for name, source, expected, actual, field in comparisons:
        match = re.fullmatch(r'trajectory\[(\d+)\]\.(.+)', name)
        year, label = match.groups() if match else ('-', name)
        ok = compare(expected, actual, field)
        rows.append((year, label, source, number(expected), number(actual),
                     number(abs(actual-expected)), 'exact' if field.annotation is int else number(tolerance(field)), 'OK' if ok else 'NOK'))
        failed.append(not ok)
    widths = [max(len(header), *(len(row[i]) for row in rows)) for i,header in enumerate(headers)] if rows else [len(h) for h in headers]
    def render(row):
        return ' | '.join(value.rjust(widths[i]) if i in (0,3,4,5,6) else value.ljust(widths[i]) for i,value in enumerate(row))
    heading = [render(headers), '-+-'.join('-'*width for width in widths)]
    full = '\n'.join(heading+[render(row) for row in rows])
    failures = '\n'.join(heading+[render(row) for row,bad in zip(rows,failed) if bad]) if any(failed) else ''
    return full, failures
