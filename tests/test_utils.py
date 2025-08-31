from __future__ import annotations

import enum
import struct
from typing import TYPE_CHECKING
from urllib.request import HTTPError

import numpy as np
import pytest

from msl.equipment.utils import (
    LXIDevice,
    LXIInterface,
    from_bytes,
    ipv4_addresses,
    parse_lxi_webserver,
    to_bytes,
    to_enum,
    to_primitive,
)

if TYPE_CHECKING:
    from typing import Literal

    from numpy.typing import DTypeLike

    from tests.conftest import HTTPServer


class MyEnum(enum.Enum):
    """For to_enum() tests."""

    ONE = "value"
    XXX_TWO = 2
    three = 3.0
    F_O_U_R = "f o U r"
    FiVe = -5 + 5j
    SIX = True
    BYTES = b"\x00\x01"


def test_to_enum_raises() -> None:
    # not a member name nor value
    with pytest.raises(ValueError, match=r"Cannot create <enum 'MyEnum'> from 'unknown'"):
        _ = to_enum("unknown", MyEnum)

    # must be uppercase
    with pytest.raises(ValueError, match="Cannot create"):
        _ = to_enum("one", MyEnum)

    # wrong prefix
    with pytest.raises(ValueError, match="Cannot create"):
        _ = to_enum("TWO", MyEnum, prefix="xxx")

    # member name must be lowercase
    with pytest.raises(ValueError, match="Cannot create"):
        _ = to_enum("THREE", MyEnum)
    with pytest.raises(ValueError, match="Cannot create"):
        _ = to_enum("three", MyEnum, to_upper=True)
    with pytest.raises(ValueError, match="Cannot create"):
        _ = to_enum("f o u r", MyEnum)

    # being uppercase is wrong
    with pytest.raises(ValueError, match="Cannot create"):
        _ = to_enum("FiVe", MyEnum, to_upper=True)

    # prefix should not be uppercase
    with pytest.raises(ValueError, match="Cannot create"):
        _ = to_enum("FiVe", MyEnum, prefix="FI")

    # prefix check before to_upper
    with pytest.raises(ValueError, match="Cannot create"):
        _ = to_enum("six", MyEnum, prefix="Six", to_upper=True)


def test_to_enum() -> None:
    assert to_enum(MyEnum.ONE, MyEnum) == MyEnum.ONE
    assert to_enum("value", MyEnum) == MyEnum.ONE
    assert to_enum("ONE", MyEnum) == MyEnum.ONE
    assert to_enum("ONE", MyEnum, prefix="O") == MyEnum.ONE
    assert to_enum("ONE", MyEnum, prefix="ON") == MyEnum.ONE
    assert to_enum("ONE", MyEnum, prefix="ONE") == MyEnum.ONE
    assert to_enum("one", MyEnum, to_upper=True) == MyEnum.ONE
    assert to_enum("one", MyEnum, prefix="one", to_upper=True) == MyEnum.ONE

    assert to_enum(MyEnum.XXX_TWO, MyEnum) == MyEnum.XXX_TWO
    assert to_enum(2, MyEnum) == MyEnum.XXX_TWO
    assert to_enum("XXX TWO", MyEnum) == MyEnum.XXX_TWO  # space converted to underscore
    assert to_enum("xXx_twO", MyEnum, to_upper=True) == MyEnum.XXX_TWO
    assert to_enum("two", MyEnum, prefix="xxx_", to_upper=True) == MyEnum.XXX_TWO
    assert to_enum("TWO", MyEnum, prefix="XXX_") == MyEnum.XXX_TWO

    assert to_enum(MyEnum.three, MyEnum) == MyEnum.three
    assert to_enum(3, MyEnum) == MyEnum.three
    assert to_enum(3.0, MyEnum) == MyEnum.three
    assert to_enum("three", MyEnum) == MyEnum.three

    assert to_enum(MyEnum.F_O_U_R, MyEnum) == MyEnum.F_O_U_R
    assert to_enum("F O U R", MyEnum) == MyEnum.F_O_U_R  # space converted to underscore
    assert to_enum("f o U r", MyEnum) == MyEnum.F_O_U_R  # value
    assert to_enum("f o u r", MyEnum, to_upper=True) == MyEnum.F_O_U_R
    assert to_enum("F_O_U_R", MyEnum) == MyEnum.F_O_U_R

    assert to_enum(MyEnum.FiVe, MyEnum) == MyEnum.FiVe
    assert to_enum(-5 + 5j, MyEnum) == MyEnum.FiVe
    assert to_enum("FiVe", MyEnum) == MyEnum.FiVe

    assert to_enum(obj=True, enum=MyEnum) == MyEnum.SIX
    assert to_enum(1, MyEnum) == MyEnum.SIX
    assert to_enum("SIX", MyEnum) == MyEnum.SIX
    assert to_enum("six", MyEnum, to_upper=True) == MyEnum.SIX
    assert to_enum("six", MyEnum, prefix="six", to_upper=True) == MyEnum.SIX
    assert to_enum("Six", MyEnum, prefix="Si", to_upper=True) == MyEnum.SIX

    assert to_enum(b"\x00\x01", MyEnum) == MyEnum.BYTES
    assert to_enum("bytes", MyEnum, to_upper=True) == MyEnum.BYTES
    assert to_enum("BYTES", MyEnum) == MyEnum.BYTES


