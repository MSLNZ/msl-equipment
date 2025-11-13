from __future__ import annotations

from pathlib import Path

import pytest
from GTC import (  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
    pr,  # pyright: ignore[reportUnknownVariableType]
    ureal,  # pyright: ignore[reportUnknownVariableType]
)
from lxml import etree
from lxml.builder import E
from msl.equipment_validate import log_warn
from msl.equipment_validate.validate import (
    Info,
    Summary,
    log_debug,
    log_error,
    log_info,
    recursive_validate,
    validate_checked_by_checked_date,
    validate_equation,
    validate_file,
    validate_serialised,
    validate_table,
)

schema_dir = Path(__file__).parent.parent / "src" / "msl" / "equipment_validate" / "schema"


def test_log_debug(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("INFO", "msl.equipment_validate"):
        caplog.clear()
        log_debug("Hello %s", "foo", no_colour=True)
        assert not caplog.records

    with caplog.at_level("DEBUG", "msl.equipment_validate"):
        caplog.clear()
        log_debug("Hello %s", "foo", no_colour=True)
        r = caplog.records
        assert r[0].message == "DEBUG Hello foo"


def test_log_info(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING", "msl.equipment_validate"):
        caplog.clear()
        log_info("Hello %s", "world", no_colour=True)
        assert not caplog.records

    with caplog.at_level("INFO", "msl.equipment_validate"):
        caplog.clear()
        log_info("Hello %s", "world", no_colour=True)
        r = caplog.records
        assert r[0].message == "INFO  Hello world"


def test_log_warn(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("ERROR", "msl.equipment_validate"):
        caplog.clear()
        log_warn("Hello %s", "world", no_colour=True)
        assert not caplog.records

    with caplog.at_level("WARNING", "msl.equipment_validate"):
        caplog.clear()
        log_warn("Hello %s", "world", no_colour=True)
        r = caplog.records
        assert r[0].message == "WARN  Hello world"


def test_log_error_with_uri_scheme(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("ERROR", "msl.equipment_validate")
    caplog.clear()

    file = Path("file.xml").resolve()
    log_error(file="file.xml", line=7, column=3, uri_scheme="vscode", message="foo bar", no_colour=True)

    r = caplog.records
    assert r[0].message == f"ERROR \033]8;;vscode://file/{file}:7:3\033\\file.xml:7:3\033]8;;\033\\\n  foo bar"


@pytest.mark.parametrize("exit_first", [True, False])
def test_recursive_invalid_xml(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
    exit_first: bool,  # noqa: FBT001
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    register = tmp_path / "register.xml"
    _ = register.write_text("""<?xml version='1.0' encoding='utf-8'?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <foo>bar</foo>
""")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")
    summary = recursive_validate(
        files=[register, Path("missing.xml")],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=exit_first,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records
    assert r[0].message == f"ERROR {register}:4:1\n  Premature end of data in tag register line 2, line 4, column 1"

    if exit_first:
        assert len(r) == 1
        assert summary.num_issues == 1
    else:
        assert r[1].message == "ERROR missing.xml:0:0\n  Cannot parse missing.xml"
        assert len(r) == 2
        assert summary.num_issues == 2

    assert summary.num_register == 0


def test_fails_schema(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    register = tmp_path / "register.xml"
    _ = register.write_text("""<?xml version="1.0" encoding="utf-8"?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <equipment enteredBy="">
        <id>MSLE.M.001</id>
        <model>T-1000</model>
        <manufacturer>Sky-net</manufacturer>
        <serial>00000000001</serial>
        <description>A mimetic poly-alloy (liquid metal)</description>
        <specifications/>
        <location>Kibble Balance</location>
        <status>Active</status>
        <loggable>false</loggable>
        <traceable>true</traceable>
        <calibrations/>
        <maintenance/>
        <alterations/>
        <firmware/>
        <specifiedRequirements/>
        <referenceMaterials/>
        <qualityManual/>
    </equipment>
</register>
""")

    caplog.set_level("ERROR", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")
    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=False,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records

    lines = r[0].message.splitlines()
    assert lines[0] == f"ERROR {register}:3:0"
    assert lines[1].startswith("  Element 'equipment', attribute 'enteredBy'")

    assert r[1].message == (
        f"ERROR {register}:5:0\n  Element 'model': This element is not expected. Expected is ( manufacturer )."
    )

    assert len(r) == 2
    assert summary.num_issues == 2
    assert summary.num_register == 1


def test_fails_schema_exit_first(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    register = tmp_path / "register.xml"
    _ = register.write_text("""<?xml version="1.0" encoding="utf-8"?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <equipment enteredBy="">
        <id>MSLE.M.001</id>
        <model>T-1000</model>
        <manufacturer>Sky-net</manufacturer>
        <serial>00000000001</serial>
        <description>A mimetic poly-alloy (liquid metal)</description>
        <specifications/>
        <location>Kibble Balance</location>
        <status>Active</status>
        <loggable>false</loggable>
        <traceable>true</traceable>
        <calibrations/>
        <maintenance/>
        <alterations/>
        <firmware/>
        <specifiedRequirements/>
        <referenceMaterials/>
        <qualityManual/>
    </equipment>
</register>
""")

    caplog.set_level("ERROR", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")
    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=True,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records

    lines = r[0].message.splitlines()
    assert lines[0] == f"ERROR {register}:3:0"
    assert lines[1].startswith("  Element 'equipment', attribute 'enteredBy'")

    assert len(r) == 1
    assert summary.num_issues == 1
    assert summary.num_register == 1


def test_table_bool_value_ok(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = E.table(
        E.type("bool"), E.unit("n/a"), E.header("Flag"), E.data("true\nTrue\nTRUE\n1\nfalse\nFalse\nFALSE\n0")
    )

    caplog.set_level("DEBUG", "msl.equipment_validate")
    assert validate_table(table, info=info)

    r = caplog.records
    assert r[0].message == "DEBUG Validating <table> for 'Name'"
    assert len(r) == 1


def test_table_bool_value_error(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = E.table(
        E.type("bool"), E.unit("n/a"), E.header("Flag"), E.data("true\nTrue\nTRUE\n1\nfalse\nFalse\nFALSE\n0\n2")
    )

    assert not validate_table(table, info=info)

    r = caplog.records
    assert r[0].message == (
        "ERROR register.xml:8:0\n"
        "  Invalid table <data> for 'Name': '2' is not valid for a `bool` data type, must be one of: 0, 1, FALSE, False, TRUE, True, false, true"  # noqa: E501
    )
    assert len(r) == 1


def test_table_int_value_ok(info: Info) -> None:
    table = E.table(E.type("int"), E.unit("n/a"), E.header("int32"), E.data("0\n-2147483648\n2147483647\n1\n-1"))
    assert validate_table(table, info=info)


@pytest.mark.parametrize("value", [-2147483649, 2147483648, 2.3])
def test_table_int_value_error(info: Info, value: int | float, caplog: pytest.LogCaptureFixture) -> None:  # noqa: PYI041
    table = E.table(E.type("int"), E.unit("n/a"), E.header("int32"), E.data(f"0\n1\n-1\n{value}"))
    assert not validate_table(table, info=info)

    if isinstance(value, float):
        msg = "is not valid for an `int` data type"
    else:
        msg = "must be in the range [-2147483648, 2147483647]"

    r = caplog.records
    assert r[0].message == (f"ERROR register.xml:3:0\n  Invalid table <data> for 'Name': '{value}' {msg}")
    assert len(r) == 1


def test_table_double_value_ok(info: Info) -> None:
    table = E.table(E.type("double"), E.unit("n/a"), E.header("double"), E.data("0\n2E-308\n2E+308\n0.000000000000001"))
    assert validate_table(table, info=info)


def test_table_double_value_error(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = E.table(E.type("double"), E.unit("n/a"), E.header("double"), E.data("0\n2e9\nE+300\n1.2"))
    assert not validate_table(table, info=info)

    r = caplog.records
    assert r[0].message == (
        "ERROR register.xml:2:0\n  Invalid table <data> for 'Name': 'E+300' is not valid for a `double` data type"
    )
    assert len(r) == 1


def test_table_string_value_ok(info: Info) -> None:
    table = E.table(E.type("string"), E.unit("n/a"), E.header("string"), E.data("abc\n0\n2E-308\ntrue"))
    assert validate_table(table, info=info)


def test_table_multiple_issues(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,integer,double,string</type>
            <unit>a, b, c</unit>
            <header>w</header>
            <data>1, 0, 1.2, s, s</data>
        </table>
    """

    info.exit_first = False
    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records
    assert r[0].message == (
        "ERROR register.xml:4:0\n"
        "  The table <type> and <unit> have different lengths for 'Name'\n"
        "  type: ['bool', 'integer', 'double', 'string']\n"
        "  unit: ['a', 'b', 'c']"
    )

    assert r[1].message == (
        "ERROR register.xml:5:0\n"
        "  The table <type> and <header> have different lengths for 'Name'\n"
        "  type  : ['bool', 'integer', 'double', 'string']\n"
        "  header: ['w']"
    )

    assert r[2].message == (
        "ERROR register.xml:6:0\n"
        "  The table <data> does not have the expected number of columns for 'Name'\n"
        "  Expected 4 columns, row data is '1, 0, 1.2, s, s'"
    )

    assert r[3].message == (
        "ERROR register.xml:3:0\n  Invalid table <type> 'integer' for 'Name', must be one of: bool, int, double, string"
    )

    assert len(r) == 4


def test_table_exit_first_unit(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,integer,double,string</type>
            <unit>a, b, c</unit>
            <header>w</header>
            <data>1, 0, 1.2, s, s</data>
        </table>
    """

    info.exit_first = True
    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records
    assert r[0].message == (
        "ERROR register.xml:4:0\n"
        "  The table <type> and <unit> have different lengths for 'Name'\n"
        "  type: ['bool', 'integer', 'double', 'string']\n"
        "  unit: ['a', 'b', 'c']"
    )

    assert len(r) == 1


def test_table_exit_first_header(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,integer,double,string</type>
            <unit>a, b, c, d</unit>
            <header>w</header>
            <data>1, 0, 1.2, s, s</data>
        </table>
    """

    info.exit_first = True
    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records
    assert r[0].message == (
        "ERROR register.xml:5:0\n"
        "  The table <type> and <header> have different lengths for 'Name'\n"
        "  type  : ['bool', 'integer', 'double', 'string']\n"
        "  header: ['w']"
    )

    assert len(r) == 1


def test_table_exit_first_data(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,integer,double,string</type>
            <unit>a, b, c, d</unit>
            <header>w, x, y, z</header>
            <data>1, 0, 1.2, s, s</data>
        </table>
    """

    info.exit_first = True
    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:6:0\n"
        "  The table <data> does not have the expected number of columns for 'Name'\n"
        "  Expected 4 columns, row data is '1, 0, 1.2, s, s'"
    )

    assert len(r) == 1


def test_table_exit_first_invalid_type(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,integer,double,string</type>
            <unit>a, b, c, d</unit>
            <header>w, x, y, z</header>
            <data>1, 0, 1.2, s</data>
        </table>
    """

    info.exit_first = True
    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:3:0\n  Invalid table <type> 'integer' for 'Name', must be one of: bool, int, double, string"
    )

    assert len(r) == 1


def test_table_empty_data_row(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,int,double,string</type>
            <unit>a, b, c, d</unit>
            <header>w, x, y, z</header>
            <data>
                  1, 0, 1.2, s

                  1, 0, 1.2, s
            </data>
        </table>
    """

    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records

    assert r[0].message == ("ERROR register.xml:8:0\n  The table <data> cannot have an empty row for 'Name'")

    assert len(r) == 1


def test_table_empty_data_row_begin_at_data(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,int,double,string</type>
            <unit>a, b, c, d</unit>
            <header>w, x, y, z</header>
            <data>1, 0, 1.2, s
                  1, 0, 1.2, s
                  1, 0, 1.2, s

                  1, 0, 1.2, s
            </data>
        </table>
    """

    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records

    assert r[0].message == ("ERROR register.xml:9:0\n  The table <data> cannot have an empty row for 'Name'")

    assert len(r) == 1


def test_table_empty_data_row_exit_first(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,int,double,string</type>
            <unit>a, b, c, d</unit>
            <header>w, x, y, z</header>
            <data>
                  1, 0, 1.2, s
                  1, 0, 1.2, s

                  1, 0, 1.2, s, extra
            </data>
        </table>
    """

    info.exit_first = True
    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records

    assert r[0].message == ("ERROR register.xml:9:0\n  The table <data> cannot have an empty row for 'Name'")

    assert len(r) == 1


def test_table_data_row_issue_1(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,int,double,string</type>
            <unit>a, b, c, d</unit>
            <header>w, x, y, z</header>
            <data>



                  1, 0, 1.2, s
                  1, 0, 1.2, s, s

            </data>
        </table>
    """

    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:11:0\n"
        "  The table <data> does not have the expected number of columns for 'Name'\n"
        "  Expected 4 columns, row data is '1, 0, 1.2, s, s'"
    )

    assert len(r) == 1


def test_table_data_row_issue_2(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,int,double,string</type>
            <unit>a, b, c, d</unit>
            <header>w, x, y, z</header>
            <data>



                  1, 0, 1.2, s
                  1, 0, 1.2, s, s
            </data>
        </table>
    """

    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:11:0\n"
        "  The table <data> does not have the expected number of columns for 'Name'\n"
        "  Expected 4 columns, row data is '1, 0, 1.2, s, s'"
    )

    assert len(r) == 1


def test_table_data_row_issue_3(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,int,double,string</type>
            <unit>a, b, c, d</unit>
            <header>w, x, y, z</header>
            <data>








                  1, 0, 1.2, s, s
            </data>
        </table>
    """

    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:15:0\n"
        "  The table <data> does not have the expected number of columns for 'Name'\n"
        "  Expected 4 columns, row data is '1, 0, 1.2, s, s'"
    )

    assert len(r) == 1


def test_table_invalid_data_exit_first(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    table = """
        <table>
            <type>bool,int,double,string</type>
            <unit>a, b, c, d</unit>
            <header>w, x, y, z</header>
            <data>0, X, 1.2, s
                  1, 0, 1.2, s, XXXXX
            </data>
        </table>
    """

    info.exit_first = True
    assert not validate_table(etree.XML(table), info=info)

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:6:0\n  Invalid table <data> for 'Name': 'X' is not valid for an `int` data type"
    )

    assert len(r) == 1


def test_serialized_unknown_tag(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    serialised = """
        <serialised>
            <format>whatever</format>
        </serialised>
    """

    assert not validate_serialised(etree.XML(serialised), info=info)

    r = caplog.records

    assert r[0].message == ("ERROR register.xml:3:0\n  Don't know how to deserialize 'format'")

    assert len(r) == 1


def test_serialized_invalid_gtc_archive_xml(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    serialised = """
        <serialised>
            <gtcArchive version="1.4.0" xmlns="gtc/xml">whatever</gtcArchive>
        </serialised>
    """

    assert not validate_serialised(etree.XML(serialised), info=info)

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:3:0\n"
        "  Invalid serialised '{gtc/xml}gtcArchive' for 'Name': Invalid XML Archive version '1.4.0'"
    )

    assert len(r) == 1


def test_serialized_invalid_gtc_archive_json(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    serialised = """
        <serialised>
            <gtcArchiveJSON>{"CLASS": "Archive", "version": "https://measurement.govt.nz/gtc/json_1.5.0"}</gtcArchiveJSON>
        </serialised>
    """

    assert not validate_serialised(etree.XML(serialised), info=info)

    r = caplog.records

    assert r[0].message == ("ERROR register.xml:3:0\n  Invalid serialised 'gtcArchiveJSON' for 'Name': 'leaf_nodes'")

    assert len(r) == 1


def test_serialized_valid_gtc_archive_json(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    archive = pr.Archive()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    archive.add(x=ureal(1, 0.1))  # pyright: ignore[reportUnknownMemberType]
    string = pr.dumps_json(archive)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    serialised = f"""
        <serialised>
            <gtcArchiveJSON>{string}</gtcArchiveJSON>
        </serialised>
    """

    caplog.set_level("DEBUG", "msl.equipment_validate")
    assert validate_serialised(etree.XML(serialised), info=info)

    r = caplog.records
    assert r[0].message == "DEBUG Validating <gtcArchiveJSON> for 'Name'"
    assert len(r) == 1


def test_serialized_valid_gtc_archive_xml(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    archive = pr.Archive()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    archive.add(x=ureal(1, 0.1))  # pyright: ignore[reportUnknownMemberType]
    string = pr.dumps_xml(archive)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    serialised = f"""
        <serialised>
            {string}
        </serialised>
    """

    caplog.set_level("DEBUG", "msl.equipment_validate")
    assert validate_serialised(etree.XML(serialised), info=info)

    r = caplog.records
    assert r[0].message == "DEBUG Validating <gtcArchive> for 'Name'"
    assert len(r) == 1


def test_file_invalid_scheme(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    file = """
        <file>
            <url>ftp://server.nz/file.xml</url>
            <sha256>abc</sha256>
        </file>
    """

    assert not validate_file(etree.XML(file), info=info, roots=[], name="file")

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:3:0\n  The url scheme 'ftp' is not yet supported for validation [url=ftp://server.nz/file.xml]"
    )

    assert len(r) == 1


def test_file_fixing_scheme_and_windows_drive(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    file = """
        <file>
            <url>c://host/file</url>
            <sha256>abc</sha256>
        </file>
    """

    assert not validate_file(etree.XML(file), info=info, roots=[], name="file")

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:3:0\n  Cannot find 'c://host/file', include --root arguments if the url is a relative path"
    )

    assert len(r) == 1


@pytest.mark.parametrize(
    "scheme",
    [
        "",
        "file:",  # rfc8089#appendix-E.2
        "file://",
    ],
)
def test_file_relative(info: Info, scheme: str) -> None:
    file = f"""
        <file>
            <url>{scheme}do_not_modify_this_file.txt</url>
            <sha256>699521aa6d52651ef35ee84232f657490eb870543119810f2af8bc68496d693c</sha256>
        </file>
    """

    registers = Path(__file__).parent / "registers"
    assert validate_file(etree.XML(file), info=info, roots=["nope", str(registers)], name="file")


def test_file_cannot_find_with_roots(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    file = """
        <file>

            <url>file.xml</url>
            <sha256>whatever</sha256>
        </file>
    """
    assert not validate_file(etree.XML(file), info=info, roots=["nope", "never/here"], name="file")

    r = caplog.records
    assert r[0].message == ("ERROR register.xml:4:0\n  Cannot find 'file.xml', using the roots: nope, never/here")
    assert len(r) == 1


def test_file_cannot_find_without_roots(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    file = """
        <file>

            <url>file.xml</url>
            <sha256>whatever</sha256>
        </file>
    """
    assert not validate_file(etree.XML(file), info=info, roots=[], name="file")

    r = caplog.records
    assert r[0].message == (
        "ERROR register.xml:4:0\n  Cannot find 'file.xml', include --root arguments if the url is a relative path"
    )
    assert len(r) == 1


@pytest.mark.parametrize(
    "scheme",
    [
        "",
        "file:",  # rfc8089#appendix-E.2
        "file://",
    ],
)
def test_file_absolute(info: Info, scheme: str) -> None:
    register = (Path(__file__).parent / "registers" / "do_not_modify_this_file.txt").resolve()

    file = f"""
        <file>
            <url>{scheme}{register}</url>
            <sha256>699521aa6d52651ef35ee84232f657490eb870543119810f2af8bc68496d693c</sha256>
        </file>
    """

    assert validate_file(etree.XML(file), info=info, roots=[], name="file")


def test_file_absolute_rfc8089_e_2_1(info: Info) -> None:
    # rfc8089#appendix-E.2.1
    # file:///c:/path/to/file.txt
    register = (Path(__file__).parent / "registers" / "do_not_modify_this_file.txt").resolve()
    file = f"""
        <file>
            <url>file:///{register}</url>
            <sha256>699521aa6d52651ef35ee84232f657490eb870543119810f2af8bc68496d693c</sha256>
        </file>
    """
    registers = Path(__file__).parent / "registers"
    assert validate_file(etree.XML(file), info=info, roots=[str(registers)], name="file")


def test_file_relative_rfc8089_e_2_1(info: Info) -> None:
    # rfc8089#appendix-E.2.1, but with a relative path
    file = """
        <file>
            <url>file:///do_not_modify_this_file.txt</url>
            <sha256>699521aa6d52651ef35ee84232f657490eb870543119810f2af8bc68496d693c</sha256>
        </file>
    """
    registers = Path(__file__).parent / "registers"
    assert not validate_file(etree.XML(file), info=info, roots=[str(registers)], name="file")


def test_equation_valid(info: Info) -> None:
    equation = (
        '<equation xmlns="eqn">'
        '  <value variables="x y z">'
        "  0.1 * x \t    "
        "  + 2.3e-5 * pow(y, 2) "
        "  - sqrt(0.2*x) "
        "  + sin((0.1*x+1.1))"
        "  - asin(0.1)"
        "  + cos(0.1)"
        "  - acos(0.1)"
        "  + tan(0.4)"
        "  - atan(0.1)"
        "  + exp(0.2)"
        "  - log(2.1)"
        "  + log10(1.1)"
        "  + 2*pi/z"
        "  </value>"
        '  <uncertainty variables="">1.0</uncertainty>'
        "  <unit>m</unit>"
        "  <ranges>"
        '    <range variable="x">'
        "      <minimum>1</minimum>"
        "      <maximum>2</maximum>"
        "    </range>"
        '    <range variable="y">'
        "      <minimum>10</minimum>"
        "      <maximum>20</maximum>"
        "    </range>"
        '    <range variable="z">'
        "      <minimum>1e2</minimum>"
        "      <maximum>2e2</maximum>"
        "    </range>"
        "  </ranges>"
        "</equation>"
    )
    assert validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})


def test_equation_syntax_error(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="x">1.2 + 0.2*pow(x,3) - ((6+2/x)*sin(1.0) </value>
          <uncertainty variables="">1.0</uncertainty>
          <unit>m</unit>
          <ranges>
            <range variable="x">
              <minimum>1</minimum>
              <maximum>2</maximum>
            </range>
          </ranges>
        </equation>
    """
    assert not validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})

    r = caplog.records
    lines = r[0].message.splitlines()
    assert lines[0] == "ERROR register.xml:3:0"
    assert lines[1].startswith(
        "  Invalid equation syntax for 'Name' [equation=1.2 + 0.2*pow(x,3) - ((6+2/x)*sin(1.0) ]:"
    )
    assert len(r) == 1


def test_equation_name_error(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="x">x+epsilon</value>
          <uncertainty variables="">1.0</uncertainty>
          <unit>m</unit>
          <ranges>
            <range variable="x">
              <minimum>1</minimum>
              <maximum>2</maximum>
            </range>
          </ranges>
        </equation>
    """
    assert not validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})

    r = caplog.records
    assert r[0].message == (
        "ERROR register.xml:3:0\n"
        "  Invalid equation syntax for 'Name' [equation=x+epsilon]: name 'epsilon' is not defined"
    )
    assert len(r) == 1


def test_equation_extra_range_variables(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="x">1.2 + 0.2*acos(0.1*x)</value>
          <uncertainty variables="">1.0</uncertainty>
          <unit>m</unit>
          <ranges>
            <range variable="x">
              <minimum>1</minimum>
              <maximum>2</maximum>
            </range>
            <range variable="y">
              <minimum>10</minimum>
              <maximum>20</maximum>
            </range>
          </ranges>
        </equation>
    """
    assert not validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:2:0\n"
        "  The equation variables and the range variables are not the same for 'Name'\n"
        "  equation variables: x\n"
        "  range variables   : x, y"
    )

    assert len(r) == 1


def test_equation_multiple_variable_issues(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="x">1.2 + 0.2*acos(0.1*x)</value>
          <uncertainty variables="">1.0</uncertainty>
          <unit>m</unit>
          <ranges>
            <range variable="x">
              <minimum>1</minimum>
              <maximum>2</maximum>
            </range>
            <range variable="y">
              <minimum>10</minimum>
              <maximum>20</maximum>
            </range>
            <range variable="x">
              <minimum>1e2</minimum>
              <maximum>2e2</maximum>
            </range>
          </ranges>
        </equation>
    """
    assert not validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:6:0\n  The names of the range variables are not unique for 'Name': ['x', 'y', 'x']"
    )

    assert r[1].message == (
        "ERROR register.xml:2:0\n"
        "  The equation variables and the range variables are not the same for 'Name'\n"
        "  equation variables: x\n"
        "  range variables   : x, y, x"
    )

    assert len(r) == 2


def test_equation_multiple_variable_issues_exit_first(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="x">1.2 + 0.2*acos(0.1*x)</value>
          <uncertainty variables="">1.0</uncertainty>
          <unit>m</unit>
          <ranges>
            <range variable="x">
              <minimum>1</minimum>
              <maximum>2</maximum>
            </range>
            <range variable="x">
              <minimum>1e2</minimum>
              <maximum>2e2</maximum>
            </range>
            <range variable="y">
              <minimum>10</minimum>
              <maximum>20</maximum>
            </range>
          </ranges>
        </equation>
    """
    info.exit_first = True
    assert not validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:6:0\n  The names of the range variables are not unique for 'Name': ['x', 'x', 'y']"
    )

    assert len(r) == 1


def test_equation_variable_and_eval_issues(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="x y">1.2*x + 0.2*arccos(0.1*y)</value>
          <uncertainty variables="">1.0</uncertainty>
          <unit>m</unit>
          <ranges>
            <range variable="x">
              <minimum>1e2</minimum>
              <maximum>2e2</maximum>
            </range>
          </ranges>
        </equation>
    """
    assert not validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:2:0\n"
        "  The equation variables and the range variables are not the same for 'Name'\n"
        "  equation variables: x, y\n"
        "  range variables   : x"
    )

    assert r[1].message == (
        "ERROR register.xml:3:0\n"
        "  Invalid equation syntax for 'Name' [equation=1.2*x + 0.2*arccos(0.1*y)]: name 'arccos' is not defined"
    )

    assert len(r) == 2


def test_equation_variable_and_eval_issues_exit_first(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="x y">1.2*x + 0.2*arccos(0.1*y)</value>
          <uncertainty variables="">1.0</uncertainty>
          <unit>m</unit>
          <ranges>
            <range variable="x">
              <minimum>1e2</minimum>
              <maximum>2e2</maximum>
            </range>
          </ranges>
        </equation>
    """
    info.exit_first = True
    assert not validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:2:0\n"
        "  The equation variables and the range variables are not the same for 'Name'\n"
        "  equation variables: x, y\n"
        "  range variables   : x"
    )

    assert len(r) == 1


def test_equation_value_uncertainty_eval_issues(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="x y">1.2*x + 0.2*arccos(0.1*y)</value>
          <uncertainty variables="">0.1*Pow(0.1, 4)</uncertainty>
          <unit>m</unit>
          <ranges>
            <range variable="x">
              <minimum>1</minimum>
              <maximum>2</maximum>
            </range>
            <range variable="y">
              <minimum>1</minimum>
              <maximum>2</maximum>
            </range>
          </ranges>
        </equation>
    """
    assert not validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:3:0\n"
        "  Invalid equation syntax for 'Name' [equation=1.2*x + 0.2*arccos(0.1*y)]: name 'arccos' is not defined"
    )

    assert r[1].message == (
        "ERROR register.xml:4:0\n"
        "  Invalid equation syntax for 'Name' [equation=0.1*Pow(0.1, 4)]: name 'Pow' is not defined"
    )

    assert len(r) == 2


def test_equation_value_uncertainty_eval_issues_exit_first(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="x y">1.2*x + 0.2*arccos(0.1*y)</value>
          <uncertainty variables="">0.1*Pow(0.1, 4)</uncertainty>
          <unit>m</unit>
          <ranges>
            <range variable="x">
              <minimum>1</minimum>
              <maximum>2</maximum>
            </range>
            <range variable="y">
              <minimum>1</minimum>
              <maximum>2</maximum>
            </range>
          </ranges>
        </equation>
    """
    info.exit_first = True
    assert not validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})

    r = caplog.records

    assert r[0].message == (
        "ERROR register.xml:3:0\n"
        "  Invalid equation syntax for 'Name' [equation=1.2*x + 0.2*arccos(0.1*y)]: name 'arccos' is not defined"
    )

    assert len(r) == 1


def test_equation_divide_by_zero_ok(info: Info) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="x">1/(1-x)</value>
          <uncertainty variables="">0.1</uncertainty>
          <unit>m</unit>
          <ranges>
            <range variable="x">
              <minimum>-0.99</minimum>
              <maximum>0.99</maximum>
            </range>
          </ranges>
        </equation>
    """
    assert validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})


def test_equation_math_domain_error_ok(info: Info, recwarn: pytest.WarningsRecorder) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="x">asin(1+x)</value>
          <uncertainty variables="">0.1</uncertainty>
          <unit>m</unit>
          <ranges>
            <range variable="x">
              <minimum>-0.99</minimum>
              <maximum>0.99</maximum>
            </range>
          </ranges>
        </equation>
    """

    assert len(recwarn) == 0
    assert validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})
    assert len(recwarn) == 0


def test_equation_no_variables(info: Info) -> None:
    equation = """
        <equation xmlns="eqn">
          <value variables="">1</value>
          <uncertainty variables="">0.1</uncertainty>
          <unit>m</unit>
          <ranges/>
        </equation>
    """
    assert validate_equation(etree.XML(equation), info=info, ns_map={"reg": "eqn"})


@pytest.mark.parametrize("exit_first", [False, True])
def test_recursive_with_serialised(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
    exit_first: bool,  # noqa: FBT001
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    archive = pr.Archive()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    archive.add(x=ureal(1, 0.1))  # pyright: ignore[reportUnknownMemberType]
    string = pr.dumps_json(archive)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    register = tmp_path / "register.xml"
    _ = register.write_text(f"""<?xml version='1.0' encoding='utf-8'?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <equipment enteredBy="Joseph Borbely">
        <id>MSLE.P.001</id>
        <manufacturer>MSL</manufacturer>
        <model>ABC</model>
        <serial>123</serial>
        <description>Something</description>
        <specifications/>
        <location>CMM Lab</location>
        <status>Active</status>
        <loggable/>
        <traceable>false</traceable>
        <calibrations>
            <measurand quantity="Humidity" calibrationInterval="5">
                <component name="">
                    <report id="Humidity/2023/1024" enteredBy="Joseph Borbely">
                        <reportIssueDate>2023-08-18</reportIssueDate>
                        <measurementStartDate>2023-08-08</measurementStartDate>
                        <measurementStopDate>2023-08-14</measurementStopDate>
                        <issuingLaboratory>MSL</issuingLaboratory>
                        <technicalProcedure>MSLT.H.062</technicalProcedure>
                        <conditions/>
                        <acceptanceCriteria/>
                        <serialised>
                            <gtcArchiveJSON>X{string}</gtcArchiveJSON>
                        </serialised>
                        <serialised>
                            <gtcArchiveJSON>{string}</gtcArchiveJSON>
                        </serialised>
                        <serialised>
                            <gtcArchiveJSON>X{string}</gtcArchiveJSON>
                        </serialised>
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
    </equipment>
</register>
""")

    caplog.set_level("ERROR", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")

    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=exit_first,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records
    assert r[0].message.startswith(f"ERROR {register}:26:0\n  Invalid serialised")
    if exit_first:
        assert len(r) == 1
        assert summary.num_issues == 1
    else:
        assert r[1].message.startswith(f"ERROR {register}:32:0\n  Invalid serialised")
        assert len(r) == 2
        assert summary.num_issues == 2


@pytest.mark.parametrize("exit_first", [False, True])
def test_recursive_with_digital_report(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
    exit_first: bool,  # noqa: FBT001
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    url = (Path(__file__).parent / "registers" / "do_not_modify_this_file.txt").resolve()

    register = tmp_path / "register.xml"
    _ = register.write_text(f"""<?xml version='1.0' encoding='utf-8'?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <equipment enteredBy="Joseph Borbely">
        <id>MSLE.P.001</id>
        <manufacturer>MSL</manufacturer>
        <model>ABC</model>
        <serial>123</serial>
        <description>Something</description>
        <specifications/>
        <location>CMM Lab</location>
        <status>Active</status>
        <loggable/>
        <traceable>false</traceable>
        <calibrations>
            <measurand quantity="Humidity" calibrationInterval="5">
                <component name="">
                    <digitalReport format="MSL PDF/A-3" id="Pressure/2025/092">
                        <url>{url}</url>
                        <sha256>{"a" * 64}</sha256>
                    </digitalReport>
                    <digitalReport format="MSL PDF/A-3" id="Pressure/2025/092">
                        <url>{url}</url>
                        <sha256>{"a" * 64}</sha256>
                    </digitalReport>
                </component>
            </measurand>
        </calibrations>
        <maintenance/>
        <alterations/>
        <firmware/>
        <specifiedRequirements/>
        <referenceMaterials/>
        <qualityManual/>
    </equipment>
</register>
""")

    caplog.set_level("ERROR", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")

    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=exit_first,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records
    assert r[0].message.startswith(f"ERROR {register}:19:0\n  The SHA-256 checksum")
    if exit_first:
        assert len(r) == 1
        assert summary.num_issues == 1
    else:
        assert r[1].message.startswith(f"ERROR {register}:23:0\n  The SHA-256 checksum")
        assert len(r) == 2
        assert summary.num_issues == 2


@pytest.mark.parametrize("exit_first", [False, True])
def test_recursive_with_equation(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
    exit_first: bool,  # noqa: FBT001
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0
    assert Summary.num_warnings == 0

    register = tmp_path / "register.xml"
    _ = register.write_text("""<?xml version='1.0' encoding='utf-8'?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <equipment enteredBy="Joseph Borbely" checkedBy="Joseph Borbely">
        <id>MSLE.P.001</id>
        <manufacturer>MSL</manufacturer>
        <model>ABC</model>
        <serial>123</serial>
        <description>Something</description>
        <specifications/>
        <location>CMM Lab</location>
        <status>Active</status>
        <loggable/>
        <traceable>false</traceable>
        <calibrations>
            <measurand quantity="Humidity" calibrationInterval="5">
                <component name="">
                    <report id="Humidity/2023/1024" enteredBy="Joseph Borbely" checkedBy="Joseph Borbely">
                        <reportIssueDate>2023-08-18</reportIssueDate>
                        <measurementStartDate>2023-08-08</measurementStartDate>
                        <measurementStopDate>2023-08-14</measurementStopDate>
                        <issuingLaboratory>MSL</issuingLaboratory>
                        <technicalProcedure>MSLT.H.062</technicalProcedure>
                        <conditions/>
                        <acceptanceCriteria/>
                        <equation>
                            <value variables="a">acos(1)</value>
                            <uncertainty variables="">0.1</uncertainty>
                            <unit>m</unit>
                            <ranges/>
                        </equation>
                        <equation>
                            <value variables="x">1+x</value>
                            <uncertainty variables="">0.1</uncertainty>
                            <unit>m</unit>
                            <ranges/>
                        </equation>
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
    </equipment>
</register>
""")

    caplog.set_level("WARNING", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")

    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=exit_first,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records
    assert r[0].message.startswith(f"ERROR {register}:25:0\n  The equation variables")
    if exit_first:
        assert len(r) == 1
        assert summary.num_issues == 1
    else:
        # using variable="a" will check if "cos" is replace before "acos"
        assert r[1].message == (
            f"WARN  {register}:26:0\n"
            "  The variable 'a' is not used in the equation for 'MSL|ABC|123' [equation=acos(1)]"
        )
        assert r[2].message.startswith(f"ERROR {register}:31:0\n  The equation variables")
        assert r[3].message == f"ERROR {register}:3:0\n  checkedBy='Joseph Borbely' specified without a checkedDate"
        assert r[4].message == f"ERROR {register}:17:0\n  checkedBy='Joseph Borbely' specified without a checkedDate"

        assert len(r) == 5
        assert summary.num_issues == 4
        assert summary.num_warnings == 1


@pytest.mark.parametrize("exit_first", [False, True])
def test_recursive_with_file(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
    exit_first: bool,  # noqa: FBT001
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    url = (Path(__file__).parent / "registers" / "do_not_modify_this_file.txt").resolve()

    register = tmp_path / "register.xml"
    _ = register.write_text(f"""<?xml version='1.0' encoding='utf-8'?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <equipment enteredBy="Joseph Borbely">
        <id>MSLE.P.001</id>
        <manufacturer>MSL</manufacturer>
        <model>ABC</model>
        <serial>123</serial>
        <description>Something</description>
        <specifications/>
        <location>CMM Lab</location>
        <status>Active</status>
        <loggable/>
        <traceable>false</traceable>
        <calibrations>
            <measurand quantity="Humidity" calibrationInterval="5">
                <component name="">
                    <report id="Humidity/2023/1024" enteredBy="Joseph Borbely">
                        <reportIssueDate>2023-08-18</reportIssueDate>
                        <measurementStartDate>2023-08-08</measurementStartDate>
                        <measurementStopDate>2023-08-14</measurementStopDate>
                        <issuingLaboratory>MSL</issuingLaboratory>
                        <technicalProcedure>MSLT.H.062</technicalProcedure>
                        <conditions/>
                        <acceptanceCriteria/>
                        <file>
                            <url>{url}</url>
                            <sha256>{"a" * 64}</sha256>
                        </file>
                        <file>
                            <url>{url}</url>
                            <sha256>{"a" * 64}</sha256>
                        </file>
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
    </equipment>
</register>
""")

    caplog.set_level("ERROR", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")

    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=exit_first,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records
    assert r[0].message.startswith(f"ERROR {register}:27:0\n  The SHA-256 checksum")
    if exit_first:
        assert len(r) == 1
        assert summary.num_issues == 1
    else:
        assert r[1].message.startswith(f"ERROR {register}:31:0\n  The SHA-256 checksum")
        assert len(r) == 2
        assert summary.num_issues == 2


@pytest.mark.parametrize("exit_first", [False, True])
def test_recursive_with_table(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
    exit_first: bool,  # noqa: FBT001
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    register = tmp_path / "register.xml"
    _ = register.write_text("""<?xml version='1.0' encoding='utf-8'?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <equipment enteredBy="Joseph Borbely">
        <id>MSLE.P.001</id>
        <manufacturer>MSL</manufacturer>
        <model>ABC</model>
        <serial>123</serial>
        <description>Something</description>
        <specifications/>
        <location>CMM Lab</location>
        <status>Active</status>
        <loggable/>
        <traceable>false</traceable>
        <calibrations>
            <measurand quantity="Humidity" calibrationInterval="5">
                <component name="">
                    <report id="Humidity/2023/1024" enteredBy="Joseph Borbely">
                        <reportIssueDate>2023-08-18</reportIssueDate>
                        <measurementStartDate>2023-08-08</measurementStartDate>
                        <measurementStopDate>2023-08-14</measurementStopDate>
                        <issuingLaboratory>MSL</issuingLaboratory>
                        <technicalProcedure>MSLT.H.062</technicalProcedure>
                        <conditions/>
                        <acceptanceCriteria/>
                        <table>
                            <type>bool,int</type>
                            <unit>a,b</unit>
                            <header>a,b</header>
                            <data>1, 0, s</data>
                        </table>
                        <table>
                            <type>bool,int</type>
                            <unit>a,b</unit>
                            <header>a,b</header>
                            <data>

                            1, 0, s

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
    </equipment>
</register>
""")

    caplog.set_level("ERROR", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")

    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=exit_first,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records
    assert r[0].message.startswith(f"ERROR {register}:29:0\n  The table <data>")
    if exit_first:
        assert len(r) == 1
        assert summary.num_issues == 1
    else:
        assert r[1].message.startswith(f"ERROR {register}:37:0\n  The table <data>")
        assert len(r) == 2
        assert summary.num_issues == 2


@pytest.mark.parametrize("exit_first", [False, True])
def test_recursive_with_cvd(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
    exit_first: bool,  # noqa: FBT001
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    register = tmp_path / "register.xml"
    _ = register.write_text("""<?xml version='1.0' encoding='utf-8'?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <equipment enteredBy="Joseph Borbely">
        <id>MSLE.P.001</id>
        <manufacturer>MSL</manufacturer>
        <model>ABC</model>
        <serial>123</serial>
        <description>Something</description>
        <specifications/>
        <location>CMM Lab</location>
        <status>Active</status>
        <loggable/>
        <traceable>false</traceable>
        <calibrations>
            <measurand quantity="Humidity" calibrationInterval="5">
                <component name="">
                    <report id="Humidity/2023/1024" enteredBy="Joseph Borbely">
                        <reportIssueDate>2023-08-18</reportIssueDate>
                        <measurementStartDate>2023-08-08</measurementStartDate>
                        <measurementStopDate>2023-08-14</measurementStopDate>
                        <issuingLaboratory>MSL</issuingLaboratory>
                        <technicalProcedure>MSLT.H.062</technicalProcedure>
                        <conditions/>
                        <acceptanceCriteria/>
                        <cvdCoefficients>
                            <R0>100.0189</R0>
                            <A>3.913e-3</A>
                            <B>-6.056e-7</B>
                            <C>1.372e-12</C>
                            <D>0</D>
                            <uncertainty variables="">0.0056*x</uncertainty>
                            <range>
                                <minimum>-10</minimum>
                                <maximum>70</maximum>
                            </range>
                        </cvdCoefficients>
                        <cvdCoefficients>
                            <R0>100.0189</R0>
                            <A>3.913e-3</A>
                            <B>-6.056e-7</B>
                            <C>1.372e-12</C>
                            <D>0</D>
                            <uncertainty variables="">0.0056*x</uncertainty>
                            <range>
                                <minimum>-10</minimum>
                                <maximum>70</maximum>
                            </range>
                        </cvdCoefficients>
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
    </equipment>
</register>
""")

    caplog.set_level("ERROR", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")

    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=exit_first,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records
    assert r[0].message.startswith(f"ERROR {register}:31:0\n  Invalid equation syntax")
    if exit_first:
        assert len(r) == 1
        assert summary.num_issues == 1
    else:
        assert r[1].message.startswith(f"ERROR {register}:43:0\n  Invalid equation syntax")
        assert len(r) == 2
        assert summary.num_issues == 2


@pytest.mark.parametrize("exit_first", [False, True])
def test_recursive_with_connections(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
    exit_first: bool,  # noqa: FBT001
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    register = tmp_path / "register.xml"
    _ = register.write_text("""<?xml version='1.0' encoding='utf-8'?>
<connections>
  <connection/>
  <connection><apple>8</apple></connection>
</connections>
""")

    caplog.set_level("ERROR", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")

    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=exit_first,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records
    assert r[0].message.startswith(f"ERROR {register}:3:0\n  Element 'connection': Missing child element(s)")
    if exit_first:
        assert len(r) == 1
        assert summary.num_issues == 1
    else:
        assert r[1].message.startswith(f"ERROR {register}:4:0\n  Element 'apple': This element is not expected. ")
        assert len(r) == 2
        assert summary.num_issues == 2


def test_checked_by_checked_date_both_missing(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    element = '<whatever enteredBy="Me"/>'
    assert validate_checked_by_checked_date(etree.XML(element), info=info)
    assert len(caplog.records) == 0


def test_checked_by_checked_date_date_missing(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    element = '<whatever enteredBy="Me" checkedBy="Joe"/>'
    assert not validate_checked_by_checked_date(etree.XML(element), info=info)

    r = caplog.records
    assert r[0].message == ("ERROR register.xml:1:0\n  checkedBy='Joe' specified without a checkedDate")
    assert len(r) == 1


def test_checked_by_checked_date_by_missing(info: Info, caplog: pytest.LogCaptureFixture) -> None:
    element = '<whatever checkedDate="2025-11-13"/>'
    assert not validate_checked_by_checked_date(etree.XML(element), info=info)

    r = caplog.records
    assert r[0].message == ("ERROR register.xml:1:0\n  checkedDate='2025-11-13' specified without a checkedBy")
    assert len(r) == 1


@pytest.mark.parametrize("exit_first", [False, True])
def test_recursive_with_checked_by_checked_date_performance_check(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
    exit_first: bool,  # noqa: FBT001
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    register = tmp_path / "register.xml"
    _ = register.write_text("""<?xml version='1.0' encoding='utf-8'?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <equipment enteredBy="Joseph Borbely">
        <id>MSLE.P.001</id>
        <manufacturer>MSL</manufacturer>
        <model>ABC</model>
        <serial>123</serial>
        <description>Something</description>
        <specifications/>
        <location>CMM Lab</location>
        <status>Active</status>
        <loggable/>
        <traceable>false</traceable>
        <calibrations>
            <measurand quantity="Humidity" calibrationInterval="5">
                <component name="">
                    <performanceCheck completedDate="2023-04-02" enteredBy="Joseph Borbely" checkedBy="Joseph Borbely">
                        <competency>
                            <worker>Joseph Borbely</worker>
                            <checker>Joseph Borbely</checker>
                            <technicalProcedure>MSLT.E.048.005</technicalProcedure>
                        </competency>
                        <conditions/>
                        <equation>
                            <value variables="">1</value>
                            <uncertainty variables="">1</uncertainty>
                            <unit>x</unit>
                            <ranges/>
                        </equation>
                    </performanceCheck>
                    <performanceCheck completedDate="2023-04-02" enteredBy="Joseph Borbely" checkedDate="2023-04-03">
                        <competency>
                            <worker>Joseph Borbely</worker>
                            <checker>Joseph Borbely</checker>
                            <technicalProcedure>MSLT.E.048.005</technicalProcedure>
                        </competency>
                        <conditions/>
                        <equation>
                            <value variables="">1</value>
                            <uncertainty variables="">1</uncertainty>
                            <unit>x</unit>
                            <ranges/>
                        </equation>
                    </performanceCheck>
                </component>
            </measurand>
        </calibrations>
        <maintenance/>
        <alterations/>
        <firmware/>
        <specifiedRequirements/>
        <referenceMaterials/>
        <qualityManual/>
    </equipment>
</register>
""")

    caplog.set_level("ERROR", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")

    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=exit_first,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records
    assert r[0].message == f"ERROR {register}:17:0\n  checkedBy='Joseph Borbely' specified without a checkedDate"
    if exit_first:
        assert len(r) == 1
        assert summary.num_issues == 1
    else:
        assert r[1].message == f"ERROR {register}:31:0\n  checkedDate='2023-04-03' specified without a checkedBy"
        assert len(r) == 2
        assert summary.num_issues == 2


@pytest.mark.parametrize("exit_first", [False, True])
def test_recursive_with_checked_by_checked_date_report(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
    exit_first: bool,  # noqa: FBT001
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    register = tmp_path / "register.xml"
    _ = register.write_text("""<?xml version='1.0' encoding='utf-8'?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <equipment enteredBy="Joseph Borbely">
        <id>MSLE.P.001</id>
        <manufacturer>MSL</manufacturer>
        <model>ABC</model>
        <serial>123</serial>
        <description>Something</description>
        <specifications/>
        <location>CMM Lab</location>
        <status>Active</status>
        <loggable/>
        <traceable>false</traceable>
        <calibrations>
            <measurand quantity="Humidity" calibrationInterval="5">
                <component name="">
                    <report id="Humidity/2023/1024" enteredBy="Joseph Borbely" checkedBy="Joseph Borbely">
                        <reportIssueDate>2023-08-18</reportIssueDate>
                        <measurementStartDate>2023-08-08</measurementStartDate>
                        <measurementStopDate>2023-08-14</measurementStopDate>
                        <issuingLaboratory>MSL</issuingLaboratory>
                        <technicalProcedure>MSLT.H.062</technicalProcedure>
                        <conditions/>
                        <acceptanceCriteria/>
                        <cvdCoefficients>
                            <R0>100.0189</R0>
                            <A>3.913e-3</A>
                            <B>-6.056e-7</B>
                            <C>1.372e-12</C>
                            <D>0</D>
                            <uncertainty variables="">0.0056</uncertainty>
                            <range>
                                <minimum>-10</minimum>
                                <maximum>70</maximum>
                            </range>
                        </cvdCoefficients>
                    </report>
                    <report id="Humidity/2023/1024" enteredBy="Joseph Borbely" checkedDate="2023-08-18">
                        <reportIssueDate>2023-08-18</reportIssueDate>
                        <measurementStartDate>2023-08-08</measurementStartDate>
                        <measurementStopDate>2023-08-14</measurementStopDate>
                        <issuingLaboratory>MSL</issuingLaboratory>
                        <technicalProcedure>MSLT.H.062</technicalProcedure>
                        <conditions/>
                        <acceptanceCriteria/>
                        <cvdCoefficients>
                            <R0>100.0189</R0>
                            <A>3.913e-3</A>
                            <B>-6.056e-7</B>
                            <C>1.372e-12</C>
                            <D>0</D>
                            <uncertainty variables="">0.0056</uncertainty>
                            <range>
                                <minimum>-10</minimum>
                                <maximum>70</maximum>
                            </range>
                        </cvdCoefficients>
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
    </equipment>
</register>
""")

    caplog.set_level("ERROR", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")

    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=exit_first,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records
    assert r[0].message == f"ERROR {register}:17:0\n  checkedBy='Joseph Borbely' specified without a checkedDate"
    if exit_first:
        assert len(r) == 1
        assert summary.num_issues == 1
    else:
        assert r[1].message == f"ERROR {register}:38:0\n  checkedDate='2023-08-18' specified without a checkedBy"
        assert len(r) == 2
        assert summary.num_issues == 2


@pytest.mark.parametrize("exit_first", [False, True])
def test_recursive_with_checked_by_checked_date_equipment(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    reset_summary: None,
    exit_first: bool,  # noqa: FBT001
) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    register = tmp_path / "register.xml"
    _ = register.write_text("""<?xml version='1.0' encoding='utf-8'?>
<register team="Mass" xmlns="https://measurement.govt.nz/equipment-register">
    <equipment enteredBy="Joseph Borbely" checkedDate="2025-04-19">
        <id>MSLE.P.002</id>
        <manufacturer>MSL</manufacturer>
        <model>ABC</model>
        <serial>123</serial>
        <description>Something</description>
        <specifications/>
        <location>CMM Lab</location>
        <status>Active</status>
        <loggable/>
        <traceable>false</traceable>
        <calibrations/>
        <maintenance/>
        <alterations/>
        <firmware/>
        <specifiedRequirements/>
        <referenceMaterials/>
        <qualityManual/>
    </equipment>
    <equipment enteredBy="Joseph Borbely" checkedBy="Joseph Borbely">
        <id>MSLE.P.001</id>
        <manufacturer>MSL</manufacturer>
        <model>ABC</model>
        <serial>123</serial>
        <description>Something</description>
        <specifications/>
        <location>CMM Lab</location>
        <status>Active</status>
        <loggable/>
        <traceable>false</traceable>
        <calibrations/>
        <maintenance/>
        <alterations/>
        <firmware/>
        <specifiedRequirements/>
        <referenceMaterials/>
        <qualityManual/>
    </equipment>
</register>
""")

    caplog.set_level("ERROR", "msl.equipment_validate")

    er_schema = etree.XMLSchema(file=schema_dir / "equipment-register.xsd")
    c_schema = etree.XMLSchema(file=schema_dir / "connections.xsd")

    summary = recursive_validate(
        files=[register],
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=exit_first,
        uri_scheme=None,
        skip_checksum=False,
        no_colour=True,
    )

    r = caplog.records
    assert r[0].message == f"ERROR {register}:3:0\n  checkedDate='2025-04-19' specified without a checkedBy"
    if exit_first:
        assert len(r) == 1
        assert summary.num_issues == 1
    else:
        assert r[1].message == f"ERROR {register}:22:0\n  checkedBy='Joseph Borbely' specified without a checkedDate"
        assert len(r) == 2
        assert summary.num_issues == 2
