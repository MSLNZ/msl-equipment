# cSpell: ignore documentclass embedfile
from __future__ import annotations

import sys
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from xml.etree.ElementTree import fromstring

import pytest
from dash import html
from msl.equipment_webapp import utils
from msl.equipment_webapp.config import EquipmentRegister, cfg
from msl.equipment_webapp.typing import Scope
from pikepdf import Pdf

from .conftest import has_pdflatex, has_vera_pdf, has_word_app

if TYPE_CHECKING:
    from msl.equipment_webapp.typing import AgGridData


@pytest.mark.anyio
async def test_validate_register_success() -> None:
    out: list[tuple[AgGridData, str]] = []

    async def update(data: AgGridData, msg: str = "") -> None:
        out.append((data, msg))
        await utils.process_events()

    files = [Path("tests/data/light/register.xml")]
    success = await utils.validate_register(files, "Light", [], update)
    assert success
    assert out[0][0] == []
    assert out[0][1] == "Validating Light register (skipping sha256 checksums)"


@pytest.mark.anyio
async def test_validate_register_error(tmp_path: Path) -> None:
    out: list[tuple[AgGridData, str]] = []

    async def update(data: AgGridData, msg: str = "") -> None:
        out.append((data, msg))
        await utils.process_events()

    file = tmp_path / "reg.xml"
    _ = file.write_text("<register><id>1</id></register>")

    success = await utils.validate_register([file], "Mass", [], update)
    assert not success
    assert out[0][0] == []
    assert out[0][1] == "Validating Mass register (skipping sha256 checksums)"
    assert out[1][0] == []
    assert out[1][1] == "  \u274c ERROR! Mass register invalid (skipping)"


@pytest.mark.anyio
async def test_validate_register_error_without_update_function(tmp_path: Path) -> None:
    file = tmp_path / "reg.xml"
    _ = file.write_text("<register><id>1</id></register>")

    success = await utils.validate_register([file], "Mass", [])
    assert not success


@pytest.mark.anyio
async def test_process_events() -> None:
    out = await utils.process_events()  # type: ignore[func-returns-value]
    assert out is None


@pytest.mark.anyio
async def test_git_pull_error() -> None:
    out: list[tuple[AgGridData, str]] = []

    async def update(data: AgGridData, msg: str = "") -> None:
        out.append((data, msg))
        await utils.process_events()

    git = cfg.git
    cfg.git = "missing"
    registers = [EquipmentRegister("Light", Path()), EquipmentRegister("Mass", Path())]
    success = await utils.git_pull(registers, update)
    cfg.git = git

    assert not success
    assert out[0][0] == []
    assert out[0][1] == "Syncing register for Light, Mass"
    assert out[1][0] == []
    assert out[1][1].startswith("  \u274c ERROR! Cannot sync")


@pytest.mark.anyio
async def test_git_pull_error_without_update_function() -> None:
    git = cfg.git
    cfg.git = "missing"
    success = await utils.git_pull([EquipmentRegister("Light", Path())])
    cfg.git = git
    assert not success


@pytest.mark.anyio
async def test_git_pull_success(tmp_path: Path) -> None:
    out: list[tuple[AgGridData, str]] = []

    async def update(data: AgGridData, msg: str = "") -> None:
        out.append((data, msg))
        await utils.process_events()

    registers = [EquipmentRegister("Length", tmp_path)]
    success = await utils.git_pull(registers, update)
    assert success  # no error, directory without a .git subdirectory is ignored
    assert out[0][0] == []
    assert out[0][1] == "Syncing register for Length"


@pytest.mark.anyio
async def test_pdflatex_not_installed() -> None:
    pdflatex = cfg.pdflatex
    cfg.pdflatex = "missing"
    pdf_path, error = await utils.to_pdf(Path("not-used.tex"), {})
    cfg.pdflatex = pdflatex

    assert pdf_path == Path("not-used.pdf")
    assert error.startswith("ERROR! `pdflatex` cannot be found.")


@pytest.mark.anyio
@pytest.mark.skipif(not has_pdflatex, reason="pdflatex is not installed")
async def test_pdflatex_fails() -> None:
    # don't use the `tmp_path` fixture from pytest, want to mimic exactly with is done in pages/pdf.py
    with TemporaryDirectory() as tmp:
        file = Path(tmp) / "example.tex"
        _ = file.write_text(
            "\\documentclass{article}\n\\begin{document}\n\\embedfile[mimetype=text/plain]{data.text}\n\\end{document}"
        )
        _, error = await utils.to_pdf(file, {})
        assert error.rstrip().endswith("==> Fatal error occurred, no output PDF file produced!")