def test_to_primitive() -> None:
    assert to_primitive("none") is None
    assert to_primitive("None") is None
    assert to_primitive("nOnE") is None
    assert to_primitive("\n  None \t") is None

    assert to_primitive("true") is True
    assert to_primitive("True") is True
    assert to_primitive("TRuE") is True
    assert to_primitive("  True\n") is True
    assert to_primitive("false") is False
    assert to_primitive("False") is False
    assert to_primitive("FaLSe") is False
    assert to_primitive("\nFalse\n") is False

    assert isinstance(to_primitive("0"), int)
    assert isinstance(to_primitive("\n1\n"), int)
    assert isinstance(to_primitive("-999"), int)
    assert to_primitive("0") == 0
    assert to_primitive(" 0 ") == 0
    assert to_primitive("1") == 1
    assert to_primitive("       1\n") == 1
    assert to_primitive("-999") == -999  # noqa: PLR2004

    assert isinstance(to_primitive("1.9"), float)
    assert isinstance(to_primitive("-49.4"), float)
    assert isinstance(to_primitive("2.553e83"), float)
    assert to_primitive("1.9") == 1.9  # noqa: PLR2004
    assert to_primitive("-49.4") == -49.4  # noqa: PLR2004
    assert to_primitive("\t-49.4\n") == -49.4  # noqa: PLR2004
    assert to_primitive("2.553e83") == 2.553e83  # noqa: PLR2004

    assert to_primitive("") == ""
    assert to_primitive(" \t \n ") == " \t \n "
    assert to_primitive("hello") == "hello"
    assert to_primitive("hello\tworld\r\n") == "hello\tworld\r\n"
    assert to_primitive(b"\x00\x00") == b"\x00\x00".decode()
    assert to_primitive("16i") == "16i"
    assert to_primitive("[1,2,3]") == "[1,2,3]"


def test_to_bytes_ieee() -> None:
    assert to_bytes([]) == b"#10"
    assert to_bytes(()) == b"#10"
    assert to_bytes(np.ndarray((0,))) == b"#10"

    assert to_bytes([9.8]) == b"#14\xcd\xcc\x1cA"

    expected = (
        b"#240\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00@\x00\x00@@"
        b"\x00\x00\x80@\x00\x00\xa0@\x00\x00\xc0@\x00\x00\xe0@\x00"
        b"\x00\x00A\x00\x00\x10A"
    )
    assert to_bytes(range(10)) == expected
    assert to_bytes(list(range(10))) == expected

    expected = (
        b"#240\x00\x00\x00\x00?\x80\x00\x00@\x00\x00\x00@@\x00\x00@"
        b"\x80\x00\x00@\xa0\x00\x00@\xc0\x00\x00@\xe0\x00\x00A\x00"
        b"\x00\x00A\x10\x00\x00"
    )
    assert to_bytes(range(10), dtype=">f") == expected
    assert to_bytes(list(range(10)), dtype=">f") == expected
    assert to_bytes(np.array(range(10)), dtype=">f") == expected

    expected = b"#220\x00\x00\x01\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06\x00\x07\x00\x08\x00\t\x00"
    assert to_bytes(range(10), dtype=np.uint16) == expected
    assert to_bytes(list(range(10)), dtype="ushort") == expected
    assert to_bytes(np.array(range(10)), dtype="H") == expected

    expected = b"#15\x01\x00\x01\x01\x00"
    assert to_bytes([True, False, True, True, False], dtype=np.uint8) == expected
    assert to_bytes(np.array([True, False, True, True, False]), dtype="B") == expected

    expected = (
        b"#280\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00"
        b"\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x04\x00"
        b"\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00"
        b"\x06\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00"
        b"\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\t"
    )
    assert to_bytes(range(10), dtype=">Q") == expected
    assert to_bytes(list(range(10)), dtype=">Q") == expected
    assert to_bytes(np.array(range(10)), dtype=">Q") == expected

    assert to_bytes(range(123456), dtype="float64").startswith(b"#6987648")


