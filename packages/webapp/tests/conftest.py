from __future__ import annotations

import sys
from typing import Literal

import pytest

if sys.version_info[:2] < (3, 9):
    # Avoid the following error with Python 3.8
    # ModuleNotFoundError: No module named 'trio'

    @pytest.fixture(scope="session")
    def anyio_backend() -> Literal["asyncio"]:
        """Use asyncio instead of trio."""
        return "asyncio"
