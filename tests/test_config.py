from __future__ import annotations

import os
from io import BytesIO, StringIO
from pathlib import Path
from xml.etree.ElementTree import ParseError

import pytest

from msl.equipment import Config

ORIGINAL_PATH = os.environ["PATH"]


def teardown_module() -> None:
    os.environ["PATH"] = ORIGINAL_PATH
    _ = os.environ.pop("GPIB_LIBRARY", "")
    _ = os.environ.pop("PYVISA_LIBRARY", "")


def test_parse_errors() -> None:
    with pytest.raises(FileNotFoundError):
        _ = Config("does_not_exist.xml")

    with pytest.raises(ParseError):  # empty XML
        _ = Config(StringIO('<?xml version="1.0" encoding="utf-8" ?>'))


def test_gpib_library() -> None:
    text = """<?xml version="1.0" encoding="utf-8" ?>
    <msl>
        <a>true</a>
        <gpib_library>C:/gpib/ni4822.dll</gpib_library>
        <some_value>1.2345</some_value>
    </msl>
    """
    assert "GPIB_LIBRARY" not in os.environ
    _ = Config(StringIO(text))
    assert os.environ["GPIB_LIBRARY"] == "C:/gpib/ni4822.dll"
    del os.environ["GPIB_LIBRARY"]


def test_pyvisa_library() -> None:
    text = """<?xml version="1.0" encoding="utf-8" ?>
    <msl>
        <some_value>1.2345</some_value>
        <pyvisa_library>@py</pyvisa_library>
        <a>true</a>
    </msl>
    """
    assert "PYVISA_LIBRARY" not in os.environ
    _ = Config(StringIO(text))
    assert os.environ["PYVISA_LIBRARY"] == "@py"
    del os.environ["PYVISA_LIBRARY"]


def test_environ_path(caplog: pytest.LogCaptureFixture) -> None:  # cSpell: ignore caplog
    text = """<?xml version="1.0" encoding="utf-8" ?>
    <msl>
        <a>true</a>
        <path />
        <path recursive="true">docs</path>
        <path>tests</path>
        <path>tests</path>
        <path>tests</path>
        <path>tests/test_config.py</path>
        <path recursive="true">docs</path>
        <some_value>1.2345</some_value>
    </msl>
    """

    splitted = os.environ["PATH"].split(os.pathsep)

    paths = [
        str(Path(path))
        for path in [
            "docs",
            "docs/api",
            "docs/assets",
            "docs/assets/images",
            "docs/javascripts",  # cSpell: ignore javascripts
            "docs/schema",
            "tests",
        ]
    ]
    for path in paths:
        assert path not in splitted

    _ = Config(StringIO(text))

    splitted = os.environ["PATH"].split(os.pathsep)
    for path in paths:
        assert path in splitted
    assert splitted.count("tests") == 1
    assert splitted.count("docs") == 1

    assert caplog.messages == ["skipped append to PATH: None", "skipped append to PATH: 'tests/test_config.py'"]

    os.environ["PATH"] = ORIGINAL_PATH


