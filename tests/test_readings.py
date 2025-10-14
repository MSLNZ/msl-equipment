# cSpell: ignore ISCII
from __future__ import annotations

import locale
import math
import sys
from typing import TYPE_CHECKING

import numpy as np
import pytest

from msl.equipment import Readings
from msl.equipment.readings import Format, order_of_magnitude, parse, si_prefix_factor

if TYPE_CHECKING:
    from collections.abc import Sequence

is_windows = sys.platform == "win32"
is_darwin = sys.platform == "darwin"
is_linux = sys.platform == "linux"

original_loc = locale.setlocale(locale.LC_NUMERIC)


@pytest.mark.parametrize(
    "data",
    [
        "1,2,3",
        "1,2,3\r",
        "1,2,3\n",
        "1,2,3\r\n",
        "1,  2.0e0,      0.300000e+1",
        ["1", "2", "3"],
        ["1", "2", "3\r"],
        ["1", "2", "3\n"],
        ["1", "2", "3\r\n"],
        ["1", "  2.0", "      3.000000"],
        [1, 2, 3],
        [1.0, 2.0, 3.0],
        (1, 2, 3),
        np.array([1.0, 2.0, 3.0]),
    ],
)
def test_types(data: Sequence[str | float]) -> None:
    r = Readings(data)
    assert np.array_equal(r.data, np.array([1.0, 2.0, 3.0]))
    assert r.data.dtype == np.float64


def test_2d() -> None:
    data = np.arange(64)
    r = Readings(data.reshape(32, 2))
    assert len(r) == 64
    assert r.mean == data.mean()
    assert r.std == data.std(ddof=1)
    assert r.std_mean == data.std(ddof=1) / 8.0

    array = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=float)
    r = Readings("1,2,3\r\n4,5,6\r\n7,8,9")
    assert len(r) == 9
    assert r.mean == array.mean()
    assert r.std == array.std(ddof=1)
    assert r.std_mean == array.std(ddof=1) / 3.0


def test_delimiter() -> None:
    r = Readings("1   2         3", delimiter=None)
    assert len(r) == 3
    assert r.mean == 2.0
    assert r.std == 1.0
    assert r.std_mean == pytest.approx(1.0 / math.sqrt(3))  # pyright: ignore[reportUnknownMemberType]


def test_kwargs() -> None:
    with pytest.raises(ValueError, match=r"Cannot specify data and the mean, std or size"):
        _ = Readings(np.arange(10), mean=1.0)
    with pytest.raises(ValueError, match=r"Cannot specify data and the mean, std or size"):
        _ = Readings(np.arange(10), std=1.0)
    with pytest.raises(ValueError, match=r"Cannot specify data and the mean, std or size"):
        _ = Readings(np.arange(10), size=1)

    # specifying overload is okay
    r = Readings(np.arange(10), overload=1)
    assert isinstance(r.overload, float)
    assert r.overload == 1.0

    # specifying overload is okay
    r = Readings(np.arange(10), overload=None)
    assert r.overload is None


def test_ndarray_attrib() -> None:
    r = Readings(range(10))
    assert r.max() == 9
    assert r.min() == 0
    assert r.dtype == np.float64


def test_mean_std(recwarn: pytest.WarningsRecorder) -> None:  # noqa: PLR0915
    r = Readings()
    assert isinstance(r.mean, float)
    assert isinstance(r.std, float)
    assert isinstance(r.std_mean, float)
    assert r.data.size == 0
    assert len(r) == 0
    assert math.isnan(r.mean)
    assert math.isnan(r.std)
    assert math.isnan(r.std_mean)

    data: Sequence[str] | str
    for data in ([], (), "", "  ", "\r", "\n", "\r\n", " \r \n "):  # pyright: ignore[reportUnknownVariableType]
        r = Readings(data)  # pyright: ignore[reportUnknownArgumentType]
        assert r.data.size == 0
        assert math.isnan(r.mean)
        assert math.isnan(r.std)
        assert math.isnan(r.std_mean)

    r = Readings([1])
    assert np.array_equal(r.data, np.array([1.0]))
    assert r.mean == 1.0
    assert math.isnan(r.std)
    assert math.isnan(r.std_mean)

    r = Readings("1")
    assert np.array_equal(r.data, np.array(1.0))
    assert r.mean == 1.0
    assert math.isnan(r.std)
    assert math.isnan(r.std_mean)

    r = Readings(range(10))
    assert r.mean == pytest.approx(4.5)  # pyright: ignore[reportUnknownMemberType]
    assert r.std == pytest.approx(3.02765035409749)  # pyright: ignore[reportUnknownMemberType]
    assert r.std_mean == pytest.approx(0.9574271077563375)  # pyright: ignore[reportUnknownMemberType]

    r = Readings(mean=9.9)
    assert r.data.size == 0
    assert r.size == 0
    assert r.mean == 9.9
    assert math.isnan(r.std)
    assert math.isnan(r.std_mean)

    r = Readings(std=9.9)
    assert r.data.size == 0
    assert r.size == 0
    assert math.isnan(r.mean)
    assert r.std == 9.9
    assert math.isnan(r.std_mean)

    r = Readings(mean=9.9, std=1.1)
    assert r.data.size == 0
    assert r.size == 0
    assert r.mean == 9.9
    assert r.std == 1.1
    assert math.isnan(r.std_mean)

    r = Readings(mean=0.0, std=1.0)
    assert r.data.size == 0
    assert len(r) == 0
    assert r.mean == 0.0
    assert r.std == 1.0
    assert math.isnan(r.std_mean)

    r = Readings(mean=1.23, std=1.23, size=10)
    assert r.data.size == 0
    assert len(r) == 10
    assert r.mean == 1.23
    assert r.std == 1.23
    assert r.std_mean == pytest.approx(0.3889601522007106)  # pyright: ignore[reportUnknownMemberType]

    data2: list[int]
    for data2 in ([100, 101, 103, 104], [-100, -101, -103, -104]):
        r = Readings(data2, overload=99)
        assert r.data.size == 4
        assert len(r) == 4
        assert math.isnan(r.mean)
        assert math.isnan(r.std)
        assert math.isnan(r.std_mean)
        assert r.overload == 99.0

    r = Readings(mean=1e100, std=1e99, overload=None)
    assert r.data.size == 0
    assert len(r) == 0
    assert r.mean == 1e100
    assert r.std == 1e99
    assert math.isnan(r.std_mean)
    assert r.overload is None

    assert len(recwarn) == 0


@pytest.mark.parametrize(
    ("arg", "kwargs", "expected"),
    [
        ((), {}, "Readings(mean=nan, std_mean=nan, size=0)"),
        ([1], {}, "Readings(mean=1.0, std_mean=nan, size=1)"),
        (None, {"mean": 9.9, "std": 1.1, "size": 1}, "Readings(mean=9.9, std_mean=1.1, size=1)"),
        ([2] * 10, {}, "Readings(mean=2.0, std_mean=0.0, size=10)"),
    ],
)
def test_repr_str(arg: Sequence[float], kwargs: dict[str, float], expected: str) -> None:
    r = Readings(arg, **kwargs)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    assert repr(r) == expected
    assert str(r) == expected
    assert f"{r!r}" == expected
    assert f"{r!s}" == expected


@pytest.mark.parametrize(
    "format_spec",
    [
        "A",  # invalid <type> or <fill> without <align>
        "-5.2A",  # invalid <type>
        ".",  # <decimal> without <precision>
        "2.f",  # <decimal> without <precision>
        "===",  # multiple <fill> characters
        "**<.4G",  # multiple <fill> characters
        "<<<.4G",  # multiple <fill> characters
        "#+.2f",  # <hash> before <sign>
        "0#.2f",  # <digit> before <hash>
        ",3.2f",  # <grouping> before <width>
        "0-.4G",  # <sign> after <zero>
        "#-.4G",  # <sign> after <hash>
        "=7^2,.3f",  # <width> before <align>
        "=^20,3f",  # <width> after <grouping> or forgot the <decimal> before <precision>
        "!5.2f",  # invalid <sign> character
        "5!.2f",  # invalid <grouping> character
        "!.2f",  # <fill> without <align> or invalid <sign> character
        "5.2fA",  # invalid <option> character and too many builtin fields
        "BP",  # two modes specified
        "LU",  # two styles specified
        "SB",  # <si> before <mode>
        "SL",  # <si> before <style>
        "Sf",  # <si> before <type>
    ],
)
def test_parse_raises(format_spec: str) -> None:
    with pytest.raises(ValueError, match=r"Invalid format specifier"):
        _ = parse(format_spec)


