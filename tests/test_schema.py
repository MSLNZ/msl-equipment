from datetime import date
from xml.etree.ElementTree import Element, tostring

import pytest

from msl.equipment import Alteration


def test_alteration() -> None:
    e = Element("ignored", attrib={"date": "2024-10-16", "performedBy": "Chris, MSL"})
    e.text = "Replace blown op-amp with LMP7721"

    a = Alteration.from_xml(e)
    assert a.date == date(2024, 10, 16)
    assert a.details == "Replace blown op-amp with LMP7721"
    assert a.performed_by == "Chris, MSL"

    e = a.to_xml()
    assert e.tag == "alteration"
    assert e.attrib == {"date": "2024-10-16", "performedBy": "Chris, MSL"}
    assert e.text == "Replace blown op-amp with LMP7721"
    assert (
        tostring(e)
        == b'<alteration date="2024-10-16" performedBy="Chris, MSL">Replace blown op-amp with LMP7721</alteration>'
    )


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