def test_to_bytes_no_header() -> None:
    expected = (
        b"\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00@\x00\x00@@"
        b"\x00\x00\x80@\x00\x00\xa0@\x00\x00\xc0@\x00\x00\xe0@\x00"
        b"\x00\x00A\x00\x00\x10A"
    )
    assert to_bytes(range(10), fmt=None) == expected
    assert to_bytes(list(range(10)), fmt=None) == expected
    assert to_bytes(tuple(range(10)), fmt=None) == expected
    assert to_bytes(np.array(range(10)), fmt=None) == expected

    assert to_bytes([], fmt=None) == b""
    assert to_bytes([0.1], fmt=None, dtype=np.float32) == b"\xcd\xcc\xcc="


def test_to_bytes_hp() -> None:
    expected = (
        b"#A(\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03"
        b"\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00"
        b"\x07\x00\x00\x00\x08\x00\x00\x00\t\x00\x00\x00"
    )
    assert to_bytes(range(10), fmt="hp", dtype="<i") == expected

    expected = (
        b"#A\x00(\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00"
        b"\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06"
        b"\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00\t"
    )
    assert to_bytes(range(10), fmt="hp", dtype=">i") == expected

    assert to_bytes([], fmt="hp") == b"#A\x00\x00"
    assert to_bytes([-99], fmt="hp", dtype="d") == b"#A\x08\x00\x00\x00\x00\x00\x00\xc0X\xc0"
    assert to_bytes([-99], fmt="hp", dtype="b") == b"#A\x01\x00\x9d"


def test_to_bytes_raises() -> None:
    with pytest.raises(struct.error):
        _ = to_bytes(range(0xFFFF), fmt="hp", dtype="H")

    with pytest.raises(ValueError, match=r"Unknown format code 'H'"):
        _ = to_bytes(range(10), fmt="ascii", dtype="H")

    with pytest.raises(TypeError, match=r"dtype must be of type str"):
        _ = to_bytes(range(10), fmt="ascii", dtype=float)

    with pytest.raises(OverflowError, match=r"length too big for IEEE-488.2 specification"):
        _ = to_bytes(np.empty(int(1.3e8)), fmt="ieee", dtype=float)


def test_to_bytes_ascii() -> None:
    expected = b"0.000000,1.000000,2.000000,3.000000,4.000000,5.000000,6.000000,7.000000,8.000000,9.000000"
    assert to_bytes(range(10), fmt="ascii") == expected

    expected = b"0.000,1.000,2.000,3.000,4.000,5.000,6.000,7.000,8.000,9.000"
    assert to_bytes(range(10), fmt="ascii", dtype=".3f") == expected

    expected = b"0,1,2,3,4,5,6,7,8,9"
    assert to_bytes(range(10), fmt="ascii", dtype="d") == expected

    expected = b"+0.0E+00,+1.0E+00,+2.0E+00,+3.0E+00,+4.0E+00,+5.0E+00,+6.0E+00,+7.0E+00,+8.0E+00,+9.0E+00"
    assert to_bytes(range(10), fmt="ascii", dtype="+.1E") == expected

    expected = b"0000,0001,0002,0003,0004,0005,0006,0007,0008,0009"
    assert to_bytes(range(10), fmt="ascii", dtype="04d") == expected

    assert to_bytes([], fmt="ascii") == b""
    assert to_bytes([0], fmt="ascii") == b"0.000000"
    assert to_bytes([-1, 1], fmt="ascii", dtype="03d") == b"-01,001"


