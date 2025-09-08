"""A [configuration file][configuration-files] is useful when you want to perform a measurement."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, overload
from xml.etree.ElementTree import parse

from .connections import connections
from .schema import Register
from .utils import logger, to_primitive

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Literal
    from xml.etree.ElementTree import Element

    from ._types import XMLSource
    from .schema import Equipment


def _sources(text: str | None, tag: Literal["register", "connections"]) -> list[Path | Element[str]]:
    """Get the XML source files from `<register>` or `<connections>` elements in a config file.

    Args:
        text: The text value of a `<register>` or `<connections>` element.
        tag: The name of the root tag to check for when searching a directory for XML files.
    """
    if not text or not text.strip():
        return []

    path = Path(text).expanduser()
    sources: list[Path | Element[str]] = []
    if path.is_dir():
        for file in path.rglob("*.xml"):
            # Ignore XML files in hidden directories (e.g., XML files in PyCharm's .idea directory)
            if any(part.startswith(".") for part in file.parts):
                continue
            root = parse(file).getroot()  # noqa: S314
            if root.tag.endswith(tag):
                sources.append(root)
    else:
        sources.append(path)

    return sources



class Config:
    """Load a configuration file."""

    def __init__(self, source: XMLSource) -> None:  # noqa: C901
        """Load a configuration file.

        Args:
            source: A [path-like][path-like object]{:target="_blank"} or [file-like][file-like object]{:target="_blank"}
                object containing the configuration data.
        """
        logger.debug("load configuration %s", source)
        self._source: XMLSource = source
        self._root: Element[str] = parse(source).getroot()  # noqa: S314
        self._registers: dict[str, Register] | None = None
        self._config_equipment: ConfigEquipment = ConfigEquipment(self)

        element = self.find("gpib_library")
        if element is not None and element.text:
            os.environ["GPIB_LIBRARY"] = element.text
            logger.debug("update GPIB_LIBRARY=%s", element.text)

        element = self.find("pyvisa_library")
        if element is not None and element.text:
            os.environ["PYVISA_LIBRARY"] = element.text
            logger.debug("update PyVISA_LIBRARY=%s", element.text)

        path_elements = self.findall("path")
        if path_elements:
            paths: list[str] = []
            os_paths: set[str] = set(os.environ["PATH"].split(os.pathsep))
            for element in path_elements:
                path = element.text
                if not path or not os.path.isdir(path):  # noqa: PTH112
                    logger.warning("skipped append to PATH: %r", path)
                elif element.attrib.get("recursive", "false").lower() == "true":
                    for directory, _, _ in os.walk(path):
                        if directory not in os_paths and directory not in paths:
                            paths.append(directory)
                            logger.debug("append to PATH: %r", path)
                elif path not in os_paths and path not in paths:
                    paths.append(path)
                    logger.debug("append to PATH: %r", path)

            os.environ["PATH"] += os.pathsep + os.pathsep.join(paths)

        for element in self.findall("connections"):
            connections.add(*_sources(element.text, "connections"))

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return f"<{self.__class__.__name__} path={self.path!r}>"

    def attrib(self, path: str) -> dict[str, bool | float | str]:
        """Get the attributes of the first matching element by tag name or path.

        If possible, the value is converted to a [bool][]{:target="_blank"}
        (`true` or `false` case-insensitive), an [int][]{:target="_blank"} or
        a [float][]{:target="_blank"}, otherwise the value remains a
        [str][]{:target="_blank"}.

        Args:
            path: Either an element tag name or an XPath.

        Returns:
            The attributes of the matching `path` element.
        """
        element = self.find(path)
        if element is None:
            return {}
        return {k: to_primitive(v) for k, v in element.attrib.items()}

    @property
    def equipment(self) -> ConfigEquipment:
        """Returns the `<equipment/>` elements in the configuration file like a sequence of [Equipment][] items.

        Using the returned object you can access [Equipment][] items by index (based on the order that
        `<equipment/>` elements are defined in the configuration file), by the `eid` attribute value or
        by the `name` attribute value. You can also iterate over the [Equipment][] items in the sequence.

        See [here][config-python-example] for examples.
        """
        return self._config_equipment

    def find(self, path: str) -> Element[str] | None:
        """Find the first matching element by tag name or path.

        Args:
            path: Either an element tag name or an XPath.

        Returns:
            The element or `None` if an element was not found at `path`.
        """
        return self._root.find(path)

    def findall(self, path: str) -> list[Element[str]]:
        """Find all matching sub-elements by tag name or path.

        Args:
            path: Either an element tag name or an XPath.

        Returns:
            All matching elements in document order.
        """
        return self._root.findall(path)

    @property
    def registers(self) -> dict[str, Register]:
        """Returns all equipment registers that are specified in the configuration file.

        The _key_ in the returned [dict][]{:target="_blank"} is the [team][msl.equipment.schema.Register.team]
        value of the corresponding [Register][].
        """
        if self._registers is not None:
            return self._registers

        registers: dict[str, Register] = {}
        for element in self.findall("register"):
            sources = _sources(element.text, "register")
            if sources:
                register = Register(*sources)
                registers[register.team] = register

        self._registers = registers
        return registers

    @property
    def root(self) -> Element[str]:
        """The root element (the first node) in the configuration file."""
        return self._root

    @property
    def path(self) -> str:
        """The path to the configuration file."""
        if isinstance(self._source, (bytes, str, os.PathLike)):
            return os.fsdecode(self._source)
        return f"<{self._source.__class__.__name__}>"

    @overload
    def value(self, path: str, default: None = None) -> bool | float | str | None: ...  # pragma: no cover

    @overload
    def value(self, path: str, default: bool) -> bool: ...  # pragma: no cover  # noqa: FBT001

    @overload
    def value(self, path: str, default: int) -> int: ...  # pragma: no cover

    @overload
    def value(self, path: str, default: float) -> float: ...  # pragma: no cover

    @overload
    def value(self, path: str, default: str) -> str: ...  # pragma: no cover

    def value(self, path: str, default: bool | float | str | None = None) -> bool | float | str | None:  # noqa: FBT001
        """Gets the value (text) associated with the first matching element.

        If possible, the value is converted to a [bool][]{:target="_blank"}
        (`true` or `false` case-insensitive), an [int][]{:target="_blank"} or
        a [float][]{:target="_blank"}, otherwise the value remains a
        [str][]{:target="_blank"}.

        Args:
            path: Either an element tag name or an XPath.
            default: The default value if an element cannot be found.

        Returns:
            The value of the element or `default` if an element was not found at `path`.
        """
        element = self.find(path)
        if element is None:
            return default
        if element.text is None:
            return None
        return to_primitive(element.text)


class ConfigEquipment:
    """Access `<equipment/>` elements in a configuration file like a sequence of [Equipment][] items."""

    def __init__(self, cfg: Config) -> None:
        """Access `<equipment/>` elements in a configuration file like a sequence of [Equipment][] items.

        Args:
            cfg: The configuration instance.
        """
        self._cfg: Config = cfg
        self._elements: list[Element[str]] = cfg.findall("equipment")
        self._equipment: dict[str, Equipment] = {}  # key=eid
        self._index_map: dict[int, str] = {i: e.attrib["eid"] for i, e in enumerate(self._elements)}
        self._name_map: dict[str, str] = {
            e.attrib["name"]: e.attrib["eid"] for e in self._elements if e.attrib.get("name")
        }

    def __getitem__(self, item: str | int) -> Equipment:
        """Returns the `equipment` item from the configuration file."""
        if isinstance(item, int):
            eid = self._index_map.get(item)
            if eid is None:
                msg = "index out of range"
                raise IndexError(msg)
        else:
            eid = self._name_map.get(item, item)  # assume item=eid if not a name

        equipment = self._equipment.get(eid)
        if equipment is not None:
            return equipment

        for register in self._cfg.registers.values():
            equipment = register.get(eid)
            if equipment is not None:
                self._equipment[eid] = equipment
                return equipment

        msg = (
            f"The equipment with id {eid!r} cannot be found in the "
            f"registers that are specified in the configuration file"
        )
        raise ValueError(msg)

    def __iter__(self) -> Iterator[Equipment]:
        """Yields `equipment` items from the configuration file."""
        for index in range(len(self._elements)):
            yield self[index]

    def __len__(self) -> int:
        """Returns the number of `<equipment/>` elements in the configuration file."""
        return len(self._elements)

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        n = len(self)
        plural = "" if n == 1 else "s"
        return f"<{self.__class__.__name__} ({n} equipment element{plural})>"

    @property
    def eids(self) -> tuple[str, ...]:
        """Returns the value of the `eid` attribute for each `<equipment/>` element in a configuration file."""
        return tuple(self._index_map.values())

    @property
    def names(self) -> tuple[str, ...]:
        """Returns the value of the `name` attribute for each `<equipment/>` element in a configuration file."""
        return tuple(e.attrib.get("name", "") for e in self._elements)
