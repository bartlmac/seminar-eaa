"""Independent absolute tolerances. Never adapt them to implementation errors."""
import math

NUMERIC = 1e-8
EUR = 1e-6


def tolerance(field):
    return EUR if field.json_schema_extra['unit'].startswith('EUR') else NUMERIC


def compare(expected, actual, field):
    if field.annotation is int:
        return type(actual) is int and actual == expected
    return (math.isfinite(expected) and math.isfinite(actual)
            and math.isfinite(actual-expected) and abs(actual-expected) <= tolerance(field))
