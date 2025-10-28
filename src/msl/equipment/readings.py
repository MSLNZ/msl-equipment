"""A formatting-friendly convenience class for measurement sample data."""

# cSpell: ignore bcde Gnosx qryzafpnum MGTPEZYRQ
from __future__ import annotations

import locale
import math
import re
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import sys
    from collections.abc import Iterator, Sequence
    from typing import Any, SupportsIndex

    from numpy.typing import NDArray

    if sys.version_info >= (3, 10):
        from types import EllipsisType
    else:
        # Rely on builtins.ellipsis
        EllipsisType = ellipsis  # pyright: ignore[reportUnreachable] # noqa: F821

    ToIndex = SupportsIndex | slice | EllipsisType | None

# The regular expression to parse a format specification (format_spec)
# with additional (and optional) characters at the end for custom fields.
#
# format_spec ::= [[fill]align][sign][z][#][0][width][grouping][.precision][type][mode][style][si]
# https://docs.python.org/3/library/string.html#format-specification-mini-language
_format_spec_regex = re.compile(
    # the builtin grammar fields
    r"((?P<fill>.)(?=[<>=^]))?"  # pyright: ignore[reportImplicitStringConcatenation]
    r"(?P<align>[<>=^])?"
    r"(?P<sign>[ +-])?"
    r"(?P<z>[z])?"
    r"(?P<hash>#)?"
    r"(?P<zero>0)?"
    r"(?P<width>\d+)?"
    r"(?P<grouping>[_,])?"
    r"((\.)(?P<precision>\d+))?"
    r"(?P<type>[bcdeEfFgGnosxX%])?"
    # Bracket or Plus-minus
    # NOTE: these characters cannot be in <type>
    r"(?P<mode>[BP])?"
    # Latex or Unicode
    # NOTE: these characters cannot be in <type> nor <mode>
    r"(?P<style>[LU])?"
    # SI prefix
    # NOTE: this character cannot be in <type>, <mode> nor <style>
    r"(?P<si>S)?"
    # the regex must match until the end of the string
    r"$"
)

_exponent_regex = re.compile(r"[eE][+-]\d+")

_si_map = {i * 3: c for i, c in enumerate("qryzafpnum kMGTPEZYRQ", start=-10)}

_unicode_superscripts = {
    ord("+"): "\u207a",
    ord("-"): "\u207b",
    ord("0"): "\u2070",
    ord("1"): "\u00b9",
    ord("2"): "\u00b2",
    ord("3"): "\u00b3",
    ord("4"): "\u2074",
    ord("5"): "\u2075",
    ord("6"): "\u2076",
    ord("7"): "\u2077",
    ord("8"): "\u2078",
    ord("9"): "\u2079",
}


def order_of_magnitude(value: float) -> int:
    """Returns the order of magnitude of `value`."""
    if value == 0:
        return 0
    return math.floor(math.log10(math.fabs(value)))


def parse(format_spec: str) -> dict[str, str]:
    """Parse a format specification into its grammar fields."""
    match = _format_spec_regex.match(format_spec)
    if not match:
        msg = f"Invalid format specifier {format_spec!r}"
        raise ValueError(msg)
    return match.groupdict()


def si_prefix_factor(exponent: int) -> tuple[str, float]:
    """Returns the SI prefix and scaling factor.

    Args:
        exponent: The exponent, e.g., 10 ** exponent
    """
    mod = exponent % 3
    prefix = _si_map.get(exponent - mod)
    factor = 10.0**mod
    if exponent < 0 and prefix is None:
        prefix = "q"
        factor = 10.0 ** (exponent + 30)
    elif 0 <= exponent < 3:  # noqa: PLR2004
        prefix = ""
    elif prefix is None:
        prefix = "Q"
        factor = 10.0 ** (exponent - 30)
    return prefix, factor


@dataclass
class Rounded:
    """Represents a rounded value."""

    value: float
    precision: int
    type: str
    exponent: int
    suffix: str


