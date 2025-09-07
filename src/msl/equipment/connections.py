"""Classes that contain details on how to connect to equipment."""

from __future__ import annotations

from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, parse

from .constants import Backend
from .utils import to_primitive

if TYPE_CHECKING:
    from typing import Any, Literal

    from ._types import PathLike


class Connection:
    """Information about the connection to equipment."""

    __slots__: tuple[str, ...] = (
        "address",
        "backend",
        "eid",
        "manufacturer",
        "model",
        "properties",
        "serial",
    )

    def __init__(  # noqa: PLR0913
        self,
        address: str,
        *,
        backend: Literal["MSL", "PyVISA", "NIDAQ"] | Backend = Backend.MSL,
        eid: str = "",
        manufacturer: str = "",
        model: str = "",
        serial: str = "",
        **properties: Any,  # noqa: ANN401
    ) -> None:
        """Information about the connection to equipment.

        Args:
            address: The VISA-style address to use for the connection (see [here][address-syntax] for examples).
            backend: The backend package to use to communicate with the equipment.
            eid: The [Equipment.id][msl.equipment.schema.Equipment.id] to associate with the connection.
            manufacturer: The name of the manufacturer of the equipment.
            model: The model number of the equipment.
            serial: The serial number (or unique identifier) of the equipment.
            properties: Additional key-value pairs that are required to communicate with the equipment.
        """
        self.address: str = address
        self.backend: Backend = Backend(backend)
        self.eid: str = eid
        self.manufacturer: str = manufacturer
        self.model: str = model
        self.properties: dict[str, Any] = properties
        self.serial: str = serial

    def __repr__(self)-> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return f"{self.__class__.__name__}(eid={self.eid!r} address={self.address!r})"


class Connections:
    """Singleton class containing an eid:Connection mapping from <connections> defined in a configuration file."""

    def __init__(self) -> None:
        """Singleton class containing an eid:Connection mapping from <connections> defined in a configuration file."""
        self._connections: dict[str, Connection | Element[str]] = {}

    def __contains__(self, eid: str) -> bool:
        """Check whether an eid is in the mapping."""
        return eid in self._connections

    def __getitem__(self, eid: str) -> Connection:
        """Returns a Connection instance."""
        item = self._connections.get(eid)
        if isinstance(item, Connection):
            return item

        if item is None:
            msg = (
                f"A <connection> element with eid={eid!r} cannot be found in the "
                f"connections that are specified in the configuration file"
            )
            raise KeyError(msg)

        connection = self._from_xml(item)
        self._connections[eid] = connection
        return connection

    def __len__(self) -> int:
        """Returns the size of the mapping."""
        return len(self._connections)

    def add(self, *sources: PathLike | Element[str]) -> None:
        """Add the sources from the <connections> element in a configuration file."""
        for source in sources:
            root = source if isinstance(source, Element) else parse(source).getroot()  # noqa: S314

            # schema requires that the eid is the first child element
            self._connections.update({e[0].text: e for e in root if e[0].text})

    def clear(self) -> None:
        """Remove all connections from the mapping."""
        self._connections.clear()

    def _from_xml(self, element: Element[str]) -> Connection:
        """Convert a <connection> from a connections XML file."""
        # schema requires that eid and address are the first two elements
        eid = element[0].text or ""
        address = element[1].text or ""
        # the other elements are optional (minOccurs="0")
        backend, manufacturer, model, serial = Backend.MSL, "", "", ""
        properties: dict[str, bool | float | str | None] = {}
        for e in element[2:]:
            if e.tag == "backend":
                backend = Backend[e.text or "MSL"]
            elif e.tag == "manufacturer":
                manufacturer = e.text or ""
            elif e.tag == "model":
                model = e.text or ""
            elif e.tag == "serial":
                serial = e.text or ""
            else:
                for child in e:
                    properties[child.tag] = None if child.text is None else to_primitive(child.text)

        return Connection(
            eid=eid,
            address=address,
            backend=backend,
            manufacturer=manufacturer,
            model=model,
            serial=serial,
            **properties,
        )


connections = Connections()