@pytest.mark.anyio
@pytest.mark.skipif(not has_pdflatex, reason="pdflatex is not installed")
async def test_pdflatex_passes() -> None:
    # don't use the `tmp_path` fixture from pytest, want to mimic exactly with is done in pages/pdf.py
    with TemporaryDirectory() as tmp:
        file = Path(tmp) / "file with spaces.tex"
        _ = file.write_text("\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}")

        extra = {"data.txt": b"hi"}
        assert not (Path(tmp) / "data.txt").exists()

        pdf, error = await utils.to_pdf(file, extra)

        assert error == ""
        assert (Path(tmp) / "data.txt").read_text() == "hi"
        assert pdf == Path(tmp) / "file with spaces.pdf"


@pytest.mark.anyio
async def test_vera_check_verapdf_not_installed() -> None:
    verapdf = cfg.verapdf
    cfg.verapdf = "missing"
    error = await utils.vera_check(Path("not-used"))
    cfg.verapdf = verapdf
    assert error.startswith("ERROR! `veraPDF` cannot be found.")


@pytest.mark.anyio
@pytest.mark.skipif(not has_vera_pdf, reason="veraPDF is not installed")
async def test_vera_check_fails() -> None:
    # file was download from https://github.com/veraPDF/veraPDF-corpus
    path = Path(__file__).parent / "data" / "veraPDF test suite 6-8-t02-fail-a.pdf"
    error = await utils.vera_check(path)
    assert error.startswith("ERROR! Invalid PDF file.\n```xml\n<?xml version=")


@pytest.mark.anyio
@pytest.mark.skipif(not has_vera_pdf, reason="veraPDF is not installed")
async def test_vera_check_passes() -> None:
    # file was download from https://github.com/veraPDF/veraPDF-corpus
    path = Path(__file__).parent / "data" / "veraPDF test suite 6-8-t02-pass-a.pdf"
    error = await utils.vera_check(path)
    assert error == ""


def test_dash_query_params_empty() -> None:
    dqp = utils.DashQueryParams()
    assert dqp.teams == []
    assert dqp.months == 6
    assert dqp.search == ""
    assert not dqp.sync


def test_dash_query_params_team() -> None:
    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister(team="Light", directory=Path("tests/data/light")))
    cfg.registers.append(EquipmentRegister(team="Mass", directory=Path("tests/data/mass")))

    dqp = utils.DashQueryParams(team="Light")
    assert dqp.teams == ["Light"]

    dqp = utils.DashQueryParams(team="Unknown")
    assert dqp.teams == []

    dqp = utils.DashQueryParams(team=["Light", "Unknown", "Mass"])
    assert dqp.teams == ["Light", "Mass"]


def test_dash_query_params_invalid_months_type() -> None:
    dqp = utils.DashQueryParams(months="None")
    assert dqp.months == 6


@pytest.mark.parametrize(
    ("sync", "expected"),
    [
        ("1", True),
        ("y", True),
        ("yes", True),
        ("on", True),
        ("TRUE", True),
        ("true", True),
        ("0", False),
        ("whatever", False),
    ],
)
def test_dash_query_params_sync(sync: str, expected: bool) -> None:  # noqa: FBT001
    dqp = utils.DashQueryParams(sync=sync)
    assert dqp.sync is expected


def test_get_scope() -> None:
    scope = utils.get_scope()
    assert scope == {"client": "Unknown:0", "http_version": "1.1"}


