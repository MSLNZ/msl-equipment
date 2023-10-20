"""
Load an XML :ref:`configuration-file`.
"""
from __future__ import annotations

import os
from xml.etree import cElementTree

from .utils import (
    logger,
    convert_to_primitive,
)


class Config(object):

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

    def __init__(self, path):
        """Load an XML :ref:`configuration-file`.

        This function is used to set the configuration constants to use for the Python runtime
        and it allows you to access :class:`.EquipmentRecord`'s from an :ref:`equipment-database`
        and :class:`.ConnectionRecord`'s from a :ref:`connections-database`.

        The following table summarizes the XML elements that are used by **MSL-Equipment**
        and can be defined in a :ref:`configuration-file`:

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

        Parameters
        ----------
        path : :class:`str`
            The path to an XML :ref:`configuration-file`.

        Raises
        ------
        OSError
            If `path` does not exist or if the :ref:`configuration-file` is invalid.
        """
        logger.debug('Loading %s', path)
        try:
            self._root = cElementTree.parse(path).getroot()
            parse_err = ''
        except cElementTree.ParseError as err:
            parse_err = str(err)

        element = self.find('gpib_library')
        if element is not None:
            Config.GPIB_LIBRARY = element.text
            logger.debug('update Config.GPIB_LIBRARY = %s', Config.GPIB_LIBRARY)

        self._path = path
        self._database = None

        element = self._root.find('pyvisa_library')
        if element is not None:
            Config.PyVISA_LIBRARY = element.text
            logger.debug('update Config.PyVISA_LIBRARY = %s', Config.PyVISA_LIBRARY)

        element = self._root.find('demo_mode')
        if element is not None:
            Config.DEMO_MODE = element.text.lower() == 'true'
            logger.debug('update Config.DEMO_MODE = %s', Config.DEMO_MODE)

        for element in self._root.findall('path'):
            if not os.path.isdir(element.text):
                logger.warning('Not a valid PATH %s', element.text)
                continue
            if element.attrib.get('recursive', 'false').lower() == 'true':
                for root, dirs, files in os.walk(element.text):
                    Config.PATH.append(root)
            else:
                Config.PATH.append(element.text)
        for p in Config.PATH:
            os.environ['PATH'] += os.pathsep + p
            logger.debug('append Config.PATH %s', p)

    @property
    def path(self):
        """:class:`str`: The path to the configuration file."""
        return self._path

    @property
    def root(self):
        """Returns the root element (the first node) of the XML tree.

        Returns
        -------
        :class:`~xml.etree.ElementTree.Element`
            The root element.
        """
        return self._root

    def database(self):
        """
        Returns
        -------
        :class:`~.database.Database`
            A reference to the equipment and connection records in the database(s)
            that are specified in the configuration file.
        """
        if self._database is None:
            from .database import Database  # import here to avoid circular import errors
            self._database = Database(self._path)
        return self._database

    def value(self, tag, default=None):
        """Gets the value associated with the specified `tag` in the configuration file.

        The first element with name `tag` (relative to the :obj:`root`) is used.

        The value is converted to the appropriate data type if possible. Otherwise,
        the value will be returned as a :class:`str`.

        Parameters
        ----------
        tag : :class:`str`
            The name of an XML tag in the configuration file.
        default
            The default value if `tag` cannot be found.

        Returns
        -------
        The value associated with `tag` or `default` if the tag cannot be found.
        """
        element = self._root.find(tag)
        if element is not None:
            return convert_to_primitive(element.text)
        return default

    def find(self, tag):
        """Find the first sub-element (from the :obj:`root`) matching `tag` in the configuration file.

        Parameters
        ----------
        tag : :class:`str`
            The name of an XML tag in the configuration file.

        Returns
        -------
        :class:`~xml.etree.ElementTree.Element` or :data:`None`
            The first sub-element or :data:`None` if the tag cannot be found.
        """
        return self._root.find(tag)

    def findall(self, tag):
        """Find all matching sub-elements (from the :obj:`root`) matching `tag` in the configuration file.

        Parameters
        ----------
        tag : :class:`str`
            The name of an XML tag in the configuration file.

        Returns
        -------
        :class:`list` of :class:`~xml.etree.ElementTree.Element`
            All matching elements in document order.
        """
        return self._root.findall(tag)

    def attrib(self, tag):
        """Get the attributes of an :class:`~xml.etree.ElementTree.Element` in the configuration file.

        The first element with name `tag` (relative to the :obj:`root`) is used.

        The values are converted to the appropriate data type if possible.
        Otherwise, the value will be kept as a :class:`str`.

        Parameters
        ----------
        tag : :class:`str`
            The name of an XML element in the configuration file.

        Returns
        -------
        :class:`dict`
            The attributes of the :class:`~xml.etree.ElementTree.Element`.
            If an element with the name `tag` does not exist, then an empty
            :class:`dict` is returned.
        """
        element = self._root.find(tag)
        if element is None:
            return {}
        return dict((k, convert_to_primitive(v)) for k, v in element.attrib.items())
