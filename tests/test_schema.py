from __future__ import annotations

import re
import sys
from datetime import date, datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import TYPE_CHECKING, cast
from xml.etree.ElementTree import XML, Element, ElementTree, tostring

import numpy as np
import pytest
from GTC import (  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
    pr,  # pyright: ignore[reportUnknownVariableType]
    ureal,  # pyright: ignore[reportUnknownVariableType]
)

from msl.equipment import (
    AcceptanceCriteria,
    Accessories,
    Adjustment,
    Alteration,
    CapitalExpenditure,
    Competency,
    Component,
    Conditions,
    CVDEquation,
    Deserialised,
    DigitalFormat,
    DigitalReport,
    Equation,
    Equipment,
    Evaluable,
    File,
    Financial,
    Firmware,
    IssuingLaboratory,
    Maintenance,
    Measurand,
    PerformanceCheck,
    QualityManual,
    Range,
    ReferenceMaterials,
    Register,
    Report,
    Specifications,
    SpecifiedRequirements,
    Status,
    Table,
)
from msl.equipment.schema import Latest, _future_date, _Indent, connections  # pyright: ignore[reportPrivateUsage]

if TYPE_CHECKING:
    from numpy.typing import ArrayLike

    from msl.equipment.schema import Any


def test_alteration() -> None:
    text = b'<alteration date="2024-10-16" performedBy="Chris, MSL">Replace blown op-amp with LMP7721</alteration>'

    a = Alteration.from_xml(XML(text))
    assert a.date == date(2024, 10, 16)
    assert a.details == "Replace blown op-amp with LMP7721"
    assert a.performed_by == "Chris, MSL"

    e = a.to_xml()
    assert e.tag == "alteration"
    assert e.attrib == {"date": "2024-10-16", "performedBy": "Chris, MSL"}
    assert e.text == "Replace blown op-amp with LMP7721"
    assert tostring(e) == text


def test_alteration_no_details_nor_performed_by() -> None:
    # This element fails XSD validation, but it is valid Python
    e = Element("ignored", attrib={"date": "2025-03-31", "performedBy": ""})
    assert e.text is None

    a = Alteration.from_xml(e)
    assert a.date == date(2025, 3, 31)
    assert a.details == ""
    assert a.performed_by == ""

    e = a.to_xml()
    assert e.tag == "alteration"
    assert e.attrib == {"date": "2025-03-31", "performedBy": ""}
    assert e.text == ""
    assert tostring(e) == b'<alteration date="2025-03-31" performedBy="" />'


def test_alteration_from_xml_invalid_date() -> None:
    e = Element("alteration", attrib={"date": "31-03-2025"})
    with pytest.raises(ValueError, match=r"Invalid isoformat string"):
        _ = Alteration.from_xml(e)


def test_alteration_from_xml_date_missing() -> None:
    with pytest.raises(KeyError, match=r"date"):
        _ = Alteration.from_xml(Element("alteration"))


def test_alteration_from_xml_performed_by_missing() -> None:
    with pytest.raises(KeyError, match=r"performedBy"):
        _ = Alteration.from_xml(Element("alteration", date="2025-03-31"))


@pytest.mark.parametrize(
    ("cls", "tag"),
    [
        (Specifications, "specifications"),
        (SpecifiedRequirements, "specifiedRequirements"),
        (ReferenceMaterials, "referenceMaterials"),
        (Accessories, "accessories"),
        (Conditions, "conditions"),
        (AcceptanceCriteria, "acceptanceCriteria"),
    ],
)
def test_any_element_type_subclass(cls: type[Any], tag: str) -> None:
    a = cls()
    assert len(a) == 0
    assert a.attrib == {}
    assert a.tag == tag
    assert a.tail is None
    assert a.text is None

    a = cls.from_xml(XML('<ignored one="1"/>'))
    assert len(a) == 0
    assert a.attrib == {"one": "1"}
    assert a.tag == tag
    assert a.tail is None
    assert a.text is None

    a = cls(foo="bar")
    a.text = "baz"
    a.append(XML('<a><notIgnored seven="7">7</notIgnored>tail</a>'))
    assert len(a) == 1
    assert a.attrib == {"foo": "bar"}
    assert a.tag == tag
    assert a.tail is None
    assert a.text == "baz"
    assert a[0].attrib == {}
    assert a[0].tag == "a"
    assert a[0].tail is None
    assert a[0].text is None
    assert len(a[0]) == 1
    assert a[0][0].attrib == {"seven": "7"}
    assert a[0][0].tag == "notIgnored"
    assert a[0][0].tail == "tail"
    assert a[0][0].text == "7"


@pytest.mark.parametrize("price", ["1000000", "1e6", "1000e3", "1000000.00000"])
def test_capital_expenditure_price_without_decimal(price: str) -> None:
    text = (
        f"<capitalExpenditure>"
        f"<assetNumber/>"
        f"<depreciationEndYear>2030</depreciationEndYear>"
        f'<price currency="NZD">{price}</price>'
        f"</capitalExpenditure>"
    )

    ce = CapitalExpenditure.from_xml(XML(text))
    assert ce.asset_number == ""
    assert ce.depreciation_end_year == 2030
    assert ce.price == 1e6
    assert ce.currency == "NZD"

    assert tostring(ce.to_xml()) == (
        b"<capitalExpenditure>"
        b"<assetNumber />"
        b"<depreciationEndYear>2030</depreciationEndYear>"
        b'<price currency="NZD">1000000</price>'
        b"</capitalExpenditure>"
    )


def test_capital_expenditure_price_with_decimal() -> None:
    text = (
        "<capitalExpenditure>"
        "<assetNumber/>"
        "<depreciationEndYear>2030</depreciationEndYear>"
        '<price currency="NZD">10000000.01</price>'
        "</capitalExpenditure>"
    )

    ce = CapitalExpenditure.from_xml(XML(text))
    assert ce.asset_number == ""
    assert ce.depreciation_end_year == 2030
    assert ce.price == 10000000.01
    assert ce.currency == "NZD"

    assert tostring(ce.to_xml()) == (
        b"<capitalExpenditure>"
        b"<assetNumber />"
        b"<depreciationEndYear>2030</depreciationEndYear>"
        b'<price currency="NZD">10000000.01</price>'
        b"</capitalExpenditure>"
    )


def test_financial_empty() -> None:
    text = b"<financial />"
    f = Financial.from_xml(XML(text))
    assert f.capital_expenditure is None
    assert f.warranty_expiration_date is None
    assert f.purchase_year == 0
    assert tostring(f.to_xml()) == text


def test_financial_all() -> None:
    text = (
        b"<financial>"
        b"<capitalExpenditure>"
        b"<assetNumber>7265817</assetNumber>"
        b"<depreciationEndYear>2030</depreciationEndYear>"
        b'<price currency="NZD">1000000</price>'
        b"</capitalExpenditure>"
        b"<purchaseYear>2025</purchaseYear>"
        b"<warrantyExpirationDate>2026-08-01</warrantyExpirationDate>"
        b"</financial>"
    )

    f = Financial.from_xml(XML(text))
    assert f.capital_expenditure is not None
    assert f.capital_expenditure.asset_number == "7265817"
    assert f.capital_expenditure.depreciation_end_year == 2030
    assert f.capital_expenditure.price == 1000000.0
    assert f.capital_expenditure.currency == "NZD"
    assert f.warranty_expiration_date == date(2026, 8, 1)
    assert f.purchase_year == 2025
    assert tostring(f.to_xml()) == text


def test_financial_asset_number_empty() -> None:
    text = (
        b"<financial>"
        b"<capitalExpenditure>"
        b"<assetNumber />"
        b"<depreciationEndYear>2052</depreciationEndYear>"
        b'<price currency="CAD">48000</price>'
        b"</capitalExpenditure>"
        b"</financial>"
    )
    f = Financial.from_xml(XML(text))
    assert f.capital_expenditure is not None
    assert f.capital_expenditure.asset_number == ""
    assert f.capital_expenditure.depreciation_end_year == 2052
    assert f.capital_expenditure.price == 48000.0
    assert f.capital_expenditure.currency == "CAD"
    assert f.warranty_expiration_date is None
    assert f.purchase_year == 0
    assert tostring(f.to_xml()) == text


def test_financial_warranty_expiration_date() -> None:
    text = b"<financial><warrantyExpirationDate>2026-08-01</warrantyExpirationDate></financial>"
    f = Financial.from_xml(XML(text))
    assert f.capital_expenditure is None
    assert f.warranty_expiration_date == date(2026, 8, 1)
    assert f.purchase_year == 0
    assert tostring(f.to_xml()) == text


def test_financial_year_purchased() -> None:
    text = b"<financial><purchaseYear>2025</purchaseYear></financial>"
    f = Financial.from_xml(XML(text))
    assert f.capital_expenditure is None
    assert f.warranty_expiration_date is None
    assert f.purchase_year == 2025
    assert tostring(f.to_xml()) == text


@pytest.mark.parametrize("date", ["26-08-01", "", "Sunday"])
def test_financial_invalid_date(date: str) -> None:
    text = f"<financial><warrantyExpirationDate>{date}</warrantyExpirationDate></financial>"
    with pytest.raises(ValueError, match=r"Invalid isoformat string"):
        _ = Financial.from_xml(XML(text))


@pytest.mark.parametrize("year", ["26-08-01", "2k"])
def test_financial_invalid_year(year: str) -> None:
    text = f"<financial><purchaseYear>{year}</purchaseYear></financial>"
    with pytest.raises(ValueError, match=r"invalid literal"):
        _ = Financial.from_xml(XML(text))


def test_firmware() -> None:
    text = b'<version date="2025-01-14">1.4.0b</version>'
    f = Firmware.from_xml(XML(text))
    assert f.version == "1.4.0b"
    assert f.date == date(2025, 1, 14)
    assert tostring(f.to_xml()) == text


def test_firmware_from_xml_no_date() -> None:
    with pytest.raises(KeyError, match=r"date"):
        _ = Firmware.from_xml(Element("not used"))


@pytest.mark.parametrize("date", ["26-08-01", "", "Sunday"])
def test_firmware_from_xml_invalid_date(date: str) -> None:
    with pytest.raises(ValueError, match=r"Invalid isoformat string"):
        _ = Firmware.from_xml(Element("not used", date=date))


def test_maintenance_empty() -> None:
    text = b"<maintenance />"
    m = Maintenance.from_xml(XML(text))
    assert len(m.planned) == 0
    assert len(m.completed) == 0
    assert tostring(m.to_xml()) == text


def test_maintenance_two_planned_none_completed() -> None:
    text = (
        b"<maintenance>"
        b"<planned>"
        b'<task dueDate="2024-12-01">Refill helium gas</task>'
        b'<task dueDate="2025-05-15" performedBy="Company X">Service laser</task>'
        b"</planned>"
        b"<completed />"
        b"</maintenance>"
    )
    m = Maintenance.from_xml(XML(text))
    assert len(m.planned) == 2
    assert m.planned[0].due_date == date(2024, 12, 1)
    assert m.planned[0].performed_by == ""
    assert m.planned[0].task == "Refill helium gas"
    assert m.planned[1].due_date == date(2025, 5, 15)
    assert m.planned[1].performed_by == "Company X"
    assert m.planned[1].task == "Service laser"
    assert len(m.completed) == 0
    assert tostring(m.to_xml()) == text


def test_maintenance_one_planned_one_completed() -> None:
    text = (
        b"<maintenance>"
        b"<planned>"
        b'<task dueDate="2025-05-15" performedBy="Company X">Service laser</task>'
        b"</planned>"
        b"<completed>"
        b'<task dueDate="2024-12-01" completedDate="2024-12-02" performedBy="Tom, MSL">Refill helium gas</task>'
        b"</completed>"
        b"</maintenance>"
    )
    m = Maintenance.from_xml(XML(text))
    assert len(m.planned) == 1
    assert m.planned[0].due_date == date(2025, 5, 15)
    assert m.planned[0].performed_by == "Company X"
    assert m.planned[0].task == "Service laser"
    assert len(m.completed) == 1
    assert m.completed[0].due_date == date(2024, 12, 1)
    assert m.completed[0].completed_date == date(2024, 12, 2)
    assert m.completed[0].performed_by == "Tom, MSL"
    assert m.completed[0].task == "Refill helium gas"
    assert tostring(m.to_xml()) == text