class Format:
    """Format specification."""

    def __init__(self, **kwargs: str) -> None:
        """Format specification."""
        # builtin grammar fields
        self.fill: str = kwargs["fill"] or ""
        self.align: str = kwargs["align"] or ""
        self.sign: str = kwargs["sign"] or ""
        self.z: str = kwargs["z"] or ""
        self.hash: str = kwargs["hash"] or ""
        self.zero: str = kwargs["zero"] or ""
        self.width: str = kwargs["width"] or ""
        self.grouping: str = kwargs["grouping"] or ""
        self.precision: int = int(kwargs["precision"] or 2)
        self.type: str = kwargs["type"] or "f"

        if self.type == "n" and self.grouping:
            msg = f"Cannot use 'n' and grouping={self.grouping!r}"
            raise ValueError(msg)

        # custom grammar fields
        self.mode: str = kwargs["mode"] or "B"
        self.style: str = kwargs["style"] or ""
        self.si: str = kwargs["si"] or ""

        if self.si:
            self.type = "e"

        # these attributes are used when rounding
        self.digits: int = self.precision
        self.u_exponent: int = 0

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        # Use .digits instead of .precision in the result
        spec = (
            f"{self.fill}{self.align}{self.sign}{self.z}{self.hash}{self.zero}"
            f"{self.width}{self.grouping}.{self.digits}{self.type}"
            f"{self.mode}{self.style}{self.si}"
        )
        return f"Format(format_spec={spec!r})"

    def result(self, text: str) -> str:
        """Format `text` using the fill, align, zero and width fields."""
        fmt = f"{self.fill}{self.align}{self.zero}{self.width}"
        return f"{text:{fmt}s}"

    def uncertainty(
        self,
        uncertainty: float,
        *,
        hash: str | None = None,  # noqa: A002
        type: str | None = "f",  # noqa: A002
        precision: int | None = None,
    ) -> str:
        """Format `uncertainty` using the hash, grouping, precision and type fields.

        Args:
            uncertainty: The uncertainty to format.
            hash: Can be either # or '' (an empty string)
            type: Can be one of: e, E, f, F, g, G, n
            precision: Indicates how many digits should be displayed after
                the decimal point for presentation types f and F, or before
                and after the decimal point for presentation types g or G.

        Returns:
            The `uncertainty` formatted.
        """
        return self.value(uncertainty, hash=hash, type=type, sign="", precision=precision)

    def update(self, std: float) -> None:
        """Update the `precision` and `u_exponent` attributes.

        Args:
            std: The standard uncertainty of the readings.
        """
        if std == 0 or not math.isfinite(std):
            return

        exponent = order_of_magnitude(std)
        if exponent - self.precision + 1 >= 0:
            self.precision = 0
        else:
            self.precision = int(self.precision - exponent + 1)

        u_exponent = exponent - self.digits + 1

        # edge case, for example, if 0.099 then round to 0.1
        rounded = round(std, -u_exponent)
        e_rounded = order_of_magnitude(rounded)
        if e_rounded > exponent:
            u_exponent += 1

        self.u_exponent = u_exponent

    def value(
        self,
        value: float,
        *,
        hash: str | None = None,  # noqa: A002
        type: str | None = None,  # noqa: A002
        sign: str | None = None,
        precision: int | None = None,
    ) -> str:
        """Format `value` using the sign, hash, grouping, precision and type fields.

        Args:
            value: The value to format.
            hash: Can be either # or '' (an empty string)
            type: Can be one of: e, E, f, F, g, G, n
            sign: Can be one of: +, -, ' ' (a space)
            precision: Indicates how many digits should be displayed after
                the decimal point for presentation types f and F, or before
                and after the decimal point for presentation types g or G.

        Returns:
            The `value` formatted.
        """
        if sign is None:
            sign = self.sign

        if precision is None:
            precision = self.precision

        if type is None:
            type = self.type  # noqa: A001

        if hash is None:
            hash = self.hash  # noqa: A001

        if type == "n":
            fmt = f"%{sign}{hash}.{precision}f"
            return locale.format_string(fmt, value, grouping=True)

        return f"{value:{sign}{self.z}{hash}{self.grouping}.{precision}{type}}"


