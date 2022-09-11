"""
Exceptions used by MSL-Equipment.
"""


class MSLConnectionError(OSError):
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


class AimTTiError(MSLConnectionError):
    """Exception for equipment from Aim and Thurlby Thandar Instruments."""


class AvantesError(MSLConnectionError):
    """Exception for equipment from Avantes."""


class BenthamError(MSLConnectionError):
    """Exception for equipment from Bentham."""


class CMIError(MSLConnectionError):
    """Exception for equipment from the Czech Metrology Institute."""


class DataRayError(MSLConnectionError):
    """Exception for equipment from DataRay Inc."""


class EnergetiqError(MSLConnectionError):
    """Exception for equipment from Energetiq."""


class MKSInstrumentsError(MSLConnectionError):
    """Exception for equipment from MKS Instruments."""
    pass


class NKTError(MSLConnectionError):
    """Exception for equipment from NKT Photonics."""


class OmegaError(MSLConnectionError):
    """Exception for equipment from OMEGA."""


class OptoSigmaError(MSLConnectionError):
    """Exception for equipment from OptoSigma."""


class OptronicLaboratoriesError(MSLConnectionError):
    """Exception for equipment from Optronic Laboratories."""


class PicoTechError(MSLConnectionError):
    """Exception for equipment from Pico Technology."""


class PrincetonInstrumentsError(MSLConnectionError):
    """Exception for equipment from Princeton Instruments."""


class RaicolCrystalsError(MSLConnectionError):
    """Exception for equipment from Raicol Crystals."""


class ThorlabsError(MSLConnectionError):
    """Exception for equipment from Thorlabs."""