def test_log_and_href(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO", "uvicorn.error")
    scope = Scope({"client": "127.0.0.1:12345", "http_version": "1.2"})
    href = utils.log_and_href(
        scope, "http://localhost:8080/search?foo=bar", method="POST", a="0", b=[1, 2, 3], c="hello world"
    )

    assert href == "http://localhost:8080/search?a=0&b=1&b=2&b=3&c=hello%20world"

    records = caplog.records
    if sys.version_info[:2] > (3, 10):
        # pytest does not capture the uvicorn log message in Python 3.8 and 3.9
        # but the message is shown when running the webapp and visiting pages in a browser
        assert len(records) == 1
        assert records[0].name == "uvicorn.error"
        assert records[0].levelname == "INFO"
        assert (
            records[0].getMessage()
            == '127.0.0.1:12345 - "POST /search?a=0&b=1&b=2&b=3&c=hello%20world HTTP/1.2" \x1b[32m200 OK\x1b[0m'
        )


def test_word_to_pdf_word_not_installed() -> None:
    utils.word_app = None
    wordapp = cfg.wordapp
    cfg.wordapp = "MS.Word.Object"
    error = utils.word_to_pdf(Path("file.docx"), {})
    cfg.wordapp = wordapp
    assert error == "Converting a docx file is not supported by the server. Microsoft Word is not installed."


@pytest.mark.skipif(not has_word_app, reason="Microsoft Word is not installed")
def test_word_to_pdf_corrupt_file(tmp_path: Path) -> None:
    utils.word_app = None
    file = tmp_path / "example.docx"
    _ = file.write_bytes(b"1,2,3\n4,5,6\n")
    error = utils.word_to_pdf(file, {})
    assert error.startswith("ERROR! Microsoft Word: Word experienced an error trying to open the file.")


@pytest.mark.skipif(not has_word_app, reason="Microsoft Word is not installed")
def test_word_to_pdf_success(tmp_path: Path) -> None:
    path = Path(__file__).parent / "data" / "Hello.docx"

    docx = tmp_path / "Hello.docx"
    _ = docx.write_bytes(path.read_bytes())

    pdf = tmp_path / "Hello.pdf"
    error = utils.word_to_pdf(docx, {})
    assert not error
    assert pdf.exists()
    assert pdf.read_bytes().startswith(b"%PDF-")


@pytest.mark.anyio
@pytest.mark.skipif(not has_word_app, reason="Microsoft Word is not installed")
@pytest.mark.skipif(not has_vera_pdf, reason="veraPDF is not installed")
async def test_convert_to_pdf_word(tmp_path: Path) -> None:
    path = Path(__file__).parent / "data" / "Hello.docx"

    docx = tmp_path / "Hello.docx"
    _ = docx.write_bytes(path.read_bytes())

    extra = Path("tests/data/irradiance.xlsx").read_bytes()  # noqa: ASYNC240
    pdf, error = await utils.convert_to_pdf("Hello.docx", docx.read_bytes(), {"irradiance.xlsx": extra})
    assert not error
    assert pdf["path"].name == "Hello.pdf"
    assert pdf["content"].startswith(b"%PDF-")
    assert pdf["mime_type"] == "application/pdf"
    assert len(pdf["checksum"]) == 32

    with Pdf.open(BytesIO(pdf["content"])) as f:
        attached = f.attachments["irradiance.xlsx"].get_file()
        assert attached.read_bytes() == extra


def test_element_to_component() -> None:  # noqa: PLR0915
    element = fromstring("""
        <equipment keywords="Laser Tape">
            <id>MSLE.O.ABC123</id>
            <manufacturer>MSL</manufacturer>
            <model>ABC</model>
            <serial>123</serial>
            <description>Steel tape laser</description>
            <specifications/>
            <location>Photometric Bench</location>
            <status>Active</status>
            <loggable>false</loggable>
            <traceable>true</traceable>
            <calibrations>
                <measurand quantity="Deviation in Length" calibrationInterval="5">
                    <component name="">
                        <report id="ReportID">
                            <reportIssueDate>2022-10-19</reportIssueDate>
                            <measurementStartDate>2022-09-05</measurementStartDate>
                            <measurementStopDate>2022-09-05</measurementStopDate>
                            <issuingLaboratory>MSL</issuingLaboratory>
                            <technicalProcedure>MSLT.L.023.005</technicalProcedure>
                            <conditions/>
                            <acceptanceCriteria/>
                            <table>
                                <type>double,int,double,int</type>
                                <unit>mm,mm,mm,mm</unit>
                                <header>Minimum,Min Deviation@,Maximum,Max Deviation@</header>
                                <data>
                                    -0.628,8756,0.013,1211
                                    -0.842,6426,0.041,2475
                                </data>
                            </table>
                        </report>
                    </component>
                </measurand>
            </calibrations>
            <maintenance/>
            <alterations/>
            <firmware/>
            <specifiedRequirements/>
            <referenceMaterials/>
            <qualityManual/>
        </equipment>""")  # noqa: S314

    equipment = utils.element_to_component(element)

    assert isinstance(equipment, html.Details)
    assert equipment.children is not None  # pyright: ignore[reportUnknownMemberType]
    assert len(equipment.children) == 19  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    summary = equipment.children[0]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(summary, html.Summary)
    assert isinstance(summary.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert summary.children[0].children == "<equipment"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert summary.children[1].children == " keywords="  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert summary.children[2].children == '"Laser Tape"'  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert summary.children[3].children == ">"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]

    eid = equipment.children[1]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(eid, html.Div)
    assert eid.children[0].children == "<id"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert eid.children[1].children == ">"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert eid.children[2].children == "MSLE.O.ABC123"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert eid.children[3].children == "</id>"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]

    calibrations = equipment.children[11]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(calibrations, html.Details)
    assert calibrations.children is not None  # pyright: ignore[reportUnknownMemberType]
    c = calibrations.children[0]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(c, html.Summary)
    assert isinstance(c.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert c.children[0].children == "<calibrations"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert c.children[1].children == ">"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]

    measurand = calibrations.children[1]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(measurand, html.Details)
    assert measurand.children is not None  # pyright: ignore[reportUnknownMemberType]
    m = measurand.children[0]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(m, html.Summary)
    assert isinstance(m.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert m.children[0].children == "<measurand"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert m.children[1].children == " quantity="  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert m.children[2].children == '"Deviation in Length"'  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert m.children[3].children == " calibrationInterval="  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert m.children[4].children == '"5"'  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert m.children[5].children == ">"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]

    component = measurand.children[1]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(component, html.Details)
    assert component.children is not None  # pyright: ignore[reportUnknownMemberType]
    com = component.children[0]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(com, html.Summary)
    assert isinstance(com.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert com.children[0].children == "<component"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert com.children[1].children == " name="  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert com.children[2].children == '""'  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert com.children[3].children == ">"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]

    report = component.children[1]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(report, html.Details)
    assert report.children is not None  # pyright: ignore[reportUnknownMemberType]
    r = report.children[0]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(r, html.Summary)
    assert isinstance(r.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert r.children[0].children == "<report"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert r.children[1].children == " id="  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert r.children[2].children == '"ReportID"'  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert r.children[3].children == ">"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]

    rid = report.children[1]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(rid.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType]
    assert rid.children[0].children == "<reportIssueDate"  # pyright: ignore[reportUnknownMemberType]
    assert rid.children[1].children == ">"  # pyright: ignore[reportUnknownMemberType]
    assert rid.children[2].children == "2022-10-19"  # pyright: ignore[reportUnknownMemberType]
    assert rid.children[3].children == "</reportIssueDate>"  # pyright: ignore[reportUnknownMemberType]

    ac = report.children[7]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(ac.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType]
    assert ac.children[0].children == "<acceptanceCriteria"  # pyright: ignore[reportUnknownMemberType]
    assert ac.children[1].children == " />"  # pyright: ignore[reportUnknownMemberType]

    table = report.children[8]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(table, html.Details)
    assert table.children is not None  # pyright: ignore[reportUnknownMemberType]
    t = table.children[0]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(t, html.Summary)
    assert isinstance(t.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert t.children[0].children == "<table"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]
    assert t.children[1].children == ">"  # pyright: ignore[reportUnknownMemberType, reportOptionalSubscript]

    typ = table.children[1]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(typ.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType]
    assert typ.children[0].children == "<type"  # pyright: ignore[reportUnknownMemberType]
    assert typ.children[1].children == ">"  # pyright: ignore[reportUnknownMemberType]
    assert typ.children[2].children == "double,int,double,int"  # pyright: ignore[reportUnknownMemberType]
    assert typ.children[3].children == "</type>"  # pyright: ignore[reportUnknownMemberType]

    unit = table.children[2]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(unit.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType]
    assert unit.children[0].children == "<unit"  # pyright: ignore[reportUnknownMemberType]
    assert unit.children[1].children == ">"  # pyright: ignore[reportUnknownMemberType]
    assert unit.children[2].children == "mm,mm,mm,mm"  # pyright: ignore[reportUnknownMemberType]
    assert unit.children[3].children == "</unit>"  # pyright: ignore[reportUnknownMemberType]

    header = table.children[3]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(header.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType]
    assert header.children[0].children == "<header"  # pyright: ignore[reportUnknownMemberType]
    assert header.children[1].children == ">"  # pyright: ignore[reportUnknownMemberType]
    assert header.children[2].children == "Minimum,Min Deviation@,Maximum,Max Deviation@"  # pyright: ignore[reportUnknownMemberType]
    assert header.children[3].children == "</header>"  # pyright: ignore[reportUnknownMemberType]

    data = table.children[4]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(data.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType]
    assert data.children[0].children == "<data"  # pyright: ignore[reportUnknownMemberType]
    assert data.children[1].children == ">"  # pyright: ignore[reportUnknownMemberType]
    assert isinstance(data.children[2], html.Pre)  # pyright: ignore[reportUnknownMemberType]
    assert (
        data.children[2].children  # pyright: ignore[reportUnknownMemberType]
        == "-0.628,8756,0.013,1211\n                                    -0.842,6426,0.041,2475"
    )
    assert data.children[3].children == "</data>"  # pyright: ignore[reportUnknownMemberType]

    assert table.children[-1].children == "</table>"  # pyright: ignore[reportUnknownMemberType]
    assert report.children[-1].children == "</report>"  # pyright: ignore[reportUnknownMemberType]
    assert component.children[-1].children == "</component>"  # pyright: ignore[reportUnknownMemberType]
    assert measurand.children[-1].children == "</measurand>"  # pyright: ignore[reportUnknownMemberType]
    assert calibrations.children[-1].children == "</calibrations>"  # pyright: ignore[reportUnknownMemberType]

    maintenance = equipment.children[12]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(maintenance.children[0], html.Span)  # pyright: ignore[reportUnknownMemberType]
    assert maintenance.children[0].children == "<maintenance"  # pyright: ignore[reportUnknownMemberType]
    assert maintenance.children[1].children == " />"  # pyright: ignore[reportUnknownMemberType]

    assert equipment.children[18].children == "</equipment>"  # pyright: ignore[reportUnknownMemberType]


