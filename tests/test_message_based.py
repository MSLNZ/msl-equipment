from __future__ import annotations

# pyright: reportUnusedVariable=false
from typing import TYPE_CHECKING

import numpy as np
import pytest

from msl.equipment import Connection, Equipment, MSLConnectionError
from msl.equipment.interfaces import MessageBased

if TYPE_CHECKING:
    from msl.equipment._types import NumpyArray1D


def test_termination() -> None:  # noqa: PLR0915
    mb = MessageBased(Equipment(connection=Connection("COM1")))

    mb.encoding = "cp1252"
    assert mb.encoding == "cp1252"

    assert isinstance(mb.read_termination, bytes)
    assert isinstance(mb.write_termination, bytes)
    assert mb.read_termination == b"\n"
    assert mb.write_termination == b"\r\n"

    mb.encoding = "utf-8"
    assert mb.encoding == "utf-8"

    mb.read_termination = "xxx"
    mb.write_termination = "xxx"
    assert isinstance(mb.read_termination, bytes)
    assert isinstance(mb.write_termination, bytes)
    assert mb.read_termination == b"xxx"
    assert mb.write_termination == b"xxx"

    mb.read_termination = b"yyy"
    mb.write_termination = b"yyy"
    assert isinstance(mb.read_termination, bytes)
    assert isinstance(mb.write_termination, bytes)
    assert mb.read_termination == b"yyy"
    assert mb.write_termination == b"yyy"

    mb.read_termination = None
    mb.write_termination = None
    mb.encoding = "ascii"
    assert mb.read_termination is None
    assert mb.write_termination is None

    term = "zzz".encode("ascii")
    mb.read_termination = term
    mb.write_termination = term
    assert isinstance(mb.read_termination, bytes)
    assert isinstance(mb.write_termination, bytes)
    assert mb.read_termination == term
    assert mb.write_termination == term

    mb.read_termination = bytes(bytearray([13, 10]))
    mb.write_termination = bytes(bytearray([13]))
    assert isinstance(mb.read_termination, bytes)
    assert isinstance(mb.write_termination, bytes)
    assert mb.read_termination == b"\r\n"
    assert mb.write_termination == b"\r"

    # check that the encoding is valid
    assert mb.read_termination == b"\r\n"
    assert mb.write_termination == b"\r"
    with pytest.raises(LookupError):
        mb.encoding = "unknown"
    mb.read_termination = None
    mb.write_termination = None
    assert mb.read_termination is None
    assert mb.write_termination is None
    with pytest.raises(LookupError):
        mb.encoding = "unknown"

    mb = MessageBased(Equipment(connection=Connection("COM1", termination="abc")))
    assert mb.read_termination == b"abc"
    assert mb.write_termination == b"abc"


def test_timeout_value() -> None:
    mb = MessageBased(Equipment(connection=Connection("COM1")))
    assert mb.timeout is None
    mb.timeout = 10
    assert isinstance(mb.timeout, float)
    assert mb.timeout == 10.0
    mb.timeout = -1
    assert mb.timeout is None
    mb.timeout = 0  # type: ignore[unreachable]
    assert isinstance(mb.timeout, float)
    assert mb.timeout == 0
    mb.timeout = None
    assert mb.timeout is None

    mb = MessageBased(Equipment(connection=Connection("COM1", timeout=99)))
    assert mb.timeout == 99


def test_max_read_size_value() -> None:
    mb = MessageBased(Equipment(connection=Connection("COM1")))
    assert mb.max_read_size == 1 << 20

    with pytest.raises(ValueError, match="must be >= 1, got 0"):
        mb.max_read_size = 0

    mb.max_read_size = 123.4567  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue]
    assert mb.max_read_size == 123

    with pytest.raises(MSLConnectionError, match="max_read_size is 123 bytes"):
        r: str = mb.read(size=124)  # noqa: F841


def test_rstrip() -> None:
    mb = MessageBased(Equipment(connection=Connection("COM1")))
    assert not mb.rstrip
    mb.rstrip = True
    assert mb.rstrip


def test_write() -> None:
    mb = MessageBased(Equipment(connection=Connection("COM1")))

    with pytest.raises(MSLConnectionError, match="MessageBased"):
        _ = mb.write("hi", data=[1, 2, 3])

    assert mb.write_termination == b"\r\n"
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        _ = mb.write(b"hi\r\n")

    mb.write_termination = None
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        _ = mb.write(b"hi")


def test_type_annotation_read_query() -> None:  # noqa: PLR0915
    # A test for type checking with mypy and pyright for the overload signatures
    mb = MessageBased(Equipment(connection=Connection("COM1")))

    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r1: str = mb.read()  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r2: str = mb.read(size=None)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r3: str = mb.read(size=10)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r4: str = mb.read(decode=True)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r5: str = mb.read(decode=True, size=100)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r6: str = mb.read(size=100, dtype=None, fmt=None, decode=True)  # noqa: F841

    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r7: bytes = mb.read(decode=False)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r8: bytes = mb.read(decode=False, size=100)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r9: bytes = mb.read(fmt=None, dtype=None, size=100, decode=False)  # noqa: F841

    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r10: NumpyArray1D = mb.read(dtype=int)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r11: NumpyArray1D = mb.read(decode=True, dtype=float)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r12: NumpyArray1D = mb.read(dtype="<f")  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r13: NumpyArray1D = mb.read(decode=False, dtype=np.float64)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r14: NumpyArray1D = mb.read(dtype=np.uint16)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r15: NumpyArray1D = mb.read(dtype=int, fmt="ascii")  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r16: NumpyArray1D = mb.read(dtype=int, decode=False, fmt="hp")  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r17: NumpyArray1D = mb.read(size=100, dtype=int, decode=False, fmt="hp")  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        r18: NumpyArray1D = mb.read(fmt="ieee", dtype=int, decode=True)  # noqa: F841

    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q1: str = mb.query("hi")  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q2: str = mb.query(b"hi", size=None)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q3: str = mb.query("hi", delay=10, size=10)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q4: str = mb.query(b"hi", decode=True)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q5: str = mb.query("hi", decode=True, size=100)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q6: str = mb.query(b"hi", size=100, dtype=None, delay=5, decode=True, fmt=None)  # noqa: F841

    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q7: bytes = mb.query("hi", decode=False)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q8: bytes = mb.query(b"hi", decode=False, size=100)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q9: bytes = mb.query("hi", fmt=None, delay=1, size=100, decode=False)  # noqa: F841

    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q10: NumpyArray1D = mb.query(b"hi", dtype=int)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q11: NumpyArray1D = mb.query("hi", decode=True, delay=10, dtype=float)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q12: NumpyArray1D = mb.query(b"hi", dtype="<f")  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q13: NumpyArray1D = mb.query("hi", size=100, decode=False, dtype=np.float64)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q14: NumpyArray1D = mb.query(b"hi", dtype=np.uint16)  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q15: NumpyArray1D = mb.query("hi", dtype=int, delay=1, size=16, fmt="ascii")  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q16: NumpyArray1D = mb.query(b"hi", dtype=int, decode=False, fmt="hp")  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q17: NumpyArray1D = mb.query("hi", size=100, dtype=int, decode=False, fmt="hp")  # noqa: F841
    with pytest.raises(MSLConnectionError, match="MessageBased"):
        q18: NumpyArray1D = mb.query(b"hi", fmt="ieee", dtype=int, decode=True)  # noqa: F841
