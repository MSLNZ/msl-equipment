from __future__ import annotations

import logging
from pathlib import Path

import pytest
from msl.equipment_validate import (
    IS_WINDOWS,
    cli,
    configure_logging,
    configure_parser,
    main,
    maybe_enable_ansi,
    modify_windows_registry,
    recursive,
)
from msl.equipment_validate.validate import Summary
from msl.io import is_admin

root_path = Path(__file__).parent.parent.parent.parent / "tests"


def test_recursive() -> None:
    files = recursive(Path("tests"))
    assert files == [
        Path("tests/resources/config.xml"),
        Path("tests/resources/connections.xml"),
        Path("tests/resources/light/register.xml"),
        # the 'tests/mass/.hidden' directory is not included
        Path("tests/resources/mass/not-a-register.xml"),
        Path("tests/resources/mass/register.xml"),
        Path("tests/resources/mass/register2.xml"),
    ]


def test_recursive_empty() -> None:
    files = recursive(Path("README.md"))
    assert len(files) == 0


@pytest.mark.parametrize(
    ("quiet", "verbose", "level"),
    [
        (0, 0, logging.INFO),
        (0, 1, logging.DEBUG),
        (1, 1, logging.INFO),
        (0, 10, logging.DEBUG),
        (1, 0, logging.WARNING),
        (2, 0, logging.ERROR),
        (2, 1, logging.WARNING),
        (2, 2, logging.INFO),
        (3, 0, logging.CRITICAL),
        (10, 0, logging.CRITICAL),
        (10, 11, logging.DEBUG),
    ],
)
def test_configure_logging(quiet: int, verbose: int, level: int) -> None:
    logger = configure_logging(quiet=quiet, verbose=verbose)
    assert logger.level == level


def test_modify_windows_registry_neither() -> None:
    logger = configure_logging(quiet=0, verbose=0)
    result = modify_windows_registry(log=logger, remove=False, add=False)
    assert result == 0


def test_modify_windows_registry_add(caplog: pytest.LogCaptureFixture) -> None:
    logger = configure_logging(quiet=0, verbose=0)
    caplog.set_level(logging.INFO, "msl")

    code = modify_windows_registry(log=logger, remove=False, add=True)

    if IS_WINDOWS and is_admin():  # GHA runs tests with an admin account
        assert code == 0
        assert len(caplog.records) == 0
        return

    assert code == 1

    if IS_WINDOWS:
        msg = "You must use an elevated (admin) terminal to modify the Windows Registry"
    else:
        msg = "Registering a URI Scheme is only supported on Windows"

    records = caplog.records
    assert len(records) == 1
    assert records[0].levelname == "ERROR"
    assert records[0].message == msg


def test_modify_windows_registry_remove(caplog: pytest.LogCaptureFixture) -> None:
    logger = configure_logging(quiet=0, verbose=0)
    caplog.set_level(logging.INFO, "msl")

    result = modify_windows_registry(log=logger, remove=True, add=False)

    if IS_WINDOWS:
        if result == 0:
            assert len(caplog.records) == 0
        else:
            assert result == 1
            records = caplog.records
            assert len(records) == 1
            assert records[0].levelname == "ERROR"
            assert records[0].message == "You must use an elevated (admin) terminal to modify the Windows Registry"
    else:
        assert result == 1
        records = caplog.records
        assert len(records) == 1
        assert records[0].levelname == "ERROR"
        assert records[0].message == "Unregistering a URI Scheme is only supported on Windows"


def test_maybe_enable_ansi() -> None:
    # just check that no error is raised
    maybe_enable_ansi()


def test_configure_parser() -> None:
    parser = configure_parser()
    args = parser.parse_args(
        [
            "-s",
            "schema.xsd",
            "-r",
            "/home/data",
            "/usr/data",
            "--root",
            "C:/Users/First Last",
            "--link",
            "n++",
            "-AvqRxcVnq",
        ]
    )
    assert args.schema == "schema.xsd"
    assert args.root == ["/home/data", "/usr/data", "C:/Users/First Last"]
    assert args.link == "n++"
    assert args.add_winreg_keys is True
    assert args.verbose == 1
    assert args.quiet == 2
    assert args.remove_winreg_keys is True
    assert args.exit_first is True
    assert args.skip_checksum is True
    assert args.version is True
    assert args.no_colour is True