@pytest.mark.anyio
async def test_recalibrations(tmp_path: Path) -> None:
    mass = tmp_path / "mass"
    mass.mkdir()
    _ = (mass / "m.xml").write_text("""<?xml version='1.0' encoding='utf-8'?>
        <register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment />
        </register>
        """)

    temperature = tmp_path / "temperature"
    temperature.mkdir()
    _ = (temperature / "t.xml").write_text("""<?xml version='1.0' encoding='utf-8'?>
        <register team="Temperature" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.T.001</id>
                <manufacturer>MSL</manufacturer>
                <model>Model</model>
                <serial>abc</serial>
                <description>Temperature probe</description>
                <specifications />
                <location>Spectrophotometer</location>
                <status>Dormant</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations />
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.T.002</id>
                <manufacturer>MSL</manufacturer>
                <model>Model</model>
                <serial>abc</serial>
                <description>Temperature probe</description>
                <specifications />
                <location>Spectrophotometer</location>
                <status>Active</status>
                <loggable />
                <traceable>false</traceable>
                <calibrations />
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.T.003</id>
                <manufacturer>A</manufacturer>
                <model>B</model>
                <serial>C</serial>
                <description>ABC</description>
                <specifications />
                <location>Single Photon</location>
                <status>Active</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations />
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.T.004</id>
                <manufacturer>D</manufacturer>
                <model>D</model>
                <serial>D</serial>
                <description>D</description>
                <specifications />
                <location>Single Photon</location>
                <status>Active</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations>
                    <measurand quantity="Deviation in Length" calibrationInterval="0" />
                </calibrations>
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
        </register>
        """)

    today = date.today()  # noqa: DTZ011
    plus_3_months = today + timedelta(days=90)
    previous = plus_3_months.replace(today.year - 2)

    light = tmp_path / "light"
    light.mkdir()
    _ = (light / "l.xml").write_text(f"""<?xml version='1.0' encoding='utf-8'?>
        <register team="Light" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.O.001</id>
                <manufacturer>MSL</manufacturer>
                <model>Model</model>
                <serial>abc</serial>
                <description>Temperature probe</description>
                <specifications />
                <location>Spectrophotometer</location>
                <status>Active</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations>
                    <measurand quantity="Temperature" calibrationInterval="5">
                        <component name="">
                            <report id="ReportID" enteredBy="Joseph Borbely">
                                <reportIssueDate>{today.year - 1}-10-19</reportIssueDate>
                                <measurementStartDate>{today.year - 1}-09-05</measurementStartDate>
                                <measurementStopDate>{today.year - 1}-09-05</measurementStopDate>
                                <issuingLaboratory>MSL</issuingLaboratory>
                                <technicalProcedure/>
                                <conditions/>
                                <acceptanceCriteria/>
                                <table>
                                    <type>double,double</type>
                                    <unit>mm,mm</unit>
                                    <header>Minimum,Maximum</header>
                                    <data>-0.628,0.013</data>
                                </table>
                            </report>
                        </component>
                    </measurand>
                </calibrations>
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.O.002</id>
                <manufacturer>X</manufacturer>
                <model>Y</model>
                <serial>Z</serial>
                <description>Current source</description>
                <specifications />
                <location>Single Photon</location>
                <status>Active</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations>
                    <measurand quantity="Current DC" calibrationInterval="5">
                        <component name="">
                            <performanceCheck completedDate="2021-04-02" enteredBy="Tom Stewart" checkedBy="Tim Lawson" checkedDate="2021-04-04">
                                <competency>
                                    <worker>Tim Lawson</worker>
                                    <checker>Tom Stewart</checker>
                                    <technicalProcedure>MSLT.E.048.005</technicalProcedure>
                                </competency>
                                <conditions/>
                                <equation>
                                    <value variables="">0.1</value>
                                    <uncertainty variables="">0.01</uncertainty>
                                    <unit>C</unit>
                                    <ranges/>
                                </equation>
                            </performanceCheck>
                        </component>
                    </measurand>
                </calibrations>
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.O.099</id>
                <manufacturer>M</manufacturer>
                <model>N</model>
                <serial>O</serial>
                <description>P</description>
                <specifications />
                <location>Spectrophotometer</location>
                <status>Active</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations>
                    <measurand quantity="Temperature" calibrationInterval="2">
                        <component name="">
                            <report id="ReportID" enteredBy="Joseph Borbely">
                                <reportIssueDate>{previous}</reportIssueDate>
                                <measurementStartDate>{previous}</measurementStartDate>
                                <measurementStopDate>{previous}</measurementStopDate>
                                <issuingLaboratory>MSL</issuingLaboratory>
                                <technicalProcedure/>
                                <conditions/>
                                <acceptanceCriteria/>
                                <table>
                                    <type>double,double</type>
                                    <unit>mm,mm</unit>
                                    <header>Minimum,Maximum</header>
                                    <data>-0.628,0.013</data>
                                </table>
                            </report>
                        </component>
                    </measurand>
                </calibrations>
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.O.721</id>
                <manufacturer>Q</manufacturer>
                <model>Q</model>
                <serial>Q</serial>
                <description>Q</description>
                <specifications />
                <location>Single Photon</location>
                <status>Active</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations>
                    <measurand quantity="Temperature" calibrationInterval="0" />
                    <measurand quantity="Humidity" calibrationInterval="3" />
                </calibrations>
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
        </register>
        """)  # noqa: E501

    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister("Temperature", temperature))
    cfg.registers.append(EquipmentRegister("Mass", mass))
    cfg.registers.append(EquipmentRegister("Light", light))

    table, is_valid, synced = await utils.recalibrations(teams=["Temperature", "Mass", "Light"], months=6, sync=True)
    assert synced
    assert is_valid == {"Temperature": True, "Mass": False, "Light": True}
    assert table == [
        {
            "ID": "MSLE.T.003",
            "Team": "Temperature",
            "Due Date": today.isoformat(),
            "Overdue?": "Yes (uncalibrated)",
            "Description": "ABC",
            "Manufacturer": "A",
            "Model": "B",
            "Serial": "C",
        },
        {
            "ID": "MSLE.O.002",
            "Team": "Light",
            "Due Date": "2026-04-02",
            "Overdue?": "Yes",
            "Description": "Current source",
            "Manufacturer": "X",
            "Model": "Y",
            "Serial": "Z",
        },
        {
            "ID": "MSLE.O.099",
            "Team": "Light",
            "Due Date": previous.replace(previous.year + 2).isoformat(),
            "Overdue?": "No",
            "Description": "P",
            "Manufacturer": "M",
            "Model": "N",
            "Serial": "O",
        },
        {
            "ID": "MSLE.O.721",
            "Team": "Light",
            "Due Date": today.isoformat(),
            "Overdue?": "Yes (uncalibrated)",
            "Description": "Q",
            "Manufacturer": "Q",
            "Model": "Q",
            "Serial": "Q",
        },
    ]


