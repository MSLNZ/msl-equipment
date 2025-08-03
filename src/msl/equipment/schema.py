from __future__ import annotations  # noqa: D100

from dataclasses import dataclass
from datetime import date as _date
from enum import Enum
from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, SubElement

if TYPE_CHECKING:
    from typing import TypeVar

    A = TypeVar("A", bound="Any")


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


class Any(Element):
    """Base class that represents the [any][type_any]{:target="_blank"} type in the XML Schema Definition."""

    def __init__(self, **attributes: str) -> None:
        """Base class that represents the [any][type_any]{:target="_blank"} type in the XML Schema Definition.

        Args:
            attributes: All keyword arguments are used as the element's attributes.
        """
        super().__init__(self.tag, attrib={}, **attributes)

    @classmethod
    def from_xml(cls: type[A], element: Element[str]) -> A:  # noqa: PYI019
        """Copies an XML element into the [Any][msl.equipment.schema.Any] subclass.

        Args:
            element: An XML element from an equipment register.

        Returns:
            The subclass instance.
        """
        c = cls(**element.attrib)
        c.tail = element.tail
        c.text = element.text
        c.extend(element)
        return c


class Accessories(Any):
    """Additional accessories that may be required to use the equipment.

    Since this class is currently represented by the [any][type_any]{:target="_blank"} type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element]{:target="_blank"}.
    It may be updated to be a more specific class at a later date.
    """

    tag: str = "accessories"
    """The element's name."""


@dataclass(frozen=True)
class Alteration:
    """Represents the [alteration][type_alteration]{:target="_blank"} element in an equipment register.

    Args:
        date: The date that the alteration was performed.
        details: The details of the alteration.
        performed_by: The person or company that performed the alteration.
    """

    date: _date
    """The date that the alteration was performed."""

    details: str
    """The details of the alteration."""

    performed_by: str
    """The person or company that performed the alteration."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Alteration:
        """Convert an XML element into an [Alteration][msl.equipment.schema.Alteration] instance.

        Args:
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


class AcceptanceCriteria(Any):
    """Represents the acceptance criteria in a calibration [report][type_report]{:target="_blank"}.

    Since this class is currently represented by the [any][type_any]{:target="_blank"} type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element]{:target="_blank"}.
    It may be updated to be a more specific class at a later date.
    """

    tag: str = "acceptanceCriteria"
    """The element's name."""


class Conditions(Any):
    """Conditions under which a [performance check][type_performanceCheck]{:target="_blank"} or calibration [report][type_report]{:target="_blank"} is valid.

    Since this class is currently represented by the [any][type_any]{:target="_blank"} type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element]{:target="_blank"}.
    It may be updated to be a more specific class at a later date.
    """  # noqa: E501

    tag: str = "conditions"
    """The element's name."""


