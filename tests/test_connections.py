import pytest

from msl.equipment import Config
from msl.equipment.schema import connections


def test_from_config() -> None:
    connections.clear()
    assert len(connections) == 0

    _ = Config("tests/resources/config.xml")
    assert len(connections) == 7  # noqa: PLR2004
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
        "write_termination": r"\r",
        "timeout": 10.2,
        "check": True,
        "empty": None,
    }

    assert str(connections["MSLE.M.092"]) == "Connection(eid='MSLE.M.092' address='COM1')"

    with pytest.raises(KeyError, match="eid='unknown' cannot be found"):
        _ = connections["unknown"]
