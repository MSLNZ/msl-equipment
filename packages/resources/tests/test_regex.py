# cSpell: ignore Thandar TCLV Koki optroniclabs CNEB
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from msl.equipment import Connection, Equipment
from msl.equipment.resources import (
    BSC,
    EQ99,
    GMH3000,
    ITHX,
    K10CR,
    KDC,
    KSC,
    KST,
    LTS,
    MFF,
    OL756,
    PR4000B,
    PT104,
    PTB330,
    PTU300,
    SHOT702,
    SIA3,
    AvaSpec,
    DataRay,
    FWxx2C,
    MilliK,
    MXSeries,
    OLxxA,
    PicoScope,
    PrincetonInstruments,
    RaicolTEC,
    SuperK,
    TCSeries,
)
from msl.equipment.schema import _find_interface_class  # pyright: ignore[reportPrivateUsage]

if TYPE_CHECKING:
    from msl.equipment import Interface


def find(manufacturer: str, model: str) -> type[Interface]:
    return _find_interface_class(
        Equipment(
            manufacturer=manufacturer,
            model=model,
            connection=Connection(""),
        )
    )


@pytest.mark.parametrize("manufacturer", ["", "XXXXX"])
@pytest.mark.parametrize("model", ["", "XXXXX"])
def test_cannot_find(manufacturer: str, model: str) -> None:
    with pytest.raises(ValueError, match=r"^Cannot determine the interface from the address ''$"):
        _ = find(manufacturer, model)