def test_parse() -> None:
    # also call the builtin format(float, format_spec) to verify
    # that the formatting.parse function is okay
    def _parse(format_spec: str, *, check: bool = True) -> dict[str, str]:
        if check:  # must ignore for the custom fields
            _ = format(1.0, format_spec)
        return parse(format_spec)

    def expect(**kwargs: str | None) -> dict[str, str | None]:
        out: dict[str, str | None] = {
            "fill": None,
            "align": None,
            "sign": None,
            "z": None,
            "hash": None,
            "zero": None,
            "width": None,
            "grouping": None,
            "precision": None,
            "type": None,
            "mode": None,
            "style": None,
            "si": None,
        }
        out.update(**kwargs)
        return out

    # check the builtin-supported fields
    assert _parse("G") == expect(type="G")
    assert _parse("=") == expect(align="=")
    assert _parse(" =") == expect(fill=" ", align="=")
    assert _parse("<<") == expect(fill="<", align="<")
    assert _parse(" 10.1") == expect(sign=" ", width="10", precision="1")
    assert _parse("0") == expect(zero="0")
    assert _parse("0.0") == expect(zero="0", precision="0")
    assert _parse("02") == expect(zero="0", width="2")
    assert _parse("02.0") == expect(zero="0", width="2", precision="0")
    assert _parse(".10") == expect(precision="10")
    assert _parse("07.2f") == expect(zero="0", width="7", precision="2", type="f")
    assert _parse("*<-06,.4E") == expect(
        fill="*", align="<", sign="-", zero="0", width="6", grouping=",", precision="4", type="E"
    )

    if sys.version_info[:2] >= (3, 11):
        assert _parse("*<-z06,.4E") == expect(
            fill="*", align="<", sign="-", z="z", zero="0", width="6", grouping=",", precision="4", type="E"
        )

    # custom fields
    assert _parse("B", check=False) == expect(mode="B")
    assert _parse("U", check=False) == expect(style="U")
    assert _parse("S", check=False) == expect(si="S")
    assert _parse("GB", check=False) == expect(type="G", mode="B")
    assert _parse("GBL", check=False) == expect(type="G", mode="B", style="L")
    assert _parse(".2U", check=False) == expect(precision="2", style="U")
    assert _parse("9P", check=False) == expect(width="9", mode="P")
    assert _parse(".7", check=False) == expect(precision="7")
    assert _parse("e", check=False) == expect(type="e")
    assert _parse(".2f", check=False) == expect(precision="2", type="f")
    assert _parse(".2fP", check=False) == expect(precision="2", type="f", mode="P")
    assert _parse(" ^16.4fL", check=False) == expect(
        fill=" ", align="^", width="16", precision="4", type="f", style="L"
    )
    assert _parse("^^03S", check=False) == expect(fill="^", align="^", zero="0", width="3", si="S")
    assert _parse("^^03BUS", check=False) == expect(
        fill="^", align="^", zero="0", width="3", mode="B", style="U", si="S"
    )
    assert _parse("^^03gBS", check=False) == expect(
        fill="^", align="^", zero="0", width="3", type="g", mode="B", si="S"
    )
    assert _parse("^^03gB", check=False) == expect(fill="^", align="^", zero="0", width="3", type="g", mode="B")
    assert _parse("*> #011,.2gL", check=False) == expect(
        fill="*", align=">", sign=" ", hash="#", zero="0", width="11", grouping=",", precision="2", type="g", style="L"
    )


def test_format_class() -> None:
    f = Format(**parse(""))
    assert repr(f) == "Format(format_spec='.2fB')"
    assert str(f) == "Format(format_spec='.2fB')"
    assert f.digits == 2

    f = Format(**parse("*> #020,.3gPL"))
    assert repr(f) == "Format(format_spec='*> #020,.3gPL')"
    assert f.digits == 3

    f = Format(**parse("+z10eS"))
    assert repr(f) == "Format(format_spec='+z10.2eBS')"
    assert f.digits == 2

    f = Format(**parse(".1U"))
    assert repr(f) == "Format(format_spec='.1fBU')"
    assert f.digits == 1

    f = Format(**parse(""))
    number = 123.456789
    assert f.value(number, precision=4, type="f", sign=" ") == f"{number: .4f}"

    f = Format(**parse("+.4"))
    number = 123.456789
    assert f.value(number), f"{number:+.4f}"

    f = Format(**parse("*>+20.4"))
    number = 123.456789
    assert f.result(f.value(number)) == f"{number:*>+20.4f}"

    f = Format(**parse("+.4e"))
    number = 123.456789
    assert f.value(number) == f"{number:+.4e}"

    f = Format(**parse(",.0"))
    number = 123456789
    assert f.value(number) == f"{number:,.0f}"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.000000000000000123456789, -16),
        (0.00000000000000123456789, -15),
        (0.0000000000000123456789, -14),
        (0.000000000000123456789, -13),
        (0.00000000000123456789, -12),
        (0.0000000000123456789, -11),
        (0.000000000123456789, -10),
        (0.00000000123456789, -9),
        (0.0000000123456789, -8),
        (0.000000123456789, -7),
        (0.00000123456789, -6),
        (0.0000123456789, -5),
        (0.000123456789, -4),
        (0.00123456789, -3),
        (0.0123456789, -2),
        (0.123456789, -1),
        (0, 0),
        (1.23456789, 0),
        (12.3456789, 1),
        (123.456789, 2),
        (1234.56789, 3),
        (12345.6789, 4),
        (123456.789, 5),
        (1234567.89, 6),
        (12345678.9, 7),
        (123456789.0, 8),
        (1234567890.0, 9),
        (12345678900.0, 10),
        (123456789000.0, 11),
        (1234567890000.0, 12),
        (12345678900000.0, 13),
        (123456789000000.0, 14),
        (1234567890000000.0, 15),
        (12345678900000000.0, 16),
    ],
)
def test_order_of_magnitude(value: float, expected: int) -> None:
    assert order_of_magnitude(value) == expected
    assert order_of_magnitude(-value) == expected


def test_nan_inf() -> None:  # noqa: C901, PLR0912, PLR0915
    r = Readings(mean=np.inf, std=np.inf, size=1)
    assert f"{r}" == "inf(inf)"
    assert f"{r:B}" == "inf(inf)"
    assert f"{r:P}" == "inf+/-inf"
    for t in ["f", "g", "e"]:
        assert f"{r:{t}}" == "inf(inf)"
    for t in ["F", "G", "E"]:
        assert f"{r:{t}}" == "INF(INF)"
    for t in ["f", "g", "e"]:
        assert f"{r:{t}P}" == "inf+/-inf"
    for t in ["F", "G", "E"]:
        assert f"{r:{t}P}" == "INF+/-INF"

    r = Readings(mean=np.inf, std=np.nan, size=1)
    assert f"{r}" == "inf(nan)"
    assert f"{r:B}" == "inf(nan)"
    assert f"{r:P}" == "inf+/-nan"
    for t in ["f", "g", "e"]:
        assert f"{r:{t}}" == "inf(nan)"
    for t in ["F", "G", "E"]:
        assert f"{r:{t}}" == "INF(NAN)"
    for t in ["f", "g", "e"]:
        assert f"{r:{t}P}" == "inf+/-nan"
    for t in ["F", "G", "E"]:
        assert f"{r:{t}P}" == "INF+/-NAN"

    r = Readings(mean=-np.inf, std=np.nan, size=1)
    assert f"{r}" == "-inf(nan)"
    assert f"{r:B}" == "-inf(nan)"
    assert f"{r:P}" == "-inf+/-nan"
    for t in ["f", "g", "e"]:
        assert f"{r:{t}}" == "-inf(nan)"
    for t in ["F", "G", "E"]:
        assert f"{r:{t}}" == "-INF(NAN)"
    for t in ["f", "g", "e"]:
        assert f"{r:{t}P}" == "-inf+/-nan"
    for t in ["F", "G", "E"]:
        assert f"{r:{t}P}" == "-INF+/-NAN"

    r = Readings(mean=np.nan, std=np.inf, size=1)
    assert f"{r}" == "nan(inf)"
    assert f"{r:B}" == "nan(inf)"
    assert f"{r:P}" == "nan+/-inf"
    for t in ["f", "g", "e"]:
        assert f"{r:{t}}" == "nan(inf)"
    for t in ["F", "G", "E"]:
        assert f"{r:{t}}" == "NAN(INF)"
    for t in ["f", "g", "e"]:
        assert f"{r:{t}P}" == "nan+/-inf"
    for t in ["F", "G", "E"]:
        assert f"{r:{t}P}" == "NAN+/-INF"

    r = Readings()
    assert f"{r}" == "nan(nan)"
    assert f"{r:B}" == "nan(nan)"
    assert f"{r:P}" == "nan+/-nan"
    for t in ["f", "g", "e"]:
        assert f"{r:{t}}" == "nan(nan)"
    for t in ["F", "G", "E"]:
        assert f"{r:{t}}" == "NAN(NAN)"
    for t in ["f", "g", "e"]:
        assert f"{r:{t}P}" == "nan+/-nan"
    for t in ["F", "G", "E"]:
        assert f"{r:{t}P}" == "NAN+/-NAN"

    r = Readings(mean=3.14159)
    assert f"{r}" == "3.14(nan)"
    assert f"{r:B}" == "3.14(nan)"
    assert f"{r:P}" == "3.14+/-nan"
    assert f"{r:f}" == "3.14(nan)"
    assert f"{r:e}" == "3.14(nan)e+00"
    assert f"{r:g}" == "3.1(nan)"
    assert f"{r:F}" == "3.14(NAN)"
    assert f"{r:E}" == "3.14(NAN)E+00"
    assert f"{r:G}" == "3.1(NAN)"
    assert f"{r:fP}" == "3.14+/-nan"
    assert f"{r:eP}" == "(3.14+/-nan)e+00"
    assert f"{r:gP}" == "3.1+/-nan"
    assert f"{r:FP}" == "3.14+/-NAN"
    assert f"{r:EP}" == "(3.14+/-NAN)E+00"
    assert f"{r:GP}" == "3.1+/-NAN"
    assert f"{r:.4f}" == "3.1416(nan)"
    assert f"{r:.4e}" == "3.1416(nan)e+00"
    assert f"{r:.4g}" == "3.142(nan)"
    assert f"{r:.4F}" == "3.1416(NAN)"
    assert f"{r:.4E}" == "3.1416(NAN)E+00"
    assert f"{r:.4G}" == "3.142(NAN)"
    assert f"{r:.4fP}" == "3.1416+/-nan"
    assert f"{r:.4eP}" == "(3.1416+/-nan)e+00"
    assert f"{r:.4gP}" == "3.142+/-nan"
    assert f"{r:.4FP}" == "3.1416+/-NAN"
    assert f"{r:.4EP}" == "(3.1416+/-NAN)E+00"
    assert f"{r:.4GP}" == "3.142+/-NAN"
    assert f"{r:.4}" == "3.1416(nan)"
    assert f"{r:.4B}" == "3.1416(nan)"
    assert f"{r:.4P}" == "3.1416+/-nan"

    r = Readings(mean=3.141e8, std=np.inf, size=1)
    assert f"{r}" == "314100000.00(inf)"
    assert f"{r: .1F}" == " 314100000.0(INF)"
    assert f"{r: .1e}" == " 3.1(inf)e+08"
    assert f"{r: .4E}" == " 3.1410(INF)E+08"
    assert f"{r: .1FP}" == " 314100000.0+/-INF"
    assert f"{r:.1eP}" == "(3.1+/-inf)e+08"
    assert f"{r: .4EP}" == "( 3.1410+/-INF)E+08"

    r = Readings(mean=3.141, std=np.nan, size=1)
    assert f"{r}" == "3.14(nan)"
    assert f"{r: F}" == " 3.14(NAN)"
    assert f"{r:.1F}" == "3.1(NAN)"
    assert f"{r:.1FP}" == "3.1+/-NAN"

    r = Readings(mean=np.nan, std=3.141, size=1)
    assert f"{r}" == "nan(3.141)"
    assert f"{r:P}" == "nan+/-3.141"
    assert f"{r: F}" == " NAN(3.141)"

    r = Readings(mean=np.nan, std=3.141e8, size=1)
    assert f"{r}" == "nan(314100000)"
    assert f"{r:P}" == "nan+/-314100000"
    assert f"{r: E}" == " NAN(3)E+08"
    assert f"{r:+e}" == "+nan(3)e+08"
    assert f"{r: EP}" == "( NAN+/-3)E+08"
    assert f"{r:+eP}" == "(+nan+/-3)e+08"

    r = Readings(mean=1.8667540e8)
    assert f"{r:.3S}" == "187(nan) M"
    assert f"{r:.3PS}" == "187+/-nan M"

    r = Readings(mean=1.8667540e4)
    assert f"{r:S}" == "19(nan) k"
    assert f"{r:.6PS}" == "18.6675+/-nan k"

    r = Readings(mean=1.8667540e-6)
    assert f"{r:.1US}" == "2(nan) µ"
    assert f"{r: .2PS}" == " 1.9+/-nan u"
    assert f"{r:.5PUS}" == "1.8668±nan µ"


