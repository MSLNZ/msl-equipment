"""
Exceptions used by MSL-Equipment.
"""


class MSLConnectionError(IOError):
    """Base class for all MSL :class:`~.connection.Connection` exceptions."""


class MSLTimeoutError(MSLConnectionError):
    """A timeout exception for I/O operations."""


class ResourceClassNotFound(MSLConnectionError):
    """Exception if a resource class cannot be found to connect to the equipment."""

    def __init__(self, record):
        msg = 'Cannot find a resource class for {}\n' \
              'If you know that a resource class exists then define a ' \
              '"resource_class_name" property\nin the Connection Database ' \
              'with the name of the resource class as the property value '.format(record)
        super(ResourceClassNotFound, self).__init__(msg)


class AvantesError(MSLConnectionError):
    """Exception for equipment from Avantes."""


class BenthamError(MSLConnectionError):
    """Exception for equipment from Bentham."""


class CMIError(MSLConnectionError):
    """Exception for equipment from the Czech Metrology Institute."""


class OmegaError(MSLConnectionError):
    """Exception for equipment from OMEGA."""


class OptoSigmaError(MSLConnectionError):
    """Exception for equipment from OptoSigma."""


class PicoTechError(MSLConnectionError):
    """Exception for equipment from Pico Technology."""


class ThorlabsError(MSLConnectionError):
    """Exception for equipment from Thorlabs."""
