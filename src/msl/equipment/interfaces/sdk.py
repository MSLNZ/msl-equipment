"""Base class for equipment that use the SDK provided by the manufacturer for the connection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from msl.equipment.constants import REGEX_SDK
from msl.equipment.utils import logger
from msl.loadlib import LoadLibrary

from . import Interface

if TYPE_CHECKING:
    from ctypes import _CData, _CDataType, _NamedFuncPointer  # pyright: ignore[reportPrivateUsage]
    from typing import Any

    from msl.equipment._types import PathLike
    from msl.equipment.schema import Equipment
    from msl.loadlib._types import LibType


class SDK(Interface):
    """Base class for equipment that use the SDK provided by the manufacturer for the connection."""

    def __init__(self, equipment: Equipment, libtype: LibType | None = None, path: PathLike | None = None) -> None:
        """Base class for equipment that use the SDK provided by the manufacturer for the connection.

        Args:
            equipment: The [Equipment][] instance.
            libtype: The library type. See [LoadLibrary][msl.loadlib.load_library.LoadLibrary] for more details.
            path: The path to the SDK, only required if the [address][msl.equipment.connections.Connection.address]
                does not contain this information.
        """
        super().__init__(equipment)

        if path is None:
            assert equipment.connection is not None  # noqa: S101
            info = parse_sdk_address(equipment.connection.address)
            if info is None:
                msg = f"Invalid SDK interface address {equipment.connection.address!r}"
                raise ValueError(msg)
            path = info.path

        self._lib: LoadLibrary = LoadLibrary(path, libtype)
        self._sdk: Any = self._lib.lib

    @property
    def assembly(self) -> Any:  # noqa: ANN401
        """[assembly][msl.loadlib.load_library.LoadLibrary.assembly &mdash; The reference to the .NET assembly."""
        return self._lib.assembly

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Cleanup references to the SDK library."""
        if hasattr(self, "_lib"):
            self._lib.cleanup()

    @property
    def gateway(self) -> Any:  # noqa: ANN401
        """[gateway][msl.loadlib.load_library.LoadLibrary.gateway] &mdash; The reference to the JAVA gateway."""
        return self._lib.gateway

    def log_errcheck(
        self, result: _CData | _CDataType | None, func: _NamedFuncPointer, arguments: tuple[_CData | _CDataType, ...]
    ) -> _CData | _CDataType | None:
        """Convenience method for logging an [errcheck][ctypes._CFuncPtr.errcheck]."""
        logger.debug("%s.%s%s -> %s", self.__class__.__name__, func.__name__, arguments, result)
        return result

    @property
    def path(self) -> str:
        """The path to the SDK file."""
        return self._lib.path

    @property
    def sdk(self) -> Any:  # noqa: ANN401
        """[lib][msl.loadlib.load_library.LoadLibrary.lib] &mdash; The reference to the SDK object."""
        return self._sdk


def parse_sdk_address(address: str) -> ParsedSDKAddress | None:
    """Get the path to the SDK library from an address.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed SDK address or `None` if `address` is not valid for the SDK interface.
    """
    match = REGEX_SDK.match(address)
    return ParsedSDKAddress(path=match["path"]) if match else None


@dataclass
class ParsedSDKAddress:
    """The parsed result of a VISA-style address for the SDK interface.

    Args:
        path: The path to the SDK library.
    """

    path: str