def test_to_bytes_as_bytes() -> None:
    assert to_bytes(b"abc_xyz", dtype="b") == b"#17abc_xyz"
    assert to_bytes(b"abcdefghijklmnopqrstuvwxyz", dtype="B") == b"#226abcdefghijklmnopqrstuvwxyz"
    assert to_bytes(bytearray(b"abc"), fmt=None, dtype="b") == b"abc"
    assert to_bytes(b"MSL", fmt=None, dtype="int8") == b"MSL"


def test_from_bytes_no_header() -> None:
    dtype = "<f"
    array = np.arange(123, dtype=dtype)
    assert np.array_equal(from_bytes(array.tobytes(), fmt=None), array)

    dtype = "ushort"
    array = np.arange(64, dtype=dtype)
    assert np.array_equal(from_bytes(array.tobytes(), fmt=None, dtype=dtype), array)

    array = from_bytes(b"", fmt=None)
    assert array.shape == (0,)
    assert array.size == 0
    assert array.ndim == 1

    array = from_bytes(b"@\xe2\x01\x00\x00\x00\x00\x00", fmt=None, dtype="<Q")
    assert np.array_equal(array, [123456])


def test_from_bytes_ieee() -> None:
    array = from_bytes(b"#10")
    assert array.shape == (0,)
    assert array.size == 0
    assert array.ndim == 1

    array = from_bytes(b"#0")
    assert array.shape == (0,)
    assert array.size == 0
    assert array.ndim == 1

    array = from_bytes(b"#0\n")
    assert array.shape == (0,)
    assert array.size == 0
    assert array.ndim == 1

    assert np.array_equal(from_bytes(b"#14E\x17\xf0\x00", dtype=">f"), [2431.0])
    assert np.array_equal(from_bytes(b"#0E\x17\xf0\x00", dtype=">f"), [2431.0])

    buffer = (
        b"#240\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00@\x00\x00@@"
        b"\x00\x00\x80@\x00\x00\xa0@\x00\x00\xc0@\x00\x00\xe0@\x00"
        b"\x00\x00A\x00\x00\x10A"
    )
    assert np.array_equal(from_bytes(buffer), list(range(10)))

    buffer = b"c35de90ae*9a2-4932=bf1b!2312f1+46-af7f" + buffer
    assert np.array_equal(from_bytes(buffer), list(range(10)))

    buffer = (
        b",#280\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00"
        b"\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x04\x00"
        b"\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00"
        b"\x06\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00"
        b"\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\t"
    )
    assert np.array_equal(from_bytes(buffer, dtype=">Q"), list(range(10)))

    buffer = (
        b"#0\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00@\x00\x00@@"
        b"\x00\x00\x80@\x00\x00\xa0@\x00\x00\xc0@\x00\x00\xe0@\x00"
        b"\x00\x00A\x00\x00\x10A\n"
    )  # ends in LF, this is what the IEEE standard requires
    assert np.array_equal(from_bytes(buffer), list(range(10)))

    buffer = b"c35de90ae*9a2-4932=bf1b!2312f1+46-af7f8qwy3v87yq2" + buffer
    assert np.array_equal(from_bytes(buffer), list(range(10)))

    buffer = (
        b", #0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00"
        b"\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x04\x00"
        b"\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00"
        b"\x06\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00"
        b"\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\t"
    )  # does not end in LF, should still work
    assert np.array_equal(from_bytes(buffer, dtype=">Q"), list(range(10)))


def test_from_bytes_raises() -> None:
    with pytest.raises(ValueError, match=r"cannot find # character"):
        _ = from_bytes(b"123")

    with pytest.raises(ValueError, match=r"character after # is not an integer"):
        _ = from_bytes(b"#")

    with pytest.raises(ValueError, match=r"character after # is not an integer"):
        _ = from_bytes(b"#A")

    with pytest.raises(ValueError, match=r"character after # is not an integer"):
        _ = from_bytes(b"123#r")

    with pytest.raises(ValueError, match=r"characters after #3 are not integers"):
        _ = from_bytes(b"#3a2")

    with pytest.raises(ValueError, match=r"characters after #3 are not integers"):
        _ = from_bytes(b"#322a")

    with pytest.raises(ValueError, match=r"buffer is smaller"):
        _ = from_bytes(b"#0\x00\x00\x00\x00\x00\x00\x80")

    with pytest.raises(ValueError, match=r"buffer is smaller"):
        _ = from_bytes(b"#41024\x00\x00\x00\x00\x00\x00\x80")

    with pytest.raises(ValueError, match=r"cannot find #A character"):
        _ = from_bytes(b"#22\x00\x00", fmt="hp")

    with pytest.raises(ValueError, match=r"characters after #A are not an unsigned short integer"):
        _ = from_bytes(b"#A\x06", fmt="hp")

    with pytest.raises(TypeError, match=r"buffer must be of type bytes | bytearray"):
        _ = from_bytes([0, 0, 0])  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]


