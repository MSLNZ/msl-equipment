import pytest
from msl.equipment_validate import osc8

file = "does-not-exist.txt:4:10"


@pytest.mark.parametrize(
    ("command", "expect"),
    [
        ("vs", False),
        ("vs://ftp", False),
        ("vs://file/", False),
        ("vs://file/a", True),
        ("vs://file/a:10", True),
        ("vs://file/a:10:5", True),
        ("vs://ftp/a:10:5", False),
        ("vs://file//path/to/file.xml:10:5", True),
        ("vs://file//C:\\path\\to\\file.xml:10:5", True),
        ("vs://file//C:\\path\\to file\\ with spaces.xml:10:5", True),
    ],
)
def test_regex(command: str, expect: bool) -> None:  # noqa: FBT001
    assert osc8.uri_scheme_handler(command) is expect


def test_uri_scheme_handler_invalid_command() -> None:
    assert not osc8.uri_scheme_handler(f"pycharm://wrong/{file}")


def test_uri_scheme_handler_unknown() -> None:
    assert not osc8.uri_scheme_handler(f"unknown://file/{file}")


def test_uri_scheme_handler_notepad_pp() -> None:
    assert osc8.uri_scheme_handler(f"n++://file/{file}")


def test_uri_scheme_handler_pycharm() -> None:
    assert osc8.uri_scheme_handler(f"pycharm://file/{file}")


def test_uri_scheme_handler_vs() -> None:
    assert osc8.uri_scheme_handler(f"vs://file/{file}")


def test_uri_scheme_handler_vscode() -> None:
    # vscode registers it's own handler in the Windows registry
    assert not osc8.uri_scheme_handler(f"vscode://file/{file}")


def test_register_uri_scheme_vscode() -> None:
    assert not osc8.register_uri_scheme("vscode")


def test_unregister_uri_scheme_vscode() -> None:
    assert not osc8.unregister_uri_scheme("vscode")
