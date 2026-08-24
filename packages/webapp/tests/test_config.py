from __future__ import annotations

from pathlib import Path

import pytest
from msl.equipment_webapp.config import Config, EquipmentRegister, SHA256Validation


def test_default() -> None:
    cfg = Config()
    assert cfg.equipment_registers("ignored") == []
    assert cfg.teams == []
    assert cfg.static == "static"
    assert cfg.host == "0.0.0.0"  # noqa: S104
    assert cfg.port == 17025
    assert cfg.nmi == "MSL"
    assert cfg.navbar.logo.src == ""
    assert cfg.navbar.logo.height == 0
    assert cfg.navbar.logo.margin_left == 5
    assert cfg.navbar.logo.margin_right == 25
    assert cfg.navbar.logo.style == {"marginLeft": 5, "marginRight": 25}
    assert cfg.navbar.dark is True
    assert cfg.navbar.colour == "dark"
    assert cfg.registers == []
    assert cfg.pdflatex == "pdflatex"
    assert cfg.git == "git"
    assert cfg.verapdf.startswith("verapdf")
    assert cfg.theme == "BOOTSTRAP"
    assert cfg.set_props_delay == 0.01
    assert cfg.price.format == ",.2f"
    assert cfg.price.decimal == "."
    assert cfg.price.thousands == ","
    assert cfg.price.grouping == [3]
    assert cfg.price.currency.prefix == ""
    assert cfg.price.currency.suffix == ""
    assert cfg.price.format_locale == (
        'd3.formatLocale({"decimal": ".", "thousands": ",", "grouping": [3], '
        '"currency": ["", ""]}).format(",.2f")(params.value)'
    )
    assert cfg.wordapp == "Word.Application"
    assert cfg.sha256_validation == {}


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
    _ = file.write_text(
        """{
            "git": "~/the/git",
            "host": "1.2.3.4",
            "navbar": {
                "colour": "light",
                "dark": false,
                "logo": {
                    "src": "logo.ico",
                    "height": 101,
                    "margin_left": 79,
                    "margin_right": 33
                }
            },
            "nmi": "Any",
            "pdflatex": "~/pdflatex/pdflatex.exe",
            "port": "8080",
            "price": {
                "format": "$,.3f",
                "decimal": ",",
                "thousands": " ",
                "grouping": [1, 2],
                "currency": {
                    "prefix": "A",
                    "suffix": "\u00a0€"
                }
            },
            "registers": [
                "tests/data/light"
            ],
            "set_props_delay": 0.025,
            "sha256_validation": {
                "Light": {
                    "skip": true,
                    "roots": []
                },
                "Mass": {
                    "skip": false,
                    "roots": ["M:/data/files"]
                }
            },
            "static": "~/my/assets",
            "theme": "simplex",
            "verapdf": "~/verapdf/verapdf.bat",
            "wordapp": "MS-Word-COM"
            }""",
        encoding="utf-8",
    )

    cfg = Config()
    cfg.load(file)

    home = Path("~").expanduser()

    assert cfg.static == (home / "my/assets").as_posix()
    assert cfg.git == (home / "the/git").as_posix()
    assert cfg.host == "1.2.3.4"
    assert cfg.navbar.logo.src == "logo.ico"
    assert cfg.navbar.logo.height == 101
    assert cfg.navbar.logo.style == {"marginLeft": 79, "marginRight": 33}
    assert cfg.navbar.dark is False
    assert cfg.navbar.colour == "light"
    assert cfg.nmi == "Any"
    assert cfg.pdflatex == (home / "pdflatex/pdflatex.exe").as_posix()
    assert cfg.port == 8080
    assert cfg.price.format == "$,.3f"
    assert cfg.price.decimal == ","
    assert cfg.price.thousands == " "
    assert cfg.price.grouping == [1, 2]
    assert cfg.price.currency.prefix == "A"
    assert cfg.price.currency.suffix == "\u00a0€"
    assert cfg.price.format_locale == (
        'd3.formatLocale({"decimal": ",", "thousands": " ", "grouping": [1, 2], '
        '"currency": ["A", "\u00a0€"]}).format("$,.3f")(params.value)'
    )
    assert cfg.registers == [
        EquipmentRegister(team="Light", directory=Path("tests/data/light")),
    ]
    assert cfg.theme == "simplex"
    assert cfg.verapdf == (home / "verapdf/verapdf.bat").as_posix()
    assert cfg.set_props_delay == 0.025
    assert cfg.wordapp == "MS-Word-COM"

    assert cfg.equipment_registers("Light") == [EquipmentRegister("Light", Path("tests/data/light"))]
    assert cfg.equipment_registers("Mass") == []
    assert cfg.teams == ["Light"]

    assert cfg.sha256_validation == {
        "Light": SHA256Validation(skip=True, roots=[]),
        "Mass": SHA256Validation(skip=False, roots=["M:/data/files"]),
    }

    assert cfg.registers[0].files() == [Path("tests/data/light/register.xml")]


