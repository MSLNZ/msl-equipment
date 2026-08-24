# cSpell: ignore documentclass usepackage pdfx
# pyright: reportUnknownMemberType=false, reportOptionalSubscript=false, reportUnknownVariableType=false, reportArgumentType=false
from __future__ import annotations

import base64
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from dash import dcc, html, no_update
from msl.equipment_webapp.config import EquipmentRegister, cfg
from msl.equipment_webapp.pages import assets, home, maintenance, pdf, recalibrations, search
from msl.equipment_webapp.typing import Scope

from .conftest import has_pdflatex, has_vera_pdf

if TYPE_CHECKING:
    from types import ModuleType


scope = Scope({"client": "127.0.0.1:12345", "http_version": "1.1"})


def test_home_layout() -> None:
    div = home.layout()
    assert isinstance(div, html.Div)
    assert len(div.children) == 2
    assert isinstance(div.children[0], html.H3)


def test_page_layout() -> None:
    div = pdf.layout()
    assert len(div.children) == 8
    assert isinstance(div.children[0], dcc.Store)


@pytest.mark.parametrize(
    ("kwargs", "teams", "sync"),
    [
        ({}, [], False),
        ({"sync": "0"}, [], False),
        ({"sync": "1"}, [], True),
        ({"team": "Unknown", "sync": "True"}, [], True),
        ({"team": "Light", "sync": "yes"}, ["Light"], True),
    ],
)
def test_assets_layout(kwargs: dict[str, str], teams: list[str], sync: bool) -> None:  # noqa: FBT001
    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister(team="Light", directory=Path("tests/data/light")))

    div = assets.layout(**kwargs)
    dropdown = div.children[0].children[1].children[1]
    assert dropdown.id == "assets-team-dropdown"
    assert dropdown.value == teams

    checkbox = div.children[0].children[2].children.children[1]
    assert checkbox.id == "assets-sync-checkbox"
    assert checkbox.value is sync


@pytest.mark.parametrize(
    ("kwargs", "teams", "months", "sync"),
    [
        ({}, [], 2, False),
        ({"months": "12"}, [], 12, False),
        ({"months": "-1", "sync": "False"}, [], 0, False),
        ({"months": "Not-an-integer", "sync": "False"}, [], 2, False),  # months=2 on ValueError
        ({"team": "Unknown", "months": "1000", "sync": "True"}, [], maintenance.MONTHS_MAX, True),
        ({"team": "Light", "sync": "yes"}, ["Light"], 2, True),
    ],
)
def test_maintenance_layout(kwargs: dict[str, str], teams: list[str], months: int, sync: bool) -> None:  # noqa: FBT001
    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister(team="Light", directory=Path("tests/data/light")))

    div = maintenance.layout(**kwargs)
    dropdown = div.children[0].children[1].children[1]
    assert dropdown.id == "maintenance-team-dropdown"
    assert dropdown.value == teams

    _input = div.children[0].children[2].children[1]
    assert _input.id == "maintenance-months-input"
    assert _input.value == months

    checkbox = div.children[0].children[3].children.children[1]
    assert checkbox.id == "maintenance-sync-checkbox"
    assert checkbox.value is sync


@pytest.mark.parametrize(
    ("kwargs", "teams", "months", "sync"),
    [
        ({}, [], 6, False),
        ({"months": "12"}, [], 12, False),
        ({"months": "-1", "sync": "False"}, [], 0, False),
        ({"months": "Not-an-integer", "sync": "False"}, [], 6, False),  # months=6 on ValueError
        ({"team": "Unknown", "months": "1000", "sync": "True"}, [], recalibrations.MONTHS_MAX, True),
        ({"team": "Light", "sync": "yes"}, ["Light"], 6, True),
    ],
)
def test_recalibrations_layout(kwargs: dict[str, str], teams: list[str], months: int, sync: bool) -> None:  # noqa: FBT001
    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister(team="Light", directory=Path("tests/data/light")))

    div = recalibrations.layout(**kwargs)
    dropdown = div.children[0].children[1].children[1]
    assert dropdown.id == "recalibrations-team-dropdown"
    assert dropdown.value == teams

    _input = div.children[0].children[2].children[1]
    assert _input.id == "recalibrations-months-input"
    assert _input.value == months

    checkbox = div.children[0].children[3].children.children[1]
    assert checkbox.id == "recalibrations-sync-checkbox"
    assert checkbox.value is sync


@pytest.mark.parametrize(
    ("kwargs", "teams", "text", "sync"),
    [
        ({}, [], "", False),
        ({"text": "Foo%7CBar"}, [], "Foo|Bar", False),
        ({"text": ".", "sync": "False"}, [], ".", False),
        ({"team": "Unknown", "text": "hello%20world", "sync": "True"}, [], "hello world", True),
        ({"team": "Light", "sync": "yes"}, ["Light"], "", True),
    ],
)
def test_search_layout(kwargs: dict[str, str], teams: list[str], text: str, sync: bool) -> None:  # noqa: FBT001
    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister(team="Light", directory=Path("tests/data/light")))

    div = search.layout(**kwargs)
    dropdown = div.children[0].children[1].children[1]
    assert dropdown.id == "search-team-dropdown"
    assert dropdown.value == teams

    _input = div.children[0].children[2].children[0]
    assert _input.id == "search-input"
    assert _input.value == text

    checkbox = div.children[0].children[3].children.children[1]
    assert checkbox.id == "search-sync-checkbox"
    assert checkbox.value is sync