def test_maintenance_none_planned_two_completed() -> None:
    text = (
        b"<maintenance>"
        b"<planned />"
        b"<completed>"
        b'<task dueDate="2025-05-15" completedDate="2025-05-15" performedBy="Company X">Service laser</task>'
        b'<task dueDate="2024-12-01" completedDate="2024-12-02" performedBy="Tom, MSL">Refill helium gas</task>'
        b"</completed>"
        b"</maintenance>"
    )
    m = Maintenance.from_xml(XML(text))
    assert len(m.planned) == 0
    assert len(m.completed) == 2
    assert m.completed[0].due_date == date(2025, 5, 15)
    assert m.completed[0].completed_date == date(2025, 5, 15)
    assert m.completed[0].performed_by == "Company X"
    assert m.completed[0].task == "Service laser"
    assert m.completed[1].due_date == date(2024, 12, 1)
    assert m.completed[1].completed_date == date(2024, 12, 2)
    assert m.completed[1].performed_by == "Tom, MSL"
    assert m.completed[1].task == "Refill helium gas"
    assert tostring(m.to_xml()) == text


def test_quality_manual_empty() -> None:
    text = b"<qualityManual />"
    qm = QualityManual.from_xml(XML(text))
    assert len(qm.accessories) == 0
    assert qm.accessories.attrib == {}
    assert qm.documentation == ""
    assert qm.financial == Financial()
    assert qm.personnel_restrictions == ""
    assert qm.service_agent == ""
    assert len(qm.technical_procedures) == 0
    assert tostring(qm.to_xml()) == text


def test_quality_manual_accessories() -> None:
    text = (
        b"<qualityManual>"
        b'<accessories a="a">Any text'
        b'<child b="b">More info.</child>Sneak tail.'
        b'<nested-1 c="c"><nested-2 d="d">Text</nested-2></nested-1>'
        b"Some tail text"
        b"</accessories>"
        b"</qualityManual>"
    )
    qm = QualityManual.from_xml(XML(text))
    assert qm.accessories.tag == "accessories"
    assert qm.accessories.attrib == {"a": "a"}
    assert qm.accessories.text == "Any text"
    assert len(qm.accessories) == 2
    assert qm.accessories[0].tag == "child"
    assert qm.accessories[0].attrib == {"b": "b"}
    assert qm.accessories[0].text == "More info."
    assert qm.accessories[0].tail == "Sneak tail."
    assert qm.accessories[1].tag == "nested-1"
    assert qm.accessories[1].attrib == {"c": "c"}
    assert qm.accessories[1].text is None
    assert qm.accessories[1].tail == "Some tail text"
    assert len(qm.accessories[1]) == 1
    assert qm.accessories[1][0].tag == "nested-2"
    assert qm.accessories[1][0].attrib == {"d": "d"}
    assert qm.accessories[1][0].text == "Text"
    assert qm.accessories[1][0].tail is None
    assert qm.documentation == ""
    assert qm.financial == Financial()
    assert qm.personnel_restrictions == ""
    assert qm.service_agent == ""
    assert len(qm.technical_procedures) == 0
    assert tostring(qm.to_xml()) == text


def test_quality_manual_documentation() -> None:
    text = b"<qualityManual><documentation>https://link.com</documentation></qualityManual>"
    qm = QualityManual.from_xml(XML(text))
    assert len(qm.accessories) == 0
    assert qm.accessories.attrib == {}
    assert qm.documentation == "https://link.com"
    assert qm.financial == Financial()
    assert qm.personnel_restrictions == ""
    assert qm.service_agent == ""
    assert len(qm.technical_procedures) == 0
    assert tostring(qm.to_xml()) == text


def test_quality_manual_financial() -> None:
    text = (
        b"<qualityManual>"
        b"<financial>"
        b"<capitalExpenditure>"
        b"<assetNumber>abc</assetNumber>"
        b"<depreciationEndYear>1</depreciationEndYear>"
        b'<price currency="NZD">1</price>'
        b"</capitalExpenditure>"
        b"<purchaseYear>2000</purchaseYear>"
        b"</financial>"
        b"</qualityManual>"
    )
    qm = QualityManual.from_xml(XML(text))
    assert len(qm.accessories) == 0
    assert qm.accessories.attrib == {}
    assert qm.documentation == ""
    assert qm.financial.capital_expenditure is not None
    assert qm.financial.capital_expenditure.asset_number == "abc"
    assert qm.financial.capital_expenditure.depreciation_end_year == 1
    assert qm.financial.capital_expenditure.price == 1.0
    assert qm.financial.capital_expenditure.currency == "NZD"
    assert qm.financial.warranty_expiration_date is None
    assert qm.financial.purchase_year == 2000
    assert qm.personnel_restrictions == ""
    assert qm.service_agent == ""
    assert len(qm.technical_procedures) == 0
    assert tostring(qm.to_xml()) == text


def test_quality_manual_personnel_restrictions() -> None:
    text = b"<qualityManual><personnelRestrictions>Light team</personnelRestrictions></qualityManual>"
    qm = QualityManual.from_xml(XML(text))
    assert len(qm.accessories) == 0
    assert qm.accessories.attrib == {}
    assert qm.documentation == ""
    assert qm.financial == Financial()
    assert qm.personnel_restrictions == "Light team"
    assert qm.service_agent == ""
    assert len(qm.technical_procedures) == 0
    assert tostring(qm.to_xml()) == text


def test_quality_manual_service_agent() -> None:
    text = b"<qualityManual><serviceAgent>MSL</serviceAgent></qualityManual>"
    qm = QualityManual.from_xml(XML(text))
    assert len(qm.accessories) == 0
    assert qm.accessories.attrib == {}
    assert qm.documentation == ""
    assert qm.financial == Financial()
    assert qm.personnel_restrictions == ""
    assert qm.service_agent == "MSL"
    assert len(qm.technical_procedures) == 0
    assert tostring(qm.to_xml()) == text


def test_quality_manual_technical_procedures() -> None:
    text = b"<qualityManual><technicalProcedures><id>A</id><id>B</id><id>C.c</id></technicalProcedures></qualityManual>"
    qm = QualityManual.from_xml(XML(text))
    assert len(qm.accessories) == 0
    assert qm.accessories.attrib == {}
    assert qm.documentation == ""
    assert qm.financial == Financial()
    assert qm.personnel_restrictions == ""
    assert qm.service_agent == ""
    assert qm.technical_procedures == ("A", "B", "C.c")
    assert tostring(qm.to_xml()) == text


def test_status_valid() -> None:
    assert Status("Active") == Status.Active
    assert Status["Active"] == Status.Active


def test_status_invalid() -> None:
    with pytest.raises(ValueError, match=r"not a valid Status"):
        _ = Status("Nope")


def test_digital_format_valid() -> None:
    assert DigitalFormat("MSL PDF/A-3") == DigitalFormat.MSL_PDF
    assert DigitalFormat["MSL_PDF"] == DigitalFormat.MSL_PDF


def test_digital_format_invalid() -> None:
    with pytest.raises(ValueError, match=r"not a valid DigitalFormat"):
        _ = DigitalFormat("Nope")


def test_competency() -> None:
    text = (
        b"<competency>"
        b"<worker>Person A.</worker>"
        b"<checker>B</checker>"
        b"<technicalProcedure>value is not checked</technicalProcedure>"
        b"</competency>"
    )
    c = Competency.from_xml(XML(text))
    assert c.worker == "Person A."
    assert c.checker == "B"
    assert c.technical_procedure == "value is not checked"
    assert tostring(c.to_xml()) == text


def test_file_no_comment_nor_url_attributes() -> None:
    text = b"<file><url>whatever</url><sha256>anything</sha256></file>"
    f = File.from_xml(XML(text))
    assert f.url == "whatever"
    assert f.sha256 == "anything"
    assert f.attributes == {}
    assert f.comment == ""
    assert tostring(f.to_xml()) == text


def test_file() -> None:
    text = b'<file comment="hi"><url foo="bar">whatever</url><sha256>anything</sha256></file>'
    f = File.from_xml(XML(text))
    assert f.url == "whatever"
    assert f.sha256 == "anything"
    assert f.attributes == {"foo": "bar"}
    assert f.comment == "hi"
    assert tostring(f.to_xml()) == text


@pytest.mark.parametrize(
    ("url", "scheme"),
    [
        ("filename.xls", ""),
        (":filename.xls", ""),
        (r"C:\filename.xls", ""),
        ("C:", "C"),  # `:` is not followed by `/` or `\`
        ("C:/filename.xls", ""),
        ("C:filename.xls", "C"),
        (r"ab:\filename.xls", "ab"),
        ("file://host/path", "file"),
        ("https://www.measurement.govt.nz/", "https"),
    ],
)
def test_file_scheme(url: str, scheme: str) -> None:
    text = f"<file><url>{url}</url><sha256>anything</sha256></file>"
    f = File.from_xml(XML(text))
    assert f.url == url
    assert f.scheme == scheme


def test_digital_report_no_comment_nor_url_attributes() -> None:
    text = (
        b'<digitalReport format="MSL PDF/A-3" id="Pressure/2025/092">'
        b"<url>reports/2025/job092.pdf</url>"
        b"<sha256>76e4e036da8722b55362912396a01a07bb61e6260c7c4b6150d431e613529a54</sha256>"
        b"</digitalReport>"
    )
    dr = DigitalReport.from_xml(XML(text))
    assert dr.url == "reports/2025/job092.pdf"
    assert dr.format == DigitalFormat.MSL_PDF
    assert dr.id == "Pressure/2025/092"
    assert dr.sha256 == "76e4e036da8722b55362912396a01a07bb61e6260c7c4b6150d431e613529a54"
    assert dr.attributes == {}
    assert dr.comment == ""
    assert tostring(dr.to_xml()) == text


def test_digital_report() -> None:
    text = (
        b'<digitalReport format="PTB DCC" id="Pressure/2025/092" comment="hi">'
        b'<url foo="bar">reports/2025/job092.pdf</url>'
        b"<sha256>76e4e036da8722b55362912396a01a07bb61e6260c7c4b6150d431e613529a54</sha256>"
        b"</digitalReport>"
    )
    dr = DigitalReport.from_xml(XML(text))
    assert dr.url == "reports/2025/job092.pdf"
    assert dr.format == DigitalFormat.PTB_DCC
    assert dr.id == "Pressure/2025/092"
    assert dr.sha256 == "76e4e036da8722b55362912396a01a07bb61e6260c7c4b6150d431e613529a54"
    assert dr.attributes == {"foo": "bar"}
    assert dr.comment == "hi"
    assert tostring(dr.to_xml()) == text


def test_adjustment() -> None:
    text = b'<adjustment date="2024-10-16">Did something</adjustment>'
    a = Adjustment.from_xml(XML(text))
    assert a.date == date(2024, 10, 16)
    assert a.details == "Did something"
    assert tostring(a.to_xml()) == text


def test_adjustment_invalid_date() -> None:
    e = Element("adjustment", attrib={"date": "31-03-2025"})
    with pytest.raises(ValueError, match=r"Invalid isoformat string"):
        _ = Adjustment.from_xml(e)


def test_adjustment_date_missing() -> None:
    with pytest.raises(KeyError, match=r"date"):
        _ = Adjustment.from_xml(Element("adjustment"))


@pytest.mark.parametrize("value", [-99, 99.9, [-1, 0, 1], (10, 9, 8), np.array([[11, -22], [-33, 44]])])
def test_range_bounds_valid(value: float | ArrayLike) -> None:
    r = Range(-100, 100)
    assert r.minimum == -100
    assert r.maximum == 100
    assert r == (-100, 100)
    assert r.check_within_range(value)


@pytest.mark.parametrize("value", [-1, 2e6, [1.001, 2], np.array([[11, -22], [-33, 44]])])
def test_range_bounds_invalid(value: float | ArrayLike) -> None:
    r = Range(0, 1)
    expect = str(value) if isinstance(value, (int, float)) else "sequence"
    with pytest.raises(ValueError, match=f"{expect} is not within the range"):
        _ = r.check_within_range(value)


def test_evaluable_constant() -> None:
    e = Evaluable("0.5/2", ())
    assert e.equation == "0.5/2"
    assert e.ranges == {}
    assert e() == 0.5 / 2


def test_evaluable_constant_broadcasted() -> None:
    expect = 0.5 / 2
    e = Evaluable("0.5/2", ())
    assert e.equation == "0.5/2"
    assert e.ranges == {}
    assert e() == expect
    assert e(x=1) == expect
    assert np.array_equal(e(x=[1]), np.array([expect]))
    assert np.array_equal(e(x=[1, 2, 3]), np.array([expect, expect, expect]))
    assert np.array_equal(e(x=[1, 2, 3], y=8), np.array([expect, expect, expect]))
    assert np.array_equal(e(x=[[1, 2, 3]], y=[[8, 1, 2]]), np.array([[expect, expect, expect]]))

    shape = (5, 4, 3, 2, 1)
    assert np.array_equal(e(x=np.empty(shape)), np.full(shape, fill_value=expect))


def test_evaluable_1d_no_range() -> None:
    e = Evaluable("2*pi*sin(x+0.1) - cos(x/2)", ("x",))
    assert e(x=0.1) == 2 * np.pi * np.sin(0.1 + 0.1) - np.cos(0.1 / 2)


