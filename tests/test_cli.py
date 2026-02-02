from __future__ import annotations

import errno
import json
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from msl.equipment.cli import cli, main, run_external
from msl.equipment.cli.find import Device, DeviceType, print_stdout
from msl.equipment.interfaces.ftdi import _D2XX  # pyright: ignore[reportPrivateUsage]
from msl.equipment.interfaces.gpib import GPIB

if TYPE_CHECKING:
    from collections.abc import Iterator

gpib_ext = {"win32": "dll", "linux": "so", "darwin": "dylib"}[sys.platform]

"""
Coverage version 7.10.0 added support for the following

[tool.coverage.run]
patch=["subprocess"]

to measure coverage in Python subprocesses, but 7.10 requires Python 3.9+.
"""

no_libusb = sys.platform == "darwin" and sys.version_info[:2] == (3, 8)


@pytest.fixture
def reset_d2xx_gpib() -> Iterator[None]:
    _D2XX.ftd2xx = None
    GPIB.gpib_library = None
    _ = os.environ.pop("D2XX_LIBRARY", "")
    _ = os.environ.pop("GPIB_LIBRARY", "")
    yield
    _D2XX.ftd2xx = None
    GPIB.gpib_library = None
    _ = os.environ.pop("D2XX_LIBRARY", "")
    _ = os.environ.pop("GPIB_LIBRARY", "")


