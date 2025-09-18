from xml.etree.ElementTree import XML

import pytest

from msl.equipment import Config, Connection
from msl.equipment.enumerations import Backend
from msl.equipment.schema import connections


def test_from_config() -> None:
    connections.clear()
    assert len(connections) == 0

    _ = Config("tests/resources/config.xml")
    assert len(connections) == 7
    assert "MSLE.M.092" in connections
    assert "unknown" not in connections

    assert connections["MSLE.M.092"].address == "COM1"
    assert connections["MSLE.M.001"].address == "GPIB::22"
    assert connections["MSLE.M.100"].address == "TCPIP::dev.company.com::hislip0"
    assert connections["MSLE.O.231"].address == "SDK::library.dll"
    assert connections["MSLE.O.103"].address == "TCPIP::192.168.1.100"

    assert connections["MSLE.O.061"].address == "TCP::192.168.1.100::5000"
    assert connections["MSLE.O.061"].properties == {}

    assert connections["MSLE.O.023"].eid == "MSLE.O.023"
    assert connections["MSLE.O.023"].address == "ASRL/dev/ttyS1"
    assert connections["MSLE.O.023"].backend.value == "PyVISA"
    assert connections["MSLE.O.023"].manufacturer == "Manufacturer"
    assert connections["MSLE.O.023"].model == "Model"
    assert connections["MSLE.O.023"].serial == "Serial"
    assert connections["MSLE.O.023"].properties == {
        "baud_rate": 19200,
        "read_termination": "\n",
        "write_termination": "\r",
        "both_termination": "\r\n",
        "timeout": 10.2,
        "check": True,
        "empty": None,
    }

    assert str(connections["MSLE.M.092"]) == "Connection(eid='MSLE.M.092' address='COM1')"

    with pytest.raises(KeyError, match=r"eid='unknown' cannot be found"):
        _ = connections["unknown"]


def test_properties() -> None:
    c = Connection("A", properties={"a": 0, "b": 1})
    assert c.properties == {"a": 0, "b": 1}

    c = Connection("A", a=0, b=1)
    assert c.properties == {"a": 0, "b": 1}

    c = Connection("A", properties=0)
    assert c.properties == {"properties": 0}


def test_from_xml() -> None:
    text = r"""
        <connection>
            <eid>A</eid>
            <address>B</address>
            <backend>MSL</backend>
            <manufacturer>C</manufacturer>
            <model>D</model>
            <serial>E</serial>
            <properties>
                <foo>bar</foo>
                <b/>
                <empty_termination/>
                <read_termination>\r</read_termination>
                <write_termination>\r\n</write_termination>
                <other_termination>\n</other_termination>
            </properties>
        </connection>
    """

    c = connections._from_xml(XML(text))  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert c.eid == "A"
    assert c.address == "B"
    assert c.backend == Backend.MSL
    assert c.manufacturer == "C"
    assert c.model == "D"
    assert c.serial == "E"

    # empty_termination is ignored
    assert c.properties == {
        "foo": "bar",
        "b": None,
        "read_termination": "\r",
        "write_termination": "\r\n",
        "other_termination": "\n",
    }


def test_unknown_address() -> None:
    with pytest.raises(ValueError, match=r"Cannot determine the interface from the address 'UNKNOWN'"):
        _ = Connection("UNKNOWN").connect()