def test_from_bytes_hp() -> None:
    buffer = (
        b"#A(\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03"
        b"\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00"
        b"\x07\x00\x00\x00\x08\x00\x00\x00\t\x00\x00\x00"
    )
    assert np.array_equal(from_bytes(buffer, fmt="hp", dtype="<i"), list(range(10)))

    buffer = (
        b"#A\x00(\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00"
        b"\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06"
        b"\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00\t"
    )
    assert np.array_equal(from_bytes(buffer, fmt="hp", dtype=">i"), list(range(10)))

    buffer = (
        b"#A(\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03"
        b"\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00"
        b"\x07\x00\x00\x00\x08\x00\x00\x00\t\x00\x00\x00\r\n"
    )  # append CR+LF
    assert np.array_equal(from_bytes(buffer, fmt="hp", dtype="<i"), list(range(10)))

    array = from_bytes(b"#A\x00\x00", fmt="hp")
    assert array.shape == (0,)
    assert array.size == 0
    assert array.ndim == 1

    buffer = b"#A\x02\x00\x00\x00"
    assert np.array_equal(from_bytes(buffer, fmt="hp", dtype="<H"), [0])

    buffer = b"#A\x04\x00\x00\x00\x00\x01"
    assert np.array_equal(from_bytes(buffer, fmt="hp", dtype="<H"), [0, 256])


def test_from_bytes_ascii() -> None:
    buffer = b"1,2,3,4,5"
    expected = np.array([1, 2, 3, 4, 5], dtype=int)
    assert np.array_equal(from_bytes(buffer, fmt="ascii", dtype="<i"), expected)
    assert np.array_equal(from_bytes(bytearray(buffer), fmt="ascii", dtype="<i"), expected)
    assert np.array_equal(from_bytes(buffer.decode(), fmt="ascii", dtype="<i"), expected)

    buffer = b"1.1,2.2,3.3\n"
    expected = np.array([1.1, 2.2, 3.3], dtype=np.float32)
    assert np.array_equal(from_bytes(buffer, fmt="ascii"), expected)

    assert from_bytes("", fmt="ascii").size == 0
    assert np.array_equal(from_bytes("1", fmt="ascii", dtype="i"), [1])
    assert np.array_equal(from_bytes("1,2", fmt="ascii", dtype="i"), [1, 2])


@pytest.mark.parametrize(
    ("size", "fmt", "dtype"),
    [
        (0, None, int),
        (1, None, int),
        (2, None, int),
        (12345, None, ">Q"),
        (6432, None, np.ushort),
        (54, None, "b"),
        (278, None, "B"),
        (12, None, "<i"),
        (100, None, "l"),
        (1234, None, float),
        (123456, None, "d"),
        (0, "ieee", int),
        (1, "ieee", int),
        (2, "ieee", int),
        (12345, "ieee", ">Q"),
        (6432, "ieee", np.ushort),
        (54, "ieee", "b"),
        (278, "ieee", "B"),
        (12, "ieee", "<i"),
        (100, "ieee", "l"),
        (1234, "ieee", float),
        (123456, "ieee", "d"),
        (0, "hp", int),
        (1, "hp", int),
        (2, "hp", int),
        (6432, "hp", np.ushort),
        (54, "hp", ">Q"),
        (8000, "hp", "<i"),
        (100, "hp", "l"),
        (100, "hp", "b"),
        (256, "hp", ">l"),
        (1234, "hp", float),
        (731, "hp", "B"),
        (128, "hp", "d"),
    ],
)
def test_to_bytes_from_bytes(size: int, fmt: Literal["hp", "ieee"] | None, dtype: DTypeLike) -> None:  # type: ignore[misc]
    array = np.arange(size, dtype=dtype)
    buffer = to_bytes(array, fmt=fmt, dtype=dtype)
    assert np.array_equal(from_bytes(buffer, fmt=fmt, dtype=dtype), array)