@pytest.mark.anyio
async def test_search(tmp_path: Path) -> None:
    mass = tmp_path / "mass"
    mass.mkdir()
    _ = (mass / "m.xml").write_text("""<?xml version='1.0' encoding='utf-8'?>
        <register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment />
        </register>
        """)

    temperature = tmp_path / "temperature"
    temperature.mkdir()
    _ = (temperature / "t.xml").write_text("""<?xml version='1.0' encoding='utf-8'?>
        <register team="Temperature" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.T.001</id>
                <manufacturer>MSL</manufacturer>
                <model>Model</model>
                <serial>abc</serial>
                <description>Temperature probe</description>
                <specifications />
                <location>Contact thermometry lab</location>
                <status>Dormant</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations />
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.T.002</id>
                <manufacturer>MSL</manufacturer>
                <model>Model</model>
                <serial>abc</serial>
                <description>Temperature probe</description>
                <specifications />
                <location>Spectrophotometer</location>
                <status>Active</status>
                <loggable />
                <traceable>false</traceable>
                <calibrations />
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
        </register>
        """)

    light = tmp_path / "light"
    light.mkdir()
    _ = (light / "l.xml").write_text("""<?xml version='1.0' encoding='utf-8'?>
        <register team="Light" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.O.001</id>
                <manufacturer>M</manufacturer>
                <model>M</model>
                <serial>M</serial>
                <description>Alien</description>
                <specifications />
                <location>Spectrophotometer</location>
                <status>Active</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations/>
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.O.002</id>
                <manufacturer>X</manufacturer>
                <model>Y</model>
                <serial>Z</serial>
                <description>Current source</description>
                <specifications />
                <location>Single Photon</location>
                <status>Active</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations />
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
        </register>
        """)

    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister("Temperature", temperature))
    cfg.registers.append(EquipmentRegister("Mass", mass))
    cfg.registers.append(EquipmentRegister("Light", light))

    table, is_valid, synced, error = await utils.search(
        teams=["Temperature", "Mass", "Light"], text="Spectrophotometer", sync=True
    )
    assert error == ""
    assert synced
    assert is_valid == {"Temperature": True, "Mass": False, "Light": True}
    assert table == [
        {
            "ID": "MSLE.T.002",
            "Team": "Temperature",
            "Location": "Spectrophotometer",
            "Description": "Temperature probe",
            "Manufacturer": "MSL",
            "Model": "Model",
            "Serial": "abc",
        },
        {
            "ID": "MSLE.O.001",
            "Team": "Light",
            "Location": "Spectrophotometer",
            "Description": "Alien",
            "Manufacturer": "M",
            "Model": "M",
            "Serial": "M",
        },
    ]


