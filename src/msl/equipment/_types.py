"""Custom type annotations."""

from __future__ import annotations

import os
from collections.abc import Sequence
from enum import Enum
from typing import Literal, Protocol, TypeAlias, TypeVar, Union  # pyright: ignore[reportDeprecated]

import numpy as np

_T_co = TypeVar("_T_co", covariant=True)


class SupportsRead(Protocol[_T_co]):
    """A [file-like object][] that has a `read` method."""

    def read(self, size: int | None = -1, /) -> _T_co:
        """Read from the stream."""
        ...


PathLike = Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]  # pyright: ignore[reportDeprecated]
"""A [path-like object][]."""

XMLSource: TypeAlias = Union[int, PathLike, SupportsRead[bytes] | SupportsRead[str]]  # pyright: ignore[reportDeprecated]
"""A [path-like object][] or a [file-like object][] for parsing XML content."""

MessageFormat = Literal["ascii", "hp", "ieee"]
"""Format to use to read/write bytes from/to equipment."""

MessageDataType = type[int] | type[float] | str | type[np.number]
"""Data type to use to read/write bytes from/to equipment."""

NumpyArray1D = np.ndarray[tuple[int], np.dtype[np.number]]
"""A 1-dimensional [numpy.array][] of numbers."""

Sequence1D = Sequence[float] | NumpyArray1D
"""A 1-dimensional sequence of numbers."""

EnumType = TypeVar("EnumType", bound=Enum)
"""An [Enum][enum.Enum] subclass."""