@pytest.mark.parametrize(
    ("size", "dtype"),
    [
        (0, "d"),
        (1, "d"),
        (2, "d"),
        (12, ".2E"),
        (64321, "f"),
        (54, " .3f"),
        (278, "g"),
        (12, "+.5e"),
        (100, ""),
        (100, "05d"),
    ],
)
def test_to_bytes_from_bytes_ascii(size: int, dtype: str) -> None:
    t = "i" if "d" in dtype else "f"
    array = np.arange(size, dtype=t)
    buffer = to_bytes(array, fmt="ascii", dtype=dtype)
    assert np.array_equal(from_bytes(buffer, fmt="ascii", dtype=t), array)


def test_ipv4_addresses() -> None:
    assert len(ipv4_addresses()) >= 1


def test_parse_lxi_webserver_400(http_server: type[HTTPServer]) -> None:
    with http_server() as server:
        server.add_response(code=400)
        with pytest.raises(HTTPError, match="Bad Request"):
            _ = parse_lxi_webserver(server.host, port=server.port, timeout=2)


def test_parse_lxi_webserver_404(http_server: type[HTTPServer]) -> None:
    content = b"""<!DOCTYPE html>
<html>
    <head>
        <title>My web page</title>
    </head>
    <body>
        <h1>Hello, world!</h1>
    </body>
</html>
"""

    with http_server() as server:
        server.add_response(code=404)
        server.add_response(content)
        device = parse_lxi_webserver(server.host, port=server.port, timeout=2)

    assert device == LXIDevice(description="My web page")


def test_parse_lxi_webserver_html_title_multiline(http_server: type[HTTPServer]) -> None:
    content = b"""<!DOCTYPE
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
    <link href="default_css.css" rel="stylesheet" type="text/css">
    <title>

    Manufacturer Model <SerialNo.>

    </title>

  </head>
</html>
"""

    with http_server() as server:
        server.add_response(code=404)
        server.add_response(content)
        device = parse_lxi_webserver(server.host, port=server.port, timeout=2)

    assert device == LXIDevice(description="Manufacturer Model <SerialNo.>")


def test_parse_lxi_webserver_html_title_missing(http_server: type[HTTPServer]) -> None:
    with http_server() as server:
        server.add_response(code=404)
        server.add_response(b"<html><body><h1>Hello, world!</h1></body></html>")
        device = parse_lxi_webserver(server.host, port=server.port, timeout=2)

    assert device == LXIDevice()


def test_parse_lxi_webserver_html_xml_parse_error(http_server: type[HTTPServer]) -> None:
    # server return status code 200, but the contents are not valid XML
    content = b"""<!DOCTYPE
<html>
  <head>
    <title>Hello, World!</title>
  </head>
</html>
"""

    with http_server() as server:
        server.add_response(content)
        device = parse_lxi_webserver(server.host, port=server.port, timeout=2)

    assert device == LXIDevice(description="Hello, World!")


