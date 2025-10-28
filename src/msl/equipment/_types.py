"""Custom type annotations."""

from __future__ import annotations

import os
from collections.abc import Sequence
from ctypes import _Pointer, c_int32  # pyright: ignore[reportPrivateUsage]
from enum import Enum
from typing import Callable, Literal, Protocol, TypeVar, Union  # pyright: ignore[reportDeprecated]

import numpy as np

_T_co = TypeVar("_T_co", covariant=True)


class SupportsRead(Protocol[_T_co]):
    """A [file-like object][] that has a `read` method."""

    def read(self, size: int | None = -1, /) -> _T_co:
        """Read from the stream."""
        ...


PathLike = Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]  # pyright: ignore[reportDeprecated]
"""A [path-like object][]."""

XMLSource = Union[int, PathLike, SupportsRead[bytes] | SupportsRead[str]]  # pyright: ignore[reportDeprecated]
"""A [path-like object][] or a [file-like object][] for parsing XML content."""

MessageFormat = Literal["ascii", "hp", "ieee"] | None
"""Format to use to read(write) bytes from(to) equipment.

Possible values are:

* `None` &mdash; do not use a header.

    !!! example "Format"
        `<byte><byte><byte>...`

* `ascii` &mdash; comma-separated ASCII characters, see the
        `<PROGRAM DATA SEPARATOR>` standard that is defined in Section 7.4.2.2 of
        [IEEE 488.2-1992](https://standards.ieee.org/ieee/488.2/718/){:target="_blank"}.

    !!! example "Format"
        `<string>,<string>,<string>,...`

* `ieee` &mdash; arbitrary block data for `SCPI` messages, see the
        `<DEFINITE LENGTH ARBITRARY BLOCK RESPONSE DATA>` standard that is defined in
        Section 8.7.9 of [IEEE 488.2-1992](https://standards.ieee.org/ieee/488.2/718/){:target="_blank"}.

    !!! example "Format"
        `#<length of num bytes value><num bytes><byte><byte><byte>...`

* `hp` &mdash; the HP-IB data transfer standard, i.e., the `FORM#` command
        option. See the programming guide for an
        [HP 8530A](https://www.keysight.com/us/en/product/8530A/microwave-receiver.html#resources){:target="_blank"}
        for more details.

    !!! example "Format"
        `#A<num bytes as uint16><byte><byte><byte>...`
"""

MessageDataType = type[int] | type[float] | type[np.number] | str
"""Data type to use to read(write) bytes from(to) equipment.

The data type to use to convert each element in a [Sequence1D][msl.equipment._types.Sequence1D]
to. If the corresponding [MessageFormat][msl.equipment._types.MessageFormat] is `ascii` then the
data type value must be of type [str][] and it is used as the `format_spec` argument in [format][]
to first convert each element in [Sequence1D][msl.equipment._types.Sequence1D] to a string, and
then it is encoded (e.g., `'.2e'` converts each element to scientific notation with two digits
after the decimal point). If the data type includes a byte-order character, it is ignored. For
all other values of [MessageFormat][msl.equipment._types.MessageFormat], the data type can be any
object that numpy [dtype][numpy.dtype] supports (e.g., `'H'`, `'uint16'` and [ushort][numpy.ushort]
are equivalent values to convert each element to an *unsigned short*). If a byte-order character is
specified then it is used, otherwise the native byte order of the CPU architecture is used. See
[struct-format-strings][] for more details.
"""

NumpyArray1D = np.ndarray[tuple[int], np.dtype[np.number]]
"""A 1-dimensional numpy [ndarray][numpy.ndarray] of numbers."""

Sequence1D = Sequence[float] | NumpyArray1D
"""A 1-dimensional sequence of numbers."""

EnumType = TypeVar("EnumType", bound=Enum)
"""An [Enum][enum.Enum] subclass."""

AvaSpecCallback = Callable[[_Pointer[c_int32], _Pointer[c_int32]], None]
"""Callback handler for the [AvaSpec][msl.equipment_resources.avantes.avaspec.AvaSpec] SDK."""

NKTPortStatusCallback = Callable[[str, int, int, int, int], None]
"""Callback handler for the [NKT][msl.equipment_resources.nkt.nktpdll.NKT] SDK when the status of a port changes."""

NKTDeviceStatusCallback = Callable[[str, int, int, int, int], None]
"""Callback handler for the [NKT][msl.equipment_resources.nkt.nktpdll.NKT] SDK when the status of a device changes."""

NKTRegisterStatusCallback = Callable[[str, int, int, int, int, int, int], None]
"""Callback handler for the [NKT][msl.equipment_resources.nkt.nktpdll.NKT] SDK when the status of a register changes."""