def test_bracket_type_f() -> None:  # noqa: PLR0915
    r = Readings(mean=1.23456789, std=0.0123456789, size=1)
    assert f"{r:.1}" == "1.23(1)"
    assert f"{r:.2f}" == "1.235(12)"
    assert f"{r:.3}" == "1.2346(123)"
    assert f"{r:.9F}" == "1.2345678900(123456789)"
    assert f"{r:.14f}" == "1.234567890000000(12345678900000)"

    factor = 10**-20
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:> 39.4f}" == "      0.0000000000000000000123457(1235)"

    factor = 10**-19
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:> 39.4f}" == "       0.000000000000000000123457(1235)"

    factor = 10**-18
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:< 39.4f}" == " 0.00000000000000000123457(1235)       "

    factor = 10**-12
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:-^39.4f}" == "-------0.00000000000123457(1235)-------"

    factor = 10**-6
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:19.4f}" == "0.00000123457(1235)"

    r = Readings(mean=1.23456789, std=0.0123456789, size=1)
    assert f"{r:> 15.4f}" == "  1.23457(1235)"

    factor = 10**1
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:> 15.4f}" == "  12.3457(1235)"

    factor = 10**2
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:> 15.4f}" == " 123.457(1.235)"

    factor = 10**3
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:> 15.4f}" == " 1234.57(12.35)"

    factor = 10**4
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:> 15.4f}" == " 12345.7(123.5)"

    factor = 10**5
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:> 15.4f}" == "   123457(1235)"

    factor = 10**6
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r: >+20.4f}" == "     +1234570(12350)"

    factor = 10**7
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:> 16.4f}" == " 12345700(123500)"

    factor = 10**8
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:.4}" == "123457000(1235000)"

    factor = 10**18
    r = Readings(mean=1.23456789 * factor, std=0.0123456789 * factor, size=1)
    assert f"{r:.4}" == "1234570000000000000(12350000000000000)"

    r = Readings(mean=1.23456789, std=1234.56789, size=1)
    assert f"{r: .2}" == " 0(1200)"

    r = Readings(mean=1.23456789, std=123.456789, size=1)
    assert f"{r:.2}" == "0(120)"

    r = Readings(mean=1.23456789, std=12.3456789, size=1)
    assert f"{r: }" == " 1(12)"

    r = Readings(mean=1.23456789, std=1.23456789, size=1)
    assert f"{r:}" == "1.2(1.2)"

    r = Readings(mean=1.23456789, std=0.123456789, size=1)
    assert f"{r}" == "1.23(12)"

    r = Readings(mean=1.23456789, std=0.0123456789, size=1)
    assert f"{r}" == "1.235(12)"

    r = Readings(mean=1.23456789, std=0.00123456789, size=1)
    assert f"{r}" == "1.2346(12)"

    r = Readings(mean=1.23456789, std=0.000123456789, size=1)
    assert f"{r}" == "1.23457(12)"

    r = Readings(mean=1.23456789, std=0.000000123456789, size=1)
    assert f"{r}" == "1.23456789(12)"

    r = Readings(mean=1.23456789, std=0.000000000123456789, size=1)
    assert f"{r}" == "1.23456789000(12)"

    r = Readings(mean=1.23456789e-4, std=0.000000000123456789, size=1)
    assert f"{r}" == "0.00012345679(12)"

    r = Readings(mean=1.23456789e4, std=0.000000123456789, size=1)
    assert f"{r}" == "12345.67890000(12)"

    r = Readings(mean=1.23456789, std=0.0123456789, size=1)
    assert f"{r:.1}" == "1.23(1)"

    r = Readings(mean=1.23456789, std=0.0123456789, size=1)
    assert f"{r}" == "1.235(12)"

    r = Readings(mean=123456789.0, std=1234.56789, size=1)
    assert f"{r:.6e}" == "1.2345678900(123457)e+08"
    assert f"{r:.1f}" == "123457000(1000)"

    r = Readings(mean=1.23456789, std=0.12345, size=1)
    assert f"{r:.1}" == "1.2(1)"
    assert f"{r:.4}" == "1.2346(1235)"

    r = Readings(mean=1.23456789, std=0.945, size=1)
    assert f"{r:.1f}" == "1.2(9)"

    r = Readings(mean=-1.23456789, std=0.945, size=1)
    assert f"{r:.2f}" == "-1.23(94)"

    r = Readings(mean=1.23456789, std=0.95, size=1)
    assert f"{r:.1}" == "1.2(9)"
    assert f"{r:+.3f}" == "+1.235(950)"

    r = Readings(mean=1.23456789, std=0.951, size=1)
    assert f"{r:.1f}" == "1(1)"
    assert f"{r:.2f}" == "1.23(95)"
    assert f"{r:.3f}" == "1.235(951)"

    r = Readings(mean=1.23456789, std=0.999999999999, size=1)
    assert f"{r:.1}" == "1(1)"
    assert f"{r:.2}" == "1.2(1.0)"
    assert f"{r:.5}" == "1.2346(1.0000)"

    r = Readings(mean=1.23456789, std=1.5, size=1)
    assert f"{r:.1}" == "1(2)"

    r = Readings(mean=1.23456789, std=9.5, size=1)
    assert f"{r:.1f}" == "0(10)"

    r = Readings(mean=1.23456789, std=10.00, size=1)
    assert f"{r:.1f}" == "0(10)"

    r = Readings(mean=123.456789, std=0.321, size=1)
    assert f"{r:.1f}" == "123.5(3)"
    assert f"{r}" == "123.46(32)"

    r = Readings(mean=123.456789, std=0.95, size=1)
    assert f"{r:.1}" == "123.5(9)"
    assert f"{r:.3f}" == "123.457(950)"

    r = Readings(mean=123.456789, std=0.951, size=1)
    assert f"{r:.1}" == "123(1)"
    assert f"{r:.4}" == "123.4568(9510)"

    r = Readings(mean=123.456789, std=0.999999999999999, size=1)
    assert f"{r:.1f}" == "123(1)"

    r = Readings(mean=-123.456789, std=0.999999999999999, size=1)
    assert f"{r:.6}" == "-123.45679(1.00000)"

    r = Readings(mean=0.9876, std=0.1234, size=1)
    assert f"{r:.1f}" == "1.0(1)"
    assert f"{r:.3f}" == "0.988(123)"

    r = Readings(mean=0.000003512, std=0.00000006551, size=1)
    assert f"{r:.1}" == "0.00000351(7)"
    assert f"{r}" == "0.000003512(66)"

    r = Readings(mean=0.000003512, std=0.0000008177, size=1)
    assert f"{r:.1f}" == "0.0000035(8)"
    assert f"{r:.3}" == "0.000003512(818)"

    r = Readings(mean=0.000003512, std=0.000009773, size=1)
    assert f"{r:.1}" == "0.00000(1)"
    assert f"{r:.4}" == "0.000003512(9773)"

    r = Readings(mean=0.000003512, std=0.00001241, size=1)
    assert f"{r:.1}" == "0.00000(1)"
    assert f"{r}" == "0.000004(12)"

    r = Readings(mean=0.000003512, std=0.0009998, size=1)
    assert f"{r:.1}" == "0.000(1)"
    assert f"{r:.4f}" == "0.0000035(9998)"

    r = Readings(mean=0.000003512, std=0.006563, size=1)
    assert f"{r:.1f}" == "0.000(7)"
    assert f"{r:}" == "0.0000(66)"

    r = Readings(mean=0.000003512, std=0.09564, size=1)
    assert f"{r:.1}" == "0.0(1)"
    assert f"{r:.4f}" == "0.00000(9564)"

    r = Readings(mean=0.000003512, std=0.7772, size=1)
    assert f"{r:.1}" == "0.0(8)"

    r = Readings(mean=0.000003512, std=9.75, size=1)
    assert f"{r:.1}" == "0(10)"

    r = Readings(mean=0.000003512, std=33.97, size=1)
    assert f"{r:.1}" == "0(30)"

    r = Readings(mean=0.000003512, std=715.5, size=1)
    assert f"{r:.1}" == "0(700)"
    assert f"{r:.5f}" == "0.00(715.50)"

    r = Readings(mean=0.07567, std=0.00000007018, size=1)
    assert f"{r:.1f}" == "0.07567000(7)"
    assert f"{r:.5}" == "0.075670000000(70180)"

    r = Readings(mean=0.07567, std=0.0000003645, size=1)
    assert f"{r:.1}" == "0.0756700(4)"

    r = Readings(mean=-0.07567, std=0.0000003645, size=1)
    assert f"{r:.3f}" == "-0.075670000(365)"

    r = Readings(mean=0.07567, std=0.000005527, size=1)
    assert f"{r:.1}" == "0.075670(6)"
    assert f"{r: .2F}" == " 0.0756700(55)"

    r = Readings(mean=0.07567, std=0.00004429, size=1)
    assert f"{r:.1f}" == "0.07567(4)"
    assert f"{r}" == "0.075670(44)"

    r = Readings(mean=0.07567, std=0.0008017, size=1)
    assert f"{r:.1}" == "0.0757(8)"
    assert f"{r:.3}" == "0.075670(802)"

    r = Readings(mean=0.07567, std=0.006854, size=1)
    assert f"{r:.1}" == "0.076(7)"
    assert f"{r:.4}" == "0.075670(6854)"

    r = Readings(mean=0.07567, std=0.06982, size=1)
    assert f"{r:.1}" == "0.08(7)"
    assert f"{r}" == "0.076(70)"

    r = Readings(mean=0.07567, std=0.7382, size=1)
    assert f"{r:.1}" == "0.1(7)"
    assert f"{r:.3}" == "0.076(738)"

    r = Readings(mean=0.07567, std=7.436, size=1)
    assert f"{r:.1}" == "0(7)"
    assert f"{r}" == "0.1(7.4)"

    r = Readings(mean=0.07567, std=48.75, size=1)
    assert f"{r:.1}" == "0(50)"
    assert f"{r:.3}" == "0.1(48.8)"

    r = Readings(mean=0.07567, std=487.9, size=1)
    assert f"{r:.1}" == "0(500)"
    assert f"{r:.5f}" == "0.08(487.90)"

    r = Readings(mean=8.545, std=0.00000007513, size=1)
    assert f"{r:.1}" == "8.54500000(8)"
    assert f"{r}" == "8.545000000(75)"

    r = Readings(mean=8.545, std=0.000009935, size=1)
    assert f"{r:.1}" == "8.54500(1)"
    assert f"{r:.2}" == "8.5450000(99)"

    r = Readings(mean=8.545, std=0.003243, size=1)
    assert f"{r:.1}" == "8.545(3)"
    assert f"{r:.3}" == "8.54500(324)"

    r = Readings(mean=8.545, std=0.0812, size=1)
    assert f"{r:.1}" == "8.54(8)"
    assert f"{r}" == "8.545(81)"

    r = Readings(mean=8.545, std=0.4293, size=1)
    assert f"{r:.1}" == "8.5(4)"
    assert f"{r:.4}" == "8.5450(4293)"

    r = Readings(mean=8.545, std=6.177, size=1)
    assert f"{r:.1}" == "9(6)"
    assert f"{r:.2}" == "8.5(6.2)"
    assert f"{r:.3}" == "8.54(6.18)"
    assert f"{r:.4}" == "8.545(6.177)"
    assert f"{r:.7}" == "8.545000(6.177000)"

    r = Readings(mean=8.545, std=26.02, size=1)
    assert f"{r:.1}" == "10(30)"
    assert f"{r:.3}" == "8.5(26.0)"

    r = Readings(mean=8.545, std=406.1, size=1)
    assert f"{r:.1}" == "0(400)"
    assert f"{r:.3}" == "9(406)"

    r = Readings(mean=8.545, std=3614.0, size=1)
    assert f"{r:.1}" == "0(4000)"
    assert f"{r:.5f}" == "8.5(3614.0)"

    r = Readings(mean=89.95, std=0.00000006815, size=1)
    assert f"{r:.1}" == "89.95000000(7)"
    assert f"{r:.4}" == "89.95000000000(6815)"

    r = Readings(mean=89.95, std=0.0000002651, size=1)
    assert f"{r:.1}" == "89.9500000(3)"
    assert f"{r}" == "89.95000000(27)"

    r = Readings(mean=89.95, std=0.0001458, size=1)
    assert f"{r:.1}" == "89.9500(1)"
    assert f"{r:.4f}" == "89.9500000(1458)"

    r = Readings(mean=89.95, std=0.009532, size=1)
    assert f"{r:.1}" == "89.95(1)"
    assert f"{r}" == "89.9500(95)"

    r = Readings(mean=89.95, std=0.09781, size=1)
    assert f"{r:.1}" == "90.0(1)"
    assert f"{r:.2f}" == "89.950(98)"

    r = Readings(mean=89.95, std=0.7335, size=1)
    assert f"{r:.1}" == "90.0(7)"
    assert f"{r:.2}" == "89.95(73)"
    assert f"{r:.3}" == "89.950(734)"

    r = Readings(mean=89.95, std=3.547, size=1)
    assert f"{r:.1}" == "90(4)"
    assert f"{r:.2}" == "90.0(3.5)"
    assert f"{r:.3}" == "89.95(3.55)"
    assert f"{r:.4}" == "89.950(3.547)"

    r = Readings(mean=89.95, std=31.4, size=1)
    assert f"{r:.1}" == "90(30)"
    assert f"{r:.2f}" == "90(31)"
    assert f"{r:.3}" == "90.0(31.4)"

    r = Readings(mean=89.95, std=623.1, size=1)
    assert f"{r:.1}" == "100(600)"
    assert f"{r}" == "90(620)"

    r = Readings(mean=89.95, std=2019.0, size=1)
    assert f"{r:.1}" == "0(2000)"
    assert f"{r:.3}" == "90(2020)"

    r = Readings(mean=89.95, std=94600.0, size=1)
    assert f"{r:.1}" == "0(90000)"
    assert f"{r:.3}" == "100(94600)"

    r = Readings(mean=58740.0, std=0.00000001402, size=1)
    assert f"{r:.1}" == "58740.00000000(1)"
    assert f"{r}" == "58740.000000000(14)"

    r = Readings(mean=58740.0, std=0.000000975, size=1)
    assert f"{r:.1}" == "58740.000000(1)"
    assert f"{r}" == "58740.00000000(97)"

    r = Readings(mean=58740.0, std=0.0001811, size=1)
    assert f"{r:.1}" == "58740.0000(2)"
    assert f"{r:.4f}" == "58740.0000000(1811)"

    r = Readings(mean=58740.0, std=0.04937, size=1)
    assert f"{r:.1}" == "58740.00(5)"
    assert f"{r:.2}" == "58740.000(49)"

    r = Readings(mean=58740.0, std=0.6406, size=1)
    assert f"{r:.1}" == "58740.0(6)"
    assert f"{r:.3}" == "58740.000(641)"

    r = Readings(mean=58740.0, std=9.357, size=1)
    assert f"{r:.1}" == "58740(9)"
    assert f"{r}" == "58740.0(9.4)"

    r = Readings(mean=58740.0, std=99.67, size=1)
    assert f"{r:.1f}" == "58700(100)"
    assert f"{r}" == "58740(100)"
    assert f"{r:.3}" == "58740.0(99.7)"

    r = Readings(mean=58740.0, std=454.6, size=1)
    assert f"{r:.1}" == "58700(500)"
    assert f"{r:.3f}" == "58740(455)"

    r = Readings(mean=58740.0, std=1052.0, size=1)
    assert f"{r:.1}" == "59000(1000)"
    assert f"{r}" == "58700(1100)"

    r = Readings(mean=58740.0, std=87840.0, size=1)
    assert f"{r:.1}" == "60000(90000)"
    assert f"{r:.3f}" == "58700(87800)"

    r = Readings(mean=58740.0, std=5266000.0, size=1)
    assert f"{r:.1f}" == "0(5000000)"
    assert f"{r:.4f}" == "59000(5266000)"

    r = Readings(mean=58740.0, std=97769999.0, size=1)
    assert f"{r:.1}" == "0(100000000)"
    assert f"{r}" == "0(98000000)"
    assert f"{r:.5}" == "59000(97770000)"