def test_find_attrib_value() -> None:
    text = """<?xml version="1.0" encoding="utf-8" ?>
    <msl>
        <fruits>
          <fruit colour="red">apple</fruit>
          <fruit colour="orange">orange</fruit>
          <fruit colour="yellow">mango</fruit>
        </fruits>

        <numbers i1="0" i2="-987" f1="1.234" f2="-9.2e-6"/>
        <cases n1="None" n2="none" b1="true" b2="TruE" b3="false" b4="FalSe"/>
        <strings s1="this is a string" s2="[1,2, 3]"/>

        <n1>NONE</n1>
        <n2>none</n2>
        <b1>true</b1>
        <b2>false</b2>
        <b3>TRUE</b3>
        <b4>FALSE</b4>
        <i1>0</i1>
        <i2>-99999</i2>
        <f1>1.23</f1>
        <f2>-1.712e-12</f2>

        <veggie colour="orange">carrot</veggie>
        <veggie colour="red">beet</veggie>
        <veggie colour="green">asparagus</veggie>

    </msl>
    """
    c = Config(StringIO(text))

    assert c.root.tag == "msl"
    assert c.root.text is not None

    assert c.attrib("numbers") == {"i1": 0, "i2": -987, "f1": 1.234, "f2": -9.2e-6}
    assert c.attrib("cases") == {"n1": None, "n2": None, "b1": True, "b2": True, "b3": False, "b4": False}
    assert c.attrib("strings") == {"s1": "this is a string", "s2": "[1,2, 3]"}
    assert c.attrib("missing") == {}
    assert c.attrib("fruits/fruit") == {"colour": "red"}
    assert c.attrib("veggie") == {"colour": "orange"}

    assert c.value("n1") is None
    assert c.value("n2") is None
    assert c.value("b1") is True
    assert c.value("b2") is False
    assert c.value("b3") is True
    assert c.value("b4") is False
    assert c.value("i1") == 0
    assert isinstance(c.value("i1"), int)
    assert c.value("i2") == -99999  # noqa: PLR2004
    assert isinstance(c.value("i2"), int)
    assert c.value("f1") == 1.23  # noqa: PLR2004
    assert c.value("f2") == -1.712e-12  # noqa: PLR2004
    assert c.value("i1", -1) == 0
    assert c.value("missing", "ok") == "ok"
    assert c.value("fruits/fruit") == "apple"
    assert c.value("veggie") == "carrot"
    assert c.value("numbers") is None
    assert c.value("numbers", 0) is None

    assert c.find("invalid") is None
    assert c.findall("invalid") == []

    fruits = c.find("fruits")
    assert fruits is not None
    assert fruits.text is not None
    assert len(c.findall("fruits")) == 1

    assert c.find("fruit") is None
    assert c.findall("fruit") == []

    fruit = c.find("fruits/fruit")
    assert fruit is not None
    assert fruit.text == "apple"
    assert len(c.findall("fruits/fruit")) == 3  # noqa: PLR2004

    veggie = c.find("veggie")
    assert veggie is not None
    assert veggie.text == "carrot"
    assert len(c.findall("veggie")) == 3  # noqa: PLR2004

    numbers = c.find("numbers")
    assert numbers is not None
    assert numbers.text is None
    assert len(c.findall("numbers")) == 1


def test_register_empty_text() -> None:
    text = """<?xml version="1.0" encoding="utf-8" ?>
    <msl>
        <a>A</a>
        <registers>
            <register />
            <register>     </register>
        </registers>
    </msl>
    """
    c = Config(StringIO(text))
    assert len(c.registers) == 0


def test_registers_directory() -> None:
    text = """<?xml version="1.0" encoding="utf-8" ?>
    <msl>
        <a>A</a>
        <registers>
            <register>tests/resources/mass</register>
        </registers>
    </msl>
    """
    # The "bad" XML file in tests/resources/.hidden is ignored
    c = Config(StringIO(text))
    assert len(c.registers) == 1
    assert str(c.registers["Mass"]) == "<Register team='Mass' (3 equipment)>"


def test_registers_file() -> None:
    text = """<?xml version="1.0" encoding="utf-8" ?>
    <msl>
        <a>A</a>
        <registers>
            <register>tests/resources/mass/register.xml</register>
        </registers>
    </msl>
    """
    # The "bad" XML file in tests/resources/.hidden is ignored
    c = Config(StringIO(text))
    assert len(c.registers) == 1
    assert str(c.registers["Mass"]) == "<Register team='Mass' (2 equipment)>"


def test_source_types() -> None:
    path = str(Path(__file__).parent / "resources" / "config.xml")
    assert Config(path).path == path
    assert Config(path.encode()).path == path
    assert Config(Path(path)).path == path
    assert Config(BytesIO(b'<?xml version="1.0"?><msl/>')).path == "<BytesIO>"
    assert Config(StringIO('<?xml version="1.0"?><msl/>')).path == "<StringIO>"

    with Path(path).open("rt") as ft:
        c = Config(ft)
        assert c.path == "<TextIOWrapper>"
        assert str(c) == "<Config path='<TextIOWrapper>'>"
        assert repr(c) == "<Config path='<TextIOWrapper>'>"

    with Path(path).open("rb") as fb:
        c = Config(fb)
        assert c.path == "<BufferedReader>"
        assert str(c) == "<Config path='<BufferedReader>'>"
        assert repr(c) == "<Config path='<BufferedReader>'>"
