from __future__ import annotations

import errno
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from msl.equipment.cli import run_external
from msl.equipment.cli.find import Device, DeviceType, print_stdout

gpib_ext = {"win32": "dll", "linux": "so", "darwin": "dylib"}[sys.platform]


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(("msl-equipment", *args), capture_output=True, text=True)  # noqa: PLW1510, S603


@pytest.mark.parametrize("args", [[], ["--help"], ["help"]])
def test_help(args: list[str]) -> None:
    out = run(args)
    assert out.returncode == 0
    assert not out.stderr
    assert out.stdout.startswith("usage: msl-equipment [OPTIONS] COMMAND [ARGS]...")


@pytest.mark.parametrize("args", [["help", "find"], ["find", "--help"]])
def test_help_find(args: list[str]) -> None:
    out = run(args)
    assert out.returncode == 0
    assert not out.stderr
    assert out.stdout.startswith("usage: msl-equipment find")


@pytest.mark.parametrize("args", [["help", "validate"], ["validate", "--help"]])
def test_help_validate(args: list[str]) -> None:
    out = run(args)
    assert out.returncode == 0
    assert not out.stderr
    assert out.stdout.startswith("usage: msl-equipment-validate")


def test_help_unknown_command() -> None:
    out = run(["help", "unknown"])
    assert out.returncode == errno.ENOENT
    assert not out.stdout
    assert "invalid choice: 'unknown' (choose from" in out.stderr


def test_run_external_unknown_name(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_external("unknown") == errno.ENOENT

    captured = capsys.readouterr()
    assert not captured.err
    assert captured.out.splitlines() == [
        "Please install the `msl-equipment-unknown` package.",
        "",
        "If you have installed the package, add the directory to where the",
        "msl-equipment-unknown executable is located to the PATH environment variable.",
    ]


def test_run_external_unknown_arg(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_external("validate", "file.xml", "--carrot") == errno.ENOENT

    captured = capsys.readouterr()
    assert not captured.out
    assert captured.err.rstrip().endswith("msl-equipment-validate: error: unrecognized arguments: --carrot")


def test_cli_find_json() -> None:
    args = ["find", "-i", "127.0.0.1", "-t", "0.1", "-g", f"tests/resources/gpib.{gpib_ext}", "-j"]
    out = run(args)
    assert out.returncode == 0
    assert not out.stderr

    devices = json.loads(out.stdout)
    assert isinstance(devices, list)

    gpib_devices: list[dict[str, str | list[str]]] = [d for d in devices if d["type"] == "GPIB"]  # pyright: ignore[reportUnknownVariableType]
    assert gpib_devices[0]["addresses"] == ["GPIB0::5::INSTR", "GPIB15::11::INSTR"]
    assert gpib_devices[0]["description"] == ""
    assert gpib_devices[0]["webserver"] == ""


def test_cli_find_verbose() -> None:
    args = ["find", "-i", "127.0.0.1", "-v", "-t", "0.1", "-g", f"tests/resources/gpib.{gpib_ext}"]
    out = run(args)
    assert out.returncode == 0

    gpib_file = Path().parent / "tests" / "resources" / f"gpib.{gpib_ext}"
    offset = len("HH:MM:SS.fff ")
    lines = out.stderr.splitlines()
    assert lines[0][offset:] == "Start searching for devices"
    assert lines[1][offset:] == "Broadcasting for Prologix ENET-GPIB Controllers: {'127.0.0.1'}"
    assert lines[2][offset:] == "Broadcasting for LXI devices: {'127.0.0.1'}"
    assert lines[3][offset:] == "Broadcasting for VXI-11 devices: {'127.0.0.1'}"
    assert lines[4][offset:] == "Searching for Serial ports"
    assert lines[5][offset:] == "Searching for GPIB devices (include_sad=False)"
    assert lines[6][offset:] == f"Loaded {gpib_file.resolve()}"

    # annoying logs from the mocked GPIB library
    index = 6
    for board in range(16):
        if board == 3:
            continue
        for pad in range(1, 31):
            if (board == 0 and pad == 5) or (board == 15 and pad == 11):
                continue
            index += 1
            assert (
                lines[index][offset:]
                == f"gpib.ibln({board}, {pad}, 0) -> 0x8000 | One or more arguments to the function call were invalid (iberr: 0x4)"  # noqa: E501
            )

    assert lines[index + 1][offset:] == "Waiting approximately 0.1 second(s) for network devices to respond..."
    assert re.match(r"Found \d+ devices", lines[index + 2][offset:])

    # check stdout, but must ignore all Serial devices
    lines = out.stdout.splitlines()
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
        Device(type=DeviceType.ASRL, addresses=["COM1"], description="Communications Port (COM1)", webserver=""),
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
        Device(type=DeviceType.ASRL, addresses=["COM2"], description="Communications Port (COM2)", webserver=""),
        Device(type=DeviceType.GPIB, addresses=["GPIB::1", "GPIB0::2::INSTR"], description="", webserver=""),
        Device(
            type=DeviceType.ASRL,
            addresses=["COM3"],
            description="Intel(R) Active Management Technology - SOL (COM3)",
            webserver="",
        ),
        Device(
            type=DeviceType.VXI11,
            addresses=["TCPIP::169.254.100.5::5025::SOCKET", "TCPIP::169.254.100.5::inst0::INSTR"],
            description="Data Acquisition / Switch Unit",
            webserver="http://169.254.100.5",
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
    captured = capsys.readouterr()
    assert not captured.err
    assert (
        captured.out
        == """ASRL Ports
  COM1 [Communications Port (COM1)]
  COM2 [Communications Port (COM2)]
  COM3 [Intel(R) Active Management Technology - SOL (COM3)]
GPIB Devices
  GPIB::1
  GPIB0::2::INSTR
PROLOGIX Devices
  Prologix GPIB-ETHERNET Controller version 01.06.06.00 (MAC Address: 00-01-02-03-04-05)
    Prologix::169.254.100.2::1234::GPIB::<PAD>[::<SAD>]
    Prologix::prologix-00-01-02-03-04-05::1234::GPIB::<PAD>[::<SAD>]
LXI Devices
  Digital Multimeter - MY0123456789 [webserver: http://169.254.100.3]
    TCPIP::169.254.100.3::5025::SOCKET
    TCPIP::169.254.100.3::hislip0::INSTR
    TCPIP::169.254.100.3::inst0::INSTR
  Digital Multimeter - MY9876543210 [webserver: http://169.254.100.4]
    TCPIP::169.254.100.4::5025::SOCKET
    TCPIP::169.254.100.4::hislip0::INSTR
    TCPIP::169.254.100.4::inst0::INSTR
VXI11 Devices
  Data Acquisition / Switch Unit [webserver: http://169.254.100.5]
    TCPIP::169.254.100.5::5025::SOCKET
    TCPIP::169.254.100.5::inst0::INSTR
  Digital Voltmeter [webserver: http://169.254.100.6]
    TCPIP::169.254.100.6::inst0::INSTR
"""
    )