def test_std_is_zero() -> None:
    m = 1.23456789
    r = Readings(mean=m, std=0, size=1)
    assert f"{r}" == f"{m:.2f}"
    assert f"{r:.4}" == f"{m:.4f}"
    assert f"{r:g}" == f"{m:.2g}"
    assert f"{r:.5g}" == f"{m:.5g}"
    assert f"{r:E}" == f"{m:.2E}"
    assert f"{r:.1E}" == f"{m:.1E}"

    r = Readings(mean=123.456e6, std=0, size=1)
    assert f"{r:S}" == "120 M"
    assert f"{r:>+20.4S}" == "            +123.5 M"


def test_bracket_type_e_ureal() -> None:  # noqa: PLR0915
    r = Readings(mean=1.23456789, std=0.0001, size=1)
    assert f"{r:.1e}" == "1.2346(1)e+00"
    assert f"{r:.3e}" == "1.234568(100)e+00"

    r = Readings(mean=1.23456789, std=0.96, size=1)
    assert f"{r:.1e}" == "1(1)e+00"
    assert f"{r:.2e}" == "1.23(96)e+00"

    r = Readings(mean=1.23456789, std=1.0, size=1)
    assert f"{r:.1e}" == "1(1)e+00"
    assert f"{r:.3e}" == "1.23(1.00)e+00"

    r = Readings(mean=123.456789, std=0.1, size=1)
    assert f"{r:.1e}" == "1.235(1)e+02"
    assert f"{r:.4e}" == "1.234568(1000)e+02"

    r = Readings(mean=123.456789, std=0.950, size=1)
    assert f"{r:.1e}" == "1.235(9)e+02"
    assert f"{r:.2e}" == "1.2346(95)e+02"

    r = Readings(mean=123.456789, std=0.951, size=1)
    assert f"{r:.1e}" == "1.23(1)e+02"
    assert f"{r:.3e}" == "1.23457(951)e+02"

    r = Readings(mean=123.456789, std=1.0, size=1)
    assert f"{r:.1e}" == "1.23(1)e+02"
    assert f"{r:E}" == "1.235(10)E+02"

    r = Readings(mean=123.456789, std=9.123, size=1)
    assert f"{r:.1e}" == "1.23(9)e+02"
    assert f"{r:.4e}" == "1.23457(9123)e+02"

    r = Readings(mean=123.456789, std=9.9, size=1)
    assert f"{r:.1e}" == "1.2(1)e+02"
    assert f"{r:e}" == "1.235(99)e+02"

    r = Readings(mean=123.456789, std=94.9, size=1)
    assert f"{r:.1e}" == "1.2(9)e+02"
    assert f"{r:.3e}" == "1.235(949)e+02"

    r = Readings(mean=-1.23456789, std=0.0123456789, size=1)
    assert f"{r:.1e}" == "-1.23(1)e+00"
    assert f"{r:.5e}" == "-1.234568(12346)e+00"

    r = Readings(mean=1.257e-6, std=0.00007453e-6, size=1)
    assert f"{r:.1e}" == "1.25700(7)e-06"
    assert f"{r:+.3E}" == "+1.2570000(745)E-06"

    r = Readings(mean=1.257e-6, std=0.00909262e-6, size=1)
    assert f"{r:.1e}" == "1.257(9)e-06"
    assert f"{r:e}" == "1.2570(91)e-06"

    r = Readings(mean=1.257e-6, std=0.1174e-6, size=1)
    assert f"{r:.1e}" == "1.3(1)e-06"
    assert f"{r:.3e}" == "1.257(117)e-06"

    r = Readings(mean=1.257e-6, std=7.287e-6, size=1)
    assert f"{r:.1e}" == "1(7)e-06"
    assert f"{r:.4e}" == "1.257(7.287)e-06"

    r = Readings(mean=1.257e-6, std=67.27e-6, size=1)
    assert f"{r:.1e}" == "0(7)e-05"
    assert f"{r:E}" == "0.1(6.7)E-05"

    r = Readings(mean=1.257e-6, std=124.1e-6, size=1)
    assert f"{r:.1e}" == "0(1)e-04"
    assert f"{r:.2e}" == "0.0(1.2)e-04"

    r = Readings(mean=1.257e-6, std=4583.0e-6, size=1)
    assert f"{r:.1e}" == "0(5)e-03"
    assert f"{r:.3e}" == "0.00(4.58)e-03"

    r = Readings(mean=1.257e-6, std=74743.0e-6, size=1)
    assert f"{r:.1e}" == "0(7)e-02"

    r = Readings(mean=1.257e-6, std=4575432.0e-6, size=1)
    assert f"{r:.1e}" == "0(5)e+00"

    r = Readings(mean=7.394e-3, std=0.00002659e-3, size=1)
    assert f"{r:.1e}" == "7.39400(3)e-03"
    assert f"{r:.3e}" == "7.3940000(266)e-03"

    r = Readings(mean=7.394e-3, std=0.0007031e-3, size=1)
    assert f"{r:.1E}" == "7.3940(7)E-03"
    assert f"{r:e}" == "7.39400(70)e-03"

    r = Readings(mean=7.394e-3, std=0.003659e-3, size=1)
    assert f"{r:.1e}" == "7.394(4)e-03"
    assert f"{r:.2e}" == "7.3940(37)e-03"

    r = Readings(mean=7.394e-3, std=0.04227e-3, size=1)
    assert f"{r:.1e}" == "7.39(4)e-03"
    assert f"{r:.4e}" == "7.39400(4227)e-03"

    r = Readings(mean=7.394e-3, std=0.9072e-3, size=1)
    assert f"{r:.1e}" == "7.4(9)e-03"
    assert f"{r:.3e}" == "7.394(907)e-03"

    r = Readings(mean=7.394e-3, std=4.577e-3, size=1)
    assert f"{r:.1e}" == "7(5)e-03"
    assert f"{r:.2e}" == "7.4(4.6)e-03"

    r = Readings(mean=7.394e-3, std=93.41e-3, size=1)
    assert f"{r:.1e}" == "1(9)e-02"
    assert f"{r:.3e}" == "0.74(9.34)e-02"

    r = Readings(mean=7.394e-3, std=421.0e-3, size=1)
    assert f"{r:.1e}" == "0(4)e-01"
    assert f"{r:e}" == "0.1(4.2)e-01"

    r = Readings(mean=7.394e-3, std=9492.0e-3, size=1)
    assert f"{r:.1e}" == "0(9)e+00"
    assert f"{r:.3e}" == "0.01(9.49)e+00"

    r = Readings(mean=7.394e-3, std=39860.0e-3, size=1)
    assert f"{r:.1e}" == "0(4)e+01"
    assert f"{r:e}" == "0.0(4.0)e+01"

    r = Readings(mean=2.675e-2, std=0.0000019e-2, size=1)
    assert f"{r:.1e}" == "2.675000(2)e-02"
    assert f"{r:.3e}" == "2.67500000(190)e-02"

    r = Readings(mean=2.675e-2, std=0.00975e-2, size=1)
    assert f"{r:.1e}" == "2.67(1)e-02"
    assert f"{r:.3e}" == "2.67500(975)e-02"

    r = Readings(mean=2.675e-2, std=0.08942e-2, size=1)
    assert f"{r:.1e}" == "2.67(9)e-02"
    assert f"{r:e}" == "2.675(89)e-02"

    r = Readings(mean=2.675e-2, std=0.8453e-2, size=1)
    assert f"{r:.1e}" == "2.7(8)e-02"
    assert f"{r:e}" == "2.67(85)e-02"

    r = Readings(mean=2.675e-2, std=8.577e-2, size=1)
    assert f"{r:.1e}" == "3(9)e-02"
    assert f"{r:E}" == "2.7(8.6)E-02"
    assert f"{r:.3E}" == "2.67(8.58)E-02"

    r = Readings(mean=2.675e-2, std=12.37e-2, size=1)
    assert f"{r:.1e}" == "0(1)e-01"
    assert f"{r:.3e}" == "0.27(1.24)e-01"

    r = Readings(mean=2.675e-2, std=226.5e-2, size=1)
    assert f"{r:.1e}" == "0(2)e+00"
    assert f"{r:.4e}" == "0.027(2.265)e+00"

    r = Readings(mean=2.675e-2, std=964900.0e-2, size=1)
    assert f"{r:.1e}" == "0(1)e+04"
    assert f"{r:.6e}" == "0.00003(9.64900)e+03"

    r = Readings(mean=0.9767, std=0.00000001084, size=1)
    assert f"{r:.1e}" == "9.7670000(1)e-01"
    assert f"{r:.3e}" == "9.767000000(108)e-01"

    r = Readings(mean=0.9767, std=0.0000009797, size=1)
    assert f"{r:.1e}" == "9.76700(1)e-01"
    assert f"{r:e}" == "9.7670000(98)e-01"

    r = Readings(mean=0.9767, std=0.004542, size=1)
    assert f"{r:.1e}" == "9.77(5)e-01"
    assert f"{r:.5e}" == "9.767000(45420)e-01"

    r = Readings(mean=0.9767, std=0.02781, size=1)
    assert f"{r:+.1e}" == "+9.8(3)e-01"

    r = Readings(mean=-0.9767, std=0.02781, size=1)
    assert f"{r:.3e}" == "-9.767(278)e-01"

    r = Readings(mean=0.9767, std=0.4764, size=1)
    assert f"{r:.1e}" == "1.0(5)e+00"
    assert f"{r:e}" == "9.8(4.8)e-01"
    assert f"{r:.3e}" == "9.77(4.76)e-01"
    assert f"{r:.4e}" == "9.767(4.764)e-01"

    r = Readings(mean=0.9767, std=4.083, size=1)
    assert f"{r:.1e}" == "1(4)e+00"
    assert f"{r:.3e}" == "0.98(4.08)e+00"

    r = Readings(mean=0.9767, std=45.14, size=1)
    assert f"{r:.1e}" == "0(5)e+01"
    assert f"{r:.4e}" == "0.098(4.514)e+01"

    r = Readings(mean=0.9767, std=692500.0, size=1)
    assert f"{r:.1e}" == "0(7)e+05"
    assert f"{r:.3e}" == "0.00(6.92)e+05"

    r = Readings(mean=2.952, std=0.00000006986, size=1)
    assert f"{r:.1e}" == "2.95200000(7)e+00"
    assert f"{r:.5e}" == "2.952000000000(69860)e+00"

    r = Readings(mean=2.952, std=0.04441, size=1)
    assert f"{r:.1e}" == "2.95(4)e+00"
    assert f"{r:.3e}" == "2.9520(444)e+00"

    r = Readings(mean=2.952, std=0.1758, size=1)
    assert f"{r:.1e}" == "3.0(2)e+00"
    assert f"{r:.3e}" == "2.952(176)e+00"

    r = Readings(mean=2.952, std=1.331, size=1)
    assert f"{r:.1e}" == "3(1)e+00"
    assert f"{r:e}" == "3.0(1.3)e+00"

    r = Readings(mean=2.952, std=34.6, size=1)
    assert f"{r:.1e}" == "0(3)e+01"
    assert f"{r:.3e}" == "0.30(3.46)e+01"

    r = Readings(mean=2.952, std=46280.0, size=1)
    assert f"{r:.1e}" == "0(5)e+04"
    assert f"{r:.5e}" == "0.0003(4.6280)e+04"

    r = Readings(mean=96.34984, std=0.00000002628, size=1)
    assert f"{r:.1e}" == "9.634984000(3)e+01"
    assert f"{r:.3e}" == "9.63498400000(263)e+01"

    r = Readings(mean=96.34984, std=0.00008999, size=1)
    assert f"{r:.1e}" == "9.634984(9)e+01"
    assert f"{r:.3e}" == "9.63498400(900)e+01"

    r = Readings(mean=96.34984, std=0.3981, size=1)
    assert f"{r:.1e}" == "9.63(4)e+01"
    assert f"{r:.4e}" == "9.63498(3981)e+01"

    r = Readings(mean=96.34984, std=7.17, size=1)
    assert f"{r:.1e}" == "9.6(7)e+01"
    assert f"{r:.3e}" == "9.635(717)e+01"

    r = Readings(mean=96.34984, std=1074.0, size=1)
    assert f"{r:.1e}" == "0(1)e+03"
    assert f"{r:.3e}" == "0.10(1.07)e+03"

    r = Readings(mean=92270.0, std=0.00000004531, size=1)
    assert f"{r:.1e}" == "9.227000000000(5)e+04"
    assert f"{r:.3e}" == "9.22700000000000(453)e+04"

    r = Readings(mean=92270.0, std=0.007862, size=1)
    assert f"{r:.1e}" == "9.2270000(8)e+04"
    assert f"{r:e}" == "9.22700000(79)e+04"

    r = Readings(mean=92270.0, std=0.2076, size=1)
    assert f"{r:.1e}" == "9.22700(2)e+04"
    assert f"{r:.3e}" == "9.2270000(208)e+04"

    r = Readings(mean=92270.0, std=2.202, size=1)
    assert f"{r:.1e}" == "9.2270(2)e+04"
    assert f"{r:.3e}" == "9.227000(220)e+04"

    r = Readings(mean=92270.0, std=49.12, size=1)
    assert f"{r:.1e}" == "9.227(5)e+04"
    assert f"{r:.4e}" == "9.227000(4912)e+04"

    r = Readings(mean=92270.0, std=19990.0, size=1)
    assert f"{r:.1e}" == "9(2)e+04"
    assert f"{r:.6e}" == "9.22700(1.99900)e+04"

    r = Readings(mean=92270.0, std=740800.0, size=1)
    assert f"{r:.1e}" == "1(7)e+05"
    assert f"{r:.3e}" == "0.92(7.41)e+05"

    r = Readings(mean=92270.0, std=1380000.0, size=1)
    assert f"{r:.1e}" == "0(1)e+06"
    assert f"{r:.5e}" == "0.0923(1.3800)e+06"

    r = Readings(mean=92270.0, std=29030000.0, size=1)
    assert f"{r:.1e}" == "0(3)e+07"
    assert f"{r:.7e}" == "0.009227(2.903000)e+07"


