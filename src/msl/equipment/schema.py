"""Classes for the equipment-register schema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from enum import Enum
from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, SubElement

if TYPE_CHECKING:
    from typing import TypeVar

    C = TypeVar("C", bound="AnyElement")


class Status(Enum):
    """Represents the [status][type_statusEnumerationString]{:target="_blank"} enumeration in an equipment register.

    Attributes:
        Active (str): The equipment is operable and may be used.
        Damaged (str): The equipment is damaged and is no longer usable.
        Disposed (str): The equipment has been disposed of and is no longer at available
            (e.g., the equipment was sent to the landfill or to be recycled)
        Dormant (str): The equipment is still operable, it is no longer in use but may be used again
            (e.g., the equipment was replaced with a newer model, and it is kept as a backup)
        Lost (str): The equipment is lost, but if found may be put back into service.
        Retired (str): The equipment is still operable, but there are no intentions of using it again
            (e.g., the equipment depends on other equipment that is not available or is no longer manufactured).
    """

    Active = "Active"
    Damaged = "Damaged"
    Disposed = "Disposed"
    Dormant = "Dormant"
    Lost = "Lost"
    Retired = "Retired"


class AnyElement(Element):
    """Represents the [any][type_any]{:target="_blank"} type in the XML Schema Definition.

    It is simply a subclass of [Element][xml.etree.ElementTree.Element]{:target="_blank"}.
    """

    @classmethod
    def from_xml(cls: type[C], element: Element[str]) -> C:  # noqa: PYI019
        """Copies an XML element.

        Parameters:
            element: An XML element from an equipment register.

        Returns:
            The sub-class instance.
        """
        c = cls(element.tag, attrib=element.attrib)
        c.tail = element.tail
        c.text = element.text
        c.extend(element)
        return c


class Accessories(AnyElement):
    """Additional accessories that may be required to use the equipment.

    Since this class is currently represented by the [any][type_any]{:target="_blank"} type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element]{:target="_blank"},
    and it may be updated to be a more specific class at a later date.
    """


@dataclass(frozen=True)
class Alteration:
    """Represents the [alteration][type_alteration]{:target="_blank"} element in an equipment register.

    Parameters:
        date: The date that the alteration was performed.
        details: The details of the alteration.
        performed_by: The person or company that performed the alteration.
    """

    date: _date
    details: str
    performed_by: str = ""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Alteration:
        """Convert an XML element into an [Alteration][msl.equipment.schema.Alteration] instance.

        Parameters:
            element: An [alteration][type_alteration]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [Alteration][msl.equipment.schema.Alteration] instance.
        """
        return cls(
            date=_date.fromisoformat(element.attrib["date"]),
            details=element.text or "",
            performed_by=element.attrib["performedBy"],
        )

    def to_xml(self) -> Element[str]:
        """Convert the [Alteration][msl.equipment.schema.Alteration] class into an XML element.

        Returns:
            The [Alteration][msl.equipment.schema.Alteration] as an XML element.
        """
        e = Element("alteration", attrib={"date": self.date.isoformat(), "performedBy": self.performed_by})
        e.text = self.details
        return e


@dataclass(frozen=True)
class Financial:
    """Represents the [financial][type_financial]{:target="_blank"} element in an equipment register.

    Parameters:
        asset_number: The asset number in the financial system.
        warranty_expiration_date: Approximate date that the warranty expires.
        year_purchased: Approximate year that the equipment was purchased.
    """

    asset_number: str = ""
    warranty_expiration_date: _date | None = None
    year_purchased: int = 0

    @classmethod
    def from_xml(cls, element: Element[str]) -> Financial:
        """Convert an XML element into a [Financial][msl.equipment.schema.Financial] instance.

        Parameters:
            element: A [financial][type_financial]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [Financial][msl.equipment.schema.Financial] instance.
        """
        # Schema defines <financial> using xsd:all, which allows sub-elements to appear (or not appear) in any order
        # Using str.endswith() allows for ignoring XML namespaces that may be associated with each tag
        asset, warranty, year = "", None, 0
        for child in element:
            if child.tag.endswith("assetNumber"):
                asset = child.text or ""
            elif child.tag.endswith("warrantyExpirationDate"):
                warranty = _date.fromisoformat(child.text or "")
            else:
                year = int(child.text or 0)
        return cls(asset_number=asset, warranty_expiration_date=warranty, year_purchased=year)

    def to_xml(self) -> Element[str]:
        """Convert the [Financial][msl.equipment.schema.Financial] class into an XML element.

        Returns:
            The [Financial][msl.equipment.schema.Financial] as an XML element.
        """
        e = Element("financial")

        if self.asset_number:
            an = SubElement(e, "assetNumber")
            an.text = self.asset_number

        if self.warranty_expiration_date is not None:
            wed = SubElement(e, "warrantyExpirationDate")
            wed.text = self.warranty_expiration_date.isoformat()

        if self.year_purchased > 0:
            yp = SubElement(e, "yearPurchased")
            yp.text = str(self.year_purchased)

        return e


@dataclass(frozen=True)
class Firmware:
    """Represents a [firmware][type_firmware]{:target="_blank"} `<version>` sub-element in an equipment register.

    Parameters:
        version: Firmware version number.
        date: The date that the firmware was initially at or changed to `version`.
    """

    version: str
    date: _date

    @classmethod
    def from_xml(cls, element: Element[str]) -> Firmware:
        """Convert an XML element into a [Firmware][msl.equipment.schema.Firmware] instance.

        Parameters:
            element: A [firmware][type_firmware]{:target="_blank"} `<version>` XML sub-element
                from an equipment register.

        Returns:
            The [Firmware][msl.equipment.schema.Firmware] instance.
        """
        return cls(version=element.text or "", date=_date.fromisoformat(element.attrib["date"]))

    def to_xml(self) -> Element[str]:
        """Convert the [Firmware][msl.equipment.schema.Firmware] class into a `<version>` XML element.

        Returns:
            The [Firmware][msl.equipment.schema.Firmware] as a `<version>` XML element.
        """
        e = Element("version", attrib={"date": self.date.isoformat()})
        e.text = self.version
        return e


@dataclass(frozen=True)
class Maintenance:
    """Represents the [maintenance][type_maintenance]{:target="_blank"} element in an equipment register."""


@dataclass(frozen=True)
class Measurand:
    """Represents the [measurand][type_measurand]{:target="_blank"} element in an equipment register."""


@dataclass(frozen=True)
class QualityManual:
    """Represents the [qualityManual][type_qualityManual]{:target="_blank"} element in an equipment register.

    Parameters:
        accessories: Additional accessories that may be required to use the equipment.
        documentation: Information (such as URLs) about the manuals, datasheets, etc. for the equipment.
        financial: Financial information about the equipment.
        personnel_restrictions: Information about the people (or team) who are qualified to use the equipment.
        service_agent: Information about the people or company that are qualified to perform alterations and/or
            maintenance to the equipment.
        technical_procedures: The technical procedure(s) that depend on this equipment.
    """

    accessories: Accessories | None = None
    documentation: str = ""
    financial: Financial | None = None
    personnel_restrictions: str = ""
    service_agent: str = ""
    technical_procedures: tuple[str, ...] = ()

    @classmethod
    def from_xml(cls, element: Element[str]) -> QualityManual:
        """Convert an XML element into an [QualityManual][msl.equipment.schema.QualityManual] instance.

        Parameters:
            element: A [qualityManual][type_qualityManual]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [QualityManual][msl.equipment.schema.QualityManual] instance.
        """
        # Schema defines <qualityManual> using xsd:all, which allows sub-elements to appear (or not appear) in any order
        # Using str.endswith() allows for ignoring XML namespaces that may be associated with each tag
        tp: tuple[str, ...]
        a, d, f, pr, sa, tp = None, "", None, "", "", ()
        for child in element:
            if child.tag.endswith("accessories"):
                a = Accessories.from_xml(child)
            elif child.tag.endswith("documentation"):
                d = child.text or ""
            elif child.tag.endswith("financial"):
                f = Financial.from_xml(child)
            elif child.tag.endswith("personnelRestrictions"):
                pr = child.text or ""
            elif child.tag.endswith("serviceAgent"):
                sa = child.text or ""
            else:
                tp = tuple(i.text for i in child if i.text)

        return cls(
            accessories=a,
            documentation=d,
            financial=f,
            personnel_restrictions=pr,
            service_agent=sa,
            technical_procedures=tp,
        )

    def to_xml(self) -> Element[str]:
        """Convert the [QualityManual][msl.equipment.schema.QualityManual] class into an XML element.

        Returns:
            The [QualityManual][msl.equipment.schema.QualityManual] as an XML element.
        """
        e = Element("qualityManual")

        if self.accessories is not None:
            e.append(self.accessories)

        if self.documentation:
            d = SubElement(e, "documentation")
            d.text = self.documentation

        if self.financial is not None:
            e.append(self.financial.to_xml())

        if self.personnel_restrictions:
            pr = SubElement(e, "personnelRestrictions")
            pr.text = self.personnel_restrictions

        if self.service_agent:
            sa = SubElement(e, "serviceAgent")
            sa.text = self.service_agent

        if self.technical_procedures:
            tp = SubElement(e, "technicalProcedures")
            for procedure in self.technical_procedures:
                sub = SubElement(tp, "id")
                sub.text = procedure

        return e


class ReferenceMaterials(AnyElement):
    """Documentation of reference materials, results, acceptance criteria, relevant dates and the period of validity.

    Since this class is currently represented by the [any][type_any]{:target="_blank"} type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element]{:target="_blank"},
    and it may be updated to be a more specific class at a later date.
    """


class Specifications(AnyElement):
    """Specifications provided by the manufacturer of the equipment.

    Typically, the specifications are specified on the website, datasheet and/or technical notes that a
    manufacturer provides.

    Since this class is currently represented by the [any][type_any]{:target="_blank"} type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element]{:target="_blank"},
    and it may be updated to be a more specific class at a later date.
    """


class SpecifiedRequirements(AnyElement):
    """Verification that equipment conforms with specified requirements before being placed or returned into service.

    Since this class is currently represented by the [any][type_any]{:target="_blank"} type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element]{:target="_blank"},
    and it may be updated to be a more specific class at a later date.
    """


@dataclass(frozen=True)
class Equipment:
    """Represents the [equipment][type_equipment]{:target="_blank"} element in an equipment register.

    Parameters:
        alias: An alternative name to associate with the equipment.
        keywords: Keywords that describe the equipment.
        id: Identity in an equipment register.
        manufacturer: Name of manufacturer.
        model: Manufacturer's model number (or type identification).
        serial: Manufacturer's serial number (or other unique identification).
        description: A short description about the equipment.
        specifications: Specifications provided by the manufacturer of the equipment.
        location: The usual location (laboratory) that the equipment is found in.
        status: The status of the equipment is an indication of whether the equipment is active (in use)
            or inactive (not in use).
        loggable: Whether measurements from the equipment should be logged. Equipment that monitor
            (for example) pressure, temperature or humidity of a laboratory environment are considered
            as loggable.
        traceable: Whether the equipment is used for a traceable measurement.
        calibrations: The calibration history.
        maintenance: The maintenance history and maintenance plan.
        alterations: The alteration history.
        firmware: The firmware version history.
        specified_requirements: Verification that equipment conforms with specified requirements before
            being placed or returned into service.
        reference_materials: Documentation of reference materials, results, acceptance criteria, relevant
            dates and the period of validity.
        quality_manual: Information that is specified in Section 4.3.6 of the MSL Quality Manual.
    """

    alias: str = ""
    keywords: tuple[str, ...] = ()
    id: str = ""
    manufacturer: str = ""
    model: str = ""
    serial: str = ""
    description: str = ""
    specifications: Specifications | None = None
    location: str = ""
    status: Status = Status.Active
    loggable: bool = False
    traceable: bool = False
    calibrations: tuple[Measurand, ...] = ()
    maintenance: tuple[Maintenance, ...] = ()
    alterations: tuple[Alteration, ...] = ()
    firmware: tuple[Firmware, ...] = ()
    specified_requirements: SpecifiedRequirements | None = None
    reference_materials: ReferenceMaterials | None = None
    quality_manual: QualityManual | None = None
