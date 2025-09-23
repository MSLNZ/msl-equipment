"""Custom exceptions for a resource."""

from __future__ import annotations

from msl.equipment import MSLConnectionError


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
