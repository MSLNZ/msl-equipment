from __future__ import annotations

import pytest
from msl.equipment_validate.validate import Info, Summary


@pytest.fixture
def reset_summary() -> None:
    Summary.num_issues = 0
    Summary.num_skipped = 0
    Summary.num_register = 0
    Summary.num_equipment = 0
    Summary.num_connection = 0
    Summary.num_cvd = 0
    Summary.num_digital_report = 0
    Summary.num_equation = 0
    Summary.num_file = 0
    Summary.num_serialised = 0
    Summary.num_table = 0


@pytest.fixture
def info() -> Info:
    return Info(url="register.xml", exit_first=False, uri_scheme=None, debug_name="Name", no_colour=True)