def test_evaluable_1d() -> None:
    e = Evaluable("2*pi*sin(x+0.1) - cos(x/2)", ("x",), ranges={"x": Range(0, 1)})
    assert e(x=0.1) == 2 * np.pi * np.sin(0.1 + 0.1) - np.cos(0.1 / 2)

    # ok to include unused variables
    assert e(x=0.1, y=9.1, z=-0.3) == 2 * np.pi * np.sin(0.1 + 0.1) - np.cos(0.1 / 2)

    expected = 2 * np.pi * np.sin(np.array([0.1, 0.2]) + 0.1) - np.cos(np.array([0.1, 0.2]) / 2)
    assert np.array_equal(e(x=[0.1, 0.2]), expected)

    with pytest.raises(ValueError, match=r"-1.0 is not within the range"):
        _ = e(x=-1)

    with pytest.raises(NameError, match=r"'x' is not defined"):
        _ = e()

    x = -1
    expect = 2 * np.pi * np.sin(x + 0.1) - np.cos(x / 2)
    assert e(x=x, check_range=False) == expect
    assert e(x=x, check_range=False, this_kwarg_is_ignored=np.nan) == expect


def test_evaluable_2d() -> None:
    eqn = "rh - 7.131e-2 - 3.951e-2*rh + 3.412e-4*pow(rh,2) + 2.465e-3*t + 1.034e-3*rh*t - 5.297e-6*pow(rh,2)*t"
    ranges = {"rh": Range(30, 80), "t": Range(15, 25)}
    e = Evaluable(eqn, ("rh", "t"), ranges=ranges)
    rh, t = 45, 21.3
    expect = (
        rh
        - 7.131e-2
        - 3.951e-2 * rh
        + 3.412e-4 * pow(rh, 2)
        + 2.465e-3 * t
        + 1.034e-3 * rh * t
        - 5.297e-6 * pow(rh, 2) * t
    )
    assert e(rh=rh, t=t) == expect

    with pytest.raises(ValueError, match=r"-1.0 is not within the range"):
        _ = e(rh=-1, t=20)
    with pytest.raises(ValueError, match=r"200.0 is not within the range"):
        _ = e(rh=50, t=200)


def test_equation_value_uncertainty_unit() -> None:
    text = (
        b"<equation>"
        b'<value variables="x">1+x</value>'
        b'<uncertainty variables="">0.5/2</uncertainty>'
        b"<unit>C</unit>"
        b"<ranges />"
        b"</equation>"
    )
    e = Equation.from_xml(XML(text))
    assert e.value.equation == "1+x"
    assert e.value.variables == ("x",)
    assert e.value.ranges == {}
    assert e.value(x=0) == 1
    assert e.uncertainty.equation == "0.5/2"
    assert e.uncertainty.variables == ()
    assert e.uncertainty.ranges == {}
    assert e.uncertainty() == 0.5 / 2
    assert e.unit == "C"
    assert np.isinf(e.degree_freedom)
    assert e.comment == ""
    assert tostring(e.to_xml()) == text


def test_equation() -> None:
    text = (
        b'<equation comment="3D">'
        b'<value variables="x y zebra">1 + x + y + zebra</value>'
        b'<uncertainty variables="x y zebra">x/2 + y/2 + zebra/10</uncertainty>'
        b"<unit>%rh</unit>"
        b"<ranges>"
        b'<range variable="x"><minimum>0.0</minimum><maximum>1.0</maximum></range>'
        b'<range variable="y"><minimum>0.1</minimum><maximum>0.9</maximum></range>'
        b'<range variable="zebra"><minimum>0.2</minimum><maximum>0.8</maximum></range>'
        b"</ranges>"
        b"<degreeFreedom>100.2</degreeFreedom>"
        b"</equation>"
    )
    e = Equation.from_xml(XML(text))
    assert e.value.equation == "1 + x + y + zebra"
    assert e.value.variables == ("x", "y", "zebra")
    assert e.value.ranges == {"x": Range(0, 1), "y": Range(0.1, 0.9), "zebra": Range(0.2, 0.8)}
    assert e.value(x=0.1, y=0.2, zebra=0.3) == 1 + 0.1 + 0.2 + 0.3
    assert e.uncertainty.equation == "x/2 + y/2 + zebra/10"
    assert e.uncertainty.variables == ("x", "y", "zebra")
    assert e.uncertainty.ranges == {"x": Range(0, 1), "y": Range(0.1, 0.9), "zebra": Range(0.2, 0.8)}
    assert e.uncertainty(x=0.1, y=0.2, zebra=0.3) == 0.1 / 2 + 0.2 / 2 + 0.3 / 10
    assert e.unit == "%rh"
    assert e.degree_freedom == 100.2
    assert e.comment == "3D"
    assert tostring(e.to_xml()) == text


def test_serialised_gtc_xml() -> None:
    ar = pr.Archive()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    ar.add(x=ureal(1, 0.1))  # pyright: ignore[reportUnknownMemberType]

    dumped: str = pr.dumps_xml(ar, encoding="unicode")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    text = f"<serialised>{dumped}</serialised>"

    d = Deserialised.from_xml(XML(text))
    assert d.comment == ""
    assert isinstance(d.value, pr.Archive)  # pyright: ignore[reportUnknownMemberType]
    assert d.value["x"].x == 1
    assert d.value["x"].u == 0.1
    assert np.isinf(d.value["x"].df)
    assert tostring(d.to_xml()).decode() == text


def test_serialised_gtc_json() -> None:
    ar = pr.Archive()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    ar.add(x=ureal(1, 0.1))  # pyright: ignore[reportUnknownMemberType]

    dumped_json: str = pr.dumps_json(ar)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    text_json = f'<serialised comment="GTC 4ever"><gtcArchiveJSON>{dumped_json}</gtcArchiveJSON></serialised>'

    d = Deserialised.from_xml(XML(text_json))
    assert d.comment == "GTC 4ever"
    assert isinstance(d.value, pr.Archive)  # pyright: ignore[reportUnknownMemberType]
    assert d.value["x"].x == 1
    assert d.value["x"].u == 0.1
    assert np.isinf(d.value["x"].df)

    dumped_xml: str = pr.dumps_xml(ar, encoding="unicode")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    text_xml = f'<serialised comment="GTC 4ever">{dumped_xml}</serialised>'
    assert tostring(d.to_xml()).decode() == text_xml


def test_serialised_unhandled() -> None:
    text = b'<serialised comment="Not handled"><unhandled>some serialised text</unhandled></serialised>'
    d = Deserialised.from_xml(XML(text))
    assert d.comment == "Not handled"
    assert isinstance(d.value, Element)
    assert tostring(d.to_xml()) == text


def test_table() -> None:
    text = """
    <table comment="Spectral Irradiance">
        <type> int    , double,           double, bool, string </type>
        <unit> nm,   W/m^2,      W/m^2, ,   </unit>
        <header> Wavelength         , Irradiance     ,u(Irradiance), Is Good?, Letter</header>
        <data>
            250, 0.01818, 0.02033, True, A
            300, 0.18478, 0.01755, true,B
            350, 0.80845, 0.01606, 0,        C
            400, 2.21355, 0.01405, FALSE,   D
            450, 4.49004, 0.01250, 1,   E
            500, 7.45135, 0.01200, TRUE,                 F G HIJ-K L
        </data>
    </table>
    """
    t = Table.from_xml(XML(text))
    assert t.comment == "Spectral Irradiance"
    assert np.array_equal(t.units.tolist(), ["nm", "W/m^2", "W/m^2", "", ""])
    assert t.units["Wavelength"] == "nm"
    assert t.units["Irradiance"] == "W/m^2"
    assert t.units["u(Irradiance)"] == "W/m^2"
    assert t.units["Is Good?"] == ""
    assert t.units["Letter"] == ""
    assert np.array_equal(t.header, ["Wavelength", "Irradiance", "u(Irradiance)", "Is Good?", "Letter"])
    assert t.types["Wavelength"] == np.dtype(dtype=int)
    assert t.types["Irradiance"] == np.dtype(dtype=float)
    assert t.types["u(Irradiance)"] == np.dtype(dtype=float)
    assert t.types["Is Good?"] == np.dtype(dtype=bool)
    assert t.types["Letter"] == np.dtype(dtype=object)
    assert np.array_equal(t["Wavelength"], [250, 300, 350, 400, 450, 500])
    assert np.array_equal(t[1].tolist(), [300, 0.18478, 0.01755, True, "B"])  # type: ignore[arg-type]
    assert t.dtype.names is not None
    assert np.array_equal(t.dtype.names, t.header)
    assert t.units.dtype.names is not None
    assert np.array_equal(t.units.dtype.names, t.header)

    # All arrays are initially read only
    with pytest.raises(ValueError, match=r"read-only"):
        t.types[0] = np.complex64
    with pytest.raises(ValueError, match=r"read-only"):
        t.units[0] = "degC"
    with pytest.raises(ValueError, match=r"read-only"):
        t.header[0] = "Something else"
    with pytest.raises(ValueError, match=r"read-only"):
        t[0][0] = 1

    # Check that the metadata comes along, using cast() to improve type checking for the tests
    slicer = cast("Table", t[:3])
    assert slicer.comment == "Spectral Irradiance"

    by_name = cast("Table", t["Wavelength"])
    assert by_name.comment == "Spectral Irradiance"

    by_names = cast("Table", t[["Wavelength", "Irradiance"]])
    assert by_names.comment == "Spectral Irradiance"

    cosine = cast("Table", np.cos(t["Irradiance"] + 0.5))
    assert cosine.comment == "Spectral Irradiance"

    # creating an unstructured array from a structured array that contains numerics and strings
    un = t.unstructured()
    assert un.dtype == np.object_
    assert np.array_equal(
        un,
        np.array(
            [
                [250, 0.01818, 0.02033, True, "A"],
                [300, 0.18478, 0.01755, True, "B"],
                [350, 0.80845, 0.01606, False, "C"],
                [400, 2.21355, 0.01405, False, "D"],
                [450, 4.49004, 0.01250, True, "E"],
                [500, 7.45135, 0.01200, True, "F G HIJ-K L"],
            ],
            dtype=object,
        ),
    )


def test_table_to_string_indent() -> None:
    text = """
    <table comment="Spectral Irradiance">
        <type> int    , double,           double, bool, string </type>
        <unit> nm,   W/m^2,      W/m^2, ,   </unit>
        <header> Wavelength         , Irradiance     ,u(Irradiance), Is Good?, Letter</header>
        <data>
            250, 0.01818, 0.02033, True, A
            300, 0.18478, 0.01755, true,B
            350, 0.80845, 0.01606, 0, C
            400, 2.21355, 0.01405, FALSE,     D
            450, 4.49004, 0.01250, 1, E
            500, 7.45135, 0.01200, TRUE,  F
        </data>
    </table>
    """
    t = Table.from_xml(XML(text))

    _Indent.table_data = 0
    assert tostring(t.to_xml()) == (
        b'<table comment="Spectral Irradiance">'
        b"<type>int,double,double,bool,string</type>"
        b"<unit>nm,W/m^2,W/m^2,,</unit>"
        b"<header>Wavelength,Irradiance,u(Irradiance),Is Good?,Letter</header>"
        b"<data>250,0.01818,0.02033,True,A\n"
        b"300,0.18478,0.01755,True,B\n"
        b"350,0.80845,0.01606,False,C\n"
        b"400,2.21355,0.01405,False,D\n"
        b"450,4.49004,0.0125,True,E\n"
        b"500,7.45135,0.012,True,F\n"
        b"</data>"
        b"</table>"
    )

    _Indent.table_data = 2
    assert tostring(t.to_xml()) == (
        b'<table comment="Spectral Irradiance">'
        b"<type>int,double,double,bool,string</type>"
        b"<unit>nm,W/m^2,W/m^2,,</unit>"
        b"<header>Wavelength,Irradiance,u(Irradiance),Is Good?,Letter</header>"
        b"<data>250,0.01818,0.02033,True,A\n"
        b"  300,0.18478,0.01755,True,B\n"
        b"  350,0.80845,0.01606,False,C\n"
        b"  400,2.21355,0.01405,False,D\n"
        b"  450,4.49004,0.0125,True,E\n"
        b"  500,7.45135,0.012,True,F\n"
        b"</data>"
        b"</table>"
    )

    _Indent.table_data = 5
    assert tostring(t.to_xml()) == (
        b'<table comment="Spectral Irradiance">'
        b"<type>int,double,double,bool,string</type>"
        b"<unit>nm,W/m^2,W/m^2,,</unit>"
        b"<header>Wavelength,Irradiance,u(Irradiance),Is Good?,Letter</header>"
        b"<data>250,0.01818,0.02033,True,A\n"
        b"     300,0.18478,0.01755,True,B\n"
        b"     350,0.80845,0.01606,False,C\n"
        b"     400,2.21355,0.01405,False,D\n"
        b"     450,4.49004,0.0125,True,E\n"
        b"     500,7.45135,0.012,True,F\n"
        b"</data>"
        b"</table>"
    )

    _Indent.table_data = 6
    assert tostring(t.to_xml()) == (
        b'<table comment="Spectral Irradiance">'
        b"<type>int,double,double,bool,string</type>"
        b"<unit>nm,W/m^2,W/m^2,,</unit>"
        b"<header>Wavelength,Irradiance,u(Irradiance),Is Good?,Letter</header>"
        b"<data>250,0.01818,0.02033,True,A\n"
        b"      300,0.18478,0.01755,True,B\n"
        b"      350,0.80845,0.01606,False,C\n"
        b"      400,2.21355,0.01405,False,D\n"
        b"      450,4.49004,0.0125,True,E\n"
        b"      500,7.45135,0.012,True,F\n"
        b"</data>"
        b"</table>"
    )

    _Indent.table_data = 7
    assert tostring(t.to_xml()) == (
        b'<table comment="Spectral Irradiance">'
        b"<type>int,double,double,bool,string</type>"
        b"<unit>nm,W/m^2,W/m^2,,</unit>"
        b"<header>Wavelength,Irradiance,u(Irradiance),Is Good?,Letter</header>"
        b"<data>250,0.01818,0.02033,True,A\n"
        b"       300,0.18478,0.01755,True,B\n"
        b"       350,0.80845,0.01606,False,C\n"
        b"       400,2.21355,0.01405,False,D\n"
        b"       450,4.49004,0.0125,True,E\n"
        b"       500,7.45135,0.012,True,F\n"
        b" </data>"
        b"</table>"
    )


