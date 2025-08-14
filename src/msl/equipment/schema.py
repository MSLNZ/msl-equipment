from __future__ import annotations  # noqa: D100

from dataclasses import dataclass, field
from datetime import date as _date
from enum import Enum
from io import StringIO
from math import isinf
from typing import TYPE_CHECKING, NamedTuple
from xml.etree.ElementTree import Element, ElementTree, SubElement

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any as _Any
    from typing import Callable, Literal, TypeVar

    from numpy.typing import ArrayLike, DTypeLike, NDArray

    from ._types import DateValue, XMLSource

    A = TypeVar("A", bound="Any")

equation_map = {
    "pi": np.pi,
    "pow": np.power,
    "sqrt": np.sqrt,
    "sin": np.sin,
    "asin": np.arcsin,
    "cos": np.cos,
    "acos": np.arccos,
    "tan": np.tan,
    "atan": np.arctan,
    "exp": np.exp,
    "log": np.log,
    "log10": np.log10,
}

schema_numpy_map = {
    "bool": bool,
    "int": int,
    "double": float,
    "string": object,
}
numpy_schema_map = {
    "?": "bool",
    "q": "int",
    "l": "int",
    "d": "double",
    "O": "string",
}


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


class DigitalFormat(Enum):
    """Represents the [digitalFormatEnumerationString][type_digitalFormatEnumerationString]{:target="_blank"} enumeration in an equipment register.

    Attributes:
        MSL_PDF (str): `"MSL PDF/A-3"` (MSL's PDF/A-3 format).
        PTB_DCC (str): `"PTB DCC"` (PTB's Digital Calibration Certificate).
    """  # noqa: E501

    MSL_PDF = "MSL PDF/A-3"
    PTB_DCC = "PTB DCC"


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
        prefix = f"{{{Register.NAMESPACE}}}"
        for e in element.iter():
            if e.tag.startswith(prefix):  # str.removeprefix() was added in Python 3.9
                e.tag = e.tag[len(prefix) :]

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


class Range(NamedTuple):
    """The numeric range of a variable that an [equation][] is valid for.

    Attributes: Parameters:
        minimum (float): Minimum value in range.
        maximum (float): Maximum value in range.
    """

    minimum: float
    """Minimum value in range."""

    maximum: float
    """Maximum value in range."""

    def check_within_range(self, value: float | ArrayLike) -> bool:
        """Check that the value(s) is(are) within the range.

        Args:
            value: The value(s) to check.

        Returns:
            `True` is the value(s) is(are) within range.

        Raises:
            ValueError: If `value` is not within the range.
        """
        if isinstance(value, (int, float)) or (isinstance(value, np.ndarray) and value.ndim == 0):
            if value < self.minimum or value > self.maximum:
                msg = f"The value {value} is not within the range [{self.minimum}, {self.maximum}]"
                raise ValueError(msg)
        elif np.any(np.less(value, self.minimum)) or np.any(np.greater(value, self.maximum)):  # pyright: ignore[reportUnknownArgumentType]
            msg = f"A value in the sequence is not within the range [{self.minimum}, {self.maximum}]"
            raise ValueError(msg)
        return True


@dataclass(frozen=True)
class Evaluable:
    r"""Represents the `<value>` and `<uncertainty>` XML elements in an [equation][type_equation]{:target="_blank"}.

    Args:
        equation: The string representation of the equation to evaluate.
        variables: The names of the variables in the equation.
        ranges: The numeric range for a variable that the `equation` is valid for.
            The *keys* are the variable names. A range does not need to be defined for every variable.
            If a range is not defined then a range of $[-\infty, +\infty]$ is assumed.
    """

    equation: str
    """The string representation of the equation to evaluate."""

    variables: tuple[str, ...] = ()
    """The names of the variables in the equation."""

    ranges: dict[str, Range] = field(default_factory=dict)
    """The numeric range for each variable that the `equation` is valid for. The *keys* are the variable names."""

    def __call__(self, *, check_range: bool = True, **data: ArrayLike) -> NDArray[np.float64]:
        """Evaluate the equation.

        Args:
            data: A mapping of variable names to value(s) to evaluate the equation with.
            check_range: Whether to check that the data is within the allowed range(s).

        Returns:
            The equation evaluated.
        """
        _locals = {k: np.asarray(v, dtype=float) for k, v in data.items()}
        if check_range:
            for name, value in _locals.items():
                r = self.ranges.get(name)
                if r is not None:  # if None then assume [-INF, +INF] for this variable
                    _ = r.check_within_range(value)

        # If the same input data is used to evaluate the corrected value and the uncertainty
        # then one would expect the returned array to have the same shape in both cases.
        # If the equation is a constant (does not depend on variables) the input data is
        # ignored during eval() and a scalar array would have been returned. We want to
        # ensure that the output shape is always the same as the broadcasted input shape.
        in_shape = np.broadcast_shapes(*tuple(v.shape for v in _locals.values()))

        _locals.update(equation_map)  # type: ignore[arg-type]  # pyright: ignore[reportCallIssue, reportArgumentType]
        out: NDArray[np.float64] = np.asarray(eval(self.equation, None, _locals))  # noqa: S307
        if out.shape != in_shape:
            return np.broadcast_to(out, in_shape)
        return out


@dataclass(frozen=True)
class Equation:
    """Represents the [equation][type_equation]{:target="_blank"} element in an equipment register.

    Args:
        value: The equation to evaluate to calculate the *corrected* value.
        uncertainty: The equation to evaluate to calculate the *standard* uncertainty.
        unit: The unit of the measured quantity.
        degree_freedom: The degrees of freedom.
        comment: A comment to associate with the equation.
    """

    value: Evaluable
    """The equation to evaluate to calculate the *corrected* value."""

    uncertainty: Evaluable
    """The equation to evaluate to calculate the *standard* uncertainty."""

    unit: str
    """The unit of the measured quantity."""

    degree_freedom: float = float("inf")
    """The degrees of freedom."""

    comment: str = ""
    """A comment associated with the equation."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Equation:
        """Convert an XML element into an [Equation][msl.equipment.schema.Equation] instance.

        Args:
            element: An [equation][type_equation]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [Equation][msl.equipment.schema.Equation] instance.
        """
        # Schema forces order
        value = element[0]
        uncertainty = element[1]
        ranges = {
            r.attrib["variable"]: Range(minimum=float(r[0].text or -np.inf), maximum=float(r[1].text or np.inf))
            for r in element[3]
        }

        return cls(
            value=Evaluable(
                equation=value.text or "", variables=tuple(value.attrib["variables"].split()), ranges=ranges
            ),
            uncertainty=Evaluable(
                equation=uncertainty.text or "", variables=tuple(uncertainty.attrib["variables"].split()), ranges=ranges
            ),
            unit=element[2].text or "",
            degree_freedom=float(element[4].text or np.inf) if len(element) > 4 else np.inf,  # noqa: PLR2004
            comment=element.attrib.get("comment", ""),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [Equation][msl.equipment.schema.Equation] class into an XML element.

        Returns:
            The [Equation][msl.equipment.schema.Equation] as an XML element.
        """
        attrib = {"comment": self.comment} if self.comment else {}
        e = Element("equation", attrib=attrib)
        value = SubElement(e, "value", attrib={"variables": " ".join(self.value.variables)})
        value.text = self.value.equation
        uncertainty = SubElement(e, "uncertainty", attrib={"variables": " ".join(self.uncertainty.variables)})
        uncertainty.text = self.uncertainty.equation
        unit = SubElement(e, "unit")
        unit.text = self.unit

        ranges = SubElement(e, "ranges")
        for name, _range in self.value.ranges.items():  # self.value.ranges and self.uncertainty.ranges are the same
            rng = SubElement(ranges, "range", attrib={"variable": name})
            mn = SubElement(rng, "minimum")
            mn.text = str(_range.minimum)
            mx = SubElement(rng, "maximum")
            mx.text = str(_range.maximum)

        if not isinf(self.degree_freedom):
            dof = SubElement(e, "degreeFreedom")
            dof.text = str(self.degree_freedom)

        return e


