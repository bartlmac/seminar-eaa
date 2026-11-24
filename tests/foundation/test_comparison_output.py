"""Console readability must preserve precision, exact indices and failure details."""
from ontology.tbox import Result, ProjectionYear
from tests.comparison_output import comparison_table


def test_columns_align_and_failures_keep_the_same_heading():
    scalar = Result.model_fields['gross_annual_premium']
    integer = ProjectionYear.model_fields['year']
    rows = [('gross_annual_premium','Calculation!K6',1234.5678901234567,1234.5678901234567,scalar),
            ('trajectory[12].year','Calculation!A28',12,13,integer)]
    table,failures = comparison_table(rows)
    lines=table.splitlines()
    separators=[[i for i,c in enumerate(line) if c=='|'] for line in (lines[0],*lines[2:])]
    assert all(positions==separators[0] for positions in separators)
    assert '1234.5678901234567' in table
    assert 'trajectory[' not in table
    assert 'NOK' in failures and 'gross_annual_premium' not in failures
    assert failures.splitlines()[0]==lines[0]
    assert 'Calculation!A28' in failures and 'Tolerance' in failures


def test_nonfinite_values_are_visible_failures():
    field=Result.model_fields['gross_premium_factor']
    table,failures=comparison_table([('factor','Calculation!K5',1.0,float('nan'),field),
                                    ('factor','Calculation!K5',1.0,float('inf'),field)])
    assert 'nan' in table and 'inf' in table
    assert failures.count('NOK')==2


def test_no_failures_and_empty_comparison_table():
    field=ProjectionYear.model_fields['year']
    table,failures=comparison_table([('trajectory[0].year','Calculation!A16',0,0,field)])
    assert not failures and 'OK' in table
    table,failures=comparison_table([])
    assert 'Field' in table and not failures