def test_main(caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]) -> None:  # noqa: PLR0915
    caplog.set_level(logging.INFO, "msl")

    with pytest.raises(SystemExit) as e:
        main([str(root_path)])

    assert e.value.code == 3  # 3 issues

    out, err = capsys.readouterr()
    assert not err
    assert "Found 3 issues" in out

    r = caplog.records
    assert r[0].levelname == "INFO"
    assert r[0].message == "============================== Validation Starts =============================="
    assert r[1].levelname == "INFO"
    assert r[1].message.startswith("platform:")
    assert r[2].levelname == "INFO"
    assert r[2].message.startswith("msl-equipment-validate:")
    assert r[3].levelname == "INFO"
    assert r[3].message.startswith("lxml:")
    assert r[4].levelname == "INFO"
    assert r[4].message.startswith("GTC:")
    assert r[5].levelname == "INFO"
    assert r[5].message.startswith("equipment-register:")
    assert r[6].levelname == "INFO"
    assert r[6].message.startswith("connections:")

    assert r[7].levelname == "INFO"
    assert r[7].message == ""

    assert r[8].levelname == "INFO"
    assert r[8].message.endswith("connections.xml")

    assert r[9].levelname == "INFO"
    assert r[9].message.endswith("register.xml")

    assert r[10].levelname == "INFO"
    assert r[10].message.endswith("register.xml")

    assert r[11].levelname == "ERROR"
    lines = r[11].message.splitlines()
    assert lines[0].endswith("register.xml:127:0")
    assert lines[1].startswith("  The SHA-256 checksum")
    assert lines[2] == "  expected: 7a91267cfb529388a99762b891ee4b7a12463e83b5d55809f76a0c8e76c71886"
    assert lines[3] == "  <sha256>: 70d79d2eb24dc2515faaf4ab7fa3540e5a73ca6080181908a0ea87a309293609"

    assert r[12].levelname == "INFO"
    assert r[12].message.endswith("register2.xml")

    assert r[13].levelname == "ERROR"
    lines = r[13].message.splitlines()
    assert lines[0].endswith("register2.xml:32:0")
    assert lines[1].startswith("  Cannot find")

    assert r[14].levelname == "ERROR"
    lines = r[14].message.splitlines()
    assert lines[0].endswith("register2.xml:26:0")
    assert lines[1].startswith("  Cannot find")

    assert r[15].levelname == "INFO"
    assert r[15].message == ""

    assert r[16].levelname == "INFO"
    assert r[16].message == "=================================== Summary ==================================="

    assert r[17].levelname == "INFO"
    assert r[17].message == "<connection> 7"

    assert r[18].levelname == "INFO"
    assert r[18].message == "<cvdCoefficients> 1"

    assert r[19].levelname == "INFO"
    assert r[19].message == "<digitalReport> 1"

    assert r[20].levelname == "INFO"
    assert r[20].message == "<equation> 2"

    assert r[21].levelname == "INFO"
    assert r[21].message == "<equipment> 7"

    assert r[22].levelname == "INFO"
    assert r[22].message == "<file> 2"

    assert r[23].levelname == "INFO"
    assert r[23].message == "<register> 3"

    assert r[24].levelname == "INFO"
    assert r[24].message == "<serialised> 0"

    assert r[25].levelname == "INFO"
    assert r[25].message == "<table> 1"

    assert r[26].levelname == "INFO"
    assert r[26].message == ""

    with pytest.raises(IndexError):
        _ = r[27]


def test_cli_add_winreg_keys(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, "msl")

    code = cli(["--add-winreg-keys"])

    if IS_WINDOWS and is_admin():  # GHA runs tests with an admin account
        assert code == 0
        assert len(caplog.records) == 0
        return

    assert code == 1

    r = caplog.records
    assert r[0].levelname == "ERROR"
    if IS_WINDOWS:
        assert r[0].message == "You must use an elevated (admin) terminal to modify the Windows Registry"
    else:
        assert r[0].message == "Modifying the Windows Registry is only valid on Windows"


def test_cli_invalid_schema(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, "msl")
    code = cli(["--schema", "missing.xsd"])
    assert code == 1

    r = caplog.records
    assert r[0].levelname == "ERROR"
    assert r[0].message.endswith("Cannot parse missing.xsd")


def test_cli_version_roots(caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]) -> None:
    caplog.set_level(logging.INFO, "msl")

    code = cli(["--version", "-r", "folder1", "folder2", "-r", "folder3"])
    assert code == 0

    out, err = capsys.readouterr()
    assert not err
    assert not out

    r = caplog.records
    assert r[0].levelname == "INFO"
    assert r[0].message == "============================== Validation Starts =============================="
    assert r[1].levelname == "INFO"
    assert r[1].message.startswith("platform:")
    assert r[2].levelname == "INFO"
    assert r[2].message.startswith("msl-equipment-validate:")
    assert r[3].levelname == "INFO"
    assert r[3].message.startswith("lxml:")
    assert r[4].levelname == "INFO"
    assert r[4].message.startswith("GTC:")
    assert r[5].levelname == "INFO"
    assert r[5].message.startswith("equipment-register:")
    assert r[6].levelname == "INFO"
    assert r[6].message.startswith("connections:")
    assert r[7].levelname == "INFO"
    assert r[7].message == "roots: folder1\n       folder2\n       folder3"
    assert r[8].levelname == "INFO"
    assert r[8].message == ""

    with pytest.raises(IndexError):
        _ = r[9]


