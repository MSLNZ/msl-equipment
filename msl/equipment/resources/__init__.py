"""
MSL resources for connecting to equipment.
"""
import os
import re
import fnmatch
import importlib

from ..utils import logger

_registry = []


class _Resource(object):

    def __init__(self, manufacturer, model, flags, cls):
        self.manufacturer = re.compile(manufacturer, flags=flags) if manufacturer else None
        self.model = re.compile(model, flags=flags) if model else None
        self.cls = cls

    def is_match(self, record, name):
        if name is not None:
            return self.cls.__name__ == name
        if self.manufacturer is None and self.model is None:
            return False
        if self.manufacturer and not self.manufacturer.search(record.manufacturer):
            return False
        if self.model and not self.model.search(record.model):
            return False
        return True


def register(manufacturer=None, model=None, flags=0):
    """Use as a decorator to register a resource class.

    Parameters
    ----------
    manufacturer : :class:`str`, optional
        The name of the manufacturer. Can be a regex pattern.
    model : :class:`str`, optional
        The model number of the equipment. Can be a regex pattern.
    flags : :class:`int`, optional
        The flags to use for the regex pattern.
    """
    def cls(obj):
        _registry.append(_Resource(manufacturer, model, flags, obj))
        logger.debug('added %s to the registry', obj)
        return obj
    return cls


def find_resource_class(record):
    """Find the resource class for this `record`.

    Parameters
    ----------
    record : :class:`~.record_types.EquipmentRecord` or :class:`~.record_types.ConnectionRecord`
        A record type. If the :attr:`~.record_types.ConnectionRecord.properties` attribute
        contains a ``resource_class_name`` key with a value that is equal to the name of a
        resource class it forces this resource class to be returned, provided that a resource
        class with the requested name exists.

    Returns
    -------
    The :class:`~.connection.Connection` subclass or :data:`None` if a resource class cannot be found.
    """
    try:
        record = record.connection
    except AttributeError:
        pass  # assume that `record` is already a ConnectionRecord

    for resource in _registry:
        if resource.is_match(record, record.properties.get('resource_class_name')):
            return resource.cls
    return


# import all submodules to register all resources in the subpackages
for root, dirs, files in os.walk(os.path.dirname(__file__)):
    root_pkg = __name__ + root.replace(os.path.sep, '.').split(__name__)[1]
    for filename in fnmatch.filter(files, '*.py'):  # ignore .pyc files
        if not filename == '__init__.py':  # these files get imported automatically
            importlib.import_module(root_pkg + '.' + filename[:-3])


from .avantes import Avantes
from .nkt import NKT
from .princeton_instruments import PrincetonInstruments
from .dataray import DataRayOCX64
