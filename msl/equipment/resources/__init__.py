"""
MSL resources for connecting to equipment.
"""
import os
import re
import fnmatch
import logging
import importlib

_logger = logging.getLogger(__name__)

_registry = []


class _Resource(object):

    def __init__(self, manufacturer, model, cls):
        self.man = manufacturer
        self.mod = model
        self.cls = cls

    def is_match(self, record, name):
        if name:
            return self.cls.__name__ == name
        if not self.man or not self.mod:
            return False
        return re.search(self.man, record.manufacturer, re.I) and re.search(self.mod, record.model, re.I)


def register(manufacturer='', model=''):
    """Use as a decorator to register a resource class.

    Parameters
    ----------
    manufacturer : :class:`str`
        The name of the manufacturer. Can be regex pattern.
    model : :class:`str`
        The model number. Can be regex pattern.
    """
    def cls(obj):
        _registry.append(_Resource(manufacturer, model, obj))
        _logger.debug('added {} to registry'.format(obj))
        return obj
    return cls


def find_resource_class(record):
    """Find the resource class for this `record`, if a class exists.

    Parameters
    ----------
    record : :class:`~msl.equipment.record_types.ConnectionRecord`
        A connection record from a :ref:`connection_database`. If the
        :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        attribute of the `record` contains a ``resource_class_name`` key who's
        value is equal to the name of a resource class it forces this resource
        class to be returned, provided that a resource class with the requested
        name exists.

    Returns
    -------
    A :class:`~msl.equipment.connection.Connection` subclass or :obj:`None` if
    a resource class cannot be found.
    """
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

from .omega import iTHX
