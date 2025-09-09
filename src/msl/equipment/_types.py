"""Custom type annotations."""

from __future__ import annotations

import os
from typing import Protocol, TypeAlias, TypeVar, Union  # pyright: ignore[reportDeprecated]

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