@pytest.mark.anyio
async def test_assets(tmp_path: Path) -> None:
    mass = tmp_path / "mass"
    mass.mkdir()
    _ = (mass / "m.xml").write_text("""<?xml version='1.0' encoding='utf-8'?>
        <register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment />
        </register>
        """)

    temperature = tmp_path / "temperature"
    temperature.mkdir()
    _ = (temperature / "t.xml").write_text("""<?xml version='1.0' encoding='utf-8'?>
        <register team="Temperature" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.T.001</id>
                <manufacturer>MSL</manufacturer>
                <model>Model</model>
                <serial>abc</serial>
                <description>Temperature probe</description>
                <specifications />
                <location>Contact thermometry lab</location>
                <status>Dormant</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations />
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.T.002</id>
                <manufacturer>MSL</manufacturer>
                <model>Model</model>
                <serial>abc</serial>
                <description>Temperature probe</description>
                <specifications />
                <location>Spectrophotometer</location>
                <status>Active</status>
                <loggable />
                <traceable>false</traceable>
                <calibrations />
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual>
                    <financial>
                        <purchaseYear>2025</purchaseYear>
                        <warrantyExpirationDate>2026-07-31</warrantyExpirationDate>
                        <capitalExpenditure>
                            <assetNumber>12345678</assetNumber>
                            <depreciationStartDate>2015-04-20</depreciationStartDate>
                            <price currency="NZD">150e3</price>
                            <usefulLife>10</usefulLife>
                        </capitalExpenditure>
                    </financial>
                </qualityManual>
            </equipment>
        </register>
        """)

    today = date.today()  # noqa: DTZ011
    five_years_ago = today.replace(year=today.year - 5)
    three_years_in_future = today.replace(year=today.year + 3)

    light = tmp_path / "light"
    light.mkdir()
    _ = (light / "l.xml").write_text(f"""<?xml version='1.0' encoding='utf-8'?>
        <register team="Light" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.O.001</id>
                <manufacturer>M</manufacturer>
                <model>M</model>
                <serial>M</serial>
                <description>Alien</description>
                <specifications />
                <location>Spectrophotometer</location>
                <status>Active</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations/>
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual>
                    <financial>
                        <capitalExpenditure>
                            <assetNumber>987654321</assetNumber>
                            <depreciationStartDate>{five_years_ago.isoformat()}</depreciationStartDate>
                            <price currency="EUR">7654.32</price>
                            <usefulLife>8</usefulLife>
                        </capitalExpenditure>
                    </financial>
                </qualityManual>
            </equipment>
        </register>
        """)

    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister("Temperature", temperature))
    cfg.registers.append(EquipmentRegister("Mass", mass))
    cfg.registers.append(EquipmentRegister("Light", light))

    table, is_valid, synced = await utils.assets(teams=["Temperature", "Mass", "Light"], sync=True)
    assert synced
    assert is_valid == {"Temperature": True, "Mass": False, "Light": True}
    assert table == [
        {
            "ID": "MSLE.T.002",
            "Team": "Temperature",
            "Asset Number": "12345678",
            "Depreciation Start Date": "2015-04-20",
            "Depreciation End Date": "2025-04-20",
            "Depreciated?": "Yes",
            "Price": 150000.0,
            "Currency": "NZD",
            "Manufacturer": "MSL",
            "Model": "Model",
        },
        {
            "ID": "MSLE.O.001",
            "Team": "Light",
            "Asset Number": "987654321",
            "Depreciation Start Date": five_years_ago.isoformat(),
            "Depreciation End Date": three_years_in_future.isoformat(),
            "Depreciated?": "No",
            "Price": 7654.32,
            "Currency": "EUR",
            "Manufacturer": "M",
            "Model": "M",
        },
    ]