def test_type_g() -> None:
    r = Readings(mean=43.842, std=0.0123, size=1)
    assert f"{r:.1g}" == "43.84(1)"

    r = Readings(mean=4384.2, std=1.23, size=1)
    assert f"{r:.3g}" == "4384.20(1.23)"
    assert f"{r:.1G}" == "4.384(1)E+03"

    r = Readings(mean=123456789.0, std=1234.56789, size=1)
    assert f"{r:.4g}" == "1.23456789(1235)e+08"
    assert f"{r:.2G}" == "1.234568(12)E+08"

    r = Readings(mean=7.2524e-8, std=5.429e-10, size=1)
    assert f"{r:.2g}" == "7.252(54)e-08"
    assert f"{r:.1G}" == "7.25(5)E-08"

    r = Readings(mean=7.2524e4, std=5.429e3, size=1)
    assert f"{r:.4G}" == "7.2524(5429)E+04"
    assert f"{r:.1g}" == "7.3(5)e+04"


def test_unicode() -> None:
    r = Readings(mean=18.5424, std=0.94271, size=1)

    for t in ["f", "F"]:
        assert f"{r:{t}U}" == "18.54(94)"

    for t in ["e", "E"]:
        assert f"{r:{t}U}" == "1.854(94)×10¹"  # noqa: RUF001

    r = Readings(mean=1.23456789, std=0.123456789, size=1)
    assert f"{r:.3eU}" == "1.235(123)"

    factor = 1e-6
    r = Readings(mean=1.23456789 * factor, std=0.123456789 * factor, size=1)
    assert f"{r:.3EU}" == "1.235(123)×10⁻⁶"  # noqa: RUF001

    factor = 1e12
    r = Readings(mean=1.23456789 * factor, std=0.123456789 * factor, size=1)
    assert f"{r:.3EU}" == "1.235(123)×10¹²"  # noqa: RUF001

    factor = 1e100
    r = Readings(mean=1.23456789 * factor, std=0.123456789 * factor, size=1)
    assert f"{r:.3eU}" == "nan(nan)"
    r = Readings(mean=1.23456789 * factor, std=0.123456789 * factor, size=1, overload=None)
    assert f"{r:.3eU}" == "1.235(123)×10¹⁰⁰"  # noqa: RUF001

    factor = 1e-100
    r = Readings(mean=1.23456789 * factor, std=0.123456789 * factor, size=1)
    assert f"{r:.3EU}" == "1.235(123)×10⁻¹⁰⁰"  # noqa: RUF001