@pytest.mark.anyio
@pytest.mark.parametrize("mod", [maintenance, recalibrations])
@pytest.mark.parametrize(("value", "expected"), [(0, False), (None, True), (6, False)])
async def test_check_months_range(mod: ModuleType, value: int | None, expected: bool) -> None:  # noqa: FBT001
    assert await mod.check_months_range(value) is expected


@pytest.mark.anyio
@pytest.mark.parametrize("mod", [assets, maintenance, recalibrations, search])
@pytest.mark.parametrize(("n_clicks", "expected"), [(0, False), (1, True), (100, True)])
async def test_export_data_as_csv(mod: ModuleType, n_clicks: int, expected: bool) -> None:  # noqa: FBT001
    assert await mod.export_data_as_csv(n_clicks) is expected


@pytest.mark.parametrize("mod", [assets, maintenance, recalibrations, search])
def test_view_selected_row_empty(mod: ModuleType) -> None:
    assert mod.view_selected_row(0, [], scope) == (False, None)


@pytest.mark.parametrize("mod", [assets, maintenance, recalibrations, search])
def test_view_selected_row(mod: ModuleType) -> None:
    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister(team="Light", directory=Path("tests/data/light")))

    selected = {"Team": "Light", "ID": "MSLE.O.061"}
    is_open, details = mod.view_selected_row(0, [selected], scope)
    assert is_open
    assert isinstance(details, html.Details)
    assert len(details.children) == 19

    summary = details.children[0]
    assert isinstance(summary, html.Summary)
    assert isinstance(summary.children[0], html.Span)
    assert summary.children[0].children == "<equipment"
    assert summary.children[1].children == " enteredBy="
    assert summary.children[2].children == '"Joseph Borbely"'
    assert summary.children[3].children == " alias="
    assert summary.children[4].children == '"mono"'
    assert summary.children[5].children == ">"

    eid = details.children[1]
    assert isinstance(eid, html.Div)
    assert eid.children[0].children == "<id"
    assert eid.children[1].children == ">"
    assert eid.children[2].children == "MSLE.O.061"
    assert eid.children[3].children == "</id>"

    manufacturer = details.children[2]
    assert isinstance(manufacturer, html.Div)
    assert manufacturer.children[0].children == "<manufacturer"
    assert manufacturer.children[1].children == ">"
    assert manufacturer.children[2].children == "MSL"
    assert manufacturer.children[3].children == "</manufacturer>"

    model = details.children[3]
    assert isinstance(model, html.Div)
    assert model.children[0].children == "<model"
    assert model.children[1].children == ">"
    assert model.children[2].children == "Mono"
    assert model.children[3].children == "</model>"

    specifications = details.children[6]
    assert isinstance(specifications, html.Div)
    assert specifications.children[0].children == "<specifications"
    assert specifications.children[1].children == " />"

    qm = details.children[17]
    assert isinstance(qm, html.Div)
    assert qm.children[0].children == "<qualityManual"
    assert qm.children[1].children == " />"

    last = details.children[18]
    assert isinstance(last, html.Div)
    assert last.children == "</equipment>"


@pytest.mark.anyio
@pytest.mark.parametrize("mod", [maintenance, recalibrations])
async def test_update_table_teams_empty(mod: ModuleType) -> None:
    href = await mod.update_table([], 6, True, scope, "http://localhost/any")  # noqa: FBT003
    assert href == "http://localhost/any"


@pytest.mark.anyio
@pytest.mark.parametrize("mod", [maintenance, recalibrations])
async def test_update_table_months_none(mod: ModuleType) -> None:
    href = await mod.update_table(["Light"], None, True, scope, "http://localhost/any")  # noqa: FBT003
    assert href == "http://localhost/any"


@pytest.mark.anyio
@pytest.mark.parametrize("mod", [maintenance, recalibrations])
async def test_update_table(mod: ModuleType) -> None:
    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister(team="Light", directory=Path("tests/data/light")))

    href = await mod.update_table(["Light"], 8, False, scope, "http://localhost/any")  # noqa: FBT003
    assert href == "http://localhost/any?team=Light&months=8&sync=false"


@pytest.mark.anyio
async def test_search_update_table_invalid_regex() -> None:
    href, show, child = await search.update_table([], "*", True, scope, "http://localhost/search")  # noqa: FBT003
    assert href == "http://localhost/search"  # input returned unchanged
    assert show
    assert child is not None
    assert child.startswith(("PatternError:", "error:"))


@pytest.mark.anyio
async def test_search_update_table_teams_empty() -> None:
    href, show, child = await search.update_table([], "any", True, scope, "http://localhost/search")  # noqa: FBT003
    assert href == "http://localhost/search"  # input returned unchanged
    assert not show
    assert child is None