def test_parse_lxi_webserver_xml(http_server: type[HTTPServer]) -> None:
    content = b"""<?xml version="1.0" encoding="UTF-8"?>
<LXIDevice xmlns="http://www.lxistandard.org/InstrumentIdentification/1.0"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.lxistandard.org/InstrumentIdentification/1.0 http://hostname/Lxi/Identification/LxiIdentification.xsd">
  <Manufacturer>abcdefg</Manufacturer>
  <Model>xyz</Model>
  <SerialNumber>01234</SerialNumber>
  <FirmwareRevision>52.04.03</FirmwareRevision>
  <ManufacturerDescription>Our product</ManufacturerDescription>
  <HomepageURL>http://www.company.com/</HomepageURL>
  <DriverURL>http://www.company.com/drivers</DriverURL>
  <UserDescription>Buy our stuff</UserDescription>
  <IdentificationURL>http://hostname/Lxi/Identification</IdentificationURL>
  <Interface xsi:type="NetworkInformation" InterfaceType="LXI" IPType="IPv4">
    <InstrumentAddressString>TCPIP::hostname::hislip0::INSTR</InstrumentAddressString>
    <InstrumentAddressString>TCPIP::hostname::inst0::INSTR</InstrumentAddressString>
    <InstrumentAddressString>TCPIP::hostname::5025::SOCKET</InstrumentAddressString>
    <Hostname>hostname</Hostname>
    <IPAddress>192.168.1.100</IPAddress>
    <SubnetMask>255.255.255.0</SubnetMask>
    <MACAddress>00-00-00-00-00-00</MACAddress>
    <Gateway>192.168.1.1</Gateway>
    <DHCPEnabled>true</DHCPEnabled>
    <AutoIPEnabled>true</AutoIPEnabled>
  </Interface>
  <IVISoftwareModuleName>Device</IVISoftwareModuleName>
  <LXIVersion>1.4 LXI Core 2011</LXIVersion>
  <LXIExtendedFunctions>
    <Function FunctionName="LXI Wired Trigger Bus" Version="1.0" />
    <Function FunctionName="LXI Event Messaging" Version="1.0" />
    <Function FunctionName="LXI Clock Synchronization" Version="1.0" />
    <Function FunctionName="LXI Timestamped Data" Version="1.0" />
    <Function FunctionName="LXI Event Logs" Version="1.0" />
    <Function FunctionName="LXI IPv6" Version="1.0" />
    <Function FunctionName="LXI VXI-11" Version="1.0" />
    <Function FunctionName="LXI HiSLIP" Version="1.0">
      <Port>4880</Port>
    </Function>
  </LXIExtendedFunctions>
</LXIDevice>
"""

    with http_server() as server:
        server.add_response(content)
        device = parse_lxi_webserver(server.host, port=server.port, timeout=2)

    assert device.manufacturer == "abcdefg"
    assert device.model == "xyz"
    assert device.serial == "01234"
    assert device.firmware == "52.04.03"
    assert device.description == "Our product"
    assert device.interfaces == (
        LXIInterface(
            type="LXI",
            addresses=(
                "TCPIP::hostname::hislip0::INSTR",
                "TCPIP::hostname::inst0::INSTR",
                "TCPIP::hostname::5025::SOCKET",
            ),
            mac_address="00-00-00-00-00-00",
        ),
    )


def test_parse_lxi_webserver_xml_namespace(http_server: type[HTTPServer]) -> None:
    # change the LXI namespace and create a custom Interface
    content = b"""<?xml version="1.0" encoding="UTF-8"?>
<LXIDevice xmlns="http://www.lxistandard.org/InstrumentId/2.17"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.lxistandard.org/InstrumentId/2.17 http://169.254.100.2/Lxi/LxiIdentification.xsd">
  <Manufacturer>Company</Manufacturer>
  <Model>Product</Model>
  <SerialNumber>xxxx</SerialNumber>
  <FirmwareRevision>1.06</FirmwareRevision>
  <ManufacturerDescription>Oscilloscope</ManufacturerDescription>
  <HomepageURL>http://www.company.com/</HomepageURL>
  <DriverURL>http://www.company.com/drivers</DriverURL>
  <UserDescription>Our best product</UserDescription>
  <IdentificationURL>http://hostname.local/lxi/identification</IdentificationURL>
  <Interface xsi:type="NetworkInformation" InterfaceType="LXI" IPType="IPv4" InterfaceName="eth0">
    <InstrumentAddressString>TCPIP::hostname::5555::SOCKET</InstrumentAddressString>
    <Hostname>hostname</Hostname>
    <IPAddress>169.254.100.2</IPAddress>
    <SubnetMask>255.255.255.0</SubnetMask>
    <MACAddress>00:00:00:00:11:ab</MACAddress>
    <Gateway>169.254.100.1</Gateway>
    <DHCPEnabled>false</DHCPEnabled>
    <AutoIPEnabled>true</AutoIPEnabled>
  </Interface>
  <Interface InterfaceType="MyInterface" InterfaceName="MyName">
    <InstrumentAddressString>hostname:1234</InstrumentAddressString>
  </Interface>
  <Domain>1</Domain>
  <LXIVersion>1.5</LXIVersion>
</LXIDevice>
"""
    with http_server() as server:
        server.add_response(content)
        device = parse_lxi_webserver(server.host, port=server.port, timeout=2)

    assert device.manufacturer == "Company"
    assert device.model == "Product"
    assert device.serial == "xxxx"
    assert device.firmware == "1.06"
    assert device.description == "Oscilloscope"
    assert device.interfaces == (
        LXIInterface(
            type="LXI",
            addresses=("TCPIP::hostname::5555::SOCKET",),
            mac_address="00:00:00:00:11:ab",
        ),
        LXIInterface(
            type="MyInterface",
            addresses=("hostname:1234",),
            mac_address="",
        ),
    )


