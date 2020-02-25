"""
Load an XML :ref:`configuration_file`.
"""
import os
from xml.etree import cElementTree

from .utils import logger
from .database import Database


class Config(object):

    PyVISA_LIBRARY = '@ni'
    """:class:`str`: The PyVISA backend_ library to use.
    
    .. _backend: https://pyvisa.readthedocs.io/en/stable/backends.html
    """

    DEMO_MODE = False
    """:class:`bool`: Whether to open connections in demo mode. 
    
    The equipment does not need to be physically connected to a computer.
    """

    PATH = []
    """:class:`list` of :class:`str`: Paths are also appended to :data:`os.environ['PATH'] <os.environ>`."""

    def __init__(self, path):
        """Load an XML :ref:`configuration_file`.

        This function is used to set the configuration constants to use for the Python runtime
        and it allows you to access :class:`.EquipmentRecord`'s from an :ref:`equipment_database`
        and :class:`.ConnectionRecord`'s from a :ref:`connections_database`.

        **MSL-Equipment** constants that can be defined in a :ref:`configuration_file`:

        +----------------+---------------------------------------+-----------------------------------------+
        |      Name      |           Example Values              |               Description               |
        +================+=======================================+=========================================+
        | pyvisa_library | @ni, @py, @sim, /path/to/libvisa.so.7 | The PyVISA backend_ library to use.     |
        +----------------+---------------------------------------+-----------------------------------------+
        |   demo_mode    | true, false                           | Whether to open connections in demo     |
        |                |                                       | mode.                                   |
        +----------------+---------------------------------------+-----------------------------------------+
        |     path       | /path/to/SDKs, D:/images              | A path that contains external resources.|
        |                |                                       | Accepts a *recursive="true"* attribute. |
        |                |                                       | Appends the path(s) to                  |
        |                |                                       | :data:`os.environ['PATH'] <os.environ>` |
        |                |                                       | and to :attr:`.PATH`                    |
        +----------------+---------------------------------------+-----------------------------------------+

        Also, the user is encouraged to define their own application-specific constants within the
        configuration file.

        .. _backend: https://pyvisa.readthedocs.io/en/stable/backends.html

        Parameters
        ----------
        path : :class:`str`
            The path to an XML :ref:`configuration_file`.

        Raises
        ------
        IOError
            If `path` does not exist or if the :ref:`configuration_file` is invalid.
        """
        logger.debug('Loading {}'.format(path))
        try:
            self._root = cElementTree.parse(path).getroot()
            parse_err = ''
        except cElementTree.ParseError as err:
            parse_err = str(err)

        if parse_err:
            raise IOError(parse_err)

        self._path = path
        self._database = None

        element = self._root.find('pyvisa_library')
        if element is not None:
            Config.PyVISA_LIBRARY = element.text
            logger.debug('update Config.PyVISA_LIBRARY = {}'.format(Config.PyVISA_LIBRARY))

        element = self._root.find('demo_mode')
        if element is not None:
            Config.DEMO_MODE = element.text.lower() == 'true'
            logger.debug('update Config.DEMO_MODE = {}'.format(Config.DEMO_MODE))

        for element in self._root.findall('path'):
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
            self._database = Database(self._path)
        return self._database

    def value(self, tag, default=None):
        """Gets the value associated with the specified `tag` in the configuration file.

        Parameters
        ----------
        tag : :class:`str`
            The name of an XML tag in the configuration file.
        default : :class:`str`, optional
            The default value if `tag` cannot be found.

        Returns
        -------
        :class:`str`
            The value associated with `tag` or `default` if the tag cannot be found.
        """
        element = self._root.find(tag)
        if element is not None:
            return element.text
        return default

    def find(self, tag):
        """Find the first sub-element (from the :meth:`root`) matching `tag` in the configuration file.

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
        """Find all matching sub-elements (from the :meth:`root`) matching `tag` in the configuration file.

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