@pytest.mark.anyio
async def test_maintenance(tmp_path: Path) -> None:
    mass = tmp_path / "mass"
    mass.mkdir()
    _ = (mass / "m.xml").write_text("""<?xml version='1.0' encoding='utf-8'?>
        <register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment />
        </register>
        """)

    temperature = tmp_path / "temperature"
    temperature.mkdir()
    _ = (temperature / "t.xml").write_text("""<?xml version='1.0' encoding='utf-8'?>
        <register team="Temperature" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.T.001</id>
                <manufacturer>MSL</manufacturer>
                <model>Model</model>
                <serial>abc</serial>
                <description>Temperature probe</description>
                <specifications />
                <location>Spectrophotometer</location>
                <status>Dormant</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations />
                <maintenance />
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.T.002</id>
                <manufacturer>X</manufacturer>
                <model>Y</model>
                <serial>Z</serial>
                <description>Temperature probe</description>
                <specifications />
                <location>Spectrophotometer</location>
                <status>Active</status>
                <loggable />
                <traceable>false</traceable>
                <calibrations />
                <maintenance>
                  <planned>
                    <task dueDate="2024-12-01">Refill helium gas</task>
                  </planned>
                  <completed />
                </maintenance>
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.T.003</id>
                <manufacturer>A</manufacturer>
                <model>B</model>
                <serial>C</serial>
                <description>ABC</description>
                <specifications />
                <location>Single Photon</location>
                <status>Active</status>
                <loggable />
                <traceable>true</traceable>
                <calibrations />
                <maintenance>
                  <planned/>
                  <completed>
                    <task dueDate="2026-08-10" completedDate="2026-08-09" performedBy="Me">Change fan</task>
                  </completed>
                </maintenance>
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
        </register>
        """)

    today = date.today()  # noqa: DTZ011
    plus_45_days = today + timedelta(days=45)
    plus_90_days = today + timedelta(days=90)

    light = tmp_path / "light"
    light.mkdir()
    _ = (light / "l.xml").write_text(f"""<?xml version='1.0' encoding='utf-8'?>
        <register team="Light" xmlns="https://measurement.govt.nz/equipment-register">
            <equipment enteredBy="Joseph Borbely">
                <id>MSLE.O.001</id>
                <manufacturer>MSL</manufacturer>
                <model>Model</model>
                <serial>abc</serial>
                <description>Temperature probe</description>
                <specifications />
                <location>Spectrophotometer</location>
                <status>Dormant</status>
                <loggable />
                <traceable>false</traceable>
                <calibrations/>
                <maintenance>
                  <planned>
                    <task dueDate="{plus_45_days.isoformat()}" performedBy="Company X">Service laser</task>
                    <task dueDate="{plus_90_days.isoformat()}" performedBy="Joe">Clean filter</task>
                  </planned>
                  <completed/>
                </maintenance>
                <alterations />
                <firmware />
                <specifiedRequirements />
                <referenceMaterials />
                <qualityManual />
            </equipment>
        </register>
        """)

    cfg.registers.clear()
    cfg.registers.append(EquipmentRegister("Temperature", temperature))
    cfg.registers.append(EquipmentRegister("Mass", mass))
    cfg.registers.append(EquipmentRegister("Light", light))

    table, is_valid, synced = await utils.maintenance(teams=["Temperature", "Mass", "Light"], months=2, sync=True)
    assert synced
    assert is_valid == {"Temperature": True, "Mass": False, "Light": True}
    assert table == [
        {
            "ID": "MSLE.T.002",
            "Team": "Temperature",
            "Due Date": "2024-12-01",
            "Overdue?": "Yes",
            "Task": "Refill helium gas",
            "Performed By": "",
            "Manufacturer": "X",
            "Model": "Y",
            "Serial": "Z",
        },
        {
            "ID": "MSLE.O.001",
            "Team": "Light",
            "Due Date": plus_45_days.isoformat(),
            "Overdue?": "No",
            "Task": "Service laser",
            "Performed By": "Company X",
            "Manufacturer": "MSL",
            "Model": "Model",
            "Serial": "abc",
        },
    ]
