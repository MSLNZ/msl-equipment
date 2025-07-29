"""Classes for the equipment-register schema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from xml.etree.ElementTree import Element


@dataclass(frozen=True)
class Alteration:
    """Represents the [alteration][type_alteration]{:target="_blank"} element in an equipment register.

    !!! type "Satisfy ISO/IEC 17025:2017 Clause 6.4.13(h)."
        Details of any damage, malfunction, modification to, or repair of, the equipment.

    Parameters:
        date: The date that the alteration was performed.
        details: The details of the alteration.
        performed_by: The person or company that performed the alteration.
    """

    date: _date
    details: str
    performed_by: str

    @classmethod
    def from_xml(cls, element: Element) -> Alteration:
        """Returns an [Alteration][msl.equipment.schema.Alteration] instance from an XML element.

        Parameters:
            element: An [alteration][type_alteration]{:target="_blank"} XML element from an equipment register.
        """
        return cls(
            date=_date.fromisoformat(element.attrib["date"]),
            details=element.text or "",
            performed_by=element.attrib["performedBy"],
        )

    def to_xml(self) -> Element:
        """Convert the [Alteration][msl.equipment.schema.Alteration] to an XML element.

        Returns:
            The [Alteration][msl.equipment.schema.Alteration] as an XML element.
        """
        e = Element("alteration", attrib={"date": self.date.isoformat(), "performedBy": self.performed_by})
        e.text = self.details
        return e


@dataclass(frozen=True)
class Equipment:
    """Represents the [equipment][type_equipment]{:target="_blank"} element in an equipment register.

    !!! type "Satisfy ISO/IEC 17025:2017 Clause 6.4.13 as well as the MSL Quality Manual Section 4.3.6."

    Parameters:
        alterations: The history of alterations that were performed.
    """

    alterations: tuple[Alteration, ...] = ()
