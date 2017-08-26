"""
Exceptions used by MSL-Equipment.
"""


class MSLConnectionError(IOError):
    """Base class for all MSL :class:`~.connection.Connection` exceptions."""


class BenthamError(MSLConnectionError):
    """Exception for equipment from Bentham."""


class CMIError(MSLConnectionError):
    """Exception for equipment from the Czech Metrology Institute."""


class PicoTechError(MSLConnectionError):
    """Exception for equipment from Pico Technology."""


class ThorlabsError(MSLConnectionError):
    """Exception for equipment from Thorlabs."""