class Readings:
    """A formatting-friendly convenience class for measurement data."""

    def __init__(
        self,
        data: str | Sequence[str | float] | NDArray[np.number] | None = None,
        *,
        mean: float | None = None,
        std: float | None = None,
        size: int | None = None,
        overload: float | None = 1e30,
        delimiter: str | None = ",",
    ) -> None:
        """A formatting-friendly convenience class for measurement data.

        Args:
            data: The measurement data.
            mean: If specified, then the mean is not calculated from the `data`.
            std: If specified, then the standard deviation is not calculated from the `data`.
            size: If specified, then the number of items is not determined from the `data`.
            overload: For some devices, like a digital multimeter, if the input signal is
                greater than the range can measure, the device returns a large value
                (e.g., 9.9E+37) to indicate a measurement overload. If the absolute value of
                the mean is greater than `overload` then the mean and standard deviation become
                `NaN`. Setting `overload` to `None` disables this check.
            delimiter: The character used to separate values (only used if `data` is of type [str][]).
                The value `None` corresponds to whitespace.
        """
        if data is not None and any(a is not None for a in (mean, std, size)):
            msg = "Cannot specify data and the mean, std or size"
            raise ValueError(msg)

        self._data: NDArray[np.float64]
        if isinstance(data, str):
            stripped = data.strip()
            if stripped:
                self._data = np.loadtxt(StringIO(stripped), dtype=float, delimiter=delimiter)
            else:
                self._data = np.empty(0)
        elif isinstance(data, np.ndarray):
            self._data = data.astype(np.float64)
        elif data is None:
            self._data = np.empty(0)
        else:
            self._data = np.asarray(data, dtype=float)

        self._size: int = self._data.size if size is None else size
        self._overload: float | None = None if overload is None else float(overload)
        self._std: float | None = std

        self._mean: float | None
        if mean is not None:
            self._mean = self._check_overload(mean)
        else:
            self._mean = None

    def __iter__(self) -> Iterator[float]:
        """Iterate the mean and standard deviation of the mean."""
        return iter((self.mean, self.std_mean))

    def __format__(self, format_spec: str) -> str:  # pyright: ignore[reportImplicitOverride]
        """Format the readings."""
        fmt = Format(**parse(format_spec))
        fmt.update(self.std_mean)
        return fmt.result(_stylize(self._to_string(fmt), fmt))

    def __getattr__(self, item: str) -> Any:  # noqa: ANN401
        """Pass all other attributes to the ndarray."""
        return getattr(self._data, item)

    def __getitem__(self, item: ToIndex | tuple[ToIndex, ...]) -> NDArray[np.float64]:
        """Returns an item from the data."""
        return self._data[item]

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return f"{self.__class__.__name__}(mean={self.mean}, std_mean={self.std_mean}, size={self._size})"

    def __len__(self) -> int:
        """Returns the size."""
        return self._size

    def _check_overload(self, mean: float) -> float:
        if self._overload is None:
            return mean

        if math.isfinite(mean) and abs(mean) > self._overload:
            self._std = math.nan
            return math.nan

        return mean

    def _to_string(self, fmt: Format) -> str:  # noqa: C901, PLR0912
        """Convert to a formatted string."""
        x, u = self.mean, self.std_mean
        if u == 0:
            if fmt.si:
                fmt.update(x)
                r = _round(x, fmt)
                x_str = fmt.value(r.value, precision=r.precision, type=r.type)
                v_str = f"{x_str}{r.suffix}"
            else:
                v_str = fmt.value(x)
            return fmt.result(v_str)

        u_finite = math.isfinite(u)
        x_finite = math.isfinite(x)
        if not (u_finite and x_finite):
            si_prefix = ""
            if fmt.si and x_finite:
                fmt.update(x)
                r = _round(x, fmt)
                si_prefix = r.suffix
                x_str = fmt.value(r.value, precision=r.precision, type=r.type)
            else:
                x_str = fmt.value(x)

            u_str = fmt.uncertainty(u, type=None)

            result = f"{x_str}({u_str}){si_prefix}" if fmt.mode == "B" else f"{x_str}+/-{u_str}{si_prefix}"

            # move an exponential term (if it exists) to the end of the string
            exp = _exponent_regex.search(result)
            if exp:
                start, end = exp.span()
                s1, s2, s3 = result[:start], result[end:], exp.group()
                result = f"{s1}{s2}{s3}" if fmt.mode == "B" else f"({s1}{s2}){s3}"

            return result

        x_rounded, u_rounded = _round_readings(x, u, fmt)

        u_r = u_rounded.value
        precision = x_rounded.precision

        x_str = fmt.value(x_rounded.value, precision=precision, type=x_rounded.type)

        if fmt.mode == "P":  # Plus-minus mode
            u_str = fmt.uncertainty(u_r, precision=precision)
            x_u_str = f"{x_str}+/-{u_str}"
            if x_rounded.suffix:
                return f"({x_u_str}){x_rounded.suffix}"
            return x_u_str

        # Bracket mode
        oom = order_of_magnitude(u_r)
        if precision > 0 and oom >= 0:
            # the uncertainty straddles the decimal point so
            # keep the decimal point in the result
            u_str = fmt.uncertainty(u_r, precision=precision, type=u_rounded.type)
        else:
            hash_, type_ = None, u_rounded.type
            if oom < 0:
                if fmt.hash:
                    hash_ = ""
                else:
                    type_ = "f"
            u_str = fmt.uncertainty(round(u_r * 10.0**precision), precision=0, type=type_, hash=hash_)

        return f"{x_str}({u_str}){x_rounded.suffix}"

    @property
    def mean(self) -> float:
        """Returns the mean."""
        if self._mean is not None:
            return self._mean

        mean = float(np.mean(self._data)) if self._size > 0 else np.nan
        self._mean = self._check_overload(mean)
        return self._mean

    @property
    def overload(self) -> float | None:
        """Returns the overload value."""
        return self._overload

    @property
    def data(self) -> NDArray[np.float64]:
        """Returns the data."""
        return self._data

    @property
    def std(self) -> float:
        """Returns the _sample_ standard deviation (uses $N-1$ in the denominator)."""
        if self._std is not None:
            return self._std

        self._std = float(np.std(self._data, ddof=1)) if self._size > 1 else math.nan
        return self._std

    @property
    def std_mean(self) -> float:
        """Returns the standard deviation of the mean."""
        try:
            return self.std / math.sqrt(self._size)
        except ZeroDivisionError:
            return math.nan


