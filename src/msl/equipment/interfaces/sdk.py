"""Base class for equipment that use the SDK provided by the manufacturer for the connection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from msl.equipment.schema import Interface
from msl.equipment.utils import logger
from msl.loadlib import LoadLibrary

if TYPE_CHECKING:
    from typing import Any

    from msl.equipment._types import PathLike
    from msl.equipment.schema import Equipment
    from msl.loadlib.activex import Application
    from msl.loadlib.types import LibType

REGEX = re.compile(r"SDK::(?P<path>.+)", flags=re.IGNORECASE)


class SDK(Interface, regex=REGEX):
    """Base class for equipment that use the manufacturer's Software Development Kit (SDK)."""

    def __init__(
        self, equipment: Equipment, *, libtype: LibType | None = None, path: PathLike | None = None, **kwargs: Any  # noqa: ANN401
    ) -> None:
        """Base class for equipment that use the manufacturer's Software Development Kit (SDK).

        You can use the [configuration file][config-xml-example] to add the directory that the SDK
        is located at to the `PATH` environment variable.

        Args:
            equipment: An [Equipment][] instance.
            libtype: The library type. See [LoadLibrary][msl.loadlib.load_library.LoadLibrary] for more details.
            path: The path to the SDK. Specifying this value will take precedence over the
                [address][msl.equipment.schema.Connection.address] value.
            kwargs: All additional keyword arguments are passed to [LoadLibrary][msl.loadlib.load_library.LoadLibrary].
        """
        super().__init__(equipment)

        if path is None:
            assert equipment.connection is not None  # noqa: S101
            info = parse_sdk_address(equipment.connection.address)
            if info is None:
                msg = f"Invalid SDK interface address {equipment.connection.address!r}"
                raise ValueError(msg)
            path = info.path

        self._load_library: LoadLibrary = LoadLibrary(path, libtype=libtype, **kwargs)
        self._sdk: Any = self._load_library.lib

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Cleanup references to the SDK library."""
        if hasattr(self, "_sdk") and self._sdk is not None:
            self._load_library.cleanup()
            self._sdk = None
            super().disconnect()

    def _log_errcheck(self, result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
        """Convenience method for logging an [errcheck][ctypes._CFuncPtr.errcheck] from [ctypes][]."""
        logger.debug("%s.%s%s -> %s", self.__class__.__name__, func.__name__, arguments, result)
        return result

    @property
    def application(self) -> Application | None:
        """[Application][msl.loadlib.activex.Application] | `None` &mdash; Reference to the ActiveX application window.

        If the loaded library is not an ActiveX library, returns `None`.
        """
        return self._load_library.application

    @property
    def sdk(self) -> Any:  # noqa: ANN401
        """[lib][msl.loadlib.load_library.LoadLibrary.lib] &mdash; The reference to the SDK object."""
        return self._sdk

    @property
    def path(self) -> str:
        """[str][] &mdash; The path to the library file."""
        return self._load_library.path


@dataclass
class ParsedSDKAddress:
    """The parsed result of a VISA-style address for the SDK interface.

    Args:
        path: The path to the SDK library.
    """

    path: str


def parse_sdk_address(address: str) -> ParsedSDKAddress | None:
    """Get the path to the SDK library from an address.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed SDK address or `None` if `address` is not valid for the SDK interface.
    """
    match = REGEX.match(address)
    return ParsedSDKAddress(path=match["path"]) if match else None