def test_cvd() -> None:
    text = """
        <cvdCoefficients comment="My favourite PRT">
        <R0>100.0188885</R0>
        <A>0.00390969</A>
        <B>-0.000000606</B>
        <C>0.000000000001372</C>
        <D>0</D>
        <uncertainty variables="">0.0056/2</uncertainty>
        <range>
            <minimum>-10</minimum>
            <maximum>70.02</maximum>
        </range>
        <degreeFreedom>99.9</degreeFreedom>
        </cvdCoefficients>
    """
    cvd = CVDEquation.from_xml(XML(text))
    assert cvd.R0 == 100.0188885
    assert cvd.A == 0.00390969
    assert cvd.B == -6.06e-7
    assert cvd.C == 1.372e-12
    assert cvd.D == 0.0
    assert cvd.uncertainty.equation == "0.0056/2"
    assert cvd.uncertainty.variables == ()
    assert cvd.uncertainty.ranges == {"t": Range(-10, 70.02), "r": Range(96.102, 127.103)}
    assert cvd.uncertainty() == 0.0056 / 2
    assert cvd.ranges == cvd.uncertainty.ranges
    assert cvd.degree_freedom == 99.9
    assert cvd.comment == "My favourite PRT"
    assert tostring(cvd.to_xml()) == (
        b'<cvdCoefficients comment="My favourite PRT">'
        b"<R0>100.0188885</R0>"
        b"<A>0.00390969</A>"
        b"<B>-6.06e-07</B>"
        b"<C>1.372e-12</C>"
        b"<D>0.0</D>"
        b'<uncertainty variables="">0.0056/2</uncertainty>'
        b"<range>"
        b"<minimum>-10.0</minimum>"
        b"<maximum>70.02</maximum>"
        b"</range>"
        b"<degreeFreedom>99.9</degreeFreedom>"
        b"</cvdCoefficients>"
    )

    with pytest.raises(ValueError, match=r"-10.1 is not within the range"):
        _ = cvd.resistance(-10.1)
    with pytest.raises(ValueError, match=r"in the sequence is not within the range"):
        _ = cvd.resistance([0, 1, -10.1, -1])

    assert pytest.approx(cvd.resistance(-10.1, check_range=False)) == 96.0631883261  # pyright: ignore[reportUnknownMemberType]

    with pytest.raises(ValueError, match=r"96.0 is not within the range"):
        _ = cvd.temperature(96)
    with pytest.raises(ValueError, match=r"in the sequence is not within the range"):
        _ = cvd.temperature([100, 101, 96, 102])

    assert pytest.approx(cvd.temperature(96, check_range=False)) == -10.26108289  # pyright: ignore[reportUnknownMemberType]

    assert cvd.resistance(0) == 100.0188885
    assert cvd.temperature(100.0188885) == 0

    # values from Humidity Standards
    temperatures = [
        -9.752602907,
        0.127375257,
        10.08530398,
        20.00161345,
        30.04545999,
        40.01462788,
        50.02514365,
        59.83624842,
        70.01948947,
    ]
    resistances = [
        96.1994519,
        100.0686967,
        103.9565095,
        107.8161279,
        111.7132350,
        115.5692733,
        119.4291821,
        123.2004137,
        127.1023476,
    ]
    assert np.allclose(cvd.resistance(temperatures), resistances, rtol=2e-11, atol=0)
    assert np.allclose(cvd.temperature(resistances), temperatures, rtol=3e-9, atol=0)


def test_cvd_from_to_xml_no_comment_nor_dof() -> None:
    text = """
        <cvdCoefficients>
        <R0>100.02</R0>
        <A>0.0321</A>
        <B>-5e-7</B>
        <C>0</C>
        <D>0</D>
        <uncertainty variables="">0.0035</uncertainty>
        <range>
            <minimum>0</minimum>
            <maximum>100</maximum>
        </range>
        </cvdCoefficients>
    """
    cvd = CVDEquation.from_xml(XML(text))
    assert cvd.R0 == 100.02
    assert cvd.A == 0.0321
    assert cvd.B == -5.0e-7
    assert cvd.C == 0
    assert cvd.D == 0
    assert cvd.uncertainty.equation == "0.0035"
    assert cvd.uncertainty.variables == ()
    assert cvd.uncertainty.ranges == {"t": Range(0, 100), "r": Range(100.02, 420.584)}
    assert cvd.ranges == cvd.uncertainty.ranges
    assert np.isinf(cvd.degree_freedom)
    assert cvd.comment == ""
    assert tostring(cvd.to_xml()) == (
        b"<cvdCoefficients>"
        b"<R0>100.02</R0>"
        b"<A>0.0321</A>"
        b"<B>-5e-07</B>"
        b"<C>0.0</C>"
        b"<D>0.0</D>"
        b'<uncertainty variables="">0.0035</uncertainty>'
        b"<range>"
        b"<minimum>0.0</minimum>"
        b"<maximum>100.0</maximum>"
        b"</range>"
        b"</cvdCoefficients>"
    )


@pytest.mark.parametrize(
    ("r0", "a", "b", "c", "d"),
    [
        (95, 0.00390969, -6.06e-7, 1.372e-12, 0.0),
        (100, 0.00390969, -6.06e-7, 1.372e-12, 0.0),
        (105, 0.00390969, -6.06e-7, 1.372e-12, 0.0),
        (98, 0.0035, -5e-7, 2e-12, 0.0),
        (101, 0.004, 7e-7, 0.5e-12, 0.0),
        (1000.2, 0.0039, -7e-7, -1e-12, 0.0),
        (999.5, 0.004, -7e-7, 1e-12, 0.0),
        (25, 0.004, -6e-7, 1.2e-12, 0.0),
        (24, 0.003, -5e-7, 0.5e-12, 0.0),
        (26, 0.005, -7e-7, 2.0e-12, 0.0),
        (99.9, 3.92e-3, -6.68e-7, -4.27e-12, 1.01e-10),
        (99.9, 3e-3, -6.68e-7, -4.27e-12, 5e-11),
        (99.9, 5e-3, -6.68e-7, -4.27e-12, 1e-9),
        (99.9, 3.92e-3, -2e-7, -4.27e-12, 1e-10),
        (99.9, 3.92e-3, -1e-6, -4.27e-12, 1e-10),
    ],
)
def test_cvd_round_trip(r0: float, a: float, b: float, c: float, d: float) -> None:
    text = f"""
        <cvdCoefficients>
        <R0>{r0}</R0>
        <A>{a}</A>
        <B>{b}</B>
        <C>{c}</C>
        <D>{d}</D>
        <uncertainty variables="">0.0025</uncertainty>
        <range>
            <minimum>-273.15</minimum>
            <maximum>1000</maximum>
        </range>
        </cvdCoefficients>
    """
    cvd = CVDEquation.from_xml(XML(text))
    t = np.linspace(-200, 661, num=1_000_000)  # 0.000861 degC step size over entire temperature range
    assert np.allclose(cvd.temperature(cvd.resistance(t)), t, rtol=4e-6, atol=0)


def test_cvd_iec60751() -> None:
    # https://cdn.standards.iteh.ai/samples/14059/7d8443be42764357a50e53e55222996d/IEC-60751-2008.pdf
    # Table 1 in IEC60751
    data = np.array(
        [
            [-200, 18.52],
            [-190, 22.83],
            [-185, 24.97],
            [-180, 27.10],
            [-177, 28.37],
            [-170, 31.34],
            [-163, 34.28],
            [-160, 35.54],
            [-156, 37.22],
            [-146, 41.39],
            [-140, 43.88],
            [-135, 45.94],
            [-130, 48.00],
            [-127, 49.24],
            [-119, 52.52],
            [-107, 57.41],
            [-100, 60.26],
            [-92, 63.49],
            [-84, 66.72],
            [-77, 69.53],
            [-63, 75.13],
            [-55, 78.32],
            [-46, 81.89],
            [-39, 84.67],
            [-27, 89.40],
            [-20, 92.16],
            [-15, 94.12],
            [-11, 95.69],
            [-7, 97.26],
            [-1, 99.61],
            [0, 100.00],
            [100, 138.51],
            [172, 165.51],
            [203, 176.96],
            [330, 222.68],
            [361, 233.56],
            [380, 240.18],
            [409, 250.19],
            [432, 258.06],
            [449, 263.84],
            [455, 265.87],
            [493, 278.64],
            [604, 314.99],
            [658, 332.16],
            [718, 350.84],
            [805, 377.19],
            [822, 382.24],
            [850, 390.48],
        ]
    )
    text = """
        <cvdCoefficients>
        <R0>100</R0>
        <A>3.9083e-3</A>
        <B>-5.775e-7</B>
        <C>-4.183e-12</C>
        <D>0</D>
        <uncertainty variables="">1</uncertainty>
        <range>
            <minimum>-200</minimum>
            <maximum>850</maximum>
        </range>
        </cvdCoefficients>
    """
    cvd = CVDEquation.from_xml(XML(text))
    assert np.allclose(cvd.resistance(data[:, 0]), data[:, 1], rtol=1e-4, atol=0.005)
    assert np.allclose(cvd.temperature(data[:, 1]), data[:, 0], rtol=5e-4, atol=0.005)


def test_performance_check_minimal() -> None:
    text = (
        b'<performanceCheck completedDate="2023-04-02" enteredBy="Me">'
        b"<competency>"
        b"<worker>Person A.</worker>"
        b"<checker>B</checker>"
        b"<technicalProcedure>value is not checked</technicalProcedure>"
        b"</competency>"
        b"<conditions />"
        b"</performanceCheck>"
    )

    pc = PerformanceCheck.from_xml(XML(text))
    assert pc.completed_date == date(2023, 4, 2)
    assert pc.entered_by == "Me"
    assert pc.checked_by == ""
    assert pc.checked_date is None
    assert pc.competency.worker == "Person A."
    assert pc.competency.checker == "B"
    assert pc.competency.technical_procedure == "value is not checked"
    assert pc.conditions.tag == "conditions"
    assert pc.conditions.attrib == {}
    assert pc.conditions.text is None
    assert len(pc.conditions) == 0
    assert len(pc.cvd_equations) == 0
    with pytest.raises(IndexError):
        _ = pc.cvd_equation
    assert len(pc.equations) == 0
    with pytest.raises(IndexError):
        _ = pc.equation
    assert len(pc.files) == 0
    with pytest.raises(IndexError):
        _ = pc.file
    assert len(pc.deserialisers) == 0
    with pytest.raises(IndexError):
        _ = pc.deserialised
    assert len(pc.tables) == 0
    with pytest.raises(IndexError):
        _ = pc.table
    assert tostring(pc.to_xml()) == text