@pytest.mark.parametrize("args", [["--help"], ["help"]])
def test_main_help(args: list[str] | None, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(args)

    out, err = capsys.readouterr()
    assert not err
    assert out.startswith("usage: msl-equipment [OPTIONS] COMMAND [ARGS]...")


def test_help_unknown_command(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        _ = cli(["help", "unknown"])

    out, err = capsys.readouterr()
    assert not out
    assert "invalid choice: 'unknown' (choose from" in err


def test_help_find(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli(["help", "find"]) == 0

    out, err = capsys.readouterr()
    assert not err
    assert out.startswith("usage: msl-equipment find")


def test_find_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        _ = cli(["find", "--help"])

    out, err = capsys.readouterr()
    assert not err
    assert out.startswith("usage: msl-equipment find")


@pytest.mark.parametrize("args", [["help", "validate"], ["validate", "--help"]])
def test_help_validate(args: list[str], capfd: pytest.CaptureFixture[str]) -> None:
    assert cli(args) == 0

    out, err = capfd.readouterr()
    assert not err
    assert out.startswith("usage: msl-equipment-validate")


def test_run_external_unknown_name(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_external("unknown") == errno.ENOENT

    out, err = capsys.readouterr()
    assert not err
    assert out.splitlines() == [
        "Please install the `msl-equipment-unknown` package.",
        "",
        "If you have installed the package, add the directory to where the",
        "msl-equipment-unknown executable is located to the PATH environment variable.",
    ]


def test_run_external_unknown_arg(capfd: pytest.CaptureFixture[str]) -> None:
    assert run_external("validate", "file.xml", "--carrot") == errno.ENOENT

    out, err = capfd.readouterr()
    assert not out
    assert err.rstrip().endswith("msl-equipment-validate: error: unrecognized arguments: --carrot")


def test_cli_unknown(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        _ = cli(["unknown"])

    _, err = capsys.readouterr()
    assert "invalid choice: 'unknown'" in err


@pytest.mark.skipif(no_libusb, reason="libusb1 not available in CI")
def test_cli_find_json(capsys: pytest.CaptureFixture[str]) -> None:
    args = ["find", "-i", "127.0.0.1", "-t", "0.1", "-g", f"tests/resources/gpib.{gpib_ext}", "-j"]
    assert cli(args) == 0

    out, err = capsys.readouterr()
    assert not err

    devices = json.loads(out)
    assert isinstance(devices, list)

    gpib_devices: list[dict[str, str | list[str]]] = [d for d in devices if d["type"] == "GPIB"]  # pyright: ignore[reportUnknownVariableType]
    assert gpib_devices[0]["addresses"] == ["GPIB0::5::INSTR", "GPIB15::11::INSTR"]
    assert gpib_devices[0]["description"] == ""
    assert gpib_devices[0]["webserver"] == ""


@pytest.mark.skipif(no_libusb, reason="libusb1 not available in CI")
def test_cli_find_verbose(
    reset_d2xx_gpib: None, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    caplog.set_level("DEBUG", "msl")  # include msl.loadlib and msl.equipment
    caplog.clear()

    assert reset_d2xx_gpib is None

    libtype = "windll" if sys.platform == "win32" else "cdll"

    gpib_file = Path().parent / "tests" / "resources" / f"gpib.{gpib_ext}"
    args = ["find", "-i", "127.0.0.1", "-v", "-t", "0.1", "-g", str(gpib_file), "-b", "openusb", "-x", "d2xx.ignore"]
    assert cli(args) == 0

    m = caplog.messages
    assert m[0] == "Start searching for devices"
    assert m[1] == "Broadcasting for Prologix ENET-GPIB Controllers: {'127.0.0.1'}"
    assert m[2] == "Broadcasting for LXI devices: {'127.0.0.1'}"
    assert m[3] == "Broadcasting for VXI-11 devices: {'127.0.0.1'}"
    assert m[4] == "Searching for Serial ports"
    assert m[5] == "Searching for GPIB devices (include_sad=False)"
    assert m[6] == f"Loaded {gpib_file.resolve()}"
    assert m[7] == "Searching for USB devices (backend='openusb')"
    assert m[8] == "ValueError: Cannot load the requested 'openusb' PyUSB backend"
    assert m[9] == "Searching for equipment that use the D2XX driver (d2xx_library='d2xx.ignore')"
    assert (
        m[10]
        == f"OSError: Cannot find 'd2xx.ignore' for libtype={libtype!r}, download library from https://ftdichip.com/drivers/d2xx-drivers/"
    )
    assert m[11] == "Waiting approximately 0.1 second(s) for network devices to respond..."
    assert re.match(r"Found \d+ devices", m[12])

    # check stdout, but must ignore all Serial devices
    out, _ = capsys.readouterr()
    lines = out.splitlines()
    index = 0
    while True:
        if lines[index].startswith("GPIB Devices"):
            break
        index += 1

    assert lines[index] == "GPIB Devices"
    assert lines[index + 1] == "  GPIB0::5::INSTR"
    assert lines[index + 2] == "  GPIB15::11::INSTR"


def test_find_print_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    devices = [
        Device(
            type=DeviceType.ASRL,
            addresses=["COM1"],
            description="Communications Port (COM1)",
            webserver="",
        ),
        Device(
            type=DeviceType.LXI,
            addresses=[
                "TCPIP::169.254.100.4::5025::SOCKET",
                "TCPIP::169.254.100.4::hislip0::INSTR",
                "TCPIP::169.254.100.4::inst0::INSTR",
            ],
            description="Digital Multimeter - MY9876543210",
            webserver="http://169.254.100.4",
        ),
        Device(
            type=DeviceType.ASRL,
            addresses=["COM2"],
            description="Communications Port (COM2)",
            webserver="",
        ),
        Device(
            type=DeviceType.GPIB,
            addresses=["GPIB::1", "GPIB0::2::INSTR"],
            description="",
            webserver="",
        ),
        Device(
            type=DeviceType.FTDI,
            addresses=["FTDI2::0x1::0x2::a"],
            description="Manufacturer 1-2-a",
            webserver="ignored",
        ),
        Device(
            type=DeviceType.ASRL,
            addresses=["COM3"],
            description="Intel(R) Active Management Technology - SOL (COM3)",
            webserver="ignored",
        ),
        Device(
            type=DeviceType.USB,
            addresses=["USB::1::2::a"],
            description="Manufacturer",
            webserver="ignored",
        ),
        Device(
            type=DeviceType.VXI11,
            addresses=["TCPIP::169.254.100.5::5025::SOCKET", "TCPIP::169.254.100.5::inst0::INSTR"],
            description="Data Acquisition / Switch Unit",
            webserver="http://169.254.100.5",
        ),
        Device(
            type=DeviceType.FTDI,
            addresses=["FTDI::1::2::b"],
            description="Manufacturer 1-2-b",
            webserver="ignored",
        ),
        Device(
            type=DeviceType.PROLOGIX,
            addresses=[
                "Prologix::169.254.100.2::1234::GPIB::<PAD>[::<SAD>]",
                "Prologix::prologix-00-01-02-03-04-05::1234::GPIB::<PAD>[::<SAD>]",
            ],
            description="Prologix GPIB-ETHERNET Controller version 01.06.06.00 (MAC Address: 00-01-02-03-04-05)",
            webserver="",
        ),
        Device(
            type=DeviceType.VXI11,
            addresses=[],
            description="HTML title",
            webserver="",
        ),
        Device(
            type=DeviceType.USB,
            addresses=["USB::1::2::b"],
            description="Manufacturer 2",
            webserver="ignored",
        ),
        Device(
            type=DeviceType.VXI11,
            addresses=["TCPIP::169.254.100.6::inst0::INSTR"],
            description="Digital Voltmeter",
            webserver="http://169.254.100.6",
        ),
        Device(
            type=DeviceType.LXI,
            addresses=[
                "TCPIP::169.254.100.3::5025::SOCKET",
                "TCPIP::169.254.100.3::hislip0::INSTR",
                "TCPIP::169.254.100.3::inst0::INSTR",
            ],
            description="Digital Multimeter - MY0123456789",
            webserver="http://169.254.100.3",
        ),
    ]

    print_stdout(devices)
    out, err = capsys.readouterr()
    assert not err
    assert (
        out
        == """ASRL Ports
  COM1 [Communications Port (COM1)]
  COM2 [Communications Port (COM2)]
  COM3 [Intel(R) Active Management Technology - SOL (COM3)]
FTDI Devices
  FTDI2::0x1::0x2::a [Manufacturer 1-2-a]
  FTDI::1::2::b [Manufacturer 1-2-b]
GPIB Devices
  GPIB::1
  GPIB0::2::INSTR
LXI Devices
  Digital Multimeter - MY0123456789 [webserver: http://169.254.100.3]
    TCPIP::169.254.100.3::5025::SOCKET
    TCPIP::169.254.100.3::hislip0::INSTR
    TCPIP::169.254.100.3::inst0::INSTR
  Digital Multimeter - MY9876543210 [webserver: http://169.254.100.4]
    TCPIP::169.254.100.4::5025::SOCKET
    TCPIP::169.254.100.4::hislip0::INSTR
    TCPIP::169.254.100.4::inst0::INSTR
PROLOGIX Devices
  Prologix GPIB-ETHERNET Controller version 01.06.06.00 (MAC Address: 00-01-02-03-04-05)
    Prologix::169.254.100.2::1234::GPIB::<PAD>[::<SAD>]
    Prologix::prologix-00-01-02-03-04-05::1234::GPIB::<PAD>[::<SAD>]
USB Devices
  USB::1::2::a [Manufacturer]
  USB::1::2::b [Manufacturer 2]
VXI11 Devices
  Data Acquisition / Switch Unit [webserver: http://169.254.100.5]
    TCPIP::169.254.100.5::5025::SOCKET
    TCPIP::169.254.100.5::inst0::INSTR
  Digital Voltmeter [webserver: http://169.254.100.6]
    TCPIP::169.254.100.6::inst0::INSTR
  HTML title
"""
    )


def test_usb_backend_invalid(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        _ = cli(["find", "--usb-backend", "xxx"])

    out, err = capsys.readouterr()
    assert not out
    assert "invalid choice: 'xxx' (choose from" in err
