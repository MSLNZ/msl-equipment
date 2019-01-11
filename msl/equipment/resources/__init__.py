"""
MSL resources for connecting to equipment.
"""
import os
import re
import fnmatch
import logging
import importlib

from ..record_types import EquipmentRecord, ConnectionRecord

_logger = logging.getLogger(__name__)

_registry = []


class _Resource(object):

    def __init__(self, manufacturer, model, flags, cls):
        self.manufacturer = re.compile(manufacturer, flags)
        self.model = re.compile(model, flags)
        self.cls = cls

    def is_match(self, record, name):
        if name is not None:
            return self.cls.__name__ == name
        if not self.manufacturer or not self.model:
            return False
        if not self.manufacturer.search(record.manufacturer):
            return False
        return self.model.search(record.model)


def register(manufacturer, model, flags=0):
    """Use as a decorator to register a resource class.

    Parameters
    ----------
    manufacturer : :class:`str`
        The name of the manufacturer. Can be a regex pattern.
    model : :class:`str`
        The model number of the equipment. Can be a regex pattern.
    flags : :class:`int`, optional
        The flags to use for the regex pattern.
    """
    def cls(obj):
        _registry.append(_Resource(manufacturer, model, flags, obj))
        _logger.debug('added {} to the registry'.format(obj))
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
    if not isinstance(record, (ConnectionRecord, EquipmentRecord)):
        raise TypeError('Must pass in an EquipmentRecord or a ConnectionRecord')
    if isinstance(record, EquipmentRecord):
        record = record.connection
    for resource in _registry:
        if resource.is_match(record, record.properties.get('resource_class_name')):
            return resource.cls
    return None


# import all submodules to register all resources in the subpackages
for root, dirs, files in os.walk(os.path.dirname(__file__)):
    root_pkg = __name__ + root.replace(os.path.sep, '.').split(__name__)[1]
    for filename in fnmatch.filter(files, '*.py'):  # ignore .pyc files
        if not filename == '__init__.py':  # these files get imported automatically
            importlib.import_module(root_pkg + '.' + filename[:-3])


from .avantes import Avantes
from .nkt import NKT
from .princeton_instruments import PrincetonInstruments