def test_load_logo_src_local_path(tmp_path: Path) -> None:
    file = tmp_path / "example.json"
    _ = file.write_text("""{
            "navbar": {
                "logo": {
                    "src": "~/static/logo.png",
                    "margin_left": 33
                }
            }
        }""")

    cfg = Config()
    cfg.load(file)

    home = Path("~").expanduser()
    assert cfg.navbar.logo.src == (home / "static" / "logo.png").as_posix()
    assert cfg.navbar.logo.height == 50
    assert cfg.navbar.logo.margin_left == 33
    assert cfg.navbar.logo.margin_right == 25
    assert cfg.navbar.logo.style == {"marginLeft": 33, "marginRight": 25}

    assert cfg.navbar.dark is True
    assert cfg.navbar.colour == "dark"
    assert cfg.registers == []
    assert cfg.pdflatex == "pdflatex"
    assert cfg.git == "git"
    assert cfg.verapdf.startswith("verapdf")
    assert cfg.theme == "BOOTSTRAP"
    assert cfg.set_props_delay == 0.01
    assert cfg.price.format == ",.2f"
    assert cfg.price.decimal == "."
    assert cfg.price.thousands == ","
    assert cfg.price.grouping == [3]
    assert cfg.price.currency.prefix == ""
    assert cfg.price.currency.suffix == ""
    assert cfg.wordapp == "Word.Application"
    assert cfg.sha256_validation == {}


def test_load_logo_src_https(tmp_path: Path) -> None:
    file = tmp_path / "example.json"
    _ = file.write_text("""{
            "navbar": {
                "logo": {
                    "src": "https://www.measurement.govt.nz/assets/Uploads/logo.png",
                    "height": 86
                }
            }
        }""")

    cfg = Config()
    cfg.load(file)

    assert cfg.navbar.logo.src == "https://www.measurement.govt.nz/assets/Uploads/logo.png"
    assert cfg.navbar.logo.height == 86
    assert cfg.navbar.logo.margin_left == 5
    assert cfg.navbar.logo.margin_right == 25
    assert cfg.navbar.logo.style == {"marginLeft": 5, "marginRight": 25}

    assert cfg.navbar.dark is True
    assert cfg.navbar.colour == "dark"
    assert cfg.registers == []
    assert cfg.pdflatex == "pdflatex"
    assert cfg.git == "git"
    assert cfg.verapdf.startswith("verapdf")
    assert cfg.theme == "BOOTSTRAP"
    assert cfg.set_props_delay == 0.01
    assert cfg.price.format == ",.2f"
    assert cfg.price.decimal == "."
    assert cfg.price.thousands == ","
    assert cfg.price.grouping == [3]
    assert cfg.price.currency.prefix == ""
    assert cfg.price.currency.suffix == ""
    assert cfg.wordapp == "Word.Application"
    assert cfg.sha256_validation == {}


def test_load_navbar_colour_only(tmp_path: Path) -> None:
    file = tmp_path / "example.json"
    _ = file.write_text("""{
            "navbar": {
                "colour": "light"
            }
        }""")

    cfg = Config()
    cfg.load(file)

    assert cfg.navbar.dark is True
    assert cfg.navbar.colour == "light"

    assert cfg.navbar.logo.src == ""
    assert cfg.navbar.logo.height == 0
    assert cfg.navbar.logo.margin_left == 5
    assert cfg.navbar.logo.margin_right == 25
    assert cfg.navbar.logo.style == {"marginLeft": 5, "marginRight": 25}
    assert cfg.registers == []
    assert cfg.pdflatex == "pdflatex"
    assert cfg.git == "git"
    assert cfg.verapdf.startswith("verapdf")
    assert cfg.theme == "BOOTSTRAP"
    assert cfg.set_props_delay == 0.01
    assert cfg.price.format == ",.2f"
    assert cfg.price.decimal == "."
    assert cfg.price.thousands == ","
    assert cfg.price.grouping == [3]
    assert cfg.price.currency.prefix == ""
    assert cfg.price.currency.suffix == ""
    assert cfg.wordapp == "Word.Application"
    assert cfg.sha256_validation == {}


def test_load_navbar_bad_keyword(tmp_path: Path) -> None:
    file = tmp_path / "example.json"

    # specified color instead of colour
    _ = file.write_text("""{
            "navbar": {
                "color": "light"
            }
        }""")

    cfg = Config()
    with pytest.raises(TypeError, match=r"NavBar.__init__"):
        cfg.load(file)


