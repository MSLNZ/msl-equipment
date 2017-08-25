"""
MSL resources for connecting to equipment.
"""
import os
import re
import sys
import fnmatch
import importlib

from msl.equipment import connection_msl
from msl.equipment.constants import MSLInterface


def recursive_find_resource_class(class_name):
    """Find the :ref:`resources` class.

    This function is not meant to be called directly.

    Parameters
    ----------
    class_name : :obj:`str`
        The name of a :ref:`resources` class.

    Returns
    -------
    A :class:`~msl.equipment.connection.Connection` subclass.

    Raises
    ------
    IOError
        If the class cannot be found.
    """
    if not class_name:
        raise IOError('No resource class name was specified')

    for root, dirs, files in os.walk(os.path.dirname(__file__)):
        if root.endswith('__pycache__'):
            continue
        root_pkg = __name__ + root.replace(os.path.sep, '.').split(__name__)[1]
        for filename in fnmatch.filter(files, '*.py'):
            if filename.startswith('__init__'):
                continue

            cls = get_class('{}.{}'.format(root_pkg, filename[:-3]), class_name)
            if cls is not None:
                return cls

    raise IOError('Cannot find the {} class'.format(class_name))


def get_class(module_name, class_name):
    """Returns the specified :class:`~msl.equipment.connection.Connection` subclass.

    This function is not meant to be called directly.

    Parameters
    ----------
    module_name : :obj:`str`
        The name of a Python module.
    class_name : :obj:`str`
        The name of a Python class.

    Returns
    -------
    A :class:`~msl.equipment.connection.Connection` subclass or :obj:`None` if the class cannot be found.
    """
    try:
        mod = sys.modules[module_name]
    except KeyError:
        try:
            mod = importlib.import_module(module_name)
        except ValueError:
            return None
        except ImportError:
            return None

    try:
        return getattr(mod, class_name)
    except AttributeError:
        return None


def check_manufacture_model_resource_name(record):
    """Check if there is a :ref:`resources` class with a name equal to
    ``record.model`` in the
    ``msl.equipment.resources. + record.manufacturer.lower() + . + record.model.lower()``
    module.

    For example, if the `record` is for a ``Thorlabs FW102C`` Filter Wheel
    then check if a ``msl.equipment.resources.thorlabs.fw102C.FW102C`` resource class exists.

    This function is not meant to be called directly.

    Parameters
    ----------
    record : :obj:`~msl.equipment.record_types.ConnectionRecord`
        A connection record from a :ref:`connection_database`.

    Returns
    -------
    A :class:`~msl.equipment.connection.Connection` subclass or :obj:`None` if the class cannot be found.
    """
    # check if Manufacturer or Model contain any non-alphanumeric characters
    if re.findall(r'\W', record.manufacturer) or re.findall(r'\W', record.model):
        return None

    module_name = __name__ + '.' + record.manufacturer.lower() + '.' + record.model.lower()
    return get_class(module_name, record.model)


def find_sdk_class(record):
    """Find the :class:`~msl.equipment.connection_msl.ConnectionSDK` subclass that is a
    wrapper around the manufacturer's SDK.

    This function is not meant to be called directly.

    Parameters
    ----------
    record : :obj:`~msl.equipment.record_types.ConnectionRecord`
        A connection record from a :ref:`connection_database`.

    Returns
    -------
    A :class:`~msl.equipment.connection_msl.ConnectionSDK` subclass.

    Raises
    ------
    ValueError
        If the :obj:`~msl.equipment.record_types.ConnectionRecord` has an invalid
        `interface` or `address` value.
    IOError
        If the SDK class cannot be found.
    """
    if record.interface != MSLInterface.SDK:
        msg = 'The interface is {}, must be {}'.format(repr(record.interface), repr(MSLInterface.SDK))
        raise ValueError(msg)
    address_split = record.address.split('::')
    if len(address_split) != 3:
        msg = 'The address received is {}\n'.format(record.address)
        msg += 'For an SDK interface, the address must be of the form SDK::PythonClassName::PathToLibrary'
        raise ValueError(msg)
    return recursive_find_resource_class(address_split[1])


def find_serial_class(record):
    """Find the :class:`~msl.equipment.connection_msl.ConnectionSerial` class.

    This function is not meant to be called directly.

    Parameters
    ----------
    record : :obj:`~msl.equipment.record_types.ConnectionRecord`
        A connection record from a :ref:`connection_database`.

    Returns
    -------
    A :class:`~msl.equipment.connection_msl.ConnectionSerial` class.

    Raises
    ------
    ValueError
        If the :obj:`~msl.equipment.record_types.ConnectionRecord` has an invalid `interface`.
    IOError
        If the :obj:`~msl.equipment.record_types.ConnectionRecord.address` specifies
        a **PythonClassName** to use for the connection and the class cannot be found.
    """
    if 'ASRL' not in record.interface.name:
        msg = 'The interface is {} and not a ASRL-type interface'.format(repr(record.interface))
        raise ValueError(msg)
    address_split = record.address.split('::')
    if (len(address_split) == 1) or (len(address_split) == 2 and address_split[1].upper() == 'INSTR'):
        cls = check_manufacture_model_resource_name(record)
        if cls is None:
            return connection_msl.ConnectionSerial
        return cls
    return recursive_find_resource_class(address_split[1])
