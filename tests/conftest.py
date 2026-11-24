"""Optional field-by-field Excel cache comparison output."""
import pytest


def pytest_addoption(parser):
    parser.addoption('--excel-verbose', action='store_true', help='Print saved Excel/Python values, absolute differences and tolerances.')
