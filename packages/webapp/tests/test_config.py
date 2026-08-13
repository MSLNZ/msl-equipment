from __future__ import annotations

from pathlib import Path

import pytest
from msl.equipment_webapp.config import Config, EquipmentRegister


def test_default() -> None:
    cfg = Config()
    assert cfg.equipment_registers("ignored") == []
    assert cfg.teams == []
    assert cfg.assets == "assets"
    assert cfg.host == "0.0.0.0"  # noqa: S104
    assert cfg.port == 17025
    assert cfg.nmi == "MSL"
    assert cfg.logo.src == ""
    assert cfg.logo.height == 0
    assert cfg.logo.style == {"marginLeft": cfg.logo.margin_left, "marginRight": cfg.logo.margin_right}
    assert cfg.navbar.dark is True
    assert cfg.navbar.color == "dark"
    assert cfg.registers == []
    assert cfg.pdflatex == "pdflatex"
    assert cfg.git == "git"
    assert cfg.verapdf.startswith("verapdf")
    assert cfg.theme == "BOOTSTRAP"
    assert cfg.wordapp == "Word.Application"


def test_load_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        Config().load("missing.json")


def test_load_empty_dict(tmp_path: Path) -> None:
    file = tmp_path / "example.json"
    _ = file.write_text("{}")
    cfg = Config()
    cfg.load(file)
    assert cfg == Config()


def test_load_not_a_dict(tmp_path: Path) -> None:
    file = tmp_path / "example.json"
    _ = file.write_text("[1,2,3]")
    with pytest.raises(TypeError):
        Config().load(file)


def test_load_all_options(tmp_path: Path) -> None:
    file = tmp_path / "example.json"

    # defining the port as a string is also ok
    _ = file.write_text("""
            {
            "assets": "~/my/assets",
            "git": "~/the/git",
            "host": "1.2.3.4",
            "logo": {
                "src": "logo.ico",
                "height": 101,
                "margin_left": 79,
                "margin_right": 33
            },
            "navbar": {
                "color": "light",
                "dark": false
            },
            "nmi": "Any",
            "pdflatex": "~/pdflatex/pdflatex.exe",
            "port": "8080",
            "registers": [
                "tests/data/light"
            ],
            "theme": "simplex",
            "verapdf": "~/verapdf/verapdf.bat",
            "wordapp": "MS-Word-COM"
            }""")

    cfg = Config()
    cfg.load(file)

    home = Path("~").expanduser()

    assert cfg.assets == (home / "my/assets").as_posix()
    assert cfg.git == (home / "the/git").as_posix()
    assert cfg.host == "1.2.3.4"
    assert cfg.logo.src == "logo.ico"
    assert cfg.logo.height == 101
    assert cfg.logo.style == {"marginLeft": 79, "marginRight": 33}
    assert cfg.navbar.dark is False
    assert cfg.navbar.color == "light"
    assert cfg.nmi == "Any"
    assert cfg.pdflatex == (home / "pdflatex/pdflatex.exe").as_posix()
    assert cfg.port == 8080
    assert cfg.registers == [
        EquipmentRegister("Light", Path("tests/data/light")),
    ]
    assert cfg.theme == "simplex"
    assert cfg.verapdf == (home / "verapdf/verapdf.bat").as_posix()
    assert cfg.wordapp == "MS-Word-COM"

    assert cfg.equipment_registers("Light") == [EquipmentRegister("Light", Path("tests/data/light"))]
    assert cfg.equipment_registers("Mass") == []
    assert cfg.teams == ["Light"]

    assert cfg.registers[0].files() == [Path("tests/data/light/register.xml")]
