from __future__ import annotations

import os
import sys

import pytest

os.environ['MSL_EQUIPMENT_TESTING'] = 'True'


@pytest.fixture(autouse=True)
def doctest_skipif(doctest_namespace):

    if sys.version_info[:2] < (3, 6):
        less_36 = lambda: pytest.skip('ignore Python <3.6 since dict does not preserve insertion order')
    else:
        less_36 = lambda: None

    doctest_namespace['SKIP_IF_PYTHON_LESS_THAN_3_6'] = less_36
