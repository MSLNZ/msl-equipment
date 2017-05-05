"""
Load a XML configuration file.
"""
import os
import logging
from xml.etree import ElementTree

from msl.equipment.database import Database

logger = logging.getLogger(__name__)


def load(path):
    """Load a XML configuration file.
    
    This function is used to set environment variables to use for the Python 
    runtime and it creates :class:`.EquipmentRecord`'s from **Equipment-Register** 
    databases and :class:`.ConnectionRecord`'s from **Connection** databases.
    
    Environment variables, :obj:`os.environ`, that can be defined in a configuration 
    file. The **bold** values in the last column represent the default value used if 
    the variable *Name* is not found in the configuration file.    
    
    +----------------+----------------------------------------------+--------------------+
    |      Name      |                 Description                  |   Allowed Values   |  
    +================+==============================================+====================+
    | PyVISA-backend | The PyVISA backend to use.                   | **@ni**, @py, @sim |
    +----------------+----------------------------------------------+--------------------+
    |   demo_mode    | Whether to open ALL connections in demo mode | **False**, True    |
    +----------------+----------------------------------------------+--------------------+
   
    Example configuration file::
    
        <?xml version="1.0" encoding="UTF-8"?>
        <msl>
    
            <!-- The equipment that is being used to perform the measurement -->
            <equipment alias="ref" manufacturer="Keysight" model="34465A" serial="MY54506462"/>
            <equipment alias="scope" manufacturer="Pico Technologies" serial="DY135/055"/>
            <equipment alias="flipper" manufacturer="Thorlabs" model="MFF101/M" serial="37871232"/>
        
            <!-- The PyVISA backend to use -->
            <PyVISA-backend>@py</PyVISA-backend>

            <!-- By default, open all connections in demo mode -->
            <demo_mode>True</demo_mode>
        
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
    """
    def _set_environ(element):
        if element is not None:
            os.environ[element.tag] = element.text
            logger.debug('Setting os.environ[{tag}] = {text}'.format(tag=element.tag, text=element.text))

    logger.debug('Loading {}'.format(path))

    try:
        root = ElementTree.parse(path).getroot()
    except ElementTree.ParseError:
        root = None

    if root is None:
        raise IOError('Invalid XML configuration file: {}'.format(path))

    _set_environ(root.find('PyVISA-backend'))
    _set_environ(root.find('demo_mode'))

    return Database(path)
