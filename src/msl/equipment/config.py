"""
Load an XML :ref:`configuration-file`.
"""
from __future__ import annotations

import os
from typing import Any
from typing import BinaryIO
from typing import TYPE_CHECKING
from typing import TextIO
from typing import Union
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from .utils import convert_to_primitive
from .utils import logger

if TYPE_CHECKING:
    from .database import Database


XMLType = Union[str, bytes, os.PathLike, BinaryIO, TextIO]
"""An XML-document type that can be parsed."""


class Config:

    GPIB_LIBRARY: str = ''
    """The path to a GPIB library file.
    
    Setting this attribute is necessary only if you want to communicate with
    a GPIB device and the file is not automatically found or you want to
    use a different file than the default file.
    """

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

        +----------------+----------------------------+---------------------------------------------------+
        |    XML Tag     |      Example Values        |               Description                         |
        +================+============================+===================================================+
        |   demo_mode    | true, false, True, False   | Whether to open connections in demo mode. The     |
        |                |                            | value will set :attr:`.DEMO_MODE`.                |
        +----------------+----------------------------+---------------------------------------------------+
        |  gpib_library  | /opt/gpib/libgpib.so.0     | The path to a GPIB library file. Required only    |
        |                |                            | if you want to use a specific file. The value     |
        |                |                            | will set :attr:`.GPIB_LIBRARY`.                   |
        +----------------+----------------------------+---------------------------------------------------+
        |     path       | C:\\Program Files\\Company | A path that contains additional resources.        |
        |                |                            | Accepts a *recursive="true"* attribute. The       |
        |                |                            | path(s) are appended to :attr:`.PATH` and to      |
        |                |                            | :data:`os.environ['PATH'] <os.environ>`. A        |
        |                |                            | *<path>* element may be specified multiple times. |
        +----------------+----------------------------+---------------------------------------------------+
        | pyvisa_library | @ivi, @py,                 | The PyVISA :ref:`library <intro-configuring>` to  |
        |                | /opt/ni/libvisa.so.7       | use. The value will set :attr:`.PyVISA_LIBRARY`.  |
        +----------------+----------------------------+---------------------------------------------------+

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
            path = element.text
            if not os.path.isdir(path):
                logger.warning('cannot append to Config.PATH, %r is not a directory', path)
            elif element.attrib.get('recursive', 'false').lower() == 'true':
                for root, _, _ in os.walk(path):
                    if root not in Config.PATH:
                        Config.PATH.append(root)
                        os.environ['PATH'] += os.pathsep + root
                        logger.debug('append %r to Config.PATH', root)
            elif path not in Config.PATH:
                Config.PATH.append(path)
                os.environ['PATH'] += os.pathsep + path
                logger.debug('append %r to Config.PATH', path)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(path={self.path!r})'

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
    def path(self) -> str:
        """The path to the configuration file."""
        try:
            return os.fsdecode(self._source)
        except TypeError:
            return f'<{self._source.__class__.__name__}>'

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
