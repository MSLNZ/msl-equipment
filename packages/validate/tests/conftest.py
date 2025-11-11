from __future__ import annotations

import pytest
from msl.equipment_validate.validate import Info, Summary


@pytest.fixture
def reset_summary() -> None:
    for item in dir(Summary):
        if item.startswith("num"):
            setattr(Summary, item, 0)
        elif item.startswith("unchecked"):
            setattr(Summary, item, ())


@pytest.fixture
def info() -> Info:
    return Info(url="register.xml", exit_first=False, uri_scheme=None, debug_name="Name", no_colour=True)