def test_parse_lxi_webserver_xml_multiple_interfaces(http_server: type[HTTPServer]) -> None:
    content = b"""<?xml version="1.0" encoding="UTF-8"?>
<LXIDevice xmlns="http://www.lxistandard.org/InstrumentIdentification/1.0"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.lxistandard.org/InstrumentIdentification/1.0 http://10.12.102.2/Lxi/Identification/LxiIdentification.xsd">
  <Manufacturer>Manufacturer</Manufacturer>
  <Model>Model</Model>
  <SerialNumber>SerialNumber</SerialNumber>
  <FirmwareRevision>0.0.1</FirmwareRevision>
  <ManufacturerDescription>Manufacturer Description</ManufacturerDescription>
  <HomepageURL>http://www.home.page/</HomepageURL>
  <DriverURL>http://www.home.page/find/drivers</DriverURL>
  <UserDescription>User Description</UserDescription>
  <IdentificationURL>http://ip.address/Lxi/Identification</IdentificationURL>
  <Interface xsi:type="NetworkInformation" InterfaceType="LXI" IPType="IPv4">
    <InstrumentAddressString>TCPIP::ip.address::hislip0::INSTR</InstrumentAddressString>
    <InstrumentAddressString>TCPIP::ip.address::inst0::INSTR</InstrumentAddressString>
    <InstrumentAddressString>TCPIP::ip.address::5025::SOCKET</InstrumentAddressString>
    <Hostname>ip.address</Hostname>
    <IPAddress>10.12.102.2</IPAddress>
    <SubnetMask>255.255.255.128</SubnetMask>
    <MACAddress>00-01-02-03-04-05</MACAddress>
    <Gateway>10.12.102.1</Gateway>
    <DHCPEnabled>true</DHCPEnabled>
    <AutoIPEnabled>true</AutoIPEnabled>
  </Interface>
  <Interface xsi:type="NetworkInformation" InterfaceType="LXI" IPType="IPv6">
    <InstrumentAddressString>TCPIP::ip.address::hislip0::INSTR</InstrumentAddressString>
    <InstrumentAddressString>TCPIP::ip.address::5025::SOCKET</InstrumentAddressString>
    <Hostname>ip.address</Hostname>
    <IPAddress>ab01::1234:2cd:ef03:0123a</IPAddress>
    <SubnetMask />
    <MACAddress>de-ad-02-03-04-05</MACAddress>
    <Gateway />
    <DHCPEnabled>true</DHCPEnabled>
    <AutoIPEnabled>true</AutoIPEnabled>
  </Interface>
  <IVISoftwareModuleName>Xx1234x</IVISoftwareModuleName>
  <LXIVersion>1.4 LXI Core 2011</LXIVersion>
  <LXIExtendedFunctions>
    <Function FunctionName="LXI HiSLIP" Version="1.0">
      <Port>4880</Port>
    </Function>
    <Function FunctionName="LXI IPv6" Version="1.0" />
  </LXIExtendedFunctions>
</LXIDevice>
"""
    with http_server() as server:
        server.add_response(content)
        device = parse_lxi_webserver(server.host, port=server.port, timeout=2)

    assert device.manufacturer == "Manufacturer"
    assert device.model == "Model"
    assert device.serial == "SerialNumber"
    assert device.firmware == "0.0.1"
    assert device.description == "Manufacturer Description"
    assert device.interfaces == (
        LXIInterface(
            type="LXI",
            addresses=(
                "TCPIP::ip.address::hislip0::INSTR",
                "TCPIP::ip.address::inst0::INSTR",
                "TCPIP::ip.address::5025::SOCKET",
            ),
            mac_address="00-01-02-03-04-05",
        ),
        LXIInterface(
            type="LXI",
            addresses=(
                "TCPIP::ip.address::hislip0::INSTR",
                "TCPIP::ip.address::5025::SOCKET",
            ),
            mac_address="de-ad-02-03-04-05",
        ),
    )


def test_parse_lxi_webserver_xml_not_lxi(http_server: type[HTTPServer]) -> None:
    with http_server() as server:
        server.add_response(b'<?xml version="1.0" encoding="UTF-8"?><Fruit><Apple/></Fruit>')
        device = parse_lxi_webserver(server.host, port=server.port, timeout=2)

    assert device == LXIDevice()
