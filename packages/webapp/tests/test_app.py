from __future__ import annotations

import json
import logging
from typing import Any

import pytest
from dash import Dash
from fastapi import FastAPI
from fastapi.testclient import TestClient
from msl.equipment_webapp.app import SuppressDashFilter, create_app
from msl.equipment_webapp.config import cfg


@pytest.mark.anyio
async def test_create_app() -> None:
    app = create_app(cfg)
    assert isinstance(app, Dash)
    assert isinstance(app.server, FastAPI)

    callback_map: dict[str, Any] = app.callback_map  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert len(callback_map) == 1

    _id = "navbar-collapse"
    _property = "is_open"
    assert f"{_id}.{_property}" in callback_map

    # the callback is the `toggle_navbar_collapse` function
    outputs_list = {"id": _id, "property": _property}
    callback = callback_map[f"{_id}.{_property}"]["callback"]

    out = json.loads(await callback(0, True, outputs_list=outputs_list))  # noqa: FBT003
    assert out["response"][_id][_property] is False

    out = json.loads(await callback(0, False, outputs_list=outputs_list))  # noqa: FBT003
    assert out["response"][_id][_property] is False

    out = json.loads(await callback(1, True, outputs_list=outputs_list))  # noqa: FBT003
    assert out["response"][_id][_property] is False

    out = json.loads(await callback(1, False, outputs_list=outputs_list))  # noqa: FBT003
    assert out["response"][_id][_property] is True

    out = json.loads(await callback(2, False, outputs_list=outputs_list))  # noqa: FBT003
    assert out["response"][_id][_property] is True

    out = json.loads(await callback(2, True, outputs_list=outputs_list))  # noqa: FBT003
    assert out["response"][_id][_property] is False

    client = TestClient(app.server)
    response = client.get("/api/docs")
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("msg", "expected"),
    [
        ("GET /_dash-component-suites/dash/dcc/async-markdown.js HTTP/1.1", False),
        ("GET /recalibrations HTTP/1.1", True),
    ],
)
def test_dash_log_filter(msg: str, expected: bool) -> None:  # noqa: FBT001
    record = logging.LogRecord("name", logging.INFO, "pathname", 1, msg, None, None)
    assert SuppressDashFilter().filter(record) is expected