@pytest.mark.skipif(sys.version_info[:2] < (3, 11), reason="requires Python 3.11+")
def test_z_option() -> None:
    r = Readings(mean=-1e-6, std=1e-4, size=10)
    assert f"{r:.1}" == "-0.00000(3)"
    assert f"{r:z.1}" == "0.00000(3)"


def test_hash_symbol() -> None:
    r = Readings(mean=5.4, std=1.2, size=1)
    assert f"{r:#.1}" == "5.(1.)"
    assert f"{r:#}" == "5.4(1.2)"

    r = Readings(mean=1, std=0.001, size=1)
    assert f"{r:#.1}" == "1.000(1)"

    r = Readings(mean=1, std=0.1, size=1)
    assert f"{r:#.1}" == "1.0(1)"

    r = Readings(mean=1, std=1, size=1)
    assert f"{r:.1}" == "1(1)"
    assert f"{r:#.1}" == "1.(1.)"

    r = Readings(mean=1, std=0.9876, size=1)
    assert f"{r:#.1}" == "1.(1.)"

    r = Readings(mean=1, std=0.9876, size=1)
    assert f"{r:#.2f}" == "1.00(99)"

    r = Readings(mean=1, std=10, size=1)
    assert f"{r:#.1}" == "0.(10.)"

    r = Readings(mean=1, std=1000, size=1)
    assert f"{r:#.1}" == "0.(1000.)"

    r = Readings(mean=12345, std=9876, size=1)
    assert f"{r:#e}" == "1.23(99)e+04"
    assert f"{r:#}" == "12300.(9900.)"

    r = Readings(mean=10, std=10, size=1)
    assert f"{r:#.1E}" == "1.(1.)E+01"


def test_grouping_field() -> None:
    r = Readings(mean=123456789, std=123456, size=1)
    assert f"{r:,.6}" == "123,456,789(123,456)"
    assert f"{r:,}" == "123,460,000(120,000)"
    assert f"{r:_.1}" == "123_500_000(100_000)"


@pytest.mark.skipif(sys.version_info[:2] < (3, 10), reason="requires Python 3.10+")
def test_zero_field() -> None:
    # https://bugs.python.org/issue27772 was fixed in Python 3.10
    r = Readings(mean=1.342, std=0.0041, size=1)
    assert f"{r:015.1}" == "1.342(4)0000000"
    assert f"{r:>+024.3}" == "00000000000+1.34200(410)"


def test_latex() -> None:
    r = Readings(mean=1.23456789, std=0.123456789, size=1)
    assert f"{r:.3eL}" == r"1.235\left(123\right)"

    factor = 1e-6
    r = Readings(mean=1.23456789 * factor, std=0.123456789 * factor, size=1)
    assert f"{r:.3EL}" == r"1.235\left(123\right)\times10^{-6}"

    factor = 1e12
    r = Readings(mean=1.23456789 * factor, std=0.123456789 * factor, size=1)
    assert f"{r:.3EL}" == r"1.235\left(123\right)\times10^{12}"

    factor = 1e100
    r = Readings(mean=1.23456789 * factor, std=0.123456789 * factor, size=1)
    assert f"{r:.3eL}" == r"\mathrm{NaN}\left(\mathrm{NaN}\right)"
    r = Readings(mean=1.23456789 * factor, std=0.123456789 * factor, size=1, overload=None)
    assert f"{r:.3eL}" == r"1.235\left(123\right)\times10^{100}"

    factor = 1e-100
    r = Readings(mean=1.23456789 * factor, std=0.123456789 * factor, size=1)
    assert f"{r:.3EL}" == r"1.235\left(123\right)\times10^{-100}"

    r = Readings(mean=3.14159)
    assert f"{r:fL}" == r"3.14\left(\mathrm{NaN}\right)"
    assert f"{r:.4fL}" == r"3.1416\left(\mathrm{NaN}\right)"

    r = Readings(mean=np.nan, std=3.142, size=1)
    assert f"{r:L}" == r"\mathrm{NaN}\left(3.142\right)"

    r = Readings(mean=-np.inf, std=np.inf, size=1)
    assert f"{r:FL}" == r"-\infty\left(\infty\right)"


