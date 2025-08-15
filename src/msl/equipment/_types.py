"""Custom type annotations."""

from __future__ import annotations

from os import PathLike
from typing import Protocol, TypeAlias, TypeVar, Union  # pyright: ignore[reportDeprecated]

_T_co = TypeVar("_T_co", covariant=True)


class SupportsRead(Protocol[_T_co]):
    """A [file-like object][]{:target="_blank"} that has a `read` method."""

    def read(self, size: int | None = -1, /) -> _T_co:
        """Read from the stream."""
        ...


XMLSource: TypeAlias = Union[int, str, bytes, PathLike[str], PathLike[bytes], SupportsRead[bytes] | SupportsRead[str]]  # pyright: ignore[reportDeprecated]
"""A [path-like object][]{:target="_blank"} or a [file-like object][]{:target="_blank"} for parsing XML content."""
