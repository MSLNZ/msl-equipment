"""Load a configuration file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, overload
from xml.etree.ElementTree import parse

from .schema import Register
from .utils import logger, to_primitive

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

    from ._types import XMLSource


class Config:
    """Load an XML configuration-file."""

    def __init__(self, source: XMLSource) -> None:
        """Load a [configuration file][configuration-file].

        The purpose of the [configuration file][configuration-file] is to define
        parameters and equipment that are required for data acquisition and to load
        [equipment][equipment-registers] and [connection][connection-registers]
        registers.

        Args:
            source: A filename or file object containing XML data.
        """
        logger.debug("load configuration %s", source)
        self._source: XMLSource = source
        self._root: Element[str] = parse(source).getroot()  # noqa: S314
        self._registers: dict[str, Register] | None = None

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

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return f"<{self.__class__.__name__} path={self.path!r}>"

    def attrib(self, path: str) -> dict[str, bool | float | str | None]:
        """Get the attributes of the first matching element by tag name or path.

        The values are converted to the appropriate data type if possible.
        For example, if the value of an attribute is `"true"` the value is
        converted to the [True][]{:target="_blank"} boolean type.

        Args:
            path: Either an element tag name or an XPath.

        Returns:
            The attributes of the matching element.
        """
        element = self.find(path)
        if element is None:
            return {}
        return {k: to_primitive(v) for k, v in element.attrib.items()}

    def find(self, path: str) -> Element | None:
        """Find the first matching element by tag name or path.

        Args:
            path: Either an element tag name or an XPath.

        Returns:
            The element or `None` if no element was found.
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
        """[dict][[str][], [Register][]] &mdash; Returns all equipment registers specified in the configuration file.

        The keys are the [team][msl.equipment.schema.Register.team] values of each register.
        """
        if self._registers is not None:
            return self._registers

        registers: dict[str, Register] = {}
        for element in self.findall("registers/register"):
            if not element.text or not element.text.strip():
                continue

            path = Path(element.text)
            sources: list[Path | Element[str]] = []
            if path.is_dir():
                for file in path.rglob("*.xml"):
                    # Ignore XML files in hidden directories (e.g., XML files in PyCharm's .idea directory)
                    if any(part.startswith(".") for part in file.parts):
                        continue
                    root = parse(file).getroot()  # noqa: S314
                    if root.tag.endswith("register"):
                        sources.append(root)
            else:
                sources.append(path)

            register = Register(*sources)
            registers[register.team] = register

        self._registers = registers
        return registers

    @property
    def root(self) -> Element[str]:
        """The root element (the first node) in the XML document."""
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

        The value is converted to the appropriate data type if possible. For
        example, if the text of the element is `true` it will be converted
        to [True][]{:target="_blank"}.

        Args:
            path: Either an element tag name or an XPath.
            default: The default value if an element cannot be found.
            namespaces: An optional mapping from namespace prefix to full name.

        Returns:
            The value of the element or `default` if no element was found.
        """
        element = self.find(path)
        if element is None:
            return default
        if element.text is None:
            return None
        return to_primitive(element.text)
