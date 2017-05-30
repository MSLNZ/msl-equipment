"""
Load a XML configuration file.
"""
import os
import logging
from xml.etree import ElementTree

from .database import Database

logger = logging.getLogger(__name__)

PyVISA_LIBRARY = '@ni'
DEMO_MODE = False
SDK_PATH = []


class Config(object):

    def __init__(self, path):
        """Load a XML configuration file.

        This function is used to set the configuration constants to use for the Python
        runtime and it creates :class:`.EquipmentRecord`'s from **Equipment-Register**
        databases and :class:`.ConnectionRecord`'s from **Connection** databases.

        **MSL-Equipment** configuration constants that can be defined in a configuration file:

        +----------------+-----------------------------------+-----------------------------------------+
        |      Name      |           Example Values          |               Description               |
        +================+===================================+=========================================+
        | PyVISA_LIBRARY | @ni, @py, @sim, /path/to/lib\@ni  | The PyVISA backend_ library to use.     |
        +----------------+-----------------------------------+-----------------------------------------+
        |   DEMO_MODE    | true, false                       | Whether to open **all** connections in  |
        |                |                                   | demo mode.                              |
        +----------------+-----------------------------------+-----------------------------------------+
        |   SDK_PATH     | /path/to/SDKs, D:/data/SDKs       | A path that contains SDK libraries.     |
        |                |                                   | Accepts a *recursive="true"* attribute. |
        |                |                                   | Appends the path(s) to                  |
        |                |                                   | :obj:`os.environ['PATH'] <os.environ>`  |
        +----------------+-----------------------------------+-----------------------------------------+

        .. _backend: http://pyvisa.readthedocs.io/en/stable/backends.html

        Also, the user is encouraged to define their own application-specific constants within the
        configuration file.

        Example configuration file::

            <?xml version="1.0" encoding="UTF-8"?>
            <msl>

                <!-- Application-specific constant to use as a warning if the temperature of a device gets too hot -->
                <max_temperature units="C">60</max_temperature>

                <!-- Use PyVISA-py as the PyVISA library -->
                <PyVISA_LIBRARY>@py</PyVISA_LIBRARY>

                <!-- Open all connections in demo mode -->
                <DEMO_MODE>true</DEMO_MODE>

                <!-- Add a path to os.environ['PATH'] where SDK files are located -->
                <SDK_PATH>I:\Photometry\SDKs</SDK_PATH>

                <!-- Recursively add SDK paths starting from a root path -->
                <SDK_PATH recursive="true">C:\Program Files\Thorlabs</SDK_PATH>

                <!-- The equipment that is being used to perform the measurement -->
                <equipment alias="ref" manufacturer="Keysight" model="34465A" serial="MY54506462"/>
                <equipment alias="scope" manufacturer="Pico Technologies" serial="DY135/055"/>
                <equipment alias="flipper" manufacturer="Thorlabs" model="MFF101/M" serial="37871232"/>

                <!-- The database that contains the information required to connect to the equipment -->
                <equipment_connections>
                    <path>Z:\QUAL\Equipment\Equipment Register.xls</path>
                    <sheet>Connections</sheet>
                </equipment_connections>

                <!-- The equipment-register database(s) -->
                <equipment_registers>
                    <register section="P&amp;R">
                        <path>Z:\QUAL\Equipment\Equipment Register.xls</path>
                        <sheet>Equipment</sheet>
                    </register>
                    <register section="Electrical">
                        <path>H:\Quality\Registers\Equipment.xls</path>
                        <sheet>REG</sheet>
                    </register>
                    <register section="Time">
                        <path>W:\Registers\Equip.csv</path>
                    </register>
                    <register section="Mass">
                        <path>Y:\databases\equipment\equip-reg.txt</path>
                    </register>
                </equipment_registers>

            </msl>

        Parameters
        ----------
        path : :obj:`str`
            The path to a XML configuration file.

        Raises
        ------
        FileNotFoundError
            If `path` does not exist.
        :exc:`~xml.etree.ElementTree.ParseError`
            If the configuration file is invalid.
        """
        logger.debug('Loading {}'.format(path))
        self._root = ElementTree.parse(path).getroot()
        self._path = path

        element = self._root.find('PyVISA_LIBRARY')
        if element is not None:
            global PyVISA_LIBRARY
            PyVISA_LIBRARY = element.text
            logger.debug('update PyVISA_LIBRARY = {}'.format(PyVISA_LIBRARY))

        element = self._root.find('DEMO_MODE')
        if element is not None:
            global DEMO_MODE
            DEMO_MODE = element.text.lower() == 'true'
            logger.debug('update DEMO_MODE = {}'.format(DEMO_MODE))

        global SDK_PATH
        for element in self._root.findall('SDK_PATH'):
            if not os.path.isdir(element.text):
                logger.warning('Not a valid SDK_PATH ' + element.text)
                continue
            if element.attrib.get('recursive', 'false').lower() == 'true':
                for root, dirs, files in os.walk(element.text):
                    SDK_PATH.append(root)
            else:
                SDK_PATH.append(element.text)
        for p in SDK_PATH:
            os.environ['PATH'] += os.pathsep + p
            logger.debug('append SDK_PATH %s', p)

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
        return Database(self._path)

    def value(self, tag):
        """Gets the value associated with the specified `tag`.

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