def test_load_price_keys_missing(tmp_path: Path) -> None:
    file = tmp_path / "example.json"
    _ = file.write_text("""{
            "price": {
                "decimal": "X",
                "format": "anything"
            }
        }""")

    cfg = Config()
    cfg.load(file)
    assert cfg.price.format == "anything"
    assert cfg.price.decimal == "X"
    assert cfg.price.thousands == ","
    assert cfg.price.grouping == [3]
    assert cfg.price.currency.prefix == ""
    assert cfg.price.currency.suffix == ""

    assert cfg.navbar.dark is True
    assert cfg.navbar.colour == "dark"
    assert cfg.navbar.logo.src == ""
    assert cfg.navbar.logo.height == 0
    assert cfg.navbar.logo.margin_left == 5
    assert cfg.navbar.logo.margin_right == 25
    assert cfg.navbar.logo.style == {"marginLeft": 5, "marginRight": 25}
    assert cfg.registers == []
    assert cfg.pdflatex == "pdflatex"
    assert cfg.git == "git"
    assert cfg.verapdf.startswith("verapdf")
    assert cfg.theme == "BOOTSTRAP"
    assert cfg.set_props_delay == 0.01
    assert cfg.wordapp == "Word.Application"
    assert cfg.sha256_validation == {}


def test_load_price_bad_keyword(tmp_path: Path) -> None:
    file = tmp_path / "example.json"
    _ = file.write_text("""{
            "price": {
                "decimal": "X",
                "unknown": "anything"
            }
        }""")

    cfg = Config()
    with pytest.raises(TypeError, match=r"Price.__init__"):
        cfg.load(file)


def test_load_currency_bad_keyword(tmp_path: Path) -> None:
    file = tmp_path / "example.json"
    _ = file.write_text("""{
            "price": {
                "currency": {
                    "unknown": "anything"
                }
            }
        }""")

    cfg = Config()
    with pytest.raises(TypeError, match=r"Currency.__init__"):
        cfg.load(file)


def test_load_sha256_validation_skip_missing(tmp_path: Path) -> None:
    file = tmp_path / "example.json"
    _ = file.write_text("""{
            "sha256_validation": {
                "Light": {
                    "roots": ["any/path/1", "any/path/2"]
                }
            }
        }""")

    cfg = Config()
    cfg.load(file)
    assert cfg.sha256_validation == {"Light": SHA256Validation(skip=False, roots=["any/path/1", "any/path/2"])}

    assert cfg.navbar.dark is True
    assert cfg.navbar.colour == "dark"
    assert cfg.navbar.logo.src == ""
    assert cfg.navbar.logo.height == 0
    assert cfg.navbar.logo.margin_left == 5
    assert cfg.navbar.logo.margin_right == 25
    assert cfg.navbar.logo.style == {"marginLeft": 5, "marginRight": 25}
    assert cfg.registers == []
    assert cfg.pdflatex == "pdflatex"
    assert cfg.price.format == ",.2f"
    assert cfg.price.decimal == "."
    assert cfg.price.thousands == ","
    assert cfg.price.grouping == [3]
    assert cfg.price.currency.prefix == ""
    assert cfg.price.currency.suffix == ""
    assert cfg.git == "git"
    assert cfg.verapdf.startswith("verapdf")
    assert cfg.theme == "BOOTSTRAP"
    assert cfg.set_props_delay == 0.01
    assert cfg.wordapp == "Word.Application"


def test_load_sha256_validation_roots_missing(tmp_path: Path) -> None:
    file = tmp_path / "example.json"
    _ = file.write_text("""{
            "sha256_validation": {
                "Length": {
                    "skip": true
                }
            }
        }""")

    cfg = Config()
    cfg.load(file)
    assert cfg.sha256_validation == {"Length": SHA256Validation(skip=True, roots=[])}

    assert cfg.navbar.dark is True
    assert cfg.navbar.colour == "dark"
    assert cfg.navbar.logo.src == ""
    assert cfg.navbar.logo.height == 0
    assert cfg.navbar.logo.margin_left == 5
    assert cfg.navbar.logo.margin_right == 25
    assert cfg.navbar.logo.style == {"marginLeft": 5, "marginRight": 25}
    assert cfg.registers == []
    assert cfg.pdflatex == "pdflatex"
    assert cfg.price.format == ",.2f"
    assert cfg.price.decimal == "."
    assert cfg.price.thousands == ","
    assert cfg.price.grouping == [3]
    assert cfg.price.currency.prefix == ""
    assert cfg.price.currency.suffix == ""
    assert cfg.git == "git"
    assert cfg.verapdf.startswith("verapdf")
    assert cfg.theme == "BOOTSTRAP"
    assert cfg.set_props_delay == 0.01
    assert cfg.wordapp == "Word.Application"


def test_load_sha256_validation_bad_keyword(tmp_path: Path) -> None:
    file = tmp_path / "example.json"
    _ = file.write_text("""{
            "sha256_validation": {
                "Light": {
                    "bad": 7
                }
            }
        }""")

    cfg = Config()
    with pytest.raises(TypeError, match=r"SHA256Validation.__init__"):
        cfg.load(file)
