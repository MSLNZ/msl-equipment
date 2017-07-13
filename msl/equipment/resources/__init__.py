"""
MSL resources for connecting to equipment.
"""
import os
import re
import sys
import fnmatch
import importlib


def recursive_find_resource_class(class_name):
    """Find the Python resource class.

    Parameters
    ----------
    class_name : :obj:`str`
        The name of a resource class.

    Returns
    -------
    The Python resource class (a subclass of :class:`~msl.equipment.connection_msl.Connection`).

    Raises
    ------
    IOError
        If the Python resource class cannot be found.
    """
    if not class_name:
        raise IOError('No resource class name was specified')

    for root, dirs, files in os.walk(os.path.abspath(os.path.dirname(__file__))):
        root_pkg = __name__ + root.replace(os.path.sep, '.').split(__name__)[1]
        for filename in fnmatch.filter(files, '*.py'):
            if filename == '__init__.py':
                continue

            cls = get_class('{}.{}'.format(root_pkg, filename[:-3]), class_name)
            if cls is not None:
                return cls

    raise IOError('Cannot find the {} class'.format(class_name))


def get_class(module_name, class_name):
    """Returns the specified Python class.

    Parameters
    ----------
    module_name : :obj:`str`
        The name of a Python module.
    class_name : :obj:`str`
        The name of a Python class.

    Returns
    -------
    The Python resource class or :obj:`None` if the class cannot be found.
    """
    try:
        mod = sys.modules[module_name]
    except KeyError:
        try:
            mod = importlib.import_module(module_name)
        except ModuleNotFoundError:
            return None

    try:
        return getattr(mod, class_name)
    except AttributeError:
        return None


def check_manufacture_model_resource_name(connection_record):
    """Check if there is a resource class with the name equal to
    `connection_record.model` in the
    `connection_record.manufacturer.lower()` + '.' + connection_record.model.lower()`
    module.

    For example, if the `connection_record` is for a Thorlabs FW102C filter wheel
    then check if a msl.equipment.resources.thorlabs.fw102C.FW102C resource class exists.

    Parameters
    ----------
    connection_record : :obj:`.msl.equipment.record_types.ConnectionRecord`
        A :obj:`.msl.equipment.record_types.ConnectionRecord` object.

    Returns
    -------
    The Python resource class or :obj:`None` if there is no resource class available.
    """
    # check if Manufacturer or Model contain any non-alphanumeric characters
    if re.findall(r'\W', connection_record.manufacturer) or re.findall(r'\W', connection_record.model):
        return None

    module_name = __name__ + '.' + connection_record.manufacturer.lower() + '.' + connection_record.model.lower()
    return get_class(module_name, connection_record.model)


def find_sdk_class(connection_record):
    """Find the Python class that is a wrapper around the SDK.

    Parameters
    ----------
    connection_record : :obj:`.msl.equipment.record_types.ConnectionRecord`
        A :obj:`.msl.equipment.record_types.ConnectionRecord` object.

    Returns
    -------
    The Python wrapper class around the manufacturer's SDK.

    Raises
    ------
    IOError
        If the :obj:`.msl.equipment.record_types.ConnectionRecord.address` value does
        not have the required format of ``SDK::PythonClassName::PathToLibrary``.
    """
    address_split = connection_record.address.split('::')
    if len(address_split) != 3:
        msg = 'The address received is {}\n'.format(connection_record.address)
        msg += 'For an SDK interface, the address must be of the form SDK::PythonClassName::PathToLibrary'
        raise IOError(msg)
    return recursive_find_resource_class(address_split[1])


def find_serial_class(connection_record):
    """Find the Python resource class that is used for :obj:`~serial.Serial` communication.

    Parameters
    ----------
    connection_record : :obj:`.msl.equipment.record_types.ConnectionRecord`
        A :obj:`.msl.equipment.record_types.ConnectionRecord` object.

    Returns
    -------
    The Python resource class that uses :obj:`~serial.Serial` communication or
    :obj:`None` if no resource class was specified in the address.
    """
    address_split = connection_record.address.split('::')
    if len(address_split) == 1:
        return check_manufacture_model_resource_name(connection_record)
    return recursive_find_resource_class(address_split[1])