def test_performance_check() -> None:
    text = (
        b'<performanceCheck completedDate="2023-04-02" enteredBy="Me" checkedBy="A" checkedDate="2025-01-01">'
        b"<competency>"
        b"<worker>A</worker>"
        b"<checker>B</checker>"
        b"<technicalProcedure>C</technicalProcedure>"
        b"</competency>"
        b'<conditions><temperature unit="C">25</temperature></conditions>'
        b"<equation>"
        b'<value variables="x">1 + x</value>'
        b'<uncertainty variables="">0.1</uncertainty>'
        b"<unit>K</unit>"
        b'<ranges><range variable="x"><minimum>0.0</minimum><maximum>1.0</maximum></range></ranges>'
        b"</equation>"
        b"<table>"
        b"<type>int,double,double,bool,string</type>"
        b"<unit>nm,W/m^2,W/m^2,,</unit>"
        b"<header>Wavelength,Irradiance,u(Irradiance),Is Good?,Letter</header>"
        b"<data>250,0.01818,0.02033,True,A\n"
        b"   300,0.18478,0.01755,True,B\n"
        b"   350,0.80845,0.01606,False,C\n"
        b"   400,2.21355,0.01405,False,D\n"
        b"   450,4.49004,0.0125,True,E\n"
        b"   500,7.45135,0.012,True,F\n"
        b"</data>"
        b"</table>"
        b"<cvdCoefficients>"
        b"<R0>100.0188885</R0>"
        b"<A>0.00390969</A>"
        b"<B>-6.06e-07</B>"
        b"<C>1.372e-12</C>"
        b"<D>1e-10</D>"
        b'<uncertainty variables="">0.0056/2</uncertainty>'
        b"<range><minimum>-10.0</minimum><maximum>70.02</maximum></range>"
        b"</cvdCoefficients>"
        b'<file comment="hi"><url foo="bar">whatever</url><sha256>anything</sha256></file>'
        b'<serialised><gtcArchive version="1.5.0" xmlns="https://measurement.govt.nz/gtc/xml"><leafNodes><leafNode uid="(1, 1)"><u>0.1</u><df>INF</df><label /><independent>true</independent></leafNode></leafNodes><taggedReals><elementaryReal tag="x" uid="(1, 1)"><value>1.0</value></elementaryReal></taggedReals><untaggedReals /><taggedComplexes /><intermediates /></gtcArchive></serialised>'  # noqa: E501
        b"</performanceCheck>"
    )

    pc = PerformanceCheck.from_xml(XML(text))
    assert pc.completed_date == date(2023, 4, 2)
    assert pc.entered_by == "Me"
    assert pc.checked_by == "A"
    assert pc.checked_date == date(2025, 1, 1)
    assert pc.competency.worker == "A"
    assert pc.competency.checker == "B"
    assert pc.competency.technical_procedure == "C"
    assert pc.conditions.tag == "conditions"
    assert pc.conditions.attrib == {}
    assert pc.conditions.text is None
    assert len(pc.conditions) == 1
    assert pc.conditions[0].tag == "temperature"
    assert pc.conditions[0].attrib == {"unit": "C"}
    assert pc.conditions[0].text == "25"
    assert len(pc.cvd_equations) == 1
    assert pc.cvd_equation is pc.cvd_equations[0]
    assert len(pc.equations) == 1
    assert pc.equation is pc.equations[0]
    assert len(pc.files) == 1
    assert pc.file is pc.files[0]
    assert len(pc.deserialisers) == 1
    assert pc.deserialised is pc.deserialisers[0]
    assert len(pc.tables) == 1
    assert pc.table is pc.tables[0]

    _Indent.table_data = 3
    assert tostring(pc.to_xml()) == text


def test_issuing_laboratory_without_person() -> None:
    text = b"<issuingLaboratory>MSL</issuingLaboratory>"
    lab = IssuingLaboratory.from_xml(XML(text))
    assert lab.lab == "MSL"
    assert lab.person == ""
    assert tostring(lab.to_xml()) == text


def test_issuing_laboratory_with_person() -> None:
    text = b'<issuingLaboratory person="Me">MSL</issuingLaboratory>'
    lab = IssuingLaboratory.from_xml(XML(text))
    assert lab.lab == "MSL"
    assert lab.person == "Me"
    assert tostring(lab.to_xml()) == text


def test_report_minimal() -> None:
    text = (
        b'<report id="ABC" enteredBy="Me">'
        b"<reportIssueDate>2023-08-18</reportIssueDate>"
        b"<measurementStartDate>2023-08-08</measurementStartDate>"
        b"<measurementStopDate>2023-08-14</measurementStopDate>"
        b"<issuingLaboratory>MSL</issuingLaboratory>"
        b"<technicalProcedure>Anything</technicalProcedure>"
        b"<conditions />"
        b"<acceptanceCriteria />"
        b"</report>"
    )

    r = Report.from_xml(XML(text))
    assert r.id == "ABC"
    assert r.entered_by == "Me"
    assert r.checked_by == ""
    assert r.checked_date is None
    assert r.report_issue_date == date(2023, 8, 18)
    assert r.measurement_start_date == date(2023, 8, 8)
    assert r.measurement_stop_date == date(2023, 8, 14)
    assert r.issuing_laboratory.lab == "MSL"
    assert r.issuing_laboratory.person == ""
    assert r.technical_procedure == "Anything"
    assert r.conditions.tag == "conditions"
    assert r.conditions.attrib == {}
    assert r.conditions.text is None
    assert len(r.conditions) == 0
    assert r.acceptance_criteria.tag == "acceptanceCriteria"
    assert r.acceptance_criteria.attrib == {}
    assert r.acceptance_criteria.text is None
    assert len(r.acceptance_criteria) == 0
    assert len(r.cvd_equations) == 0
    with pytest.raises(IndexError):
        _ = r.cvd_equation
    assert len(r.equations) == 0
    with pytest.raises(IndexError):
        _ = r.equation
    assert len(r.files) == 0
    with pytest.raises(IndexError):
        _ = r.file
    assert len(r.deserialisers) == 0
    with pytest.raises(IndexError):
        _ = r.deserialised
    assert len(r.tables) == 0
    with pytest.raises(IndexError):
        _ = r.table
    assert tostring(r.to_xml()) == text


def test_report() -> None:
    text = (
        b'<report id="ABC" enteredBy="Me" checkedBy="A" checkedDate="2025-01-01">'
        b"<reportIssueDate>2023-08-18</reportIssueDate>"
        b"<measurementStartDate>2023-08-08</measurementStartDate>"
        b"<measurementStopDate>2023-08-14</measurementStopDate>"
        b"<issuingLaboratory>MSL</issuingLaboratory>"
        b"<technicalProcedure>Anything</technicalProcedure>"
        b'<conditions><temperature unit="C">25</temperature></conditions>'
        b'<acceptanceCriteria><temperature unit="K">300</temperature></acceptanceCriteria>'
        b"<equation>"
        b'<value variables="x">1 + x</value>'
        b'<uncertainty variables="">0.1</uncertainty>'
        b"<unit>K</unit>"
        b'<ranges><range variable="x"><minimum>0.0</minimum><maximum>1.0</maximum></range></ranges>'
        b"</equation>"
        b"<table>"
        b"<type>int,double,double,bool,string</type>"
        b"<unit>nm,W/m^2,W/m^2,,</unit>"
        b"<header>Wavelength,Irradiance,u(Irradiance),Is Good?,Letter</header>"
        b"<data>250,0.01818,0.02033,True,A\n"
        b"      300,0.18478,0.01755,True,B\n"
        b"      350,0.80845,0.01606,False,C\n"
        b"      400,2.21355,0.01405,False,D\n"
        b"      450,4.49004,0.0125,True,E\n"
        b"      500,7.45135,0.012,True,F\n"
        b"</data>"
        b"</table>"
        b"<cvdCoefficients>"
        b"<R0>100.0188885</R0>"
        b"<A>0.00390969</A>"
        b"<B>-6.06e-07</B>"
        b"<C>1.372e-12</C>"
        b"<D>0.0</D>"
        b'<uncertainty variables="">0.0056/2</uncertainty>'
        b"<range><minimum>-10.0</minimum><maximum>70.02</maximum></range>"
        b"</cvdCoefficients>"
        b'<file comment="hi"><url foo="bar">whatever</url><sha256>anything</sha256></file>'
        b'<serialised><gtcArchive version="1.5.0" xmlns="https://measurement.govt.nz/gtc/xml"><leafNodes><leafNode uid="(1, 1)"><u>0.1</u><df>INF</df><label /><independent>true</independent></leafNode></leafNodes><taggedReals><elementaryReal tag="x" uid="(1, 1)"><value>1.0</value></elementaryReal></taggedReals><untaggedReals /><taggedComplexes /><intermediates /></gtcArchive></serialised>'  # noqa: E501
        b"</report>"
    )

    r = Report.from_xml(XML(text))
    assert r.id == "ABC"
    assert r.entered_by == "Me"
    assert r.checked_by == "A"
    assert r.checked_date == date(2025, 1, 1)
    assert r.report_issue_date == date(2023, 8, 18)
    assert r.measurement_start_date == date(2023, 8, 8)
    assert r.measurement_stop_date == date(2023, 8, 14)
    assert r.issuing_laboratory.lab == "MSL"
    assert r.issuing_laboratory.person == ""
    assert r.technical_procedure == "Anything"
    assert r.conditions.tag == "conditions"
    assert r.conditions.attrib == {}
    assert r.conditions.text is None
    assert len(r.conditions) == 1
    assert r.conditions[0].tag == "temperature"
    assert r.conditions[0].attrib == {"unit": "C"}
    assert r.conditions[0].text == "25"
    assert r.acceptance_criteria.tag == "acceptanceCriteria"
    assert r.acceptance_criteria.attrib == {}
    assert r.acceptance_criteria.text is None
    assert len(r.acceptance_criteria) == 1
    assert r.acceptance_criteria[0].tag == "temperature"
    assert r.acceptance_criteria[0].attrib == {"unit": "K"}
    assert r.acceptance_criteria[0].text == "300"
    assert len(r.cvd_equations) == 1
    assert r.cvd_equation is r.cvd_equations[0]
    assert len(r.equations) == 1
    assert r.equation is r.equations[0]
    assert len(r.files) == 1
    assert r.file is r.files[0]
    assert len(r.deserialisers) == 1
    assert r.deserialised is r.deserialisers[0]
    assert len(r.tables) == 1
    assert r.table is r.tables[0]

    _Indent.table_data = 6
    assert tostring(r.to_xml()) == text


def test_component_empty() -> None:
    text = b'<component name="" />'
    c = Component.from_xml(XML(text))
    assert c.name == ""
    assert len(c.adjustments) == 0
    assert len(c.reports) == 0
    assert len(c.digital_reports) == 0
    assert len(c.performance_checks) == 0
    assert tostring(c.to_xml()) == text


def test_component() -> None:
    text = (
        b'<component name="Probe 1">'
        b'<report id="ABC" enteredBy="Me">'
        b"<reportIssueDate>2023-08-18</reportIssueDate>"
        b"<measurementStartDate>2023-08-08</measurementStartDate>"
        b"<measurementStopDate>2023-08-14</measurementStopDate>"
        b"<issuingLaboratory>MSL</issuingLaboratory>"
        b"<technicalProcedure>Anything</technicalProcedure>"
        b"<conditions />"
        b"<acceptanceCriteria />"
        b"</report>"
        b'<performanceCheck completedDate="2023-04-02" enteredBy="Me">'
        b"<competency>"
        b"<worker>A</worker>"
        b"<checker>B</checker>"
        b"<technicalProcedure>Anything</technicalProcedure>"
        b"</competency>"
        b"<conditions />"
        b"</performanceCheck>"
        b'<adjustment date="2024-10-17">Cleaned the filter</adjustment>'
        b'<digitalReport format="MSL PDF/A-3" id="Pressure/2025/092">'
        b"<url>reports/2025/job092.pdf</url>"
        b"<sha256>76e4e036da8722b55362912396a01a07bb61e6260c7c4b6150d431e613529a54</sha256>"
        b"</digitalReport>"
        b"</component>"
    )

    c = Component.from_xml(XML(text))
    assert c.name == "Probe 1"
    assert len(c.adjustments) == 1
    assert len(c.reports) == 1
    assert len(c.digital_reports) == 1
    assert len(c.performance_checks) == 1
    assert tostring(c.to_xml()) == text


def test_measurand_empty() -> None:
    text = b'<measurand quantity="Wavelength" calibrationInterval="1.0" />'
    m = Measurand.from_xml(XML(text))
    assert m.quantity == "Wavelength"
    assert m.calibration_interval == 1.0
    assert len(m.components) == 0
    assert tostring(m.to_xml()) == text