@pytest.mark.parametrize(
    "manufacturer",
    [
        "Aim & Thurlby Thandar Instruments",
        "Aim    and  Thurlby    Thandar         Instruments",
        "Aim&TTi",
        "aim & tti",
        "Aim and TTi",
        "aim-tti",
        "aim_tti",
        "aim tti",
    ],
)
@pytest.mark.parametrize("model", ["mx100tp", "Mx100tP", "mx180tp", "MX180TP", "mX100Qp", "MX100QP"])
def test_aim_tti_mx_series(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is MXSeries


@pytest.mark.parametrize("manufacturer", ["Avantes", "Avantes USA", "Avantes BV"])
@pytest.mark.parametrize("model", ["", "does not matter!"])
def test_avantes(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is AvaSpec


@pytest.mark.parametrize("manufacturer", ["CMI", "Czech Metrology Institute"])
@pytest.mark.parametrize("model", ["SIA3"])
def test_cmi_sia3(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is SIA3


@pytest.mark.parametrize("manufacturer", ["DataRay", "Data Ray", "Data Ray Inc.", "DataRay Inc."])
@pytest.mark.parametrize("model", ["", "WinCamD", "S-WCD-LCM-C-1310", "BladeCam2-HR"])
def test_dataray(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is DataRay


@pytest.mark.parametrize("manufacturer", ["Electron Dynamics", "Electron Dynamics LTD", "Electron Dynamics Ltd."])
@pytest.mark.parametrize("model", ["TC LV", "TCLV", "TC M", "TCM", "TC M PCB", "TC M Unit", "TC Lite", "TClite"])
def test_electron_dynamics_tc_series(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is TCSeries


@pytest.mark.parametrize(
    "manufacturer",
    ["Energetiq", "ENERGETIQ", "Energetiq Technology, Inc.", "Energetiq Technology Inc", "Energetiq Technology"],
)
@pytest.mark.parametrize("model", ["eq-99", "EQ-99", "eQ-99-MgR", "EQ-99-MGR"])
def test_energetiq_eq99(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is EQ99


@pytest.mark.parametrize("manufacturer", ["Greisinger", "Greisinger, GHM Group", "GHM GROUP - Greisinger"])
@pytest.mark.parametrize("model", ["GMH3710", "GMH3710-GE", "GMH 3710", "GMH 3710-GE"])
def test_greisinger_gmh3000(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is GMH3000


@pytest.mark.parametrize("manufacturer", ["IsoTech", "Isothermal Technology", "Isothermal Technology Limited"])
@pytest.mark.parametrize("model", ["milliK", "millisKanner"])
def test_isotech_millik(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is MilliK


@pytest.mark.parametrize("manufacturer", ["MKS", "mks", "mks instruments", "MKS Instruments"])
@pytest.mark.parametrize("model", ["PR4000B", "pr4000b", "PR4000BF2V2", "PR4000B-does-not-matter"])
def test_mks_pr4000b(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is PR4000B


@pytest.mark.parametrize("manufacturer", ["NKT", "NKT Photonics", "NKTPhotonics"])
@pytest.mark.parametrize("model", ["SuperK", "SuperK FIANIUM", "SuperK EXTREME", "SuperK:whatever"])
def test_nkt_superk(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is SuperK


@pytest.mark.parametrize("manufacturer", ["OMEGA", "omega", "DwyerOmega"])
@pytest.mark.parametrize("model", ["ithx-w3", "ithx-d3", "ithx-sd", "ithx-m", "ithx-w", "ithx-2"])
def test_omega_ithx(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is ITHX


@pytest.mark.parametrize("manufacturer", ["OptoSigma", "Opto Sigma", "SigmaKoki", "Sigma Koki Co. LTD"])
@pytest.mark.parametrize("model", ["SHOT-702"])
def test_optosigma_shot702(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is SHOT702


@pytest.mark.parametrize(
    "manufacturer",
    ["Optronic Laboratories", "Optronic Laboratories, Inc.", "Optronic Laboratories Inc", "Optronic", "optroniclabs"],
)
@pytest.mark.parametrize("model", ["756", "OL756", "OL 756"])
def test_optronic_labs_ol756(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is OL756


@pytest.mark.parametrize(
    "manufacturer",
    ["Optronic Laboratories", "Optronic Laboratories, Inc.", "Optronic Laboratories Inc", "Optronic", "optroniclabs"],
)
@pytest.mark.parametrize("model", ["OL 83a", "16a", "OL65A"])
def test_optronic_labs_olxxa(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is OLxxA


@pytest.mark.parametrize(
    "manufacturer",
    ["Pico Tech", "Pico Technologies", "Pico Technology", "Pico Technology Ltd."],
)
@pytest.mark.parametrize(
    "model",
    [
        "PicoScope 2104A",
        "2205A",
        "2207B MSO",
        "3203D",
        "PicoScope 5242A",
        "5242A",
        "5243B",
        "5244B",
        "5444B",
        "5242D",
        "6402C",
    ],
)
def test_picotech_picoscope(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is PicoScope


@pytest.mark.parametrize(
    "manufacturer",
    ["Pico Tech", "Pico Technologies", "Pico Technology", "Pico Technology Ltd."],
)
@pytest.mark.parametrize("model", ["PT-104", "PT104"])
def test_picotech_pt104(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is PT104


@pytest.mark.parametrize("manufacturer", ["Princeton Instruments", "Teledyne Princeton Instruments"])
@pytest.mark.parametrize("model", ["", "does not matter!"])
def test_princeton_instruments(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is PrincetonInstruments


@pytest.mark.parametrize(
    "manufacturer", ["Raicol", "Raicol Crystals", "Raicol Crystals Ltd.", "Raicol Crystals Limited"]
)
@pytest.mark.parametrize("model", ["TEC", "TEC20-60", "TEC 20 - 60"])
def test_raicol_tec(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is RaicolTEC


@pytest.mark.parametrize("manufacturer", ["Thorlabs", "Thorlabs Inc."])
@pytest.mark.parametrize("model", ["BSC201", "BSC202", "BSC203"])
def test_thorlabs_bsc(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is BSC


@pytest.mark.parametrize("manufacturer", ["Thorlabs", "Thorlabs Inc."])
@pytest.mark.parametrize("model", ["FW102C", "FW102CNEB", "FW212C", "FW212CNEB"])
def test_thorlabs_fwxx2(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is FWxx2C


@pytest.mark.parametrize("manufacturer", ["Thorlabs", "Thorlabs Inc."])
@pytest.mark.parametrize("model", ["K10CR", "K10CR1/M", "K10CR2", "K10CR2/M"])
def test_thorlabs_k10cr(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is K10CR


@pytest.mark.parametrize("manufacturer", ["Thorlabs", "Thorlabs Inc."])
@pytest.mark.parametrize("model", ["KDC101"])
def test_thorlabs_kdc(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is KDC


@pytest.mark.parametrize("manufacturer", ["Thorlabs", "Thorlabs Inc."])
@pytest.mark.parametrize("model", ["KSC101"])
def test_thorlabs_ksc(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is KSC


@pytest.mark.parametrize("manufacturer", ["Thorlabs", "Thorlabs Inc."])
@pytest.mark.parametrize("model", ["KST101", "KST201"])
def test_thorlabs_kst(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is KST


@pytest.mark.parametrize("manufacturer", ["Thorlabs", "Thorlabs Inc."])
@pytest.mark.parametrize(
    "model", ["LTS150", "LTS150/M", "LTS300", "LTS300/M", "LTS450C", "LTS450C/M", "LTS600C", "LTS600C/M"]
)
def test_thorlabs_lts(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is LTS


@pytest.mark.parametrize("manufacturer", ["Thorlabs", "Thorlabs Inc."])
@pytest.mark.parametrize("model", ["MFF101", "MFF102", "MFF101/M", "MFF102/M"])
def test_thorlabs_mff(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is MFF


@pytest.mark.parametrize("manufacturer", ["Vaisala", "VAISALA"])
@pytest.mark.parametrize("model", ["PTB330", "PTB330TS"])
def test_vaisala_ptb330(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is PTB330


@pytest.mark.parametrize("manufacturer", ["Vaisala", "VAISALA"])
@pytest.mark.parametrize("model", ["PTU300", "PTU301", "PTU303", "PTU307", "PTU30T"])
def test_vaisala_ptu300(manufacturer: str, model: str) -> None:
    assert find(manufacturer, model) is PTU300
