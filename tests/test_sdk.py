from __future__ import annotations

import ctypes
import sys

import pytest

from msl.equipment import SDK, Connection, Equipment
from msl.equipment.interfaces.sdk import parse_sdk_address
from msl.examples.loadlib import EXAMPLES_DIR

suffix = "arm64" if sys.platform == "darwin" else "64"


@pytest.mark.parametrize(
    "address",
    [
        "",
        "SDK",
        "sdk",
        "SDK:",
        "SDK::",
        "COM2",
        "ASRL7::INSTR",
        "ASRL/dev/ttyS1",
        "SOCKET::192.168.1.100::5000",
        "Prologix::192.168.1.110::1234::6",
    ],
)
def test_parse_address_none(address: str) -> None:
    assert parse_sdk_address(address) is None


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("SDK::whatever", "whatever"),
        ("SDK::file.dll", "file.dll"),
        ("SDK::/home/username/file.so", "/home/username/file.so"),
        (r"SDK::C:\a\b\c\file.dll", r"C:\a\b\c\file.dll"),
        ("SDK::C:\\name with\\spaces -_ [v1.2]\\s d k.dll", "C:\\name with\\spaces -_ [v1.2]\\s d k.dll"),
    ],
)
def test_parse_address_some(address: str, expected: str) -> None:
    parsed = parse_sdk_address(address)
    assert parsed is not None
    assert parsed.path == expected


def test_connect() -> None:
    path = EXAMPLES_DIR / f"cpp_lib{suffix}"
    e = Equipment(connection=Connection(f"SDK::{path}"))
    c = e.connect()
    assert isinstance(c, SDK)
    assert c.assembly is None
    assert c.gateway is None
    assert c.path.startswith(str(path))
    assert c.sdk.add(1, 1) == 2  # noqa: PLR2004


def test_direct_invalid_address() -> None:
    with pytest.raises(ValueError, match="Invalid SDK interface address"):
        _ = SDK(Equipment(connection=Connection("SDK")))


def test_direct_path() -> None:
    # Connection.address is ignored if `path` is specified
    path = EXAMPLES_DIR / f"cpp_lib{suffix}"
    with SDK(Equipment(connection=Connection("")), libtype="cdll", path=path) as sdk:
        assert sdk.assembly is None
        assert sdk.gateway is None
        assert sdk.path.startswith(str(path))
        assert sdk.sdk.add(1, 1) == 2  # noqa: PLR2004


def test_log_errcheck(caplog: pytest.LogCaptureFixture) -> None:
    path = EXAMPLES_DIR / f"cpp_lib{suffix}"
    with caplog.at_level("DEBUG"):
        sdk = SDK(Equipment(manufacturer="MSL", connection=Connection("")), libtype="cdll", path=path)
        assert sdk.log_errcheck(None, sdk.sdk.add, (ctypes.c_float(1), ctypes.c_float(1))) is None
        assert caplog.messages == [
            "Connecting as SDK<MSL||>",
            f"Loaded {sdk.path}",
            "SDK.add(c_float(1.0), c_float(1.0)) -> None",
        ]
