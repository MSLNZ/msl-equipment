"""Exception classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import logger

if TYPE_CHECKING:
    from .schema import Interface


class MSLConnectionError(OSError):
    """Base class for connection-related exceptions."""

    def __init__(self, interface: Interface, message: str) -> None:
        """Base class for connection-related exceptions.

        Args:
            interface: An interface subclass.
            message: A message to append to the generic error message.
        """
        logger.error("%r %s", interface, message)
        super().__init__(f"{interface!r}\n{message}")


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


class GPIBLibraryError(OSError):
    """Exception from the GPIB library."""

    def __init__(self, *, message: str, name: str = "", ibsta: int = 0, iberr: int = 0) -> None:
        """Exception from the GPIB library.

        Args:
            message: The error message.
            name: The GPIB function name.
            ibsta: The status value.
            iberr: The error code.
        """
        msg = message if not name else f"{message} [{name}(), ibsta:{hex(ibsta)}, iberr:{hex(iberr)}]"
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