@dataclass(frozen=True)
class Competency:
    """Represents the [competency][type_competency]{:target="_blank"} element in an equipment register.

    Args:
        worker: The competent person who executed the technical procedure to accomplish the performance check.
        checker: The competent person who reviewed the work done by the `worker`.
        technical_procedure: The technical procedure that was executed to accomplish the performance check.
    """

    worker: str
    """The competent person who executed the technical procedure to accomplish the performance check."""

    checker: str
    """The competent person who reviewed the work done by the `worker`."""

    technical_procedure: str
    """The technical procedure that was executed to accomplish the performance check."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Competency:
        """Convert an XML element into a [Competency][msl.equipment.schema.Competency] instance.

        Args:
            element: A [competency][type_competency]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [Competency][msl.equipment.schema.Competency] instance.
        """
        # Schema forces order
        return cls(
            worker=element[0].text or "",
            checker=element[1].text or "",
            technical_procedure=element[2].text or "",
        )

    def to_xml(self) -> Element[str]:
        """Convert the [Competency][msl.equipment.schema.Competency] class into an XML element.

        Returns:
            The [Competency][msl.equipment.schema.Competency] as an XML element.
        """
        e = Element("competency")
        worker = SubElement(e, "worker")
        worker.text = self.worker
        checker = SubElement(e, "checker")
        checker.text = self.checker
        tp = SubElement(e, "technicalProcedure")
        tp.text = self.technical_procedure
        return e


@dataclass(frozen=True)
class File:
    """Represents the [file][type_file]{:target="_blank"} element in an equipment register.

    Args:
        url: The location of the file. The syntax follows [RFC 1738](https://www.rfc-editor.org/rfc/rfc1738){:target="_blank"}
            `scheme:scheme-specific-part`. If `scheme:` is not specified, it is assumed to be `file:`.
        sha256: The SHA-256 checksum of the file.
        attributes: XML attributes associated with the `<url>` element.
        comment: A comment to associate with the file.
    """

    url: str
    """The location of the file. The syntax follows [RFC 1738](https://www.rfc-editor.org/rfc/rfc1738){:target="_blank"}
    `scheme:scheme-specific-part`. If `scheme:` is not specified, it is assumed to be `file:`."""

    sha256: str
    """The SHA-256 checksum of the file."""

    attributes: dict[str, str] = field(default_factory=dict)
    """XML attributes associated with the `<url>` element."""

    comment: str = ""
    """A comment associated with the file."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> File:
        """Convert an XML element into a [File][msl.equipment.schema.File] instance.

        Args:
            element: A [file][type_file]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [File][msl.equipment.schema.File] instance.
        """
        # Schema forces order
        return cls(
            url=element[0].text or "",
            sha256=element[1].text or "",
            attributes=element[0].attrib,
            comment=element.attrib.get("comment", ""),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [File][msl.equipment.schema.File] class into an XML element.

        Returns:
            The [File][msl.equipment.schema.File] as an XML element.
        """
        attrib = {"comment": self.comment} if self.comment else {}
        e = Element("file", attrib=attrib)
        url = SubElement(e, "url", attrib=self.attributes)
        url.text = self.url
        sha256 = SubElement(e, "sha256")
        sha256.text = self.sha256
        return e


@dataclass(frozen=True)
class Deserialised:
    """Represents the opposite of the [serialised][type_serialised]{:target="_blank"} element in an equipment register.

    Args:
        value: The value of the deserialised object.
        comment: A comment to associate with the (de)serialised object.
    """

    value: _Any
    """The value of the deserialised object. For example, an [Archive][persistence.Archive]{:target="_blank"}
    object from [GTC](https://gtc.readthedocs.io/en/stable/){:target="_blank"}.
    """

    comment: str = ""
    """A comment associated with the (de)serialised object."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Deserialised:
        """Convert a [serialised][type_serialised]{:target="_blank"} XML element into a [Deserialised][msl.equipment.schema.Deserialised] instance.

        Args:
            element: A [serialised][type_serialised]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [Deserialised][msl.equipment.schema.Deserialised] instance.
        """  # noqa: E501
        e = element[0]
        comment = element.attrib.get("comment", "")

        # GTC is not required for msl-equipment, so we import it here
        if e.tag.endswith("gtcArchive"):
            from GTC.xml_format import (  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]  # noqa: PLC0415
                xml_to_archive,  # pyright: ignore[reportUnknownVariableType]
            )

            return cls(value=xml_to_archive(e), comment=comment)

        if e.tag.endswith("gtcArchiveJSON"):
            from GTC import (  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]  # noqa: PLC0415
                pr,  # pyright: ignore[reportUnknownVariableType]
            )

            return cls(value=pr.loads_json(e.text), comment=comment)  # pyright: ignore[reportUnknownMemberType]

        # Use the Element object rather than raising an exception that the deserializer has not been implemented yet
        return cls(value=e, comment=comment)

    def to_xml(self) -> Element[str]:
        """Convert the [Deserialised][msl.equipment.schema.Deserialised] class into a [serialised][type_serialised]{:target="_blank"} XML element.

        Returns:
            The [serialised][type_serialised]{:target="_blank"} XML element.
        """  # noqa: E501
        attrib = {"comment": self.comment} if self.comment else {}
        e = Element("serialised", attrib=attrib)

        if isinstance(self.value, Element):
            e.append(self.value)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            return e

        # Currently, only a GTC Archive is supported so we don't need to check how to serialise it
        # GTC is not required for msl-equipment, so we import it here
        from GTC.persistence import (  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]  # noqa: PLC0415
            Archive,  # pyright: ignore[reportUnknownVariableType]
        )
        from GTC.xml_format import (  # pyright: ignore[reportMissingTypeStubs]  # noqa: PLC0415
            archive_to_xml,  # pyright: ignore[reportUnknownVariableType]
        )

        e.append(archive_to_xml(Archive.copy(self.value)))  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        return e


@dataclass(frozen=True)
class Adjustment:
    """An adjustment of the equipment.

    An example of an adjustment is cleaning the equipment (e.g., a spectral filter) and then
    performing another calibration measurement.

    This XML element is found in [component][type_component]{:target="_blank"}.

    Args:
        details: The details of the adjustment that was performed.
        date: The date that the adjustment was performed.
    """

    details: str
    """The details of the adjustment that was performed."""

    date: _date
    """The date that the adjustment was performed."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Adjustment:
        """Convert an XML element into a [Adjustment][msl.equipment.schema.Adjustment] instance.

        Args:
            element: An `<adjustment>` XML element from an equipment register
                (see [component][type_component]{:target="_blank"}).

        Returns:
            The [Adjustment][msl.equipment.schema.Adjustment] instance.
        """
        return cls(details=element.text or "", date=_date.fromisoformat(element.attrib["date"]))

    def to_xml(self) -> Element[str]:
        """Convert the [Adjustment][msl.equipment.schema.Adjustment] class into an XML element.

        Returns:
            The [Adjustment][msl.equipment.schema.Adjustment] as an XML element.
        """
        e = Element("adjustment", attrib={"date": self.date.isoformat()})
        e.text = self.details
        return e


@dataclass(frozen=True)
class DigitalReport:
    """Represents the [digitalReport][type_digitalReport]{:target="_blank"} element in an equipment register.

    Args:
        url: The location of the digital report. The syntax follows [RFC 1738](https://www.rfc-editor.org/rfc/rfc1738){:target="_blank"}
            `scheme:scheme-specific-part`. If `scheme:` is not specified, it is assumed to be `file:`.
        format: The format of the digital calibration report.
        id: The report identification number.
        sha256: The SHA-256 checksum of the digital report.
        attributes: XML attributes associated with the `<url>` element.
        comment: A comment to associate with the digital report.
    """

    url: str
    """The location of the digital report. The syntax follows [RFC 1738](https://www.rfc-editor.org/rfc/rfc1738){:target="_blank"}
    `scheme:scheme-specific-part`. If `scheme:` is not specified, it is assumed to be `file:`."""

    format: DigitalFormat
    """The format of the digital calibration report."""

    id: str
    """The report identification number."""

    sha256: str
    """The SHA-256 checksum of the digital report."""

    attributes: dict[str, str] = field(default_factory=dict)
    """XML attributes associated with the `<url>` element."""

    comment: str = ""
    """A comment associated with the digital report."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> DigitalReport:
        """Convert an XML element into a [DigitalReport][msl.equipment.schema.DigitalReport] instance.

        Args:
            element: A [digitalReport][type_digitalReport]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [DigitalReport][msl.equipment.schema.DigitalReport] instance.
        """
        # Schema forces order
        return cls(
            url=element[0].text or "",
            format=DigitalFormat(element.attrib["format"]),
            id=element.attrib["id"],
            sha256=element[1].text or "",
            attributes=element[0].attrib,
            comment=element.attrib.get("comment", ""),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [DigitalReport][msl.equipment.schema.DigitalReport] class into an XML element.

        Returns:
            The [DigitalReport][msl.equipment.schema.DigitalReport] as an XML element.
        """
        attrib = {"format": self.format.value, "id": self.id}
        if self.comment:
            attrib["comment"] = self.comment
        e = Element("digitalReport", attrib=attrib)
        url = SubElement(e, "url", attrib=self.attributes)
        url.text = self.url
        sha256 = SubElement(e, "sha256")
        sha256.text = self.sha256
        return e


def _cvd_resistance(array: float | np.ndarray, r0: float, a: float, b: float, c: float) -> NDArray[np.float64]:
    """Calculate resistance from CVD coefficients."""
    return np.piecewise(
        array,
        [array < 0, array >= 0],
        [
            lambda t: r0 * (1.0 + a * t + b * t**2 + c * (t - 100.0) * t**3),
            lambda t: r0 * (1.0 + a * t + b * t**2),
        ],
    )


@dataclass(frozen=True)
class CVDEquation:
    r"""The Callendar-Van Dusen (CVD) equation based on the [cvdCoefficients][type_cvdCoefficients]{:target="_blank"} element in an equipment register.

    Args:
        R0: The value, in $\Omega$, of the resistance at $0~^\circ\text{C}$, $R_0$.
        A: The value, in $^\circ\text{C}^{-1}$, of the A coefficient, $A \cdot T$.
        B: The value, in $^\circ\text{C}^{-2}$, of the B coefficient, $B \cdot T^2$.
        C: The value, in $^\circ\text{C}^{-4}$, of the C coefficient, $C \cdot (T-100) \cdot T^3$.
        uncertainty:  The equation to evaluate to calculate the *standard* uncertainty.
        ranges: The temperature range, in $^\circ\text{C}$, and the resistance range, in $\Omega$,
            that the CVD coefficients are valid. The temperature key must be `"t"` and the resistance
            key `"r"`.
        degree_freedom: The degrees of freedom.
        comment: A comment to associate with the CVD equation.
    """  # noqa: E501

    R0: float
    r"""The value, in $\Omega$, of the resistance at $0~^\circ\text{C}$, $R_0$."""

    A: float
    r"""The value, in $^\circ\text{C}^{-1}$, of the A coefficient, $A \cdot T$."""

    B: float
    r"""The value, in $^\circ\text{C}^{-2}$, of the B coefficient, $B \cdot T^2$."""

    C: float
    r"""The value, in $^\circ\text{C}^{-4}$, of the C coefficient, $C \cdot (T-100) \cdot T^3$."""

    uncertainty: Evaluable
    """The equation to evaluate to calculate the *standard* uncertainty."""

    ranges: dict[str, Range] = field(default_factory=dict)
    r"""The temperature range, in $^\circ\text{C}$, and the resistance range, in $\Omega$, that
    the Callendar-Van Dusen coefficients are valid."""

    degree_freedom: float = float("inf")
    """The degrees of freedom."""

    comment: str = ""
    """A comment associated with the Callendar-Van Dusen equation."""

    def resistance(self, temperature: ArrayLike, *, check_range: bool = True) -> NDArray[np.float64]:
        r"""Calculate resistance from temperature.

        Args:
            temperature: The temperature value(s), in $^\circ\text{C}$.
            check_range: Whether to check that the temperature value(s) is(are) within the allowed range.

        Returns:
            The resistance value(s).
        """
        array = np.asarray(temperature, dtype=float)
        if check_range and self.ranges["t"].check_within_range(array):
            pass  # check_within_range() will raise an error, if one occurred

        return _cvd_resistance(array, self.R0, self.A, self.B, self.C)

    def temperature(self, resistance: ArrayLike, *, check_range: bool = True) -> NDArray[np.float64]:
        r"""Calculate temperature from resistance.

        Args:
            resistance: The resistance value(s), in $\Omega$.
            check_range: Whether to check that the resistance value(s) is(are) within the allowed range.

        Returns:
            The temperature value(s).
        """
        array: NDArray[np.float64] = np.asarray(resistance, dtype=float)
        if check_range and self.ranges["r"].check_within_range(array):
            pass  # check_within_range raised an error, if one occurred

        def positive(r: NDArray[np.float64]) -> NDArray[np.float64]:
            # rearrange CVD equation to be: a*x^2 + b*x + c = 0
            #   a -> B, b -> A, c -> 1 - R/R0
            # then use the quadratic formula
            return (-self.A + np.sqrt(self.A**2 - 4.0 * self.B * (1.0 - r / self.R0))) / (2.0 * self.B)

        def negative(r: NDArray[np.float64]) -> NDArray[np.float64]:
            # rearrange CVD equation to be: a*x^4 + b*x^3 + c*x^2 + d*x + e = 0
            a = self.C
            b = -100.0 * self.C
            c = self.B
            d = self.A
            e = 1.0 - (r / self.R0)

            # https://en.wikipedia.org/wiki/Quartic_function#Solving_a_quartic_equation]
            # See Section "General formula for roots" for the definitions of these variables
            p = (8 * a * c - 3 * b**2) / (8 * a**2)
            q = (b**3 - 4 * a * b * c + 8 * a**2 * d) / (8 * a**3)
            delta_0 = c**2 - 3 * b * d + 12 * a * e
            delta_1 = 2 * c**3 - 9 * b * c * d + 27 * b**2 * e + 27 * a * d**2 - 72 * a * c * e
            Q = np.cbrt((delta_1 + np.sqrt(delta_1**2 - 4 * delta_0**3)) / 2)  # noqa: N806
            S = 0.5 * np.sqrt(-2 * p / 3 + 1 / (3 * a) * (Q + delta_0 / Q))  # noqa: N806

            # decide which root of the quartic to use by looking at the value under the
            # square root in the x1,2 and x3,4 equations
            t1 = -4 * S**2 - 2 * p
            t2 = q / S
            t3 = t1 - t2
            return np.piecewise(
                t3,
                [t3 >= 0, t3 < 0],
                [
                    lambda x: -b / (4.0 * a) + S - 0.5 * np.sqrt(x),  # x4 equation
                    lambda x: -b / (4.0 * a) - S + 0.5 * np.sqrt(x + 2.0 * t2),  # x1 equation
                ],
            )

        return np.piecewise(array, [array < self.R0, array >= self.R0], [negative, positive])

    @classmethod
    def from_xml(cls, element: Element[str]) -> CVDEquation:
        """Convert an XML element into a [CVDEquation][msl.equipment.schema.CVDEquation] instance.

        Args:
            element: A [cvdCoefficients][type_cvdCoefficients]{:target="_blank"} XML element
                from an equipment register.

        Returns:
            The [CVDEquation][msl.equipment.schema.CVDEquation] instance.
        """
        # Schema forces order
        r0 = float(element[0].text or 0)
        a = float(element[1].text or 0)
        b = float(element[2].text or 0)
        c = float(element[3].text or 0)

        r = element[5]
        _range = Range(float(r[0].text or -200), float(r[1].text or 661))
        ranges = {
            "t": _range,
            "r": Range(
                minimum=round(float(_cvd_resistance(_range.minimum, r0, a, b, c)), 3),
                maximum=round(float(_cvd_resistance(_range.maximum, r0, a, b, c)), 3),
            ),
        }

        u = element[4]
        uncertainty = Evaluable(
            equation=u.text or "",
            variables=tuple(u.attrib["variables"].split()),
            ranges=ranges,
        )

        return cls(
            R0=r0,
            A=a,
            B=b,
            C=c,
            uncertainty=uncertainty,
            ranges=ranges,
            degree_freedom=float(element[6].text or np.inf) if len(element) > 6 else np.inf,  # noqa: PLR2004
            comment=element.attrib.get("comment", ""),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [CVDEquation][msl.equipment.schema.CVDEquation] class into an XML element.

        Returns:
            The [CVDEquation][msl.equipment.schema.CVDEquation] as an XML element.
        """
        attrib = {"comment": self.comment} if self.comment else {}
        e = Element("cvdCoefficients", attrib=attrib)

        r0 = SubElement(e, "R0")
        r0.text = str(self.R0)

        a = SubElement(e, "A")
        a.text = str(self.A)

        b = SubElement(e, "B")
        b.text = str(self.B)

        c = SubElement(e, "C")
        c.text = str(self.C)

        u = SubElement(e, "uncertainty", attrib={"variables": " ".join(self.uncertainty.variables)})
        u.text = str(self.uncertainty.equation)

        rng = SubElement(e, "range")
        mn = SubElement(rng, "minimum")
        mn.text = str(self.ranges["t"].minimum)
        mx = SubElement(rng, "maximum")
        mx.text = str(self.ranges["t"].maximum)

        if not isinf(self.degree_freedom):
            dof = SubElement(e, "degreeFreedom")
            dof.text = str(self.degree_freedom)

        return e


class Table(np.ndarray):
    """Represents the [table][type_table]{:target="_blank"} element in an equipment register."""

    INDENT: int = 34
    """The number of spaces to indent each row in the `<data>` element when converting the
    [Table][msl.equipment.schema.Table] to an XML element, see [to_xml][msl.equipment.schema.Table.to_xml].
    The default, _34_, is appropriate when saving a [Register][msl.equipment.schema.Register] to a file
    using _4_ spaces for each child element via the [indent][xml.etree.ElementTree.indent]{:target="_blank"}
    function and _20_ if indenting with _2_ spaces."""

    comment: str = ""
    """A comment that is associated with the table."""

    header: NDArray[np.void] = np.empty(0, dtype=object)
    """The header value of each column."""

    types: NDArray[np.void] = np.empty(0, dtype=object)
    """The data type of each column."""

    units: NDArray[np.void] = np.empty(0, dtype=object)
    """The unit of each column."""

    def __new__(  # noqa: PYI034
        cls,
        *,
        types: NDArray[np.void],
        units: NDArray[np.void],
        header: NDArray[np.void],
        data: ArrayLike,
        comment: str = "",
    ) -> Table:
        """Create a new [Table][msl.equipment.schema.Table] instance.

        Args:
            types: The data type of each column.
            units: The unit of each column.
            header: The header value of each column.
            data: The table data.
            comment: A comment that is associated with the table.
        """
        obj = np.asarray(data).view(cls)
        obj.types = types
        obj.units = units
        obj.header = header
        obj.comment = comment
        return obj

    def __array_finalize__(self, obj: None | NDArray[_Any]) -> None:  # pyright: ignore[reportImplicitOverride]
        """Finalise the creation of the [Table][msl.equipment.schema.Table] by adding the metadata."""
        if obj is None:
            return  # pragma: no cover
        self.types = getattr(obj, "types", np.empty(0, dtype=object))
        self.units = getattr(obj, "units", np.empty(0, dtype=object))
        self.header = getattr(obj, "header", np.empty(0, dtype=object))
        self.comment = getattr(obj, "comment", "")

    def unstructured(
        self,
        *,
        dtype: DTypeLike = None,
        copy: bool = False,
        casting: Literal["no", "equiv", "safe", "same_kind", "unsafe"] = "unsafe",
    ) -> NDArray[_Any]:
        """Converts the structured array into an unstructured array.

        See [structured_to_unstructured][numpy.lib.recfunctions.structured_to_unstructured]{:target="_blank"}
        for more details.

        Args:
            dtype: The dtype of the output unstructured array.
            copy: If `True`, always return a copy. If `False`, a view is returned if possible.
            casting: Controls what kind of data casting may occur. See the *casting* argument of
                [numpy.ndarray.astype][]{:target="_blank"} for more details.

        Returns:
            The unstructured array. This method may return a numpy [ndarray][numpy.ndarray]{:target="_blank"}
                instance instead of a [Table][msl.equipment.schema.Table] instance if the table consists of
                numbers and strings and the appropriate `dtype` is not specified.
        """
        from numpy.lib.recfunctions import structured_to_unstructured  # noqa: PLC0415

        try:
            return structured_to_unstructured(self, dtype=dtype, copy=copy, casting=casting)
        except (TypeError, ValueError):
            return np.array(self.tolist(), dtype=object)

    @classmethod
    def from_xml(cls, element: Element[str]) -> Table:
        """Convert an XML element into a [Table][msl.equipment.schema.Table] instance.

        Args:
            element: A [table][type_table]{:target="_blank"} XML element from an equipment register.

        Returns:
            A [Table][msl.equipment.schema.Table] is an subclass of a numpy
                [structured array][structured_arrays]{:target="_blank"}, where the `header` is used as
                the *field names*. This allows for accessing a column by the header value rather than by
                the index of a column. If you prefer to work with unstructured data, call
                [unstructured][msl.equipment.schema.Table.unstructured] on the returned object.
        """
        booleans = {"True", "true", "TRUE", "1", b"True", b"true", b"TRUE", b"1"}

        def convert_bool(value: str | bytes) -> bool:
            # the value can be of type bytes for numpy < 2.0
            return value.strip() in booleans

        def strip_string(value: str | bytes) -> str:
            # the value can be of type bytes for numpy < 2.0
            stripped = value.strip()
            if isinstance(stripped, bytes):
                return stripped.decode()
            return stripped

        # Schema forces order
        _type = [s.strip() for s in (element[0].text or "").split(",")]
        _unit = [s.strip() for s in (element[1].text or "").split(",")]
        _header = [s.strip() for s in (element[2].text or "").split(",")]
        _file = StringIO((element[3].text or "").strip())

        # must handle boolean column and string column separately
        conv: dict[int, Callable[[str | bytes], str | bool]] = {
            i: convert_bool for i, v in enumerate(_type) if v == "bool"
        }
        conv.update({i: strip_string for i, v in enumerate(_type) if v == "string"})

        dtype = np.dtype([(h, schema_numpy_map[t]) for h, t in zip(_header, _type)])
        data = np.loadtxt(_file, dtype=dtype, delimiter=",", converters=conv)  # type: ignore[arg-type]  # pyright: ignore[reportCallIssue, reportArgumentType, reportUnknownVariableType]
        data.setflags(write=False)  # pyright: ignore[reportUnknownMemberType]

        header = np.asarray(_header)
        header.setflags(write=False)  # make it readonly by default

        units = np.asarray(tuple(_unit), np.dtype([(h, object) for h in _header]))
        units.setflags(write=False)  # make it readonly by default

        assert data.dtype.fields is not None  # pyright: ignore[reportUnknownMemberType]  # noqa: S101
        types = np.asarray(tuple(v[0] for v in data.dtype.fields.values()), dtype=[(h, object) for h in _header])  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType]
        types.setflags(write=False)  # make it readonly by default

        return cls(types=types, units=units, header=header, data=data, comment=element.attrib.get("comment", ""))  # pyright: ignore[reportUnknownArgumentType]

    def to_xml(self) -> Element[str]:
        """Convert the [Table][msl.equipment.schema.Table] class into an XML element.

        Returns:
            The [Table][msl.equipment.schema.Table] as an XML element.
        """
        attrib = {"comment": self.comment} if self.comment else {}
        e = Element("table", attrib=attrib)

        types = SubElement(e, "type")
        dtypes = [numpy_schema_map[t.char] for t in self.types.tolist()]
        types.text = ",".join(dtypes)

        units = SubElement(e, "unit")
        units.text = ",".join(self.units.tolist())

        header = SubElement(e, "header")
        header.text = ",".join(self.header)

        buffer = StringIO()
        newline = "\n" + " " * Table.INDENT
        np.savetxt(buffer, self, fmt="%s", delimiter=",", newline=newline)
        data = SubElement(e, "data")
        data.text = buffer.getvalue().rstrip() + "\n" + " " * max(0, Table.INDENT - len("<data>"))

        return e


@dataclass(frozen=True)
class PerformanceCheck:
    """Represents the [performanceCheck][type_performanceCheck]{:target="_blank"} element in an equipment register.

    Args:
        completed_date: The date that the performance check was completed.
        competency: The competent people who accomplished the performance check and the technical procedure
            that was executed.
        entered_by: The name of the person who initially entered the `performanceCheck` element in the register.
        checked_by: The name of the person who checked the information in the `performanceCheck` element.
        checked_date: The date that the information in the `performanceCheck` element was last checked.
        conditions: The conditions under which the performance check is valid.
        cvd_equations: Performance-check data is expressed as coefficients for the Callendar-Van Dusen equation.
        equations: Performance-check data is expressed as an equation.
        files: Performance-check data is stored in another file.
        deserialised: Performance-check data is stored in a deserialised format.
        tables: Performance-check data is expressed as a CSV table in the equipment register.
    """

    completed_date: _date
    """The date that the performance check was completed."""

    competency: Competency
    """The competent people who accomplished the performance check and the technical procedure that was executed."""

    entered_by: str
    """The name of the person who initially entered the `performanceCheck` element in the register."""

    checked_by: str = ""
    """The name of the person who checked the information in the `performanceCheck` element."""

    checked_date: _date | None = None
    """The date that the information in the `performanceCheck` element was last checked."""

    conditions: Conditions = field(default_factory=Conditions)
    """The conditions under which the performance check is valid."""

    cvd_equations: tuple[CVDEquation, ...] = ()
    """Performance-check data is expressed as coefficients for the Callendar-Van Dusen equation."""

    equations: tuple[Equation, ...] = ()
    """Performance-check data is expressed as an equation."""

    files: tuple[File, ...] = ()
    """Performance-check data is stored in another file."""

    deserialised: tuple[Deserialised, ...] = ()
    """Performance-check data is stored in a deserialised format."""

    tables: tuple[Table, ...] = ()
    """Performance-check data is expressed as a CSV table in the equipment register."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> PerformanceCheck:
        """Convert an XML element into a [PerformanceCheck][msl.equipment.schema.PerformanceCheck] instance.

        Args:
            element: A [performanceCheck][type_performanceCheck]{:target="_blank"} XML element from an
                equipment register.

        Returns:
            The [PerformanceCheck][msl.equipment.schema.PerformanceCheck] instance.
        """
        # Schema forces order for `competency` and `conditions` but uses xsd:choice,
        # which allows sub-elements to appear (or not appear) in any order, for the data elements.
        # Using str.endswith() allows for ignoring XML namespaces that may be associated with each tag
        cvd_equations: list[CVDEquation] = []
        equations: list[Equation] = []
        files: list[File] = []
        deserialised: list[Deserialised] = []
        tables: list[Table] = []
        for child in element[2:]:
            tag = child.tag
            if tag.endswith("equation"):
                equations.append(Equation.from_xml(child))
            elif tag.endswith("table"):
                tables.append(Table.from_xml(child))
            elif tag.endswith("cvdCoefficients"):
                cvd_equations.append(CVDEquation.from_xml(child))
            elif tag.endswith("file"):
                files.append(File.from_xml(child))
            else:
                deserialised.append(Deserialised.from_xml(child))

        a = element.attrib
        return cls(
            completed_date=_date.fromisoformat(a["completedDate"] or ""),
            entered_by=a["enteredBy"] or "",
            checked_by=a.get("checkedBy", ""),
            checked_date=None if not a.get("checkedDate") else _date.fromisoformat(a["checkedDate"]),
            competency=Competency.from_xml(element[0]),
            conditions=Conditions.from_xml(element[1]),
            cvd_equations=tuple(cvd_equations),
            equations=tuple(equations),
            files=tuple(files),
            deserialised=tuple(deserialised),
            tables=tuple(tables),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [PerformanceCheck][msl.equipment.schema.PerformanceCheck] class into an XML element.

        Returns:
            The [PerformanceCheck][msl.equipment.schema.PerformanceCheck] as an XML element.
        """
        a = {"completedDate": self.completed_date.isoformat(), "enteredBy": self.entered_by}
        if self.checked_by:
            a["checkedBy"] = self.checked_by
        if self.checked_date is not None:
            a["checkedDate"] = self.checked_date.isoformat()

        e = Element("performanceCheck", attrib=a)
        e.append(self.competency.to_xml())
        e.append(self.conditions)
        e.extend(equation.to_xml() for equation in self.equations)
        e.extend(table.to_xml() for table in self.tables)
        e.extend(cvd.to_xml() for cvd in self.cvd_equations)
        e.extend(file.to_xml() for file in self.files)
        e.extend(deserialised.to_xml() for deserialised in self.deserialised)
        return e


@dataclass(frozen=True)
class IssuingLaboratory:
    """Information about the laboratory that issued a calibration report.

    Args:
        lab: The name of the laboratory that issued the calibration report.
        person: The name of a person at the `laboratory` that authorised the report.
    """

    lab: str = ""
    """The name of the laboratory that issued the calibration report."""

    person: str = ""
    """The name of a person at the laboratory that authorised the report."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> IssuingLaboratory:
        """Convert an XML element into a [IssuingLaboratory][msl.equipment.schema.IssuingLaboratory] instance.

        Args:
            element: An `<issuingLaboratory>` element from a [report][type_report]{:target="_blank"} element
                in an equipment register.

        Returns:
            The [IssuingLaboratory][msl.equipment.schema.IssuingLaboratory] instance.
        """
        return cls(
            lab=element.text or "",
            person=element.attrib.get("person", ""),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [IssuingLaboratory][msl.equipment.schema.IssuingLaboratory] class into an XML element.

        Returns:
            The [IssuingLaboratory][msl.equipment.schema.IssuingLaboratory] as an XML element.
        """
        a = {"person": self.person} if self.person else {}
        e = Element("issuingLaboratory", attrib=a)
        e.text = self.lab
        return e


@dataclass(frozen=True)
class Report:
    """Represents the [report][type_report]{:target="_blank"} element in an equipment register.

    Args:
        id: The report identification number.
        entered_by: The name of the person who initially entered the `report` element in the register.
        report_issue_date: The date that the report was issued.
        measurement_start_date: The date that the calibration measurement started.
        measurement_stop_date: The date that the calibration measurement stopped.
        issuing_laboratory: Information about the laboratory that issued the calibration report.
        technical_procedure: The technical procedure(s) that was(were) followed to perform the calibration.
        checked_by: The name of the person who checked the information in the `report` element.
        checked_date: The date that the information in the `report` element was last checked.
        conditions: The conditions under which the report is valid.
        acceptance_criteria: Acceptance criteria for the calibration report.
        cvd_equations: Calibration data is expressed as coefficients for the Callendar-Van Dusen equation.
        equations: Calibration data is expressed as an equation.
        files: Calibration data is stored in another file.
        deserialised: Calibration data is stored in a deserialised format.
        tables: Calibration data is expressed as a CSV table in the equipment register.
    """

    id: str
    """The report identification number."""

    entered_by: str
    """The name of the person who initially entered the `report` element in the register."""

    report_issue_date: _date
    """The date that the report was issued."""

    measurement_start_date: _date
    """The date that the calibration measurement started."""

    measurement_stop_date: _date
    """The date that the calibration measurement stopped."""

    issuing_laboratory: IssuingLaboratory = field(default_factory=IssuingLaboratory)
    """Information about the laboratory that issued the calibration report."""

    technical_procedure: str = ""
    """The technical procedure(s) that was(were) followed to perform the calibration."""

    checked_by: str = ""
    """The name of the person who checked the information in the `report` element."""

    checked_date: _date | None = None
    """The date that the information in the `report` element was last checked."""

    conditions: Conditions = field(default_factory=Conditions)
    """The conditions under which the report is valid."""

    acceptance_criteria: AcceptanceCriteria = field(default_factory=AcceptanceCriteria)
    """Acceptance criteria for the calibration report."""

    cvd_equations: tuple[CVDEquation, ...] = ()
    """Calibration data is expressed as coefficients for the Callendar-Van Dusen equation."""

    equations: tuple[Equation, ...] = ()
    """Calibration data is expressed as an equation."""

    files: tuple[File, ...] = ()
    """Calibration data is stored in another file."""

    deserialised: tuple[Deserialised, ...] = ()
    """Calibration data is stored in a deserialised format."""

    tables: tuple[Table, ...] = ()
    """Calibration data is expressed as a CSV table in the equipment register."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Report:
        """Convert an XML element into a [Report][msl.equipment.schema.Report] instance.

        Args:
            element: A [report][type_report]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [Report][msl.equipment.schema.Report] instance.
        """
        # Schema forces order until `acceptanceCriteria` and then uses xsd:choice, which
        # allows sub-elements to appear (or not appear) in any order, for the data elements.
        # Using str.endswith() allows for ignoring XML namespaces that may be associated with each tag
        cvd_equations: list[CVDEquation] = []
        equations: list[Equation] = []
        files: list[File] = []
        deserialised: list[Deserialised] = []
        tables: list[Table] = []
        for child in element[7:]:
            tag = child.tag
            if tag.endswith("equation"):
                equations.append(Equation.from_xml(child))
            elif tag.endswith("table"):
                tables.append(Table.from_xml(child))
            elif tag.endswith("cvdCoefficients"):
                cvd_equations.append(CVDEquation.from_xml(child))
            elif tag.endswith("file"):
                files.append(File.from_xml(child))
            else:
                deserialised.append(Deserialised.from_xml(child))

        a = element.attrib
        return cls(
            id=a["id"] or "",
            entered_by=a["enteredBy"] or "",
            checked_by=a.get("checkedBy", ""),
            checked_date=None if not a.get("checkedDate") else _date.fromisoformat(a["checkedDate"]),
            report_issue_date=_date.fromisoformat(element[0].text or ""),
            measurement_start_date=_date.fromisoformat(element[1].text or ""),
            measurement_stop_date=_date.fromisoformat(element[2].text or ""),
            issuing_laboratory=IssuingLaboratory.from_xml(element[3]),
            technical_procedure=element[4].text or "",
            conditions=Conditions.from_xml(element[5]),
            acceptance_criteria=AcceptanceCriteria.from_xml(element[6]),
            cvd_equations=tuple(cvd_equations),
            equations=tuple(equations),
            files=tuple(files),
            deserialised=tuple(deserialised),
            tables=tuple(tables),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [Report][msl.equipment.schema.Report] class into an XML element.

        Returns:
            The [Report][msl.equipment.schema.Report] as an XML element.
        """
        a = {"id": self.id, "enteredBy": self.entered_by}
        if self.checked_by:
            a["checkedBy"] = self.checked_by
        if self.checked_date is not None:
            a["checkedDate"] = self.checked_date.isoformat()

        e = Element("report", attrib=a)

        rid = SubElement(e, "reportIssueDate")
        rid.text = self.report_issue_date.isoformat()

        start = SubElement(e, "measurementStartDate")
        start.text = self.measurement_start_date.isoformat()

        stop = SubElement(e, "measurementStopDate")
        stop.text = self.measurement_stop_date.isoformat()

        e.append(self.issuing_laboratory.to_xml())

        tp = SubElement(e, "technicalProcedure")
        tp.text = self.technical_procedure

        e.append(self.conditions)
        e.append(self.acceptance_criteria)
        e.extend(equation.to_xml() for equation in self.equations)
        e.extend(table.to_xml() for table in self.tables)
        e.extend(cvd.to_xml() for cvd in self.cvd_equations)
        e.extend(file.to_xml() for file in self.files)
        e.extend(deserialised.to_xml() for deserialised in self.deserialised)
        return e


@dataclass(frozen=True)
class Component:
    """Represents the [component][type_component]{:target="_blank"} element in an equipment register.

    Args:
        name: The name to associate with this component. The value must be unique amongst the other
            component elements within the same measurand element. An empty string is permitted.
        adjustments: The history of adjustments.
        digital_reports: The history of digital calibration reports.
        performance_checks: The history of performance checks.
        reports: The history of calibration reports.
    """

    name: str = ""
    """The name associated with this component."""

    adjustments: tuple[Adjustment, ...] = ()
    """The history of adjustments."""

    digital_reports: tuple[DigitalReport, ...] = ()
    """The history of digital calibration reports."""

    performance_checks: tuple[PerformanceCheck, ...] = ()
    """The history of performance checks."""

    reports: tuple[Report, ...] = ()
    """The history of calibration reports."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Component:
        """Convert an XML element into a [Component][msl.equipment.schema.Component] instance.

        Args:
            element: A [component][type_component]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [Component][msl.equipment.schema.Component] instance.
        """
        # Schema defines <component> using xsd:choice, which allows sub-elements to appear (or not appear) in any order
        # Using str.endswith() allows for ignoring XML namespaces that may be associated with each tag
        a: list[Adjustment] = []
        dr: list[DigitalReport] = []
        pc: list[PerformanceCheck] = []
        r: list[Report] = []
        for child in element:
            tag = child.tag
            if tag.endswith("report"):
                r.append(Report.from_xml(child))
            elif tag.endswith("performanceCheck"):
                pc.append(PerformanceCheck.from_xml(child))
            elif tag.endswith("adjustment"):
                a.append(Adjustment.from_xml(child))
            else:
                dr.append(DigitalReport.from_xml(child))

        return cls(
            name=element.attrib["name"],
            adjustments=tuple(a),
            digital_reports=tuple(dr),
            performance_checks=tuple(pc),
            reports=tuple(r),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [Component][msl.equipment.schema.Component] class into an XML element.

        Returns:
            The [Component][msl.equipment.schema.Component] as an XML element.
        """
        e = Element("component", attrib={"name": self.name})

        # the order is not important since xsd:choice is used
        e.extend(r.to_xml() for r in self.reports)
        e.extend(p.to_xml() for p in self.performance_checks)
        e.extend(a.to_xml() for a in self.adjustments)
        e.extend(d.to_xml() for d in self.digital_reports)
        return e


@dataclass(frozen=True)
class Measurand:
    """Represents the [measurand][type_measurand]{:target="_blank"} element in an equipment register.

    Args:
        quantity: The kind of quantity that is measured.
        calibration_interval: The number of years that may pass between a calibration or a performance check.
            For equipment that do not have a required and periodic interval, but are calibrated on demand,
            use the value `0`.
        components: The components of the equipment that measures the `quantity`.
    """

    quantity: str
    """The kind of quantity that is measured."""

    calibration_interval: float
    """The number of years that may pass between a calibration or a performance check.

    For equipment that do not have a required and periodic interval, but are calibrated on demand,
    the value is `0`.
    """

    components: tuple[Component, ...] = ()
    """The components of the equipment that measures the `quantity`."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Measurand:
        """Convert an XML element into a [Measurand][msl.equipment.schema.Measurand] instance.

        Args:
            element: A [measurand][type_measurand]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [Measurand][msl.equipment.schema.Measurand] instance.
        """
        return cls(
            quantity=element.attrib["quantity"],
            calibration_interval=float(element.attrib["calibrationInterval"]),
            components=tuple(Component.from_xml(c) for c in element),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [Measurand][msl.equipment.schema.Measurand] class into an XML element.

        Returns:
            The [Measurand][msl.equipment.schema.Measurand] as an XML element.
        """
        attrib = {"quantity": self.quantity, "calibrationInterval": str(self.calibration_interval)}
        e = Element("measurand", attrib=attrib)
        e.extend(c.to_xml() for c in self.components)
        return e


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

    accessories: Accessories = field(default_factory=Accessories)
    """Additional accessories that may be required to use the equipment."""

    documentation: str = ""
    """Information (such as URLs) about the manuals, datasheets, etc. for the equipment."""

    financial: Financial = field(default_factory=Financial)
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
        a, d, f, pr, sa = Accessories(), "", Financial(), "", ""
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

        if len(self.accessories) or len(self.accessories.attrib):
            e.append(self.accessories)

        if self.documentation:
            d = SubElement(e, "documentation")
            d.text = self.documentation

        if self.financial != Financial():
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


@dataclass(frozen=True, repr=False)
class Equipment:
    """Represents the [equipment][type_equipment]{:target="_blank"} element in an equipment register.

    Args:
        entered_by: The name of the person who initially entered the `equipment` element in the register.
        checked_by: The name of the person who checked the information in the `equipment` element.
        checked_date: The date that the information in the `equipment` element was last checked.
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

    entered_by: str = ""
    """The name of the person who initially entered the `equipment` element in the register."""

    checked_by: str = ""
    """The name of the person who checked the information in the `equipment` element."""

    checked_date: _date | None = None
    """The date that the information in the `equipment` element was last checked."""

    alias: str = ""
    """An alternative name to associate with the equipment."""

    keywords: tuple[str, ...] = ()
    """Keywords that describe the equipment."""

    id: str = ""
    """Identity in an equipment register."""

    manufacturer: str = ""
    """Name of manufacturer."""

    model: str = ""
    """Manufacturer's model number (or type identification)."""

    serial: str = ""
    """Manufacturer's serial number (or other unique identification)."""

    description: str = ""
    """A short description about the equipment."""

    specifications: Specifications = field(default_factory=Specifications)
    """Specifications provided by the manufacturer of the equipment."""

    location: str = ""
    """The usual location (laboratory) that the equipment is found in."""

    status: Status = Status.Active
    """The status of the equipment is an indication of whether the equipment
    is active (in use) or inactive (not in use)."""

    loggable: bool = False
    """Whether measurements from the equipment should be logged."""

    traceable: bool = False
    """Whether the equipment is used for a traceable measurement."""

    calibrations: tuple[Measurand, ...] = ()
    """The calibration history."""

    maintenance: Maintenance = field(default_factory=Maintenance)
    """The maintenance history and maintenance plan."""

    alterations: tuple[Alteration, ...] = ()
    """The alteration history."""

    firmware: tuple[Firmware, ...] = ()
    """The firmware version history."""

    specified_requirements: SpecifiedRequirements = field(default_factory=SpecifiedRequirements)
    """Verification that equipment conforms with specified requirements before
    being placed or returned into service."""

    reference_materials: ReferenceMaterials = field(default_factory=ReferenceMaterials)
    """Documentation of reference materials, results, acceptance criteria, relevant
    dates and the period of validity."""

    quality_manual: QualityManual = field(default_factory=QualityManual)
    """Information that is specified in Section 4.3.6 of the MSL Quality Manual."""

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        nr = sum(1 for m in self.calibrations for c in m.components for _ in c.reports)
        reports = "report" if nr == 1 else "reports"

        npc = sum(1 for m in self.calibrations for c in m.components for _ in c.performance_checks)
        checks = "check" if npc == 1 else "checks"

        return (
            f"<{self.__class__.__name__} id={self.id!r}, manufacturer={self.manufacturer!r}, "
            f"model={self.model!r}, serial={self.serial!r} ({nr} {reports}, {npc} {checks})>"
        )

    @classmethod
    def from_xml(cls, element: Element[str]) -> Equipment:
        """Convert an XML element into an [Equipment][msl.equipment.schema.Equipment] instance.

        Args:
            element: An [equipment][type_equipment]{:target="_blank"} XML element from an equipment register.

        Returns:
            The [Equipment][msl.equipment.schema.Equipment] instance.
        """
        # Schema forces order
        a = element.attrib
        return cls(
            entered_by=a["enteredBy"],
            checked_by=a.get("checkedBy", ""),
            checked_date=None if not a.get("checkedDate") else _date.fromisoformat(a["checkedDate"]),
            alias=a.get("alias", ""),
            keywords=tuple(a.get("keywords", "").split()),
            id=element[0].text or "",
            manufacturer=element[1].text or "",
            model=element[2].text or "",
            serial=element[3].text or "",
            description=element[4].text or "",
            specifications=Specifications.from_xml(element[5]),
            location=element[6].text or "",
            status=Status(element[7].text),
            loggable=element[8].text in {"1", "true"},
            traceable=element[9].text in {"1", "true"},
            calibrations=tuple(Measurand.from_xml(e) for e in element[10]),
            maintenance=Maintenance.from_xml(element[11]),
            alterations=tuple(Alteration.from_xml(e) for e in element[12]),
            firmware=tuple(Firmware.from_xml(e) for e in element[13]),
            specified_requirements=SpecifiedRequirements.from_xml(element[14]),
            reference_materials=ReferenceMaterials.from_xml(element[15]),
            quality_manual=QualityManual.from_xml(element[16]),
        )

    def to_xml(self) -> Element[str]:
        """Convert the [Equipment][msl.equipment.schema.Equipment] class into an XML element.

        Returns:
            The [Equipment][msl.equipment.schema.Equipment] as an XML element.
        """
        a = {"enteredBy": self.entered_by}
        if self.checked_by:
            a["checkedBy"] = self.checked_by
        if self.checked_date is not None:
            a["checkedDate"] = self.checked_date.isoformat()
        if self.alias:
            a["alias"] = self.alias
        if self.keywords:
            a["keywords"] = " ".join(self.keywords)

        e = Element("equipment", attrib=a)

        _id = SubElement(e, "id")
        _id.text = self.id

        manufacturer = SubElement(e, "manufacturer")
        manufacturer.text = self.manufacturer

        model = SubElement(e, "model")
        model.text = self.model

        serial = SubElement(e, "serial")
        serial.text = self.serial

        description = SubElement(e, "description")
        description.text = self.description

        e.append(self.specifications)

        location = SubElement(e, "location")
        location.text = self.location

        status = SubElement(e, "status")
        status.text = self.status.value

        loggable = SubElement(e, "loggable")
        loggable.text = "true" if self.loggable else "false"

        traceable = SubElement(e, "traceable")
        traceable.text = "true" if self.traceable else "false"

        calibrations = SubElement(e, "calibrations")
        calibrations.extend(c.to_xml() for c in self.calibrations)

        e.append(self.maintenance.to_xml())

        alterations = SubElement(e, "alterations")
        alterations.extend(a.to_xml() for a in self.alterations)

        firmware = SubElement(e, "firmware")
        firmware.extend(f.to_xml() for f in self.firmware)

        e.append(self.specified_requirements)
        e.append(self.reference_materials)
        e.append(self.quality_manual.to_xml())
        return e

    def latest_reports(self, date: DateValue = "stop") -> Iterator[tuple[str, str, Report]]:
        """Yields the latest calibration reports for every measurand _quantity_ and _component_.

        Args:
            date: Which date in a report to use to determine what _latest_ refers to:

                * `issue`: Report issue date
                * `start`: Measurement start date
                * `stop`: Measurement stop date

        Yields:
            The ([quantity][msl.equipment.schema.Measurand.quantity],
                [name][msl.equipment.schema.Component.name],
                [Report][msl.equipment.schema.Report]) value for the latest calibration report.
        """
        default = _date(1875, 5, 20)
        for m in self.calibrations:
            for c in m.components:
                latest = default
                report: Report | None = None
                for r in c.reports:
                    if date == "stop":
                        if r.measurement_stop_date > latest:
                            report = r
                            latest = r.measurement_stop_date
                    elif date == "start":
                        if r.measurement_start_date > latest:
                            report = r
                            latest = r.measurement_start_date
                    elif r.report_issue_date > latest:
                        report = r
                        latest = r.report_issue_date

                if report is not None:
                    yield m.quantity, c.name, report

    def latest_report(self, *, quantity: str = "", name: str = "", date: DateValue = "stop") -> Report | None:
        """Returns the latest calibration report.

        Args:
            quantity: The measurand [quantity][msl.equipment.schema.Measurand.quantity].
            name: The component [name][msl.equipment.schema.Component.name].
            date: Which date in a report to use to determine what _latest_ refers to:

                * `issue`: Report issue date
                * `start`: Measurement start date
                * `stop`: Measurement stop date

        Returns:
            The latest [Report][msl.equipment.schema.Report]) for the specified `quantity` and `name`.
                If the _equipment_ has only one measurand _quantity_ and only one _component_ and if the
                `quantity` and `name` values are both empty strings then that report is returned. Otherwise,
                returns `None` if there is no report that matches the `quantity` and `name` criteria or the
                _equipment_ does not have calibration reports entered in the register.
        """
        reports = list(self.latest_reports(date=date))
        if len(reports) == 1 and not quantity and not name:
            return reports[0][2]

        for q, n, report in reports:
            if quantity == q and name == n:
                return report

        return None


class Register:
    """Represents the [register][element_register]{:target="_blank"} element in an equipment register."""

    NAMESPACE: str = "https://measurement.govt.nz/equipment-register"
    """Default XML namespace."""

    def __init__(self, source: XMLSource) -> None:
        """Represents the [register][element_register]{:target="_blank"} element in an equipment register.

        Args:
            source: A [path-like object][]{:target="_blank"} or a [file-like object][]{:target="_blank"}
                that contains an equipment register.
        """
        self._root: Element[str] = ElementTree().parse(source)
        self._equipment: list[Equipment | None] = [None] * len(self._root)

        # a mapping between the alias/id and the index number in the register
        self._index_map: dict[str, int] = {
            e.attrib["alias"]: i for i, e in enumerate(self._root) if e.attrib.get("alias")
        }
        self._index_map.update({e[0].text or "": i for i, e in enumerate(self._root)})

    def __getitem__(self, item: str | int) -> Equipment:
        """Returns an Equipment item from the register."""
        if isinstance(item, str):
            index = self._index_map.get(item)
            if index is None:
                msg = f"No equipment exists with an alias or id of {item!r}"
                raise ValueError(msg)
        else:
            index = item

        e = self._equipment[index]
        if e is None:
            e = Equipment.from_xml(self._root[index])
            self._equipment[index] = e
        return e

    def __iter__(self) -> Iterator[Equipment]:
        """Yields the Equipment elements in the register."""
        for i, e in enumerate(self._equipment):
            if e is None:
                e = Equipment.from_xml(self._root[i])  # noqa: PLW2901
                self._equipment[i] = e
            yield e

    def __len__(self) -> int:
        """Returns the number of Equipment elements in the register."""
        return len(self._root)

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return f"<{self.__class__.__name__} team={self.team!r} ({len(self)} equipment)>"

    @property
    def team(self) -> str:
        """[str][] &mdash; Returns the name of the team that is responsible for the equipment register."""
        return self._root.attrib["team"]

    def tree(self, namespace: str | None = "DEFAULT") -> ElementTree[Element[str]]:
        """Convert the [Register][msl.equipment.schema.Register] class into an XML element tree.

        Args:
            namespace: The namespace to associate with the root element. If the value is
                `DEFAULT`, uses the value of [NAMESPACE][msl.equipment.schema.Register.NAMESPACE]
                as the namespace. If `None`, or an empty string, no namespace is associated
                with the root element.

        Returns:
            The [Register][msl.equipment.schema.Register] as an
                [ElementTree][xml.etree.ElementTree.ElementTree]{:target="_blank"}.
        """
        attrib = {"team": self.team}
        if namespace:
            if namespace == "DEFAULT":
                namespace = self.NAMESPACE
            attrib["xmlns"] = namespace

        e = Element("register", attrib=attrib)
        e.extend(equipment.to_xml() for equipment in self)
        return ElementTree(element=e)