def test_measurand() -> None:
    text = (
        b'<measurand quantity="Wavelength" calibrationInterval="1.0">'
        b'<component name="Probe 1">'
        b'<report id="ABC" enteredBy="Me">'
        b"<reportIssueDate>2023-08-18</reportIssueDate>"
        b"<measurementStartDate>2023-08-08</measurementStartDate>"
        b"<measurementStopDate>2023-08-14</measurementStopDate>"
        b"<issuingLaboratory>MSL</issuingLaboratory>"
        b"<technicalProcedure>Anything</technicalProcedure>"
        b"<conditions />"
        b"<acceptanceCriteria />"
        b"</report>"
        b'<performanceCheck completedDate="2023-04-02" enteredBy="Me">'
        b"<competency>"
        b"<worker>A</worker>"
        b"<checker>B</checker>"
        b"<technicalProcedure>Anything</technicalProcedure>"
        b"</competency>"
        b"<conditions />"
        b"</performanceCheck>"
        b'<adjustment date="2024-10-17">Cleaned the filter</adjustment>'
        b'<digitalReport format="MSL PDF/A-3" id="Pressure/2025/092">'
        b"<url>reports/2025/job092.pdf</url>"
        b"<sha256>76e4e036da8722b55362912396a01a07bb61e6260c7c4b6150d431e613529a54</sha256>"
        b"</digitalReport>"
        b"</component>"
        b"</measurand>"
    )
    m = Measurand.from_xml(XML(text))
    assert m.quantity == "Wavelength"
    assert m.calibration_interval == 1.0

    assert len(m.components) == 1
    c = m.components[0]
    assert c.name == "Probe 1"
    assert len(c.adjustments) == 1
    assert len(c.reports) == 1
    assert len(c.digital_reports) == 1
    assert len(c.performance_checks) == 1

    assert tostring(m.to_xml()) == text


def test_equipment_empty() -> None:
    assert tostring(Equipment().to_xml()) == (
        b'<equipment enteredBy="">'
        b"<id />"
        b"<manufacturer />"
        b"<model />"
        b"<serial />"
        b"<description />"
        b"<specifications />"
        b"<location />"
        b"<status>Active</status>"
        b"<loggable>false</loggable>"
        b"<traceable>false</traceable>"
        b"<calibrations />"
        b"<maintenance />"
        b"<alterations />"
        b"<firmware />"
        b"<specifiedRequirements />"
        b"<referenceMaterials />"
        b"<qualityManual />"
        b"</equipment>"
    )


def test_register_empty() -> None:
    text = StringIO('<?xml version="1.0" encoding="UTF-8" ?><register team="Length" />')
    r = Register(text)
    assert r.team == "Length"
    assert len(r) == 0
    assert r._equipment == []  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert r._index_map == {}  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert str(r) == "<Register team='Length' (0 equipment)>"

    with pytest.raises(ValueError, match=r"the alias or id 'invalid'"):
        _ = r["invalid"]

    with pytest.raises(IndexError):
        _ = r[0]


def test_register_tree_namespace() -> None:
    encoding, version_info = "utf-8", sys.version_info[:2]

    if version_info < (3, 9):
        if sys.platform == "win32":
            encoding = "cp1252"
        else:
            encoding = encoding.upper()  # pyright: ignore[reportUnreachable]

    if version_info == (3, 9) and sys.platform == "darwin":
        encoding = encoding.upper()  # pyright: ignore[reportUnreachable]

    r = Register(StringIO('<?xml version="1.0" encoding="UTF-8"?><register team="Length" />'))

    tree = r.tree()
    assert isinstance(tree, ElementTree)
    root = tree.getroot()
    assert root is not None
    assert root.tag == "register"
    assert root.attrib == {"team": "Length", "xmlns": r.NAMESPACE}
    assert root.tail is None
    assert root.text is None
    assert len(root) == 0

    for ns in [None, ""]:
        with StringIO() as buffer:
            r.tree(namespace=ns).write(buffer, xml_declaration=True, encoding="unicode")
            assert buffer.getvalue() == f"<?xml version='1.0' encoding='{encoding}'?>\n<register team=\"Length\" />"

    with StringIO() as buffer:
        r.tree().write(buffer, xml_declaration=True, encoding="unicode")
        assert (
            buffer.getvalue()
            == f"<?xml version='1.0' encoding='{encoding}'?>\n<register team=\"Length\" xmlns=\"{r.NAMESPACE}\" />"
        )

    with StringIO() as buffer:
        r.tree(namespace="Hi").write(buffer, xml_declaration=True, encoding="unicode")
        assert (
            buffer.getvalue()
            == f"<?xml version='1.0' encoding='{encoding}'?>\n<register team=\"Length\" xmlns=\"Hi\" />"
        )


@pytest.mark.skipif(sys.version_info[:2] < (3, 9), reason="requires xml indent() function")
def test_register_read_write_same_output() -> None:
    path = Path("tests/resources/mass/register.xml")
    r = Register(path)
    tree = r.tree()  # indent=4 by default

    buffer = StringIO()
    tree.write(buffer, xml_declaration=True, encoding="unicode")

    lines1 = buffer.getvalue().splitlines()
    lines2 = path.read_text().splitlines()
    assert len(lines1) == len(lines2)
    for i, (line1, line2) in enumerate(zip(lines1, lines2)):
        if i == 0 and (sys.platform == "darwin" and sys.version_info[:2] == (3, 9)):
            assert line1 == line2.replace("utf", "UTF")  # pyright: ignore[reportUnreachable]
        else:
            assert line1 == line2


def test_register_from_file() -> None:  # noqa: PLR0915
    r = Register("tests/resources/mass/register.xml")
    assert r.team == "Mass"
    assert len(r) == 2
    assert r._equipment == [None, None]  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert r._index_map == {"Bob": 1, "MSLE.M.001": 0, "MSLE.M.092": 1}  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert str(r) == "<Register team='Mass' (2 equipment)>"

    first = r[0]
    assert isinstance(first, Equipment)
    assert str(first) == "<Equipment manufacturer='MSL', model='ABC', serial='123'>"
    assert first.entered_by == "Peter McDowall"  # cSpell:ignore Dowall
    assert first.checked_by == ""
    assert first.checked_date is None
    assert first.alias == ""
    assert first.keywords == ()
    assert first.id == "MSLE.M.001"
    assert first.manufacturer == "MSL"
    assert first.model == "ABC"
    assert first.serial == "123"
    assert first.description == "A short description about the equipment"
    assert first.specifications.tag == "specifications"
    assert first.specifications.attrib == {}
    assert first.specifications.text is None
    assert len(first.specifications) == 0
    assert first.location == "CMM Lab"
    assert first.status == Status.Lost
    assert not first.loggable
    assert not first.traceable
    assert len(first.calibrations) == 0
    assert len(first.maintenance.completed) == 0
    assert len(first.maintenance.planned) == 0
    assert len(first.alterations) == 0
    assert len(first.firmware) == 0
    assert first.specified_requirements.tag == "specifiedRequirements"
    assert first.specified_requirements.attrib == {}
    assert first.specified_requirements.text is None
    assert len(first.specified_requirements) == 0
    assert first.reference_materials.tag == "referenceMaterials"
    assert first.reference_materials.attrib == {}
    assert first.reference_materials.text is None
    assert len(first.reference_materials) == 0
    assert first.quality_manual.accessories.tag == "accessories"
    assert first.quality_manual.accessories.attrib == {}
    assert first.quality_manual.accessories.text is None
    assert len(first.quality_manual.accessories) == 0
    assert first.quality_manual.documentation == ""
    assert first.quality_manual.financial == Financial()
    assert first.quality_manual.personnel_restrictions == ""
    assert first.quality_manual.service_agent == ""
    assert first.quality_manual.technical_procedures == ()

    assert r["MSLE.M.001"] is first
    assert r[0] is first

    with pytest.raises(ValueError, match=r"the alias or id 'invalid'"):
        _ = r["invalid"]

    with pytest.raises(IndexError):
        _ = r[2]

    assert r._equipment == [first, None]  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

    second = None
    for item in r:
        second = item

    assert isinstance(second, Equipment)
    assert second is not None
    assert str(second) == "<Equipment manufacturer='The Company Name', model='Model', serial='Serial' (4 reports)>"
    assert second is not first
    assert r["Bob"] is second
    assert r["MSLE.M.092"] is second
    assert r[1] is second
    assert r._equipment == [first, second]  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert second.entered_by == "Joseph Borbely"
    assert second.checked_by == "Adam Dunford"
    assert second.checked_date == date(2025, 8, 12)
    assert second.alias == "Bob"
    assert second.keywords == ("Thermometer", "Hygrometer")
    assert second.id == "MSLE.M.092"
    assert second.manufacturer == "The Company Name"
    assert second.model == "Model"
    assert second.serial == "Serial"
    assert second.description == "Monitors the ambient lab temperature and humidity"
    assert len(second.specifications) == 1
    assert second.specifications[0].tag == "foo"
    assert second.specifications[0].attrib == {"bar": "baz"}
    assert second.specifications[0].text == "bar"
    assert second.location == "Mass Standards Laboratories"
    assert second.status == Status.Active
    assert second.loggable
    assert second.traceable
    assert len(second.calibrations) == 2
    assert len(second.maintenance.planned) == 1
    assert second.maintenance.planned[0].due_date == date(2025, 5, 15)
    assert len(second.maintenance.completed) == 1
    assert second.maintenance.completed[0].completed_date == date(2024, 12, 2)
    assert len(second.alterations) == 1
    assert second.alterations[0].details == "Did work"
    assert len(second.firmware) == 2
    assert second.firmware[1].version == "1.02"
    assert len(second.specified_requirements) == 1
    assert second.specified_requirements[0].tag == "foo"
    assert second.specified_requirements[0].attrib == {"bar": "baz"}
    assert second.specified_requirements[0].text == "bar"
    assert len(second.reference_materials) == 1
    assert second.reference_materials.attrib == {"key": "value"}
    assert second.reference_materials[0].tag == "fruit"
    assert second.reference_materials[0].attrib == {"colour": "red", "size": "small"}
    assert second.reference_materials[0].text == "apple"
    assert len(second.quality_manual.accessories) == 1
    assert second.quality_manual.accessories[0].tag == "colour"
    assert second.quality_manual.accessories[0].attrib == {"mode": "RGB"}
    assert len(second.quality_manual.accessories[0]) == 3
    assert second.quality_manual.accessories[0][0].tag == "r"
    assert second.quality_manual.accessories[0][0].text == "34"
    assert second.quality_manual.accessories[0][1].tag == "g"
    assert second.quality_manual.accessories[0][1].text == "0"
    assert second.quality_manual.accessories[0][2].tag == "b"
    assert second.quality_manual.accessories[0][2].text == "187"
    assert second.quality_manual.financial.purchase_year == 2023
    assert second.quality_manual.financial.capital_expenditure is not None
    assert second.quality_manual.financial.capital_expenditure.asset_number == "Whatever"
    assert second.quality_manual.financial.capital_expenditure.depreciation_end_year == 2030
    assert second.quality_manual.financial.capital_expenditure.price == 10000.0
    assert second.quality_manual.financial.capital_expenditure.currency == "NZD"
    assert second.quality_manual.financial.warranty_expiration_date == date(2026, 8, 1)
    assert second.quality_manual.documentation == "https://url.com"
    assert second.quality_manual.personnel_restrictions == "Everyone"
    assert second.quality_manual.service_agent == "Someone from the Secret Service"
    assert second.quality_manual.technical_procedures == ("MSLT.E.028.017", "MSLT.O.009")


@pytest.mark.parametrize("calibrations", [(), (Measurand(quantity="A", calibration_interval=1),)])
def test_latest_report_empty(calibrations: tuple[Measurand, ...]) -> None:
    e = Equipment(calibrations=calibrations)
    assert e.latest_report() is None
    assert list(e.latest_reports()) == []


@pytest.mark.parametrize("calibrations", [(), (Measurand(quantity="A", calibration_interval=1),)])
def test_latest_performance_check_empty(calibrations: tuple[Measurand, ...]) -> None:
    e = Equipment(calibrations=calibrations)
    assert e.latest_performance_check() is None
    assert list(e.latest_performance_checks()) == []


