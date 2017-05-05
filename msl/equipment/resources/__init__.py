"""
MSL resources for connecting to equipment.
"""
import os
import sys
import fnmatch
import importlib


def find_sdk_class(address):
    """Find the Python class that is a wrapper around the SDK.

    Do not call directly. The connection :func:`factory <msl.equipment.factory.connect>`
    calls this function.

    Parameters
    ----------
    address : :obj:`str`
        A :data:`.msl.equipment.record_types.ConnectionRecord.address` value.

    Returns
    -------
    :class:`~msl.equipment.connection_msl.ConnectionSDK`
        The Python wrapper class around the manufacturer's SDK.

    Raises
    ------
    IOError
        If the Python wrapper class cannot be found or if the shared library 
        cannot be found.   
    """
    address_split = address.split('::')
    if len(address_split) != 3:
        msg = 'The address received is {}\nFor an SDK interface, the address must ' \
              'be of the form SDK::PythonClassName::PathToLibrary'.format(address)
        raise IOError(msg)

    cls = address_split[1]

    for root, dirs, files in os.walk(os.path.abspath(os.path.dirname(__file__))):
        root_pkg = __name__ + root.replace(os.path.sep, '.').split(__name__)[1]
        for filename in fnmatch.filter(files, '*.py'):
            if filename == '__init__.py':
                continue

            module_name = '{}.{}'.format(root_pkg, filename[:-3])
            if module_name in sys.modules:
                mod = sys.modules[module_name]
            else:
                mod = importlib.import_module(module_name)

            if cls in dir(mod):
                return getattr(mod, cls)

    raise IOError('Cannot find the {} class'.format(cls))
