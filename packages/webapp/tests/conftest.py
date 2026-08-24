from __future__ import annotations

import sys
from subprocess import run
from typing import Literal
from unittest.mock import AsyncMock, Mock

import pytest
from dash._callback_context import context_value
from msl.equipment_webapp.config import cfg
from msl.loadlib import LoadLibrary

if sys.version_info[:2] < (3, 9):
    # Avoid the following error with Python 3.8
    # ModuleNotFoundError: No module named 'trio'

    @pytest.fixture(scope="session")
    def anyio_backend() -> Literal["asyncio"]:
        """Use asyncio instead of trio."""
        return "asyncio"

    # Avoids getting the following exception
    # dash.exceptions.MissingCallbackContextException: dash.callback_context.set_props is only available from a callback
    _ = context_value.set(AsyncMock())
else:
    _ = context_value.set(Mock())


try:
    has_vera_pdf = run([cfg.verapdf, "--version"], check=False, capture_output=True).returncode == 0  # noqa: S603
except FileNotFoundError:
    has_vera_pdf = False

try:
    has_pdflatex = run([cfg.pdflatex, "--version"], check=False, capture_output=True).returncode == 0  # noqa: S603
except FileNotFoundError:
    has_pdflatex = False

try:
    word_app = LoadLibrary(cfg.wordapp, "com")
except OSError:
    has_word_app = False
else:
    has_word_app = True