def test_percent_type() -> None:
    r = Readings(mean=0.1548175123, std=0.0123456, size=1)
    assert f"{r:.1%}" == "15(1)%"
    assert f"{r:.4%}" == "15.482(1.235)%"
    assert f"{r:.3%L}" == r"15.48\left(1.23\right)\%"

    r = Readings(mean=0.1548175123, std=0.000123456, size=1)
    assert f"{r:%L}" == r"15.482\left(12\right)\%"
    assert f"{r:%U}" == "15.482(12)%"


def test_plus_minus() -> None:
    r = Readings(mean=1.0, std=0.000123456789, size=1)
    assert f"{r:+.4fP}" == "+1.0000000+/-0.0001235"

    r = Readings(mean=7.2524, std=0.0032153, size=1)
    assert f"{r:.4fP}" == "7.252400+/-0.003215"

    r = Readings(mean=-1.2345, std=123.456789, size=1)
    assert f"{r:12.5fP}" == "-1.23+/-123.46"

    r = Readings(mean=1.5431384e-8, std=4.32856e-12, size=1)
    assert f"{r:P}" == "0.0000000154314+/-0.0000000000043"
    assert f"{r:eP}" == "(1.54314+/-0.00043)e-08"

    r = Readings(mean=1.5431384e7, std=4.32856e6, size=1)
    assert f"{r:.1P}" == "15000000+/-4000000"
    assert f"{r:P}" == "15400000+/-4300000"
    assert f"{r:.5P}" == "15431400+/-4328600"
    assert f"{r:eP}" == "(1.54+/-0.43)e+07"
    assert f"{r: .3eP}" == "( 1.543+/-0.433)e+07"
    assert f"{r:< 30.3eP}" == "( 1.543+/-0.433)e+07          "
    assert f"{r:>30.3eP}" == "           (1.543+/-0.433)e+07"
    assert f"{r:.>30.3eP}" == "...........(1.543+/-0.433)e+07"


def test_si_prefix_factor() -> None:  # noqa: PLR0915
    prefix, factor = si_prefix_factor(-36)
    assert prefix == "q"
    assert factor == 1e-6

    prefix, factor = si_prefix_factor(-35)
    assert prefix == "q"
    assert factor == 1e-5

    prefix, factor = si_prefix_factor(-34)
    assert prefix == "q"
    assert factor == 1e-4

    prefix, factor = si_prefix_factor(-33)
    assert prefix == "q"
    assert factor == 1e-3

    prefix, factor = si_prefix_factor(-32)
    assert prefix == "q"
    assert factor == 1e-2

    prefix, factor = si_prefix_factor(-31)
    assert prefix == "q"
    assert factor == 1e-1

    prefix, factor = si_prefix_factor(-30)
    assert prefix == "q"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(-29)
    assert prefix == "q"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(-28)
    assert prefix == "q"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(-27)
    assert prefix == "r"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(-26)
    assert prefix == "r"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(-25)
    assert prefix == "r"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(-24)
    assert prefix == "y"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(-23)
    assert prefix == "y"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(-22)
    assert prefix == "y"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(-21)
    assert prefix == "z"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(-20)
    assert prefix == "z"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(-19)
    assert prefix == "z"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(-18)
    assert prefix == "a"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(-17)
    assert prefix == "a"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(-16)
    assert prefix == "a"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(-15)
    assert prefix == "f"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(-14)
    assert prefix == "f"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(-13)
    assert prefix == "f"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(-12)
    assert prefix == "p"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(-11)
    assert prefix == "p"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(-10)
    assert prefix == "p"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(-9)
    assert prefix == "n"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(-8)
    assert prefix == "n"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(-7)
    assert prefix == "n"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(-6)
    assert prefix == "u"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(-5)
    assert prefix == "u"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(-4)
    assert prefix == "u"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(-3)
    assert prefix == "m"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(-2)
    assert prefix == "m"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(-1)
    assert prefix == "m"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(0)
    assert prefix == ""
    assert factor == 1e0

    prefix, factor = si_prefix_factor(1)
    assert prefix == ""
    assert factor == 1e1

    prefix, factor = si_prefix_factor(2)
    assert prefix == ""
    assert factor == 1e2

    prefix, factor = si_prefix_factor(3)
    assert prefix == "k"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(4)
    assert prefix == "k"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(5)
    assert prefix == "k"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(6)
    assert prefix == "M"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(7)
    assert prefix == "M"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(8)
    assert prefix == "M"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(9)
    assert prefix == "G"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(10)
    assert prefix == "G"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(11)
    assert prefix == "G"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(12)
    assert prefix == "T"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(13)
    assert prefix == "T"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(14)
    assert prefix == "T"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(15)
    assert prefix == "P"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(16)
    assert prefix == "P"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(17)
    assert prefix == "P"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(18)
    assert prefix == "E"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(19)
    assert prefix == "E"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(20)
    assert prefix == "E"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(21)
    assert prefix == "Z"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(22)
    assert prefix == "Z"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(23)
    assert prefix == "Z"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(24)
    assert prefix == "Y"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(25)
    assert prefix == "Y"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(26)
    assert prefix == "Y"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(27)
    assert prefix == "R"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(28)
    assert prefix == "R"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(29)
    assert prefix == "R"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(30)
    assert prefix == "Q"
    assert factor == 1e0

    prefix, factor = si_prefix_factor(31)
    assert prefix == "Q"
    assert factor == 1e1

    prefix, factor = si_prefix_factor(32)
    assert prefix == "Q"
    assert factor == 1e2

    prefix, factor = si_prefix_factor(33)
    assert prefix == "Q"
    assert factor == 1e3

    prefix, factor = si_prefix_factor(34)
    assert prefix == "Q"
    assert factor == 1e4

    prefix, factor = si_prefix_factor(35)
    assert prefix == "Q"
    assert factor == 1e5

    prefix, factor = si_prefix_factor(36)
    assert prefix == "Q"
    assert factor == 1e6


def test_si() -> None:  # noqa: PLR0915
    r = Readings(mean=2.37216512e-32, std=1.3721356e-32, size=1)
    assert f"{r:.1S}" == "0.02(1) q"
    assert f"{r:.3PS}" == "(0.0237+/-0.0137) q"

    r = Readings(mean=4.638174e-30, std=0.0635119e-30, size=1)
    assert f"{r:.2S}" == "4.638(64) q"
    assert f"{r:.1PS}" == "(4.64+/-0.06) q"

    r = Readings(mean=8.2621518e-29, std=0.00826725e-29, size=1)
    assert f"{r:.3S}" == "82.6215(827) q"
    assert f"{r:.1PS}" == "(82.62+/-0.08) q"

    r = Readings(mean=6.547251e-27, std=0.07541268e-27, size=1)
    assert f"{r:.1S}" == "6.55(8) r"
    assert f"{r:PS}" == "(6.547+/-0.075) r"

    r = Readings(mean=9.092349e-25, std=0.0038964e-25, size=1)
    assert f"{r:.3S}" == "909.235(390) r"
    assert f"{r:PS}" == "(909.23+/-0.39) r"

    r = Readings(mean=5.206637324e-24, std=0.415002e-24, size=1)
    assert f"{r:.1S}" == "5.2(4) y"
    assert f"{r:.5PS}" == "(5.20664+/-0.41500) y"

    r = Readings(mean=9.6490243e-22, std=0.058476272e-22, size=1)
    assert f"{r:.4S}" == "964.902(5.848) y"
    assert f"{r:.1PS}" == "(965+/-6) y"

    r = Readings(mean=6.2860846e-20, std=0.02709243e-20, size=1)
    assert f"{r:S}" == "62.86(27) z"
    assert f"{r:PS}" == "(62.86+/-0.27) z"

    r = Readings(mean=5.2032008e-17, std=0.00084681469e-17, size=1)
    assert f"{r:S}" == "52.0320(85) a"
    assert f"{r:PS}" == "(52.0320+/-0.0085) a"

    r = Readings(mean=8.541971e-15, std=1.93486e-15, size=1)
    assert f"{r:.3S}" == "8.54(1.93) f"
    assert f"{r:.1PS}" == "(9+/-2) f"

    r = Readings(mean=8.541971e-14, std=1.93486e-14, size=1)
    assert f"{r:.3S}" == "85.4(19.3) f"
    assert f"{r:.1PS}" == "(90+/-20) f"

    r = Readings(mean=8.125524e-10, std=0.043966e-10, size=1)
    assert f"{r:.1S}" == "813(4) p"
    assert f"{r:.4PS}" == "(812.552+/-4.397) p"

    r = Readings(mean=1.7540272e-9, std=6.5160764e-9, size=1)
    assert f"{r:.3S}" == "1.75(6.52) n"
    assert f"{r:.3FS}" == "1.75(6.52) n"
    assert f"{r:.4PS}" == "(1.754+/-6.516) n"

    r = Readings(mean=4.5569880e-7, std=0.004160764e-7, size=1)
    assert f"{r:.1S}" == "455.7(4) n"
    assert f"{r:PS}" == "(455.70+/-0.42) n"

    r = Readings(mean=9.2863e-4, std=0.70230056610e-4, size=1)
    assert f"{r:S}" == "929(70) u"
    assert f"{r:US}" == "929(70) µ"
    assert f"{r:.6PS}" == "(928.6300+/-70.2301) u"
    assert f"{r:.6PUS}" == "(928.6300±70.2301) µ"
    assert f"{r:.2fUS}" == "929(70) µ"
    assert f"{r:.6PUS}" == "(928.6300±70.2301) µ"

    r = Readings(mean=5.6996491e-2, std=0.5302890e-2, size=1)
    assert f"{r:.4S}" == "56.996(5.303) m"
    assert f"{r:.1PS}" == "(57+/-5) m"

    r = Readings(mean=2.69364683, std=0.00236666, size=1)
    assert f"{r:BUS}" == "2.6936(24)"
    assert f"{r:.3PS}" == "2.69365+/-0.00237"

    r = Readings(mean=4.4733994e2, std=0.1085692e2, size=1)
    assert f"{r:.1S}" == "450(10)"
    assert f"{r:.4PS}" == "447.34+/-10.86"

    r = Readings(mean=8.50987467e4, std=0.6095151e4, size=1)
    assert f"{r:S}" == "85.1(6.1) k"
    assert f"{r:.1PS}" == "(85+/-6) k"

    r = Readings(mean=1.8e6, std=0.0453589e6, size=1)
    assert f"{r:.4S}" == "1.80000(4536) M"
    assert f"{r:.3PUS}" == "(1.8000±0.0454) M"

    r = Readings(mean=1.8667540e8, std=0.00771431e8, size=1)
    assert f"{r:.3S}" == "186.675(771) M"
    assert f"{r:.3PS}" == "(186.675+/-0.771) M"

    r = Readings(mean=7.789499e9, std=0.7852736e9, size=1)
    assert f"{r:.1S}" == "7.8(8) G"
    assert f"{r:PS}" == "(7.79+/-0.79) G"

    r = Readings(mean=2.2038646e13, std=12.743090e13, size=1)
    assert f"{r:.1S}" == "0(100) T"
    assert f"{r:.2fPS}" == "(20+/-130) T"

    r = Readings(mean=6.084734e16, std=1.2485885e16, size=1)
    assert f"{r:.3S}" == "60.8(12.5) P"
    assert f"{r:PS}" == "(61+/-12) P"

    r = Readings(mean=7.66790e18, std=0.05647e18, size=1)
    assert f"{r:.4S}" == "7.66790(5647) E"
    assert f"{r:.6PS}" == "(7.6679000+/-0.0564700) E"

    r = Readings(mean=3.273545e22, std=0.004964854e22, size=1)
    assert f"{r:.1S}" == "32.74(5) Z"
    assert f"{r:.1PS}" == "(32.74+/-0.05) Z"

    r = Readings(mean=4.32184e24, std=0.0005879417e24, size=1)
    assert f"{r:.3S}" == "4.321840(588) Y"
    assert f"{r:.2PS}" == "(4.32184+/-0.00059) Y"

    r = Readings(mean=752.987235265e24, std=0.32198187e24, size=1)
    assert f"{r:.1S}" == "753.0(3) Y"
    assert f"{r:.3PS}" == "(752.987+/-0.322) Y"

    r = Readings(mean=1.638324e27, std=0.773148e27, size=1)
    assert f"{r:S}" == "1.64(77) R"
    assert f"{r:.4PS}" == "(1.6383+/-0.7731) R"

    r = Readings(mean=9.276154e28, std=0.02473e28, size=1)
    assert f"{r:.2S}" == "92.76(25) R"
    assert f"{r:.2PS}" == "(92.76+/-0.25) R"

    r = Readings(mean=0.876236e30, std=0.009236721e30, size=1)
    assert f"{r:.1S}" == "876(9) R"
    assert f"{r:.2PS}" == "(876.2+/-9.2) R"

    r = Readings(mean=4.32687514e31, std=0.9211314e31, size=1, overload=1e99)
    assert f"{r:.3S}" == "43.27(9.21) Q"
    assert f"{r:.1PS}" == "(43+/-9) Q"

    r = Readings(mean=7.582761830927e34, std=0.027125e34, size=1, overload=1e99)
    assert f"{r:.1S}" == "75800(300) Q"
    assert f"{r:.4PS}" == "(75827.6+/-271.2) Q"


