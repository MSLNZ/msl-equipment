from __future__ import annotations

import pytest

from msl.equipment.connection_gpib import ConnectionGPIB
from msl.equipment.connection_gpib import _convert_timeout  # noqa
from msl.equipment.connection_gpib import find_listeners


@pytest.mark.parametrize(
    "address",
    ["", "gpi", "COM2", "ASRL/dev/ttyUSB1", "SDK::filename.so", "SOCKET::192.168.1.100::5000", "Prologix::COM6"],
)
def test_parse_address_invalid(address):
    assert ConnectionGPIB.parse_address(address) is None


@pytest.mark.parametrize(
    "address, expected",
    [
        ("GPIB", {"board": 0, "name": None, "pad": None, "sad": None}),
        ("GPIB::", {"board": 0, "name": None, "pad": None, "sad": None}),
        ("GPIB0", {"board": 0, "name": None, "pad": None, "sad": None}),
        ("GPIB3", {"board": 3, "name": None, "pad": None, "sad": None}),
        ("GPIB::voltmeter", {"board": 0, "name": "voltmeter", "pad": None, "sad": None}),
        ("GPIB0::voltmeter", {"board": 0, "name": "voltmeter", "pad": None, "sad": None}),
        ("GPIB16::dmm34401", {"board": 16, "name": "dmm34401", "pad": None, "sad": None}),
        ("GPIB::1", {"board": 0, "name": None, "pad": 1, "sad": None}),
        ("GPIB1::1", {"board": 1, "name": None, "pad": 1, "sad": None}),
        ("GPIB1::11::111", {"board": 1, "name": None, "pad": 11, "sad": 111}),
        ("GPIB10::2::96", {"board": 10, "name": None, "pad": 2, "sad": 96}),
        ("GPIB::1::0::INSTR", {"board": 0, "name": None, "pad": 1, "sad": 0}),
        ("GPIB2::INTFC", {"board": 2, "name": None, "pad": None, "sad": None}),
    ],
)
def test_parse_address_valid(address, expected):
    assert ConnectionGPIB.parse_address(address) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, 0),
        (-1, 0),
        (0, 0),
        (4.1e-6, 1),
        (10e-6, 1),
        (10.1e-6, 2),
        (29.9e-6, 2),
        (30e-6, 2),
        (50e-6, 3),
        (100e-6, 3),
        (123e-6, 4),
        (300e-6, 4),
        (0.0009, 5),
        (0.001, 5),
        (0.002, 6),
        (3e-3, 6),
        (0.005, 7),
        (10e-3, 7),
        (0.025, 8),
        (0.03, 8),
        (0.05, 9),
        (100e-3, 9),
        (0.25, 10),
        (300e-3, 10),
        (0.5, 11),
        (1, 11),
        (1.2, 12),
        (3, 12),
        (5, 13),
        (10.0, 13),
        (25, 14),
        (30, 14),
        (30.001, 15),
        (1e2, 15),
        (299.999, 16),
        (300, 16),
        (301, 17),
        (1.0e3, 17),
        (1001, 17),
        (3600.0, 17),
        (1e9, 17),
    ],
)
def test_parse_address_valid(value, expected):
    assert _convert_timeout(value) == expected


def test_find_listeners():
    listeners = find_listeners(include_sad=False)
    assert isinstance(listeners, list)