@pytest.mark.anyio
async def test_search_update_table_text_empty() -> None:
    href, show, child = await search.update_table(["Light"], "", True, scope, "http://localhost/search")  # noqa: FBT003
    assert href == "http://localhost/search"  # input returned unchanged
    assert not show
    assert child is None


@pytest.mark.anyio
async def test_search_update_table() -> None:
    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister(team="Light", directory=Path("tests/data/light")))

    href, show, child = await search.update_table(["Light"], "foo bar", False, scope, "http://localhost/search")  # noqa: FBT003
    assert href == "http://localhost/search?team=Light&text=foo%20bar&sync=false"
    assert not show
    assert child is None


@pytest.mark.anyio
async def test_assets_update_table_teams_empty() -> None:
    href = await assets.update_table([], True, scope, "http://localhost/assets")  # noqa: FBT003
    assert href == "http://localhost/assets"  # input returned unchanged


@pytest.mark.anyio
async def test_assets_update_table() -> None:
    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister(team="Light", directory=Path("tests/data/light")))

    href = await assets.update_table(["Light"], False, scope, "http://localhost/assets?team=Length&sync=yes")  # noqa: FBT003
    assert href == "http://localhost/assets?team=Light&sync=false"


def test_pdf_upload_document_invalid_extension() -> None:
    child, alert = pdf.upload_document("", "any.txt")
    assert len(child) == 0
    assert alert.children == "Unsupported file extension. Must be one of .docx or .tex."


def test_pdf_upload_document() -> None:
    child, alert = pdf.upload_document("ignored,b64", "report.tex")
    assert child == ["report.tex", "b64"]
    assert alert.children == "report.tex"


def test_pdf_upload_extra_none() -> None:
    extra, alert = pdf.upload_extra(["ignored,foo"], ["a.csv"], None)
    assert extra == {"a.csv": "foo"}
    assert alert.children == ["a.csv"]


def test_pdf_upload_extra_some() -> None:
    extra, alert = pdf.upload_extra(["ignored,bar", "ignored,baz"], ["b.txt", "c.png"], {"a.csv": "foo"})
    assert extra == {"a.csv": "foo", "b.txt": "bar", "c.png": "baz"}
    assert len(alert.children) == 5
    assert alert.children[0] == "a.csv"
    assert isinstance(alert.children[1], html.Br)
    assert alert.children[2] == "b.txt"
    assert isinstance(alert.children[3], html.Br)
    assert alert.children[4] == "c.png"


@pytest.mark.anyio
@pytest.mark.parametrize("n", [0, 1, 2])
async def test_pdf_clear_extra(n: int) -> None:
    out = await pdf.clear_extra(n)
    assert out == {}


@pytest.mark.anyio
async def test_pdf_convert_no_document() -> None:
    a, b, c = await pdf.convert(0, None, None, scope)
    assert a is no_update
    assert b.children is not None
    assert b.children.children == "Must upload a $\\LaTeX$ or Microsoft Word document to convert."
    assert c is None


@pytest.mark.anyio
async def test_pdf_convert_pdflatex_not_found() -> None:
    pdflatex = cfg.pdflatex
    cfg.pdflatex = "does-not-exist"
    a, b, c = await pdf.convert(0, ["foo.tex", base64.b64encode(b"content").decode()], None, scope)
    cfg.pdflatex = pdflatex

    assert a is no_update
    assert b.children is not None
    assert b.children.children == (
        "ERROR! `pdflatex` cannot be found. "
        "If it is installed, specify the path to the executable in the configuration file.\n"
        "```json\n"
        '  "pdflatex": "path/to/pdflatex"\n'
        "```"
    )
    assert c is None


@pytest.mark.anyio
@pytest.mark.skipif(not has_pdflatex, reason="pdflatex is not installed")
@pytest.mark.skipif(not has_vera_pdf, reason="veraPDF is not installed")
async def test_pdf_convert_verapdf_fails() -> None:
    filename = "example.tex"
    content = "\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}"
    content = base64.b64encode(content.encode()).decode()
    a, b, c = await pdf.convert(0, [filename, content], {}, scope)

    assert a is no_update
    assert b.children is not None
    assert b.children.children.startswith("ERROR! Invalid PDF file.\n```xml")
    assert c is None


@pytest.mark.anyio
@pytest.mark.skipif(not has_pdflatex, reason="pdflatex is not installed")
@pytest.mark.skipif(not has_vera_pdf, reason="veraPDF is not installed")
async def test_pdf_convert_valid() -> None:
    filename = "example.tex"
    content = "\\documentclass{article}\n\\usepackage[a-3b]{pdfx}\n\\begin{document}\nHello\n\\end{document}"
    content = base64.b64encode(content.encode()).decode()
    a, b, c = await pdf.convert(0, [filename, content], {}, scope)

    assert base64.b64decode(a["content"]).startswith(b"%PDF-")
    assert a["filename"] == "example.pdf"
    assert a["type"] == "application/pdf"
    assert a["base64"]

    assert b.children is not None
    assert b.children.startswith("MD5:")
    assert c is None
