from datetime import date
from xml.etree.ElementTree import XML, Element, tostring

import pytest

from msl.equipment import Alteration, Financial, Firmware, Maintenance, QualityManual, Status


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
    assert qm.accessories is None
    assert qm.documentation == ""
    assert qm.financial is None
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
    assert qm.accessories is not None
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
    assert qm.financial is None
    assert qm.personnel_restrictions == ""
    assert qm.service_agent == ""
    assert len(qm.technical_procedures) == 0
    assert tostring(qm.to_xml()) == text


def test_quality_manual_documentation() -> None:
    text = b"<qualityManual><documentation>https://link.com</documentation></qualityManual>"
    qm = QualityManual.from_xml(XML(text))
    assert qm.accessories is None
    assert qm.documentation == "https://link.com"
    assert qm.financial is None
    assert qm.personnel_restrictions == ""
    assert qm.service_agent == ""
    assert len(qm.technical_procedures) == 0
    assert tostring(qm.to_xml()) == text


def test_quality_manual_financial() -> None:
    text = b"<qualityManual><financial><yearPurchased>1</yearPurchased></financial></qualityManual>"
    qm = QualityManual.from_xml(XML(text))
    assert qm.accessories is None
    assert qm.documentation == ""
    assert qm.financial is not None
    assert qm.financial.asset_number == ""
    assert qm.financial.warranty_expiration_date is None
    assert qm.financial.year_purchased == 1
    assert qm.personnel_restrictions == ""
    assert qm.service_agent == ""
    assert len(qm.technical_procedures) == 0
    assert tostring(qm.to_xml()) == text


def test_quality_manual_personnel_restrictions() -> None:
    text = b"<qualityManual><personnelRestrictions>Light team</personnelRestrictions></qualityManual>"
    qm = QualityManual.from_xml(XML(text))
    assert qm.accessories is None
    assert qm.documentation == ""
    assert qm.financial is None
    assert qm.personnel_restrictions == "Light team"
    assert qm.service_agent == ""
    assert len(qm.technical_procedures) == 0
    assert tostring(qm.to_xml()) == text


def test_quality_manual_service_agent() -> None:
    text = b"<qualityManual><serviceAgent>MSL</serviceAgent></qualityManual>"
    qm = QualityManual.from_xml(XML(text))
    assert qm.accessories is None
    assert qm.documentation == ""
    assert qm.financial is None
    assert qm.personnel_restrictions == ""
    assert qm.service_agent == "MSL"
    assert len(qm.technical_procedures) == 0
    assert tostring(qm.to_xml()) == text


def test_quality_manual_technical_procedures() -> None:
    text = b"<qualityManual><technicalProcedures><id>A</id><id>B</id><id>C.c</id></technicalProcedures></qualityManual>"
    qm = QualityManual.from_xml(XML(text))
    assert qm.accessories is None
    assert qm.documentation == ""
    assert qm.financial is None
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
