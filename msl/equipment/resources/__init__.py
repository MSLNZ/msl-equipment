import os
import sys
import fnmatch
import importlib


def find_sdk_pyclass(record):
    """
    Find the Python class that is a wrapper around the SDK.

    Do not call directly. The :func:`connection factory <msl.equipment.factory.connect>`
    calls this function.

    Args:
        record (:class:`.EquipmentRecord`): An equipment record (a row) from an
            Equipment-Register database.

    Returns:
        The Python wrapper class.

    Raises:
        IOError: If the Python wrapper class cannot be found or if the shared library cannot be found.   
    """
    pyclass = record.connection.address.split('::')[1]

    for root, dirs, files in os.walk(os.path.abspath(os.path.dirname(__file__))):
        for filename in fnmatch.filter(files, '*.py'):
            if filename == '__init__.py':
                continue

            module_name = '{}.{}.{}'.format(__name__, os.path.basename(root), filename[:-3])
            if module_name in sys.modules:
                mod = sys.modules[module_name]
            else:
                mod = importlib.import_module(module_name)

            if pyclass in dir(mod):
                return getattr(mod, pyclass)(record)

    raise IOError('Cannot find ' + pyclass)
