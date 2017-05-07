"""
Load a XML configuration file.
"""
import logging
from xml.etree import ElementTree

from .database import Database

logger = logging.getLogger(__name__)

#: Default configuration key-value pairs.
CONFIG = {
    'PyVISA_library': '@ni',
    'demo_mode': False,
}


def load(path):
    """Load a XML configuration file.
    
    This function is used to set the :obj:`CONFIG` variables to use for the Python 
    runtime and it creates :class:`.EquipmentRecord`'s from **Equipment-Register** 
    databases and :class:`.ConnectionRecord`'s from **Connection** databases.
    
    Example :obj:`CONFIG` variables that can be defined in a configuration file:
    
    +----------------+-----------------------------------+-----------------------------------------+
    |      Name      |           Example Values          |               Description               |  
    +================+===================================+=========================================+
    | PyVISA_library | @ni, @py, @sim, /path/to/lib\@ni  | The PyVISA backend_ library to use.     |
    +----------------+-----------------------------------+-----------------------------------------+
    |   demo_mode    | true, True, false, False          | Open **all** connections in demo mode?  |
    +----------------+-----------------------------------+-----------------------------------------+
    
    .. _backend: http://pyvisa.readthedocs.io/en/stable/backends.html
   
    Example configuration file::
    
        <?xml version="1.0" encoding="UTF-8"?>
        <msl>

            <!-- Use PyVISA-py as the PyVISA library -->
            <PyVISA_library>@py</PyVISA_library>

            <!-- Open all connections in demo mode -->
            <demo_mode>true</demo_mode>
    
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

    Returns
    -------
    :class:`~.database.Database`
        A reference to the equipment and connection records in the database(s) 
        that are specified in the configuration file.
    
    Raises
    ------
    FileNotFoundError
        If `path` does not exist.
    :exc:`~xml.etree.ElementTree.ParseError`
        If the configuration file is invalid.
    """
    logger.debug('Loading {}'.format(path))
    root = ElementTree.parse(path).getroot()
    for key in CONFIG:
        element = root.find(key)
        if element is not None:
            CONFIG[key] = _convert(element.text)
        logger.debug('CONFIG_OPTIONS[{}] = {}'.format(key, CONFIG[key]))
    return Database(path)


def _convert(string):
    if string.lower() == 'true':
        return True
    if string.lower() == 'false':
        return False
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            return string
