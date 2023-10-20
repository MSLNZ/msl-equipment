"""
Load an XML :ref:`configuration-file`.
"""
from __future__ import annotations

import os
from typing import Any
from typing import AnyStr
from typing import IO
from typing import TYPE_CHECKING
from typing import Union
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from .utils import convert_to_primitive
from .utils import logger

if TYPE_CHECKING:
    from .database import Database


XMLType = Union[AnyStr, os.PathLike[AnyStr], IO[AnyStr]]
"""An XML-document type that can be parsed."""


class Config:

    GPIB_LIBRARY: str = ''
    """The path to a GPIB library file."""

    PyVISA_LIBRARY: str = '@ivi'
    """The PyVISA backend :ref:`library <intro-configuring>` to use."""

    DEMO_MODE: bool = False
    """Whether to open connections in demo mode. 
    
    If enabled then the equipment does not need to be physically connected
    to a computer and the connection is simulated.
    """

    PATH: list[str] = []
    """Paths are also appended to :data:`os.environ['PATH'] <os.environ>`."""

    def __init__(self, source: XMLType) -> None:
        r"""Load an XML :ref:`configuration-file`.

        The purpose of the :ref:`configuration-file` is to define parameters
        that may be required during data acquisition and to access
        :class:`.EquipmentRecord`'s from an :ref:`equipment-database` and
        :class:`.ConnectionRecord`'s from a :ref:`connections-database`.

        The following table summarizes the XML elements that are used by
        MSL-Equipment which may be defined in a :ref:`configuration-file`:

        +----------------+--------------------------+-----------------------------------------------+
        |    XML Tag     |      Example Values      |               Description                     |
        +================+==========================+===============================================+
        |   demo_mode    | true, false, True, False | Whether to open connections in demo mode.     |
        +----------------+--------------------------+-----------------------------------------------+
        |  gpib_library  | /opt/gpib/libgpib.so.0   | The path to a GPIB library file.              |
        |                | C:\gpib\ni4882.dll       |                                               |
        +----------------+--------------------------+-----------------------------------------------+
        | pyvisa_library | @ivi, @py, @sim          | The PyVISA :ref:`library <intro-configuring>` |
        |                | /path/to/libvisa.so.7    | to use.                                       |
        +----------------+--------------------------+-----------------------------------------------+
        |     path       | /path/to/lib             | A path that contains external resources.      |
        |                | D:\SDKs                  | Accepts a *recursive="true"* attribute.       |
        |                |                          | The path(s) are appended to                   |
        |                |                          | :data:`os.environ['PATH'] <os.environ>`       |
        |                |                          | and to :attr:`.PATH`                          |
        +----------------+--------------------------+-----------------------------------------------+

        You are also encouraged to define your own application-specific elements
        within your :ref:`configuration-file`.

        :param source: A filename or file object containing XML data.
        """
        logger.debug('loading %s', source)
        self._source = source
        self._database: Database | None = None
        self._root: Element = ElementTree.parse(source).getroot()

        element = self.find('gpib_library')
        if element is not None:
            Config.GPIB_LIBRARY = element.text
            logger.debug('update Config.GPIB_LIBRARY = %s', Config.GPIB_LIBRARY)

        element = self.find('pyvisa_library')
        if element is not None:
            Config.PyVISA_LIBRARY = element.text
            logger.debug('update Config.PyVISA_LIBRARY = %s', Config.PyVISA_LIBRARY)

        element = self.find('demo_mode')
        if element is not None:
            Config.DEMO_MODE = element.text.lower() == 'true'
            logger.debug('update Config.DEMO_MODE = %s', Config.DEMO_MODE)

        for element in self.findall('path'):
            if not os.path.isdir(element.text):
                logger.warning('not a valid PATH %s', element.text)
                continue
            if element.attrib.get('recursive', 'false').lower() == 'true':
                for root, _, _ in os.walk(element.text):
                    Config.PATH.append(root)
            else:
                Config.PATH.append(element.text)
        for p in Config.PATH:
            os.environ['PATH'] += os.pathsep + p
            logger.debug('append Config.PATH %s', p)

    def attrib(self, tag_or_path: str) -> dict[str, Any]:
        """Get the attributes of the first matching element by tag name or path.

        The values are converted to the appropriate data type if possible. For
        example, if the text of the element is ``true`` it will be converted
        to :data:`True`, otherwise the value will be kept as a :class:`str`.

        :param tag_or_path: Either an element tag name or an XPath.
        :return: The attributes of the matching element.
        """
        element = self.find(tag_or_path)
        if element is None:
            return {}
        return dict((k, convert_to_primitive(v)) for k, v in element.attrib.items())

    def database(self) -> Database:
        """A reference to the equipment and connection records in the database(s)."""
        if self._database is None:
            from .database import Database  # avoid circular import errors
            self._database = Database(self._source)
        return self._database

    def find(self, tag_or_path: str) -> Element | None:
        """Find the first matching element by tag name or path.

        :param tag_or_path: Either an element tag name or an XPath.
        :return: The element or :data:`None` if no element was found.
        """
        return self._root.find(tag_or_path)

    def findall(self, tag_or_path: str) -> list[Element]:
        """Find all matching sub-elements by tag name or path.

        :param tag_or_path: Either an element tag name or an XPath.
        :return: All matching elements in document order.
        """
        return self._root.findall(tag_or_path)

    @property
    def path(self) -> AnyStr | os.PathLike[AnyStr]:
        """The path to the configuration file."""
        try:
            os.path.isfile(self._source)
        except TypeError:  # raised if self._source is IO[AnyStr]
            return f'<{self._source.__class__.__name__}>'
        else:
            return self._source

    @property
    def root(self) -> Element:
        """The root element (the first node) in the XML document."""
        return self._root

    def value(self, tag_or_path: str, default: Any = None) -> Any:
        """Gets the value (text) associated with the first matching element.

        The value is converted to the appropriate data type if possible. For
        example, if the text of the element is ``true`` it will be converted
        to :data:`True`.

        :param tag_or_path: Either an element tag name or an XPath.
        :param default: The default value if an element cannot be found.
        :return: The value of the element or `default` if no element was found.
        """
        element = self.find(tag_or_path)
        if element is None:
            return default
        return convert_to_primitive(element.text)