def _round(value: float, fmt: Format, exponent: int | None = None) -> Rounded:
    """Round `value` to the appropriate number of significant digits."""
    if exponent is None:
        exponent = order_of_magnitude(value)

    _type = fmt.type
    f_or_g_as_f = (_type in "fF") or ((_type in "gGn") and (-4 <= exponent < exponent - fmt.u_exponent))  # noqa: PLR2004

    if f_or_g_as_f:
        factor = 1.0
        digits = -fmt.u_exponent
        precision = max(digits, 0)
        suffix = ""
    elif _type == "%":
        factor = 0.01
        digits = -fmt.u_exponent - 2
        precision = max(digits, 0)
        suffix = "%"
    else:
        factor = 10.0**exponent
        digits = max(exponent - fmt.u_exponent, 0)
        precision = digits
        suffix = f"{factor:.0{_type}}"[1:]

    if _type in "eg%":
        _type = "f"
    elif _type in "EG":
        _type = "F"

    if fmt.si:
        prefix, si_factor = si_prefix_factor(exponent)
        n = order_of_magnitude(si_factor)
        precision = max(0, precision - n)
        val = round(value * si_factor / factor, digits - n)
        suffix = f" {prefix}" if prefix else ""
    else:
        val = round(value / factor, digits)

    return Rounded(value=val, precision=precision, type=_type, exponent=exponent, suffix=suffix)


def _round_readings(x: float, u: float, fmt: Format) -> tuple[Rounded, Rounded]:
    """Round the readings.

    This function ensures that both x and u get scaled by the same factor.
    """
    maximum = round(max(math.fabs(x), u), -fmt.u_exponent)
    rounded = _round(maximum, fmt)
    x_rounded = _round(x, fmt, exponent=rounded.exponent)
    u_rounded = _round(u, fmt, exponent=rounded.exponent)
    return x_rounded, u_rounded


def _stylize(text: str, fmt: Format) -> str:
    """Apply the formatting style to `text`."""
    if not fmt.style or not text:
        return text

    exponent = ""
    exp_number = None
    exp_match = _exponent_regex.search(text)
    if exp_match:
        # don't care whether it starts with e or E and
        # don't want to include the + symbol
        group = exp_match.group()
        exp_number = int(group[1:])

    if fmt.style == "U":
        if exp_match and exp_number != 0:
            e = f"{exp_number}"
            translated = e.translate(_unicode_superscripts)
            exponent = f"\u00d710{translated}"

        replacements = [("+/-", "\u00b1"), ("u", "\u00b5")]

    else:  # fmt.style == "L"
        if exp_match and exp_number != 0:
            exponent = rf"\times10^{{{exp_number}}}"

        replacements = [
            ("(", r"\left("),
            (")", r"\right)"),
            ("nan", r"\mathrm{NaN}"),
            ("NAN", r"\mathrm{NaN}"),
            ("inf", r"\infty"),  # must come before 'INF'
            ("INF", r"\infty"),
            ("%", r"\%"),
        ]

    if exp_match:
        start, end = exp_match.span()
        s1, s2, s3 = text[:start], exponent, text[end:]
        text = f"{s1}{s2}{s3}"

    for old, new in replacements:
        text = text.replace(old, new)

    return text
