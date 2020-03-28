"""
Simulate a connection to the equipment.
"""
import os
import re
import random
import importlib

from .connection import Connection
from .utils import logger

_backtick_regex = re.compile(r'`(.+?)`')


class ConnectionDemo(Connection):

    def __init__(self, record, cls):
        """Simulate a connection to the equipment.

        Establishing a connection in demo mode is useful when developing a
        program and the equipment is not physically connected to a computer.

        A custom :ref:`logging level <levels>` is used for logging messages with a
        connection in demo mode. The ``logging.DEMO`` :ref:`logging level <levels>`
        is set to be between ``logging.INFO`` and ``logging.WARNING``.

        The returned data type is determined from the docstring of the called method.
        For example, if ``:rtype: int`` then an :class:`int` is returned or if
        ``:rtype: int, float`` then an :class:`int` and a :class:`float` are returned.
        Although the expected data type is returned the value(s) of the returned object
        is randomly generated. The docstring must be in either the reStructuredText_ or
        NumPy_ format.

        Do not instantiate this class directly. Use the
        :meth:`record.connect(demo=True) <.record_types.EquipmentRecord.connect>` method
        to connect to the equipment in demo mode or set :attr:`~.config.Config.DEMO_MODE`
        to be :data:`True` in the :ref:`configuration-file` to open all connections
        in demo mode.

        .. _reStructuredText: https://www.python.org/dev/peps/pep-0287/
        .. _Numpy: https://numpydoc.readthedocs.io/en/latest/

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        cls : :class:`.Connection`
            A :class:`.Connection` subclass (that has **NOT** been instantiated).
        """
        super(ConnectionDemo, self).__init__(record)
        self._connection_class = cls
        logger.demo('Connected to {} in DEMO mode'.format(record.connection))

    def disconnect(self):
        """Log a disconnection from the equipment."""
        logger.demo('Disconnected from {} in DEMO mode'.format(self.equipment_record.connection))

    def __getattr__(self, name):
        """Used for simulating method calls"""
        self._docstring = getattr(self._connection_class, name).__doc__
        if self._docstring is None:
            self._docstring = ''

        def generic_method(*args, **kwargs):
            params = ', '.join(map(str, args))
            for key, value in kwargs.items():
                params += ', {}={}'.format(key, value)
            logger.demo('{}.{}({})'.format(self._connection_class.__name__, name, params))
            return self._return_types()
        return generic_method

    def _return_types(self):
        """Parses a docstring to determine the return types."""
        int_range = (0, 10)
        list_size = 10
        types = self._find_return_types()

        out = []
        for t in types:
            m = re.findall(_backtick_regex, t)
            if m:
                t = ' of '.join(m)

            t = t.replace('~', '')

            if t == 'bool':
                out.append(random.random() > 0.5)
            elif t == 'str':
                out.append('demo:{}'.format(self.equipment_record))
            elif t == 'bytes':
                out.append(bytes('demo:{}'.format(self.equipment_record).encode('utf-8')))
            elif t == 'int':
                out.append(random.randint(*int_range))
            elif t == 'float':
                out.append(random.random())
            elif t == 'list of bool':
                out.append([random.random() > 0.5 for _ in range(list_size)])
            elif t == 'list of str':
                out.append([c for c in str(self.equipment_record)])
            elif t == 'list of bytes':
                out.append([bytes(c.encode('utf-8')) for c in str(self.equipment_record)])
            elif t == 'list of int':
                out.append([random.randint(*int_range) for _ in range(list_size)])
            elif t == 'list of float':
                out.append([random.random() for _ in range(list_size)])
            elif t.startswith('list of .'):
                obj = self._get_object(t[8:])
                if obj is not None:
                    out.append([obj])
            elif 'list' in t:
                out.append([])
            elif t == 'dict of bool':
                out.append({'demo': random.random() > 0.5})
            elif t == 'dict of str':
                out.append({'demo': str(self.equipment_record)})
            elif t == 'dict of bytes':
                out.append({'demo': bytes(str(self.equipment_record).encode('utf-8'))})
            elif t == 'dict of int':
                out.append({'demo': random.randint(*int_range)})
            elif t == 'dict of float':
                out.append({'demo': random.random()})
            elif t.startswith('dict of .'):
                obj = self._get_object(t[8:])
                if obj is not None:
                    out.append({'demo': obj})
            elif 'dict' in t:
                out.append({})
            elif t.startswith('.'):  # then it is an object
                obj = self._get_object(t)
                if obj is not None:
                    out.append(obj)

        if len(out) == 0:
            return None
        elif len(out) == 1:
            return out[0]
        else:
            return tuple(out)

    def _find_return_types(self):
        """Returns a list of strings of return types"""
        types = []
        lines = [line.rstrip() for line in self._docstring.splitlines() if line.strip()]
        i, n = 0, len(lines)
        while i < n:
            if ':rtype:' in lines[i]:
                types.append(lines[i].split(':rtype:')[1].strip())
                break
            if lines[i].endswith('Return') or lines[i].endswith('Returns'):
                i += 1
                if lines[i].endswith('-' * len('Return')):
                    indent = len(lines[i]) - len(lines[i].lstrip())
                    i += 1
                    while i < n:
                        if lines[i][indent].isspace():
                            pass  # then this line is part of a description
                        elif lines[i][indent] == '-':
                            break  # then entered a new docstring section
                        elif ' : ' in lines[i]:
                            # then there is a variable name defined before the data type
                            types.append(lines[i].split(' : ')[1])
                        elif not lines[i][indent].isupper():
                            types.append(lines[i].strip())
                        i += 1
            i += 1
        if len(types) == 0 and len(lines) > 0:
            # then maybe the first part of the first line contains the return type
            if ': ' in lines[0]:
                types.append(lines[0].split(': ')[0])
        return types

    def _get_object(self, _type):
        package = os.path.splitext(self._connection_class.__module__)[0]
        name, cls = os.path.splitext(_type)
        try:
            mod = importlib.import_module(name, package)
        except ImportError:
            return None
        _object = getattr(mod, cls[1:])
        try:
            return _object()  # try to initialize it
        except TypeError:
            return _object