def test_cli_missing_xml_file(caplog: pytest.LogCaptureFixture, reset_summary: None) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0
    caplog.set_level(logging.ERROR, "msl")

    code = cli(["missing.xml"])
    assert code == 1

    r = caplog.records
    assert r[0].levelname == "ERROR"
    assert r[0].message.endswith("Cannot parse missing.xml")


def test_cli_missing_directory(caplog: pytest.LogCaptureFixture, reset_summary: None) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0
    caplog.set_level(logging.ERROR, "msl")

    code = cli(["missing"])
    assert code == 1

    r = caplog.records
    assert r[0].levelname == "ERROR"
    assert r[0].message.endswith("Directory not found")
    assert len(r) == 1


def test_cli_no_colour(reset_summary: None, capsys: pytest.CaptureFixture[str]) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    code = cli(["--no-colour", str(root_path)])
    assert code == 3

    out, err = capsys.readouterr()
    assert not err
    assert out == "Found 3 issues [0 schema, 3 additional]\n"


def test_cli_success_skipped(reset_summary: None, capsys: pytest.CaptureFixture[str]) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    code = cli(["--skip-checksum", "-n", str(root_path)])
    assert code == 0

    out, err = capsys.readouterr()
    assert not err
    assert out == "Success, no issues found! [skipped: 3]\n"


def test_cli_success(reset_summary: None, capsys: pytest.CaptureFixture[str]) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    code = cli(["-n", "tests/resources/light/register.xml"])
    assert code == 0

    out, err = capsys.readouterr()
    assert not err
    assert out == "Success, no issues found!\n"


def test_duplicate_eid_exit_first(reset_summary: None, caplog: pytest.LogCaptureFixture) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    caplog.set_level("ERROR", "msl.equipment_validate")

    registers = Path(__file__).parent / "registers"
    assert cli([str(registers), str(root_path), "--no-colour", "--exit-first"]) == 1

    register_a = registers / "duplicate_id_a.xml"
    register_b = registers / "duplicate_id_b.xml"

    r = caplog.records
    assert r[0].message == (
        f"ERROR {register_b}:23:0\n  Duplicate equipment ID 'MSLE.M.002' also found in {register_a}, line 42"
    )
    assert len(r) == 1


def test_duplicate_eid_different_directories(reset_summary: None, caplog: pytest.LogCaptureFixture) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    caplog.set_level("ERROR", "msl.equipment_validate")

    registers_path = Path(__file__).parent / "registers"

    # 2 <id> errors
    # 3 <file> errors
    assert cli(["--no-colour", str(registers_path), str(root_path)]) == 5

    register_a = registers_path / "duplicate_id_a.xml"
    register_b = registers_path / "duplicate_id_b.xml"

    r = caplog.records
    assert r[0].message == (
        f"ERROR {register_b}:23:0\n  Duplicate equipment ID 'MSLE.M.002' also found in {register_a}, line 42"
    )

    assert r[1].levelname == "ERROR"
    lines = r[1].message.splitlines()
    assert lines[0].endswith("register.xml:127:0")
    assert lines[1].startswith("  The SHA-256 checksum")
    assert lines[2] == "  expected: 7a91267cfb529388a99762b891ee4b7a12463e83b5d55809f76a0c8e76c71886"
    assert lines[3] == "  <sha256>: 70d79d2eb24dc2515faaf4ab7fa3540e5a73ca6080181908a0ea87a309293609"

    mass_register = Path(root_path) / "resources" / "mass" / "register.xml"
    assert r[2].message == (
        f"ERROR {mass_register}:4:0\n  Duplicate equipment ID 'MSLE.M.001' also found in {register_a}, line 4"
    )

    assert r[3].levelname == "ERROR"
    lines = r[3].message.splitlines()
    assert lines[0].endswith("register2.xml:32:0")
    assert lines[1].startswith("  Cannot find")

    assert r[4].levelname == "ERROR"
    lines = r[4].message.splitlines()
    assert lines[0].endswith("register2.xml:26:0")
    assert lines[1].startswith("  Cannot find")

    assert len(r) == 5


def test_no_paths(reset_summary: None) -> None:
    assert reset_summary is None
    assert Summary.num_issues == 0

    # 2 <id> errors
    # 3 <file> errors
    assert cli([]) == 5