def test_iterable() -> None:
    r = Readings(mean=1.2, std=0.32, size=1)
    mean, std_mean = r
    assert mean == 1.2
    assert std_mean == 0.32
    assert "mean={}, std_mean={}".format(*r) == "mean=1.2, std_mean=0.32"

    r = Readings(mean=1.2, std=0.32, size=100)
    mean, std_mean = r
    assert mean == 1.2
    assert std_mean == 0.032
    assert "mean={}, std_mean={}".format(*r) == "mean=1.2, std_mean=0.032"


def test_type_n_raises() -> None:
    # can't specify both grouping and n
    r = Readings()
    with pytest.raises(ValueError, match=r"Cannot use 'n' and grouping"):
        f"{r:_n}"
    with pytest.raises(ValueError, match=r"Cannot use 'n' and grouping"):
        f"{r:,n}"


def test_type_n_swiss() -> None:
    # this locale is interesting because it can have non-ascii characters
    if is_windows:
        loc = "German_Switzerland"
    elif is_darwin:
        loc = "de_CH"
    else:
        loc = "de_CH.utf8"
    _ = locale.setlocale(locale.LC_NUMERIC, loc)

    r = Readings(mean=1.23456789, std=0.987654321, size=1)
    assert f"{r:n}" == "1.23(99)"

    r = Readings(mean=1.2345678987e6, std=0.987654321, size=1)
    assert f"{r:.4n}" == "1’234’567.8987(9877)"  # noqa: RUF001

    r = Readings(mean=12345.6789, std=9876.54321, size=1)
    assert f"{r:.8n}" == "12’345.6789(9’876.5432)"  # noqa: RUF001

    _ = locale.setlocale(locale.LC_NUMERIC, original_loc)


def test_type_n_german() -> None:
    if is_windows:
        loc = "German_Germany"
    elif is_darwin:
        loc = "de_DE"
    else:
        loc = "de_DE.utf8"
    _ = locale.setlocale(locale.LC_NUMERIC, loc)

    r = Readings(mean=1.23456789, std=0.987654321, size=1)
    assert f"{r:n}" == "1,23(99)"

    r = Readings(mean=1.2345678987e6, std=0.987654321, size=1)
    assert f"{r:.4n}" == "1.234.567,8987(9877)"

    r = Readings(mean=12345.6789, std=9876.54321, size=1)
    assert f"{r:.8n}" == "12.345,6789(9.876,5432)"

    r = Readings(mean=2345, std=1234, size=1)
    assert f"{r:#.1n}" == "2,(1,)e+03"

    r = Readings(mean=12345, std=9876, size=1)
    assert f"{r: #n}" == " 1,23(99)e+04"

    _ = locale.setlocale(locale.LC_NUMERIC, original_loc)


def test_type_n_india() -> None:
    # this locale is interesting because it can have a different
    # 'grouping' for the 'thousands_sep' key
    if is_windows:
        loc = "English_India"
    elif is_darwin:
        loc = "hi_IN.ISCII-DEV"
    else:
        loc = "en_IN.utf8"
    _ = locale.setlocale(locale.LC_NUMERIC, loc)

    r = Readings(mean=1.23456789, std=0.987654321, size=1)
    assert f"{r:n}" == "1.23(99)"

    r = Readings(mean=1.2345678987e6, std=0.987654321, size=1)
    assert f"{r:.4n}" == "12,34,567.8987(9877)"

    r = Readings(mean=12345.6789, std=9876.54321, size=1)
    assert f"{r:.8n}" == "12,345.6789(9,876.5432)"

    _ = locale.setlocale(locale.LC_NUMERIC, original_loc)


def test_type_n_kiwi() -> None:
    # make sure the native locale for MSL is good
    if is_windows:
        loc = "English_New Zealand"
    elif is_darwin:
        loc = "en_NZ"
    else:
        loc = "en_NZ.utf8"

    _ = locale.setlocale(locale.LC_NUMERIC, loc)

    r = Readings(mean=1.23456789, std=0.987654321, size=1)
    assert f"{r:n}" == "1.23(99)"

    r = Readings(mean=1.2345678987e6, std=0.987654321, size=1)
    assert f"{r:.4n}" == "1,234,567.8987(9877)"

    r = Readings(mean=12345.6789, std=9876.54321, size=1)
    assert f"{r:.8n}" == "12,345.6789(9,876.5432)"

    r = Readings(mean=12345.6789, std=9876.54321, size=1)
    assert f"{r:+.8n}" == "+12,345.6789(9,876.5432)"

    _ = locale.setlocale(locale.LC_NUMERIC, original_loc)


def test_type_n_afrikaans() -> None:
    # this locale is interesting because it can have non-ascii characters
    if is_windows:
        loc = "English_South Africa"
    elif is_darwin:
        loc = "af_ZA"
    else:
        loc = "en_ZA.utf8"
    _ = locale.setlocale(locale.LC_NUMERIC, loc)

    r = Readings(mean=1.23456789, std=0.987654321, size=1)
    if is_linux:
        assert f"{r:n}" == "1.23(99)"
    else:
        assert f"{r:n}" == "1,23(99)"

    r = Readings(mean=1.2345678987e6, std=0.987654321, size=1)
    if is_windows or is_darwin:
        assert f"{r:.4n}" == "1\xa0234\xa0567,8987(9877)"
    else:
        assert f"{r:.4n}" == "1,234,567.8987(9877)"

    r = Readings(mean=12345.6789, std=9876.54321, size=1)
    if is_windows or is_darwin:
        assert f"{r:.8n}" == "12\xa0345,6789(9\xa0876,5432)"
    else:
        assert f"{r:.8n}" == "12,345.6789(9,876.5432)"

    _ = locale.setlocale(locale.LC_NUMERIC, original_loc)


def test_len() -> None:
    r = Readings(range(8))
    assert len(r) == 8
    assert r.size == 8
    assert r.data.size == 8


def test_subscriptable_sliceable() -> None:
    r = Readings([3, 6, 1, 8])
    assert r[0] == 3
    assert r[1] == 6
    assert r[2] == 1
    assert r[3] == 8
    assert np.array_equal(r[1:3], [6, 1])
    assert np.array_equal(r[::2], [3, 1])
