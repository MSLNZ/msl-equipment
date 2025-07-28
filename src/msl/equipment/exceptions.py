"""
Exceptions used by MSL-Equipment.
"""
from __future__ import annotations


class MSLConnectionError(OSError):
    """Base class for all MSL :class:`~.connection.Connection` exceptions."""


class MSLTimeoutError(MSLConnectionError):
    """A timeout exception for I/O operations."""


class ResourceClassNotFound(MSLConnectionError):

    def __init__(self, record):
        """Exception if a resource class cannot be found to connect to the equipment."""
        super().__init__(
            f'Cannot find a resource class for {record}\n'
            f'If you know that a resource class exists, define a '
            f'"resource_class_name" property\nin the Connection '
            f'Database with the name of the resource class as the '
            f'property value.')


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


class GPIBError(MSLConnectionError):

    def __init__(self,
                 message: str,
                 *,
                 name: str = '',
                 ibsta: int = -1,
                 iberr: int = -1) -> None:
        """Exception for equipment that use the GPIB interface.

        :param message: The error message.
        :param name: The GPIB function name.
        :param ibsta: The status value.
        :param iberr: The error code.
        """
        if name:
            msg = f'{message} [{name}(), ibsta:{hex(ibsta)}, iberr:{hex(iberr)}]'
        else:
            msg = message
        super().__init__(msg)


class GreisingerError(MSLConnectionError):
    """Exception for equipment from Greisinger."""


class IsoTechError(MSLConnectionError):
    """Exception for equipment from IsoTech."""


class MKSInstrumentsError(MSLConnectionError):
    """Exception for equipment from MKS Instruments."""


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

class VaisalaError(MSLConnectionError):
    """Exception for equipment from Vaisala."""