@dataclass(frozen=True)
class Financial:
    """Represents the [financial][type_financial]{:target="_blank"} element in an equipment register.

    Args:
        asset_number: The asset number in the financial system.
        warranty_expiration_date: Approximate date that the warranty expires.
        year_purchased: Approximate year that the equipment was purchased.
            A value of `0` represents that the year is unknown.
    """

    asset_number: str = ""
    """The asset number in the financial system."""

    warranty_expiration_date: _date | None = None
    """Approximate date that the warranty expires."""

    year_purchased: int = 0
    """Approximate year that the equipment was purchased. A value of `0` represents that the year is unknown."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Financial:
        """Convert an XML element into a [Financial][msl.equipment.schema.Financial] instance.

        Args:
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

    Args:
        version: Firmware version number.
        date: The date that the firmware was initially at or changed to `version`.
    """

    version: str
    """Firmware version number."""

    date: _date
    """The date that the firmware was initially at or changed to `version`."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Firmware:
        """Convert an XML element into a [Firmware][msl.equipment.schema.Firmware] instance.

        Args:
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
class CompletedTask:
    """Represents the [completedTask][type_completedTask]{:target="_blank"} element in an equipment register.

    Args:
        task: A description of the task that was completed.
        due_date: The date that the maintenance task was due to be completed.
        performed_by: The person or company that performed the maintenance task.
        completed_date: The date that the maintenance task was completed.
    """

    task: str
    """A description of the task that was completed."""

    due_date: _date
    """The date that the maintenance task was due to be completed."""

    performed_by: str
    """The person or company that performed the maintenance task."""

    completed_date: _date
    """The date that the maintenance task was completed."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> CompletedTask:
        """Convert an XML element into a [CompletedTask][msl.equipment.schema.CompletedTask] instance.

        Args:
            element: A [completedTask][type_completedTask]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [CompletedTask][msl.equipment.schema.CompletedTask] instance.
        """
        return cls(
            task=element.text or "",
            due_date=_date.fromisoformat(element.attrib["dueDate"]),
            performed_by=element.attrib["performedBy"],
            completed_date=_date.fromisoformat(element.attrib["completedDate"]),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [CompletedTask][msl.equipment.schema.CompletedTask] class into an XML element.

        Returns:
            The [CompletedTask][msl.equipment.schema.CompletedTask] as an XML element.
        """
        attrib = {
            "dueDate": self.due_date.isoformat(),
            "completedDate": self.completed_date.isoformat(),
            "performedBy": self.performed_by,
        }

        e = Element("task", attrib=attrib)
        e.text = self.task
        return e


@dataclass(frozen=True)
class PlannedTask:
    """Represents the [plannedTask][type_plannedTask]{:target="_blank"} element in an equipment register.

    Args:
        task: A description of the task that is planned.
        due_date: The date that the planned maintenance task is due to be completed.
        performed_by: The person or company that will perform the planned maintenance task.
    """

    task: str
    """A description of the task that is planned."""

    due_date: _date
    """The date that the planned maintenance task is due to be completed."""

    performed_by: str = ""
    """The person or company that will perform the planned maintenance task."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> PlannedTask:
        """Convert an XML element into a [PlannedTask][msl.equipment.schema.PlannedTask] instance.

        Args:
            element: A [plannedTask][type_plannedTask]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [PlannedTask][msl.equipment.schema.PlannedTask] instance.
        """
        return cls(
            task=element.text or "",
            due_date=_date.fromisoformat(element.attrib["dueDate"]),
            performed_by=element.get("performedBy", ""),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [PlannedTask][msl.equipment.schema.PlannedTask] class into an XML element.

        Returns:
            The [PlannedTask][msl.equipment.schema.PlannedTask] as an XML element.
        """
        attrib = {"dueDate": self.due_date.isoformat()}
        if self.performed_by:
            attrib["performedBy"] = self.performed_by

        e = Element("task", attrib=attrib)
        e.text = self.task
        return e


@dataclass(frozen=True)
class Maintenance:
    """Represents the [maintenance][type_maintenance]{:target="_blank"} element in an equipment register.

    Args:
        planned: Maintenance tasks that are planned to be performed.
        completed: Maintenance tasks that have been completed.
    """

    planned: tuple[PlannedTask, ...] = ()
    """Maintenance tasks that are planned to be performed."""

    completed: tuple[CompletedTask, ...] = ()
    """Maintenance tasks that have been completed."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Maintenance:
        """Convert an XML element into a [Maintenance][msl.equipment.schema.Maintenance] instance.

        Args:
            element: A [maintenance][type_maintenance]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [Maintenance][msl.equipment.schema.Maintenance] instance.
        """
        if len(element) == 0:
            return cls()

        # Schema forces order, planned tasks then completed tasks (and both sub-elements must exist)
        return cls(
            planned=tuple(PlannedTask.from_xml(e) for e in element[0]),
            completed=tuple(CompletedTask.from_xml(e) for e in element[1]),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [Maintenance][msl.equipment.schema.Maintenance] class into an XML element.

        Returns:
            The [Maintenance][msl.equipment.schema.Maintenance] as an XML element.
        """
        e = Element("maintenance")
        if not (self.planned or self.completed):
            return e  # no maintenance plan

        # planned must come before completed
        planned = SubElement(e, "planned")
        planned.extend(p.to_xml() for p in self.planned)
        completed = SubElement(e, "completed")
        completed.extend(c.to_xml() for c in self.completed)
        return e


@dataclass(frozen=True)
class Measurand:
    """Represents the [measurand][type_measurand]{:target="_blank"} element in an equipment register."""


@dataclass(frozen=True)
class QualityManual:
    """Represents the [qualityManual][type_qualityManual]{:target="_blank"} element in an equipment register.

    Args:
        accessories: Additional accessories that may be required to use the equipment.
        documentation: Information (such as URLs) about the manuals, datasheets, etc. for the equipment.
        financial: Financial information about the equipment.
        personnel_restrictions: Information about the people (or team) who are qualified to use the equipment.
        service_agent: Information about the people or company that are qualified to perform alterations and/or
            maintenance to the equipment.
        technical_procedures: The technical procedure(s) that depend on this equipment.
    """

    accessories: Accessories | None = None
    """Additional accessories that may be required to use the equipment."""

    documentation: str = ""
    """Information (such as URLs) about the manuals, datasheets, etc. for the equipment."""

    financial: Financial | None = None
    """Financial information about the equipment."""

    personnel_restrictions: str = ""
    """Information about the people (or team) who are qualified to use the equipment."""

    service_agent: str = ""
    """Information about the people or company that are qualified to perform alterations
    and/or maintenance to the equipment."""

    technical_procedures: tuple[str, ...] = ()
    """The technical procedure(s) that depend on this equipment."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> QualityManual:
        """Convert an XML element into an [QualityManual][msl.equipment.schema.QualityManual] instance.

        Args:
            element: A [qualityManual][type_qualityManual]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [QualityManual][msl.equipment.schema.QualityManual] instance.
        """
        # Schema defines <qualityManual> using xsd:all, which allows sub-elements to appear (or not appear) in any order
        # Using str.endswith() allows for ignoring XML namespaces that may be associated with each tag
        tp: tuple[str, ...] = ()
        a, d, f, pr, sa = None, "", None, "", ""
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


class ReferenceMaterials(Any):
    """Documentation of reference materials, results, acceptance criteria, relevant dates and the period of validity.

    Since this class is currently represented by the [any][type_any]{:target="_blank"} type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element]{:target="_blank"}.
    It may be updated to be a more specific class at a later date.
    """

    tag: str = "referenceMaterials"
    """The element's name."""


class Specifications(Any):
    """Specifications provided by the manufacturer of the equipment.

    Typically, the specifications are specified on the website, datasheet and/or technical notes that a
    manufacturer provides.

    Since this class is currently represented by the [any][type_any]{:target="_blank"} type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element]{:target="_blank"}.
    It may be updated to be a more specific class at a later date.
    """

    tag: str = "specifications"
    """The element's name."""


class SpecifiedRequirements(Any):
    """Verification that equipment conforms with specified requirements before being placed or returned into service.

    Since this class is currently represented by the [any][type_any]{:target="_blank"} type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element]{:target="_blank"}.
    It may be updated to be a more specific class at a later date.
    """

    tag: str = "specifiedRequirements"
    """The element's name."""


@dataclass(frozen=True)
class Equipment:
    """Represents the [equipment][type_equipment]{:target="_blank"} element in an equipment register.

    Args:
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
