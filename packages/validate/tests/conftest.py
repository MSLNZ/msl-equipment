from __future__ import annotations

import pytest
from msl.equipment_validate.validate import Info


@pytest.fixture
def info() -> Info:
    return Info(url="register.xml", exit_first=False, uri_scheme=None, debug_name="Name", no_colour=True)
