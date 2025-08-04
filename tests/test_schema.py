from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from xml.etree.ElementTree import XML, Element, tostring

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
    Competency,
    Conditions,
    Deserialised,
    DigitalFormat,
    DigitalReport,
    Equation,
    Evaluable,
    File,
    Financial,
    Firmware,
    Maintenance,
    QualityManual,
    Range,
    ReferenceMaterials,
    Specifications,
    SpecifiedRequirements,
    Status,
)

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


def test_financial_empty() -> None:
    text = b"<financial />"
    f = Financial.from_xml(XML(text))
    assert f.asset_number == ""
    assert f.warranty_expiration_date is None
    assert f.year_purchased == 0
    assert tostring(f.to_xml()) == text


def test_financial_all() -> None:
    text = (
        b"<financial>"
        b"<assetNumber>7265817</assetNumber>"
        b"<warrantyExpirationDate>2026-08-01</warrantyExpirationDate>"
        b"<yearPurchased>2025</yearPurchased>"
        b"</financial>"
    )

    f = Financial.from_xml(XML(text))
    assert f.asset_number == "7265817"
    assert f.warranty_expiration_date == date(2026, 8, 1)
    assert f.year_purchased == 2025  # noqa: PLR2004
    assert tostring(f.to_xml()) == text


def test_financial_asset_number() -> None:
    text = b"<financial><assetNumber>Anything</assetNumber></financial>"
    f = Financial.from_xml(XML(text))
    assert f.asset_number == "Anything"
    assert f.warranty_expiration_date is None
    assert f.year_purchased == 0
    assert tostring(f.to_xml()) == text


def test_financial_warranty_expiration_date() -> None:
    text = b"<financial><warrantyExpirationDate>2026-08-01</warrantyExpirationDate></financial>"
    f = Financial.from_xml(XML(text))
    assert f.asset_number == ""
    assert f.warranty_expiration_date == date(2026, 8, 1)
    assert f.year_purchased == 0
    assert tostring(f.to_xml()) == text


def test_financial_year_purchased() -> None:
    text = b"<financial><yearPurchased>2025</yearPurchased></financial>"
    f = Financial.from_xml(XML(text))
    assert f.asset_number == ""
    assert f.warranty_expiration_date is None
    assert f.year_purchased == 2025  # noqa: PLR2004
    assert tostring(f.to_xml()) == text


@pytest.mark.parametrize("date", ["26-08-01", "", "Sunday"])
def test_financial_invalid_date(date: str) -> None:
    text = f"<financial><warrantyExpirationDate>{date}</warrantyExpirationDate></financial>"
    with pytest.raises(ValueError, match=r"Invalid isoformat string"):
        _ = Financial.from_xml(XML(text))


@pytest.mark.parametrize("year", ["26-08-01", "2k"])
def test_financial_invalid_year(year: str) -> None:
    text = f"<financial><yearPurchased>{year}</yearPurchased></financial>"
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
    assert len(m.planned) == 2  # noqa: PLR2004
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
    assert len(m.completed) == 2  # noqa: PLR2004
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
    assert len(qm.accessories) == 2  # noqa: PLR2004
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
        b"<financial><assetNumber>abc</assetNumber><yearPurchased>2000</yearPurchased></financial>"
        b"</qualityManual>"
    )
    qm = QualityManual.from_xml(XML(text))
    assert len(qm.accessories) == 0
    assert qm.accessories.attrib == {}
    assert qm.documentation == ""
    assert qm.financial.asset_number == "abc"
    assert qm.financial.warranty_expiration_date is None
    assert qm.financial.year_purchased == 2000  # noqa: PLR2004
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
    assert r.minimum == -100  # noqa: PLR2004
    assert r.maximum == 100  # noqa: PLR2004
    assert r == (-100, 100)
    assert r.check_within_range(value) is None


@pytest.mark.parametrize("value", [-1, 2e6, [1.001, 2], np.array([[11, -22], [-33, 44]])])
def test_range_bounds_invalid(value: float | ArrayLike) -> None:
    r = Range(0, 1)
    expect = str(value) if isinstance(value, (int, float)) else "sequence"
    with pytest.raises(ValueError, match=f"{expect} is not within the range"):
        r.check_within_range(value)


def test_evaluatable_constant() -> None:
    e = Evaluable("0.5/2", ())
    assert e.equation == "0.5/2"
    assert e.ranges == {}
    assert e() == 0.5 / 2


def test_evaluatable_1d_no_range() -> None:
    e = Evaluable("2*pi*sin(x+0.1) - cos(x/2)", ("x",))
    assert e(x=0.1) == 2 * np.pi * np.sin(0.1 + 0.1) - np.cos(0.1 / 2)


def test_evaluatable_1d() -> None:
    e = Evaluable("2*pi*sin(x+0.1) - cos(x/2)", ("x",), ranges={"x": Range(0, 1)})
    assert e(x=0.1) == 2 * np.pi * np.sin(0.1 + 0.1) - np.cos(0.1 / 2)

    # ok to include unused variables
    assert e(x=0.1, y=9.1, z=-0.3) == 2 * np.pi * np.sin(0.1 + 0.1) - np.cos(0.1 / 2)

    expected = 2 * np.pi * np.sin(np.array([0.1, 0.2]) + 0.1) - np.cos(np.array([0.1, 0.2]) / 2)
    assert np.array_equal(e(x=[0.1, 0.2]), expected)

    with pytest.raises(ValueError, match="-1 is not within the range"):
        _ = e(x=-1)

    with pytest.raises(NameError, match="'x' is not defined"):
        _ = e()

    x = -1
    expect = 2 * np.pi * np.sin(x + 0.1) - np.cos(x / 2)
    assert e(x=x, check_range=False) == expect
    assert e(x=x, check_range=False, this_kwarg_is_ignored=np.nan) == expect


def test_evaluatable_2d() -> None:
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

    with pytest.raises(ValueError, match="-1 is not within the range"):
        _ = e(rh=-1, t=20)
    with pytest.raises(ValueError, match="200 is not within the range"):
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
    assert e.degree_freedom == 100.2  # noqa: PLR2004
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
    assert d.value["x"].u == 0.1  # noqa: PLR2004
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
    assert d.value["x"].u == 0.1  # noqa: PLR2004
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


# test Measurand, Component, PerformanceCheck, Report
