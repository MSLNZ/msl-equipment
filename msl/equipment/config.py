"""
Load a XML :ref:`configuration`.
"""
import os
import logging
from xml.etree import ElementTree

from msl.equipment.database import Database

logger = logging.getLogger(__name__)


class Config(object):

    PyVISA_LIBRARY = '@ni'
    """:obj:`str`: The PyVISA backend_ library to use.
    
    .. _backend: http://pyvisa.readthedocs.io/en/stable/backends.html
    """

    DEMO_MODE = False
    """:obj:`bool`: Whether to open connections in demo mode. 
    
    The equipment does not need to be connected to the computer.
    """

    PATH = []
    """:obj:`list` of :obj:`str`: Paths that are appended to :obj:`os.environ['PATH'] <os.environ>`."""

    def __init__(self, path):
        """Load a XML :ref:`configuration`.

        This function is used to set the configuration constants to use for the Python runtime
        and it allows you to access :class:`.EquipmentRecord`'s from an :ref:`equipment_database`
        and :class:`.ConnectionRecord`'s from a :ref:`connection_database`.

        **MSL-Equipment** constants that can be defined in a :ref:`configuration`:

        +----------------+-----------------------------------+-----------------------------------------+
        |      Name      |           Example Values          |               Description               |
        +================+===================================+=========================================+
        | PyVISA_LIBRARY | @ni, @py, @sim, /path/to/lib\@ni  | The PyVISA backend_ library to use.     |
        +----------------+-----------------------------------+-----------------------------------------+
        |   DEMO_MODE    | true, false                       | Whether to open connections in demo     |
        |                |                                   | mode.                                   |
        +----------------+-----------------------------------+-----------------------------------------+
        |     PATH       | /path/to/SDKs, D:/images          | A path that contains external resources.|
        |                |                                   | Accepts a *recursive="true"* attribute. |
        |                |                                   | Appends the path(s) to                  |
        |                |                                   | :obj:`os.environ['PATH'] <os.environ>`  |
        +----------------+-----------------------------------+-----------------------------------------+

        Also, the user is encouraged to define their own application-specific constants within the
        configuration file.

        .. _backend: http://pyvisa.readthedocs.io/en/stable/backends.html

        Parameters
        ----------
        path : :obj:`str`
            The path to a XML :ref:`configuration`.

        Raises
        ------
        IOError
            If `path` does not exist.
        :exc:`~xml.etree.ElementTree.ParseError`
            If the :ref:`configuration` is invalid.
        """
        logger.debug('Loading {}'.format(path))
        self._root = ElementTree.parse(path).getroot()
        self._path = path
        self._database = None

        element = self._root.find('PyVISA_LIBRARY')
        if element is not None:
            Config.PyVISA_LIBRARY = element.text
            logger.debug('update Config.PyVISA_LIBRARY = {}'.format(Config.PyVISA_LIBRARY))

        element = self._root.find('DEMO_MODE')
        if element is not None:
            Config.DEMO_MODE = element.text.lower() == 'true'
            logger.debug('update Config.DEMO_MODE = {}'.format(Config.DEMO_MODE))

        for element in self._root.findall('PATH'):
            if not os.path.isdir(element.text):
                logger.warning('Not a valid PATH ' + element.text)
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
        """:obj:`str`: The path to the configuration file."""
        return self._path

    @property
    def root(self):
        """Returns the root element (the first node) of the XML tree.

        Returns
        -------
        :obj:`~xml.etree.ElementTree.Element`
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
            self._database = Database(self._path)
        return self._database

    def value(self, tag):
        """Gets the value associated with the specified `tag` in the configuration file.

        Parameters
        ----------
        tag : :obj:`str`
            The name of a XML tag in the configuration file.

        Returns
        -------
        :obj:`str` or :obj:`None`
            The value associated with the `tag` or :obj:`None` if the tag cannot be found.
        """
        element = self._root.find(tag)
        if element is not None:
            return element.text
        return None