@pytest.mark.parametrize(("value", "expect"), [("stop", "B"), ("issue", "C"), ("start", "B")])
def test_latest_report_single_measurand_and_component(value: str, expect: str) -> None:
    e = Equipment(
        calibrations=(
            Measurand(
                quantity="1",
                calibration_interval=1,
                components=(
                    Component(
                        name="2",
                        reports=(
                            Report(
                                id="A",
                                entered_by="",
                                report_issue_date=date(2020, 6, 3),
                                measurement_start_date=date(2020, 5, 1),
                                measurement_stop_date=date(2020, 5, 4),
                            ),
                            Report(
                                id="B",
                                entered_by="",
                                report_issue_date=date(2024, 10, 23),
                                measurement_start_date=date(2024, 2, 15),
                                measurement_stop_date=date(2024, 2, 16),
                            ),
                            Report(
                                id="C",
                                entered_by="",
                                report_issue_date=date(2025, 4, 10),  # issue date > Report(id=B) issue date
                                measurement_start_date=date(2022, 3, 20),
                                measurement_stop_date=date(2022, 3, 22),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )

    reports = list(e.latest_reports(date=value))  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    assert len(reports) == 1
    assert reports[0].quantity == "1"
    assert reports[0].name == "2"
    assert reports[0].id == expect

    # Don't specify `quantity` or `name` and the correct report is returned
    latest = e.latest_report(date=value)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    assert latest is not None
    assert latest.id == expect

    # Can specify `quantity` and/or `name` provided that the value matches a report
    latest = e.latest_report(quantity="1", date=value)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    assert latest is not None
    assert latest.id == expect

    latest = e.latest_report(name="2", date=value)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    assert latest is not None
    assert latest.id == expect

    latest = e.latest_report(quantity="1", name="2", date=value)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    assert latest is not None
    assert latest.id == expect

    # If `quantity` and/or `name` are specified then the Report must match accordingly
    latest = e.latest_report(quantity="Anything", date=value)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    assert latest is None
    latest = e.latest_report(name="Anything", date=value)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    assert latest is None
    latest = e.latest_report(quantity="2", name="1", date=value)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    assert latest is None


def test_latest_performance_check_single_measurand_and_component() -> None:
    e = Equipment(
        calibrations=(
            Measurand(
                quantity="Temperature",
                calibration_interval=1,
                components=(
                    Component(
                        name="Probe",
                        performance_checks=(
                            PerformanceCheck(
                                completed_date=date(2023, 6, 3),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="A",
                            ),
                            PerformanceCheck(
                                completed_date=date(2021, 8, 12),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="B",
                            ),
                            PerformanceCheck(
                                completed_date=date(2024, 3, 4),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="C",
                            ),
                            PerformanceCheck(
                                completed_date=date(2024, 3, 3),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="D",
                            ),
                        ),
                    ),
                ),
            ),
        )
    )

    checks = list(e.latest_performance_checks())
    assert len(checks) == 1
    assert checks[0].quantity == "Temperature"
    assert checks[0].name == "Probe"
    assert checks[0].entered_by == "C"
    assert checks[0].completed_date == date(2024, 3, 4)
    assert checks[0].competency == Competency(worker="Me", checker="You", technical_procedure="A")

    # Don't specify `quantity` or `name` and the correct report is returned
    latest = e.latest_performance_check()
    assert latest is not None
    assert latest.entered_by == "C"

    # Can specify `quantity` and/or `name` provided that the value matches a report
    latest = e.latest_performance_check(quantity="Temperature")
    assert latest is not None
    assert latest.entered_by == "C"

    latest = e.latest_performance_check(name="Probe")
    assert latest is not None
    assert latest.entered_by == "C"

    latest = e.latest_performance_check(quantity="Temperature", name="Probe")
    assert latest is not None
    assert latest.entered_by == "C"

    # If `quantity` and/or `name` are specified then the Report must match accordingly
    latest = e.latest_performance_check(quantity="Anything")
    assert latest is None
    latest = e.latest_performance_check(name="Anything")
    assert latest is None
    latest = e.latest_performance_check(quantity="2", name="1")
    assert latest is None


def test_latest_report_multiple_measurand_and_components() -> None:
    e = Equipment(
        calibrations=(
            Measurand(
                quantity="Temperature",
                calibration_interval=5,
                components=(
                    Component(
                        name="Probe 1",
                        reports=(
                            Report(
                                id="A",
                                entered_by="",
                                report_issue_date=date(2020, 6, 3),
                                measurement_start_date=date(2020, 5, 1),
                                measurement_stop_date=date(2020, 5, 4),
                            ),
                            Report(
                                id="B",
                                entered_by="Me",
                                report_issue_date=date(2024, 10, 23),
                                measurement_start_date=date(2024, 2, 15),
                                measurement_stop_date=date(2024, 2, 16),
                            ),
                            Report(
                                id="C",
                                entered_by="",
                                report_issue_date=date(2025, 4, 10),  # issue date > Report(id=B) issue date
                                measurement_start_date=date(2022, 3, 20),
                                measurement_stop_date=date(2022, 3, 22),
                            ),
                        ),
                    ),
                    Component(
                        name="Probe 2",
                        reports=(
                            Report(
                                id="E",
                                entered_by="",
                                report_issue_date=date(2024, 10, 23),
                                measurement_start_date=date(2024, 2, 15),
                                measurement_stop_date=date(2024, 2, 16),
                            ),
                            Report(
                                id="D",
                                entered_by="",
                                report_issue_date=date(2020, 6, 3),
                                measurement_start_date=date(2020, 5, 1),
                                measurement_stop_date=date(2020, 5, 4),
                            ),
                            Report(
                                id="F",
                                entered_by="",
                                report_issue_date=date(2025, 4, 10),  # issue date > Report(id=B) issue date
                                measurement_start_date=date(2022, 3, 20),
                                measurement_stop_date=date(2022, 3, 22),
                            ),
                        ),
                    ),
                ),
            ),
            Measurand(
                quantity="Humidity",
                calibration_interval=5,
                components=(
                    Component(
                        name="Probe 1",
                        reports=(
                            Report(
                                id="b",
                                entered_by="",
                                report_issue_date=date(2024, 10, 23),
                                measurement_start_date=date(2024, 2, 15),
                                measurement_stop_date=date(2024, 2, 16),
                            ),
                            Report(
                                id="c",
                                entered_by="",
                                report_issue_date=date(2025, 4, 10),  # issue date > Report(id=B) issue date
                                measurement_start_date=date(2022, 3, 20),
                                measurement_stop_date=date(2022, 3, 22),
                            ),
                            Report(
                                id="a",
                                entered_by="",
                                report_issue_date=date(2020, 6, 3),
                                measurement_start_date=date(2020, 5, 1),
                                measurement_stop_date=date(2020, 5, 4),
                            ),
                        ),
                    ),
                    Component(
                        name="Probe 2",
                        reports=(
                            Report(
                                id="d",
                                entered_by="",
                                report_issue_date=date(2020, 6, 3),
                                measurement_start_date=date(2020, 5, 1),
                                measurement_stop_date=date(2020, 5, 4),
                            ),
                            Report(
                                id="f",
                                entered_by="",
                                report_issue_date=date(2025, 4, 10),  # issue date > Report(id=B) issue date
                                measurement_start_date=date(2022, 3, 20),
                                measurement_stop_date=date(2022, 3, 22),
                            ),
                            Report(
                                id="e",
                                entered_by="",
                                report_issue_date=date(2024, 10, 23),
                                measurement_start_date=date(2024, 2, 15),
                                measurement_stop_date=date(2024, 2, 16),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )

    reports = list(e.latest_reports())
    assert len(reports) == 4
    assert reports[0].quantity == "Temperature"
    assert reports[0].name == "Probe 1"
    assert reports[0].id == "B"
    assert reports[0].entered_by == "Me"
    assert reports[0].report_issue_date == date(2024, 10, 23)
    assert reports[0].measurement_start_date == date(2024, 2, 15)
    assert reports[0].measurement_stop_date == date(2024, 2, 16)

    assert reports[1].quantity == "Temperature"
    assert reports[1].name == "Probe 2"
    assert reports[1].id == "E"

    assert reports[2].quantity == "Humidity"
    assert reports[2].name == "Probe 1"
    assert reports[2].id == "b"

    assert reports[3].quantity == "Humidity"
    assert reports[3].name == "Probe 2"
    assert reports[3].id == "e"

    report = e.latest_report()
    assert report is None

    report = e.latest_report(quantity="Temperature")
    assert report is None  # must match `name` also

    report = e.latest_report(name="Probe 1")
    assert report is None  # must match `quantity` also

    report = e.latest_report(quantity="Temperature", name="Probe 1")
    assert report is not None
    assert report.id == "B"

    report = e.latest_report(quantity="Temperature", name="Probe 1", date="start")
    assert report is not None
    assert report.id == "B"

    report = e.latest_report(quantity="Temperature", name="Probe 1", date="issue")
    assert report is not None
    assert report.id == "C"

    report = e.latest_report(quantity="Humidity", name="Probe 2", date="issue")
    assert report is not None
    assert report.id == "f"


def test_latest_performance_check_multiple_measurand_and_components() -> None:
    e = Equipment(
        calibrations=(
            Measurand(
                quantity="Temperature",
                calibration_interval=5,
                components=(
                    Component(
                        name="Probe 1",
                        performance_checks=(
                            PerformanceCheck(
                                completed_date=date(2020, 5, 4),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="A",
                            ),
                            PerformanceCheck(
                                completed_date=date(2024, 2, 16),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="B",
                            ),
                            PerformanceCheck(
                                completed_date=date(2022, 3, 22),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="C",
                            ),
                        ),
                    ),
                    Component(
                        name="Probe 2",
                        performance_checks=(
                            PerformanceCheck(
                                completed_date=date(2024, 2, 16),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="E",
                            ),
                            PerformanceCheck(
                                completed_date=date(2020, 5, 4),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="D",
                            ),
                            PerformanceCheck(
                                completed_date=date(2022, 3, 22),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="F",
                            ),
                        ),
                    ),
                ),
            ),
            Measurand(
                quantity="Humidity",
                calibration_interval=5,
                components=(
                    Component(
                        name="Probe 1",
                        performance_checks=(
                            PerformanceCheck(
                                completed_date=date(2024, 2, 16),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="b",
                            ),
                            PerformanceCheck(
                                completed_date=date(2022, 3, 22),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="c",
                            ),
                            PerformanceCheck(
                                completed_date=date(2024, 2, 17),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="a",
                            ),
                        ),
                    ),
                    Component(
                        name="Probe 2",
                        performance_checks=(
                            PerformanceCheck(
                                completed_date=date(2024, 2, 16),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="e",
                            ),
                            PerformanceCheck(
                                completed_date=date(2020, 5, 4),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="d",
                            ),
                            PerformanceCheck(
                                completed_date=date(2022, 3, 22),
                                competency=Competency(worker="Me", checker="You", technical_procedure="A"),
                                entered_by="f",
                            ),
                        ),
                    ),
                ),
            ),
        )
    )

    checks = list(e.latest_performance_checks())
    assert len(checks) == 4
    assert checks[0].quantity == "Temperature"
    assert checks[0].name == "Probe 1"
    assert checks[0].entered_by == "B"
    assert checks[0].completed_date == date(2024, 2, 16)
    assert checks[0].competency == Competency(worker="Me", checker="You", technical_procedure="A")

    assert checks[1].quantity == "Temperature"
    assert checks[1].name == "Probe 2"
    assert checks[1].entered_by == "E"

    assert checks[2].quantity == "Humidity"
    assert checks[2].name == "Probe 1"
    assert checks[2].entered_by == "a"

    assert checks[3].quantity == "Humidity"
    assert checks[3].name == "Probe 2"
    assert checks[3].entered_by == "e"

    check = e.latest_performance_check()
    assert check is None

    check = e.latest_performance_check(quantity="Temperature")
    assert check is None  # must match `name` also

    check = e.latest_performance_check(name="Probe 1")
    assert check is None  # must match `quantity` also

    check = e.latest_performance_check(quantity="Temperature", name="Probe 1")
    assert check is not None
    assert check.entered_by == "B"

    check = e.latest_performance_check(quantity="Temperature", name="Probe 2")
    assert check is not None
    assert check.entered_by == "E"

    check = e.latest_performance_check(quantity="Humidity", name="Probe 1")
    assert check is not None
    assert check.entered_by == "a"

    check = e.latest_performance_check(quantity="Humidity", name="Probe 2")
    assert check is not None
    assert check.entered_by == "e"


def test_latest_report_no_reports() -> None:
    e = Equipment(
        calibrations=(
            Measurand(
                quantity="",
                calibration_interval=1,
                components=(
                    Component(
                        name="",
                        adjustments=(
                            Adjustment(details="", date=date(2025, 1, 1)),
                            Adjustment(details="", date=date(2025, 1, 1)),
                        ),
                        digital_reports=(
                            DigitalReport(id="", url="", format=DigitalFormat.MSL_PDF, sha256=""),
                            DigitalReport(id="", url="", format=DigitalFormat.MSL_PDF, sha256=""),
                        ),
                    ),
                ),
            ),
        )
    )

    reports = list(e.latest_reports())
    assert len(reports) == 0

    assert e.latest_report() is None


def test_latest_performance_check_no_checks() -> None:
    e = Equipment(
        calibrations=(
            Measurand(
                quantity="",
                calibration_interval=1,
                components=(
                    Component(
                        name="",
                        adjustments=(
                            Adjustment(details="", date=date(2025, 1, 1)),
                            Adjustment(details="", date=date(2025, 1, 1)),
                        ),
                        digital_reports=(
                            DigitalReport(id="", url="", format=DigitalFormat.MSL_PDF, sha256=""),
                            DigitalReport(id="", url="", format=DigitalFormat.MSL_PDF, sha256=""),
                        ),
                    ),
                ),
            ),
        )
    )

    checks = list(e.latest_performance_checks())
    assert len(checks) == 0

    assert e.latest_performance_check() is None


def test_register_add() -> None:
    table = "<table><type>int,int</type><unit>m,m</unit><header>A,dA</header><data>1,2\n3,4\n</data></table>"

    r = Register()
    assert len(r) == 0
    assert r.team == ""

    r.team = "A-team"
    assert r.team == "A-team"

    r.add(Equipment())
    r.add(Equipment(id="A"))
    r.add(Equipment(id="B", alias="Bob"))
    r.add(
        Equipment(
            id="C",
            alias="Charlie",
            calibrations=(
                Measurand(
                    quantity="Temperature",
                    calibration_interval=5,
                    components=(
                        Component(
                            performance_checks=(
                                PerformanceCheck(
                                    completed_date=date(2024, 4, 10),
                                    competency=Competency(worker="Me", checker="You", technical_procedure="ABC"),
                                    entered_by="Me",
                                    tables=(Table.from_xml(XML(table)),),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )

    assert len(r) == 4
    assert r[0].id == ""
    assert r[1].id == "A"
    assert r[2].id == "B"
    assert r[3].id == "C"
    assert r["A"].id == "A"
    assert r["B"].id == "B"
    assert r["Bob"].id == "B"
    assert r["C"].id == "C"
    assert r["Charlie"].id == "C"

    buffer = BytesIO()
    tree = r.tree(indent=0)
    tree.write(buffer, xml_declaration=True, encoding="us-ascii")

    assert buffer.getvalue() == (
        b"<?xml version='1.0' encoding='us-ascii'?>\n"
        b'<register team="A-team" xmlns="https://measurement.govt.nz/equipment-register">'
        b'<equipment enteredBy="">'
        b"<id />"
        b"<manufacturer />"
        b"<model />"
        b"<serial />"
        b"<description />"
        b"<specifications />"
        b"<location />"
        b"<status>Active</status>"
        b"<loggable>false</loggable>"
        b"<traceable>false</traceable>"
        b"<calibrations />"
        b"<maintenance />"
        b"<alterations />"
        b"<firmware />"
        b"<specifiedRequirements />"
        b"<referenceMaterials />"
        b"<qualityManual />"
        b"</equipment>"
        b'<equipment enteredBy="">'
        b"<id>A</id>"
        b"<manufacturer />"
        b"<model />"
        b"<serial />"
        b"<description />"
        b"<specifications />"
        b"<location />"
        b"<status>Active</status>"
        b"<loggable>false</loggable>"
        b"<traceable>false</traceable>"
        b"<calibrations />"
        b"<maintenance />"
        b"<alterations />"
        b"<firmware />"
        b"<specifiedRequirements />"
        b"<referenceMaterials />"
        b"<qualityManual />"
        b"</equipment>"
        b'<equipment enteredBy="" alias="Bob">'
        b"<id>B</id><manufacturer />"
        b"<model />"
        b"<serial />"
        b"<description />"
        b"<specifications />"
        b"<location />"
        b"<status>Active</status>"
        b"<loggable>false</loggable>"
        b"<traceable>false</traceable>"
        b"<calibrations />"
        b"<maintenance />"
        b"<alterations />"
        b"<firmware />"
        b"<specifiedRequirements />"
        b"<referenceMaterials />"
        b"<qualityManual />"
        b"</equipment>"
        b'<equipment enteredBy="" alias="Charlie">'
        b"<id>C</id>"
        b"<manufacturer />"
        b"<model />"
        b"<serial />"
        b"<description />"
        b"<specifications />"
        b"<location />"
        b"<status>Active</status>"
        b"<loggable>false</loggable>"
        b"<traceable>false</traceable>"
        b"<calibrations>"
        b'<measurand quantity="Temperature" calibrationInterval="5">'
        b'<component name="">'
        b'<performanceCheck completedDate="2024-04-10" enteredBy="Me">'
        b"<competency><worker>Me</worker><checker>You</checker><technicalProcedure>ABC</technicalProcedure></competency>"
        b"<conditions />"
        b"<table><type>int,int</type><unit>m,m</unit><header>A,dA</header><data>1,2\n      3,4\n</data></table>"
        b"</performanceCheck>"
        b"</component>"
        b"</measurand>"
        b"</calibrations>"
        b"<maintenance />"
        b"<alterations />"
        b"<firmware />"
        b"<specifiedRequirements />"
        b"<referenceMaterials />"
        b"<qualityManual />"
        b"</equipment>"
        b"</register>"
    )


def test_register_cannot_merge() -> None:
    reg1 = StringIO('<?xml version="1.0" encoding="utf-8"?>\n<register team="A" />')
    reg2 = StringIO('<?xml version="1.0" encoding="utf-8"?>\n<register team="B" />')
    with pytest.raises(ValueError, match=r"different teams, 'A' != 'B'"):
        _ = Register(reg1, reg2)


def test_register_tree_negative_indent() -> None:
    with pytest.raises(ValueError, match=r">= 0, got -1"):
        _ = Register().tree(indent=-1)


@pytest.mark.parametrize(
    ("string", "years", "expected"),
    [
        ("2020-02-06", 2, date(2022, 2, 6)),
        ("2020-02-06", 2.5, date(2022, 8, 6)),
        ("2020-07-06", 0.8, date(2021, 4, 6)),
        ("2020-07-06", 2.8, date(2023, 4, 6)),
        ("2020-12-06", 1, date(2021, 12, 6)),
        ("2020-12-06", 2, date(2022, 12, 6)),
        ("2020-12-06", 2.3, date(2023, 3, 6)),
        ("2020-07-06", 5.5, date(2026, 1, 6)),
        ("2020-09-30", 3.9, date(2024, 7, 30)),
        ("2023-04-23", 0, date(2023, 4, 23)),
        ("2024-02-29", 1, date(2025, 2, 28)),  # leap year as input
        ("2025-01-31", 0.25, date(2025, 4, 30)),  # 31 becomes 30 for April
    ],
)
def test_future_date(string: str, years: float, expected: date) -> None:
    date = datetime.strptime(string, "%Y-%m-%d").date()  # noqa: DTZ007
    assert _future_date(date, years) == expected


def test_report_is_calibration_due() -> None:
    # NOTE: this test might fail if run on a leap year day, Feb 29
    # if so, ignore the issue and run again tomorrow

    # the value used for calibration_interval just needs to be >0 or =0
    # the actual value is not used in is_calibration_due()

    today = date.today()  # noqa: DTZ011

    d = today.replace(year=today.year + 1)
    latest = Latest(next_calibration_date=d, calibration_interval=1, name="", quantity="")
    assert not latest.is_calibration_due()
    assert not latest.is_calibration_due(1)
    assert not latest.is_calibration_due(11)
    assert latest.is_calibration_due(12)
    assert latest.is_calibration_due(13)

    d = today.replace(year=today.year + 2)
    latest = Latest(next_calibration_date=d, calibration_interval=1, name="", quantity="")
    assert not latest.is_calibration_due()
    assert not latest.is_calibration_due(23)
    assert latest.is_calibration_due(24)
    assert latest.is_calibration_due(25)

    d = date(1875, 5, 20)
    latest = Latest(next_calibration_date=d, calibration_interval=0, name="", quantity="")
    assert not latest.is_calibration_due()
    assert not latest.is_calibration_due(1000)


def test_equipment_repr() -> None:
    path = Path(__file__).parent / "resources" / "mass"
    r = Register(path / "register.xml", path / "register2.xml")
    assert r.team == "Mass"
    assert len(r) == 3
    assert str(r) == "<Register team='Mass' (3 equipment)>"
    assert repr(r["MSLE.M.001"]) == "<Equipment manufacturer='MSL', model='ABC', serial='123'>"
    assert (
        repr(r["MSLE.M.092"])
        == "<Equipment manufacturer='The Company Name', model='Model', serial='Serial' (4 reports)>"
    )
    assert (
        repr(r["MSLE.M.100"])
        == "<Equipment manufacturer='Measurement', model='Stds', serial='Lab' (2 adjustments, 1 digital report, 1 performance check, 1 report)>"  # noqa: E501
    )


def test_equipment_str_element_sources() -> None:
    path = Path(__file__).parent / "resources" / "mass"
    r = Register(str(path / "register.xml"), XML((path / "register2.xml").read_text()))
    assert r.team == "Mass"
    assert len(r) == 3
    assert str(r) == "<Register team='Mass' (3 equipment)>"
    assert repr(r["MSLE.M.001"]) == "<Equipment manufacturer='MSL', model='ABC', serial='123'>"
    assert (
        repr(r["MSLE.M.092"])
        == "<Equipment manufacturer='The Company Name', model='Model', serial='Serial' (4 reports)>"
    )
    assert (
        repr(r["MSLE.M.100"])
        == "<Equipment manufacturer='Measurement', model='Stds', serial='Lab' (2 adjustments, 1 digital report, 1 performance check, 1 report)>"  # noqa: E501
    )


@pytest.mark.parametrize(
    ("pattern", "expect"),
    [
        ("ambient", "092"),  # description
        ("Measurement", "100"),  # manufacturer
        ("ABC", "001"),  # model
        ("Serial", "092"),  # serial
        (r"M\.1", "100"),  # equipment id
        ("CMM", "001"),  # location
        ("Voltage", "100"),  # quantity
        ("Probe 1", "092"),  # name
        ("McDowall", "001"),  # equipment enteredBy
        ("Lawson", "100"),  # performanceCheck checkedBy
        ("Young", "092"),  # alteration performedBy
        ("torpedo", "100"),  # file comment
        ("PDF/A-3", "100"),  # digital report format
        ("filter", "100"),  # adjustment details
        ("helium", "092"),  # maintenance completed task
        ("Whatever", "092"),  # assetNumber
        ("Secret", "092"),  # serviceAgent
        (r"P\.\d{3}\.\d{3}", "100"),  # qualityManual technicalProcedures
        ("favourite", "092"),  # cvdEquation comment
        ("T-Rex", "092"),  # equation comment
        ("Raptor", "100"),  # equation comment
        ("Elephant", "092"),  # table comment
        ("Dubuis", "092"),  # maintenance completed performedBy  # cSpell: ignore Dubuis
        ("banana", "100"),  # maintenance planned task
        ("Knight", "100"),  # maintenance planned performedBy
        ("Did work", "092"),  # alteration details
        ("Ellie", "092"),  # report enteredBy
        ("Yang", "092"),  # report checkedBy
        ("SI/2024", "092"),  # report id
        ("Stewart", "100"),  # performanceCheck enteredBy
        ("Electrical/2025", "100"),  # digitalReport id
        ("Racoon", "100"),  # digitalReport comment
    ],
)
def test_register_find(pattern: str, expect: str) -> None:
    path = Path(__file__).parent / "resources" / "mass"
    r = Register(path / "register.xml", path / "register2.xml")
    found = list(r.find(pattern))
    assert len(found) == 1
    assert found[0].id == f"MSLE.M.{expect}"


def test_register_find_flags() -> None:
    path = Path(__file__).parent / "resources" / "mass"
    r = Register(path / "register.xml", path / "register2.xml")

    found = list(r.find("Hygrometer"))
    assert len(found) == 1
    assert found[0].id == "MSLE.M.092"

    found = list(r.find("hygrometer", flags=re.IGNORECASE))
    assert len(found) == 1
    assert found[0].id == "MSLE.M.092"


def test_register_find_multiple() -> None:
    path = Path(__file__).parent / "resources" / "mass"
    r = Register(path / "register.xml", path / "register2.xml")
    found = list(r.find("Hygrometer|AC"))
    assert len(found) == 2
    assert found[0].id == "MSLE.M.092"
    assert found[1].id == "MSLE.M.100"


def test_register_find_none() -> None:
    path = Path(__file__).parent / "resources" / "mass"
    r = Register(path / "register.xml", path / "register2.xml")
    found = list(r.find("peanut"))
    assert len(found) == 0


def test_register_get_none() -> None:
    r = Register(Path(__file__).parent / "resources" / "mass" / "register.xml")
    assert r.get(100) is None
    assert r.get("unknown-alias") is None


@pytest.mark.parametrize(
    ("item", "eid"),
    [
        ("MSLE.M.001", "MSLE.M.001"),
        (0, "MSLE.M.001"),
        ("Bob", "MSLE.M.092"),
        (1, "MSLE.M.092"),
    ],
)
def test_register_get_some(item: str | int, eid: str) -> None:
    r = Register(Path(__file__).parent / "resources" / "mass" / "register.xml")
    e = r.get(item)
    assert e is not None
    assert e.id == eid


def test_equipment_connection_none() -> None:
    connections.clear()

    with pytest.raises(KeyError, match=r"eid='MSLE.O.231' cannot be found"):
        _ = Equipment(id="MSLE.O.231").connect()

    connections.add(*("tests/resources/connections.xml",))

    with pytest.raises(OSError, match=r"Cannot find 'library.dll' for libtype='cdll'"):
        _ = Equipment(id="MSLE.O.231").connect()

    connections.clear()
