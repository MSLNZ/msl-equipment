"""Classes for the equipment register and connection schemas."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date as _date
from enum import Enum
from io import StringIO
from math import isinf
from typing import TYPE_CHECKING, NamedTuple
from xml.etree.ElementTree import Element, ElementTree, SubElement

import numpy as np

from .enumerations import Backend
from .utils import logger, to_primitive

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any as _Any
    from typing import Callable, Literal, TypeVar

    from numpy.typing import ArrayLike, DTypeLike, NDArray

    from ._types import PathLike, XMLSource

    A = TypeVar("A", bound="Any")
    L = TypeVar("L", bound="Latest")
    Self = TypeVar("Self", bound="Interface")


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


class _Indent:
    table_data: int = 0


def _future_date(relative_to: _date, years: float) -> _date:
    """Calculate a date in the future when a calibration is due.

    Args:
        relative_to: The relative-to date.
        years: The number of years in the future (e.g., use 0.5 for 6 months).

    Returns:
        The future date.
    """
    year, month_decimal = divmod(years, 1)
    month = relative_to.month + int(month_decimal * 12)  # round down so a calibration happens sooner
    if month > 12:  # noqa: PLR2004
        year += 1
        month -= 12

    if month == 2:  # noqa: PLR2004
        day = min(28, relative_to.day)  # ignore leap years
    elif month in {4, 6, 9, 11}:  # April, June, September, November
        day = min(30, relative_to.day)
    else:
        day = relative_to.day

    year = relative_to.year + int(year)
    return relative_to.replace(year=year, month=month, day=day)


def _latest(*, items: list[L], quantity: str, name: str) -> L | None:
    """Returns the latest report or performance check."""
    if len(items) == 1 and (quantity == "" or quantity == items[0].quantity) and (name == "" or name == items[0].name):
        return items[0]

    for item in items:
        if quantity == item.quantity and name == item.name:
            return item

    return None


class Status(Enum):
    """Represents the [status][type_statusEnumerationString] enumeration in an equipment register.

    Attributes:
        Active (str): The equipment is operable and may be used.
        Damaged (str): The equipment is damaged and is no longer usable.
        Disposed (str): The equipment has been disposed of and is no longer at available
            (e.g., the equipment was sent to the landfill or to be recycled).
        Dormant (str): The equipment is still operable, it is no longer in use but may be used again
            (e.g., the equipment was replaced with a newer model, and it is kept as a backup).
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
    """Represents the [digitalFormatEnumerationString][type_digitalFormatEnumerationString] enumeration in an equipment register.

    Attributes:
        MSL_PDF (str): `"MSL PDF/A-3"` (MSL's PDF/A-3 format).
        PTB_DCC (str): `"PTB DCC"` (PTB's Digital Calibration Certificate).
    """  # noqa: E501

    MSL_PDF = "MSL PDF/A-3"
    PTB_DCC = "PTB DCC"


class Any(Element):
    """Base class that represents the [any][type_any] type in the XML Schema Definition."""

    def __init__(self, **attributes: str) -> None:
        """Base class that represents the [any][type_any] type in the XML Schema Definition.

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

    Since this class is currently represented by the [any][type_any] type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element].
    It may be updated to be a more specific class at a later date.
    """

    tag: str = "accessories"
    """The element's name."""


@dataclass(frozen=True)
class Alteration:
    """Represents the [alteration][type_alteration] element in an equipment register.

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
            element: An [alteration][type_alteration] XML element from an equipment register.

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
    """Represents the acceptance criteria in a calibration [report][type_report].

    Since this class is currently represented by the [any][type_any] type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element].
    It may be updated to be a more specific class at a later date.
    """

    tag: str = "acceptanceCriteria"
    """The element's name."""


class Conditions(Any):
    """Conditions under which a [performance check][type_performanceCheck] or calibration [report][type_report] is valid.

    Since this class is currently represented by the [any][type_any] type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element].
    It may be updated to be a more specific class at a later date.
    """  # noqa: E501

    tag: str = "conditions"
    """The element's name."""


@dataclass(frozen=True)
class CapitalExpenditure:
    """Represents the [capitalExpenditure][type_capitalExpenditure] element in an equipment register.

    Args:
        asset_number: The asset number in the financial system.
        depreciation_end_year: The year (inclusive) that depreciation ends for the asset.
        price: The purchase price of the asset.
        currency: The currency associated with the `price`.
    """

    asset_number: str
    """The asset number in the financial system."""

    depreciation_end_year: int
    """The year (inclusive) that depreciation ends for the asset."""

    price: float
    """The price of the asset."""

    currency: str
    """The currency associated with the `price`."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> CapitalExpenditure:
        """Convert an XML element into a [CapitalExpenditure][msl.equipment.schema.CapitalExpenditure] instance.

        Args:
            element: A [capitalExpenditure][type_capitalExpenditure] XML element
                from an equipment register.

        Returns:
            The [CapitalExpenditure][msl.equipment.schema.CapitalExpenditure] instance.
        """
        # Schema forces order
        return cls(
            asset_number=element[0].text or "",
            depreciation_end_year=int(element[1].text or 0),
            price=float(element[2].text or 0),
            currency=element[2].attrib["currency"],
        )

    def to_xml(self) -> Element[str]:
        """Convert the [CapitalExpenditure][msl.equipment.schema.CapitalExpenditure] class into an XML element.

        Returns:
            The [CapitalExpenditure][msl.equipment.schema.CapitalExpenditure] as an XML element.
        """
        e = Element("capitalExpenditure")

        an = SubElement(e, "assetNumber")
        an.text = self.asset_number

        dey = SubElement(e, "depreciationEndYear")
        dey.text = str(self.depreciation_end_year)

        p = SubElement(e, "price", attrib={"currency": self.currency})
        p.text = f"{self.price:.14g}"

        return e


@dataclass(frozen=True)
class Financial:
    """Represents the [financial][type_financial] element in an equipment register.

    Args:
        capital_expenditure: The equipment is a capital expenditure.
        purchase_year: The (approximate) year that the equipment was purchased.
            A value of `0` represents that the year is unknown.
        warranty_expiration_date: Approximate date that the warranty expires.
    """

    capital_expenditure: CapitalExpenditure | None = None
    """The equipment is a capital expenditure."""

    purchase_year: int = 0
    """The (approximate) year that the equipment was purchased. A value of `0` represents that the year is unknown."""

    warranty_expiration_date: _date | None = None
    """Approximate date that the warranty expires."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Financial:
        """Convert an XML element into a [Financial][msl.equipment.schema.Financial] instance.

        Args:
            element: A [financial][type_financial] XML element from an equipment register.

        Returns:
            The [Financial][msl.equipment.schema.Financial] instance.
        """
        # Schema defines <financial> using xsd:all, which allows sub-elements to appear (or not appear) in any order
        # Using str.endswith() allows for ignoring XML namespaces that may be associated with each tag
        cap_ex, warranty, year = None, None, 0
        for child in element:
            if child.tag.endswith("capitalExpenditure"):
                cap_ex = CapitalExpenditure.from_xml(child)
            elif child.tag.endswith("warrantyExpirationDate"):
                warranty = _date.fromisoformat(child.text or "")
            else:
                year = int(child.text or 0)
        return cls(capital_expenditure=cap_ex, purchase_year=year, warranty_expiration_date=warranty)

    def to_xml(self) -> Element[str]:
        """Convert the [Financial][msl.equipment.schema.Financial] class into an XML element.

        Returns:
            The [Financial][msl.equipment.schema.Financial] as an XML element.
        """
        e = Element("financial")

        if self.capital_expenditure is not None:
            e.append(self.capital_expenditure.to_xml())

        if self.purchase_year > 0:
            py = SubElement(e, "purchaseYear")
            py.text = str(self.purchase_year)

        if self.warranty_expiration_date is not None:
            wed = SubElement(e, "warrantyExpirationDate")
            wed.text = self.warranty_expiration_date.isoformat()

        return e


@dataclass(frozen=True)
class Firmware:
    """Represents a [firmware][type_firmware] `<version>` sub-element in an equipment register.

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
            element: A [firmware][type_firmware] `<version>` XML sub-element
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
    """Represents the [completedTask][type_completedTask] element in an equipment register.

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
            element: A [completedTask][type_completedTask] XML element from an equipment register.

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
    """Represents the [plannedTask][type_plannedTask] element in an equipment register.

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
            element: A [plannedTask][type_plannedTask] XML element from an equipment register.

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
    """Represents the [maintenance][type_maintenance] element in an equipment register.

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
            element: A [maintenance][type_maintenance] XML element from an equipment register.

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

    def check_within_range(self, value: float | ArrayLike) -> Literal[True]:
        """Check that the values are within the range.

        Args:
            value: The values to check, raises

        Returns:
            Always returns `True`. Raises [ValueError][] if
                `value` is not within the range.
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
    r"""Represents the `<value>` and `<uncertainty>` XML elements in an [equation][type_equation].

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
            data: A mapping of variable names to values to evaluate the equation with.
            check_range: Whether to check that the data is within the allowed ranges.

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
    """Represents the [equation][type_equation] element in an equipment register.

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
            element: An [equation][type_equation] XML element from an equipment register.

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
    """Represents the [competency][type_competency] element in an equipment register.

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
            element: A [competency][type_competency] XML element from an equipment register.

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
    """Represents the [file][type_file] element in an equipment register.

    Args:
        url: The location of the file. The syntax follows [RFC 1738](https://www.rfc-editor.org/rfc/rfc1738)
            `scheme:scheme-specific-part`. If `scheme:` is not specified, it is assumed to be `file:`.
        sha256: The SHA-256 checksum of the file.
        attributes: XML attributes associated with the `<url>` element.
        comment: A comment to associate with the file.
    """

    url: str
    """The location of the file.

    The syntax follows [RFC 1738](https://www.rfc-editor.org/rfc/rfc1738) `<scheme>:<scheme-specific-part>`.
    If `<scheme>` is not specified, it shall be treated as the `file` scheme
    (see also [scheme][msl.equipment.schema.File.scheme]).
    """

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
            element: A [file][type_file] XML element from an equipment register.

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

    @property
    def scheme(self) -> str:
        """Returns the _scheme_ component that is specified in the [url][msl.equipment.schema.File.url]
        (see [RFC 1738](https://www.rfc-editor.org/rfc/rfc1738) for more details).

        If a `<scheme>` is not specified, an empty string is returned (which shall be treated
        as the `file` scheme). Drive letters on Windows are not considered as a _scheme_.
        """  # noqa: D205
        index = self.url.find(":")
        if index == -1:
            return ""

        scheme = self.url[:index]
        if index == 1 and scheme.lower() in "abcdefghijklmnopqrstuvwxyz":  # assume Windows drive letter
            return ""

        return scheme

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
    """Represents the opposite of the [serialised][type_serialised] element in an equipment register.

    Args:
        value: The value of the deserialised object.
        comment: A comment to associate with the (de)serialised object.
    """

    value: _Any
    """The value of the deserialised object. For example, an [Archive][persistence.Archive]
    object from [GTC](https://gtc.readthedocs.io/en/stable/).
    """

    comment: str = ""
    """A comment associated with the (de)serialised object."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Deserialised:
        """Convert a [serialised][type_serialised] XML element into a [Deserialised][msl.equipment.schema.Deserialised] instance.

        Args:
            element: A [serialised][type_serialised] XML element from an equipment register.

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
        """Convert the [Deserialised][msl.equipment.schema.Deserialised] class into a [serialised][type_serialised] XML element.

        Returns:
            The [serialised][type_serialised] XML element.
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

    This XML element is found in [component][type_component].

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
                (see [component][type_component]).

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
    """Represents the [digitalReport][type_digitalReport] element in an equipment register.

    Args:
        url: The location of the digital report. The syntax follows [RFC 1738](https://www.rfc-editor.org/rfc/rfc1738)
            `scheme:scheme-specific-part`. If `scheme:` is not specified, it is assumed to be `file:`.
        format: The format of the digital calibration report.
        id: The report identification number.
        sha256: The SHA-256 checksum of the digital report.
        attributes: XML attributes associated with the `<url>` element.
        comment: A comment to associate with the digital report.
    """

    url: str
    """The location of the digital report. The syntax follows [RFC 1738](https://www.rfc-editor.org/rfc/rfc1738)
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
            element: A [digitalReport][type_digitalReport] XML element from an equipment register.

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


def _cvd_resistance(  # noqa: PLR0913
    temperature: float | np.ndarray, r0: float, a: float, b: float, c: float, d: float
) -> NDArray[np.float64]:
    """Calculate resistance from temperature."""
    return np.piecewise(
        temperature,
        [temperature < 0, temperature >= 0],
        [
            lambda t: r0 * (1.0 + a * t + b * t**2 + c * t**3 * (t - 100.0)),
            lambda t: r0 * (1.0 + a * t + b * t**2 + d * t**3),
        ],
    )


@dataclass(frozen=True)
class CVDEquation:
    r"""The Callendar-Van Dusen (CVD) equation based on the [cvdCoefficients][type_cvdCoefficients] element in an equipment register.

    Args:
        R0: The value, in $\Omega$, of the resistance at $0~^\circ\text{C}$, $R_0$.
        A: The value, in $(^\circ\text{C})^{-1}$, of the A coefficient, $A \cdot t$.
        B: The value, in $(^\circ\text{C})^{-2}$, of the B coefficient, $B \cdot t^2$.
        C: The value, in $(^\circ\text{C})^{-4}$, of the C coefficient, $C \cdot t^3 \cdot (t-100)$.
        D: The value, in $(^\circ\text{C})^{-3}$, of the D coefficient, $D \cdot t^3$.
            The $D$ coefficient is typically zero but may be non-zero if $t \gtrsim 200~^{\circ}\text{C}$.
            If a calibration report does not specify the $D$ coefficient, set the value to be 0.
        uncertainty:  The equation to evaluate to calculate the *standard* uncertainty.
        ranges: The temperature range, in $(^\circ)\text{C}$, and the resistance range, in $\Omega$,
            that the CVD coefficients are valid. The temperature key must be `"t"` and the resistance
            key `"r"`.
        degree_freedom: The degrees of freedom.
        comment: A comment to associate with the CVD equation.
    """  # noqa: E501

    R0: float
    r"""The value, in $\Omega$, of the resistance at $0~^\circ\text{C}$, $R_0$."""

    A: float
    r"""The value, in $(^\circ\text{C})^{-1}$, of the A coefficient, $A \cdot t$."""

    B: float
    r"""The value, in $(^\circ\text{C})^{-2}$, of the B coefficient, $B \cdot t^2$."""

    C: float
    r"""The value, in $(^\circ\text{C})^{-4}$, of the C coefficient, $C \cdot t^3 \cdot (t-100)$."""

    D: float
    r"""The value, in $(^\circ\text{C})^{-3}$, of the D coefficient, $D \cdot t^3$."""

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
            temperature: The temperature values, in $^\circ\text{C}$.
            check_range: Whether to check that the temperature values are within the allowed range.

        Returns:
            The resistance values.
        """
        array = np.asarray(temperature, dtype=float)
        if check_range and self.ranges["t"].check_within_range(array):
            pass  # check_within_range() will raise an error, if one occurred

        return _cvd_resistance(array, self.R0, self.A, self.B, self.C, self.D)

    def temperature(self, resistance: ArrayLike, *, check_range: bool = True) -> NDArray[np.float64]:
        r"""Calculate temperature from resistance.

        Args:
            resistance: The resistance values, in $\Omega$.
            check_range: Whether to check that the resistance values are within the allowed range.

        Returns:
            The temperature values.
        """
        array: NDArray[np.float64] = np.asarray(resistance, dtype=float)
        if check_range and self.ranges["r"].check_within_range(array):
            pass  # check_within_range raised an error, if one occurred

        def positive_quadratic(r: NDArray[np.float64]) -> NDArray[np.float64]:
            # rearrange CVD equation to be: a*x^2 + b*x + c = 0
            #   a -> B, b -> A, c -> 1 - R/R0
            # then use the quadratic formula
            return (-self.A + np.sqrt(self.A**2 - 4.0 * self.B * (1.0 - r / self.R0))) / (2.0 * self.B)

        def positive_cubic(r: NDArray[np.float64]) -> NDArray[np.float64]:
            # rearrange CVD equation to be: a*x^3 + b*x^2 + c*x + d = 0
            a = self.D
            b = self.B
            c = self.A
            d = 1.0 - (r / self.R0)

            # then use Cardano's Formula
            # https://proofwiki.org/wiki/Cardano's_Formula#Real_Coefficients
            Q: float = (3.0 * a * c - b**2) / (9.0 * a**2)  # noqa: N806
            R: NDArray[np.float64] = (9.0 * a * b * c - 27.0 * a**2 * d - 2.0 * b**3) / (54.0 * a**3)  # noqa: N806
            sqrt: NDArray[np.float64] = np.sqrt(Q**3 + R**2)
            S: NDArray[np.float64] = np.cbrt(R + sqrt)  # noqa: N806
            T: NDArray[np.float64] = np.cbrt(R - sqrt)  # noqa: N806
            return S + T - (b / (3.0 * a))  # x1 equation

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

        positive = positive_quadratic if self.D == 0 else positive_cubic
        return np.piecewise(array, [array < self.R0, array >= self.R0], [negative, positive])

    @classmethod
    def from_xml(cls, element: Element[str]) -> CVDEquation:
        """Convert an XML element into a [CVDEquation][msl.equipment.schema.CVDEquation] instance.

        Args:
            element: A [cvdCoefficients][type_cvdCoefficients] XML element
                from an equipment register.

        Returns:
            The [CVDEquation][msl.equipment.schema.CVDEquation] instance.
        """
        # Schema forces order
        r0 = float(element[0].text or 0)
        a = float(element[1].text or 0)
        b = float(element[2].text or 0)
        c = float(element[3].text or 0)
        d = float(element[4].text or 0)

        r = element[6]
        _range = Range(float(r[0].text or -200), float(r[1].text or 661))
        ranges = {
            "t": _range,
            "r": Range(
                minimum=round(float(_cvd_resistance(_range.minimum, r0, a, b, c, d)), 3),
                maximum=round(float(_cvd_resistance(_range.maximum, r0, a, b, c, d)), 3),
            ),
        }

        u = element[5]
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
            D=d,
            uncertainty=uncertainty,
            ranges=ranges,
            degree_freedom=float(element[7].text or np.inf) if len(element) > 7 else np.inf,  # noqa: PLR2004
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

        d = SubElement(e, "D")
        d.text = str(self.D)

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
    """Represents the [table][type_table] element in an equipment register."""

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

        See [structured_to_unstructured][numpy.lib.recfunctions.structured_to_unstructured]
        for more details.

        Args:
            dtype: The _dtype_ of the output unstructured array.
            copy: If `True`, always return a copy. If `False`, a view is returned if possible.
            casting: Controls what kind of data casting may occur. See the *casting* argument of
                [astype][numpy.ndarray.astype] for more details.

        Returns:
            The unstructured array. This method may return a numpy [ndarray][numpy.ndarray] instance
                instead of a [Table][msl.equipment.schema.Table] instance if the table consists of
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
            element: A [table][type_table] XML element from an equipment register.

        Returns:
            A [Table][msl.equipment.schema.Table] is an subclass of a numpy
                [structured array][structured_arrays], where the `header` is used as
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
                return stripped.decode()  # pragma: no cover
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
        newline = "\n" + " " * _Indent.table_data
        np.savetxt(buffer, self, fmt="%s", delimiter=",", newline=newline)
        data = SubElement(e, "data")
        data.text = buffer.getvalue().rstrip() + "\n" + " " * max(0, _Indent.table_data - len("<data>"))

        return e


@dataclass(frozen=True)
class PerformanceCheck:
    """Represents the [performanceCheck][type_performanceCheck] element in an equipment register.

    Args:
        completed_date: The date that the performance check was completed.
        competency: The competent people who accomplished the performance check and the technical procedure
            that was executed.
        entered_by: The name of the person who initially entered the `<performanceCheck>` element in the register.
        checked_by: The name of the person who checked the information in the `<performanceCheck>` element.
        checked_date: The date that the information in the `<performanceCheck>` element was last checked.
        conditions: The conditions under which the performance check is valid.
        cvd_equations: Performance-check data is expressed as coefficients for the Callendar-Van Dusen equation.
        equations: Performance-check data is expressed as an equation.
        files: Performance-check data is stored in another file (not in the equipment register).
        deserialised: Performance-check data is stored in a serialised format and deserialised.
        tables: Performance-check data is expressed as a CSV table in the equipment register.
    """

    completed_date: _date
    """The date that the performance check was completed."""

    competency: Competency
    """The competent people who accomplished the performance check and the technical procedure that was executed."""

    entered_by: str
    """The name of the person who initially entered the `<performanceCheck>` element in the register."""

    checked_by: str = ""
    """The name of the person who checked the information in the `<performanceCheck>` element."""

    checked_date: _date | None = None
    """The date that the information in the `<performanceCheck>` element was last checked."""

    conditions: Conditions = field(default_factory=Conditions)
    """The conditions under which the performance check is valid."""

    cvd_equations: tuple[CVDEquation, ...] = ()
    """Performance-check data is expressed as coefficients for the Callendar-Van Dusen equation."""

    equations: tuple[Equation, ...] = ()
    """Performance-check data is expressed as an equation."""

    files: tuple[File, ...] = ()
    """Performance-check data is stored in another file (not in the equipment register)."""

    deserialised: tuple[Deserialised, ...] = ()
    """Performance-check data is stored in a serialised format and deserialised."""

    tables: tuple[Table, ...] = ()
    """Performance-check data is expressed as a CSV table in the equipment register."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> PerformanceCheck:
        """Convert an XML element into a [PerformanceCheck][msl.equipment.schema.PerformanceCheck] instance.

        Args:
            element: A [performanceCheck][type_performanceCheck] XML element from an
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
            element: An `<issuingLaboratory>` element from a [report][type_report] element
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
    """Represents the [report][type_report] element in an equipment register.

    Args:
        id: The report identification number.
        entered_by: The name of the person who initially entered the `<report>` element in the register.
        report_issue_date: The date that the report was issued.
        measurement_start_date: The date that the calibration measurement started.
        measurement_stop_date: The date that the calibration measurement stopped.
        issuing_laboratory: Information about the laboratory that issued the calibration report.
        technical_procedure: The technical procedure(s) that was(were) followed to perform the calibration.
        checked_by: The name of the person who checked the information in the `<report>` element.
        checked_date: The date that the information in the `<report>` element was last checked.
        conditions: The conditions under which the report is valid.
        acceptance_criteria: Acceptance criteria for the calibration report.
        cvd_equations: Calibration data is expressed as coefficients for the Callendar-Van Dusen equation.
        equations: Calibration data is expressed as an equation.
        files: Calibration data is stored in another file (not in the equipment register).
        deserialised: Calibration data is stored in a serialised format and deserialised.
        tables: Calibration data is expressed as a CSV table in the equipment register.
    """

    id: str
    """The report identification number."""

    entered_by: str
    """The name of the person who initially entered the `<report>` element in the register."""

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
    """The name of the person who checked the information in the `<report>` element."""

    checked_date: _date | None = None
    """The date that the information in the `<report>` element was last checked."""

    conditions: Conditions = field(default_factory=Conditions)
    """The conditions under which the report is valid."""

    acceptance_criteria: AcceptanceCriteria = field(default_factory=AcceptanceCriteria)
    """Acceptance criteria for the calibration report."""

    cvd_equations: tuple[CVDEquation, ...] = ()
    """Calibration data is expressed as coefficients for the Callendar-Van Dusen equation."""

    equations: tuple[Equation, ...] = ()
    """Calibration data is expressed as an equation."""

    files: tuple[File, ...] = ()
    """Calibration data is stored in another file (not in the equipment register)."""

    deserialised: tuple[Deserialised, ...] = ()
    """Calibration data is stored in a serialised format and deserialised."""

    tables: tuple[Table, ...] = ()
    """Calibration data is expressed as a CSV table in the equipment register."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Report:
        """Convert an XML element into a [Report][msl.equipment.schema.Report] instance.

        Args:
            element: A [report][type_report] XML element from an equipment register.

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
    """Represents the [component][type_component] element in an equipment register.

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
            element: A [component][type_component] XML element from an equipment register.

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
    """Represents the [measurand][type_measurand] element in an equipment register.

    Args:
        quantity: The kind of quantity that is measured.
        calibration_interval: The number of years that may pass between a calibration or a performance check.
            For equipment that do not have a required and periodic interval, but are calibrated on demand,
            set the value to `0`.
        components: The components of the equipment that measure the `quantity`.
    """

    quantity: str
    """The kind of quantity that is measured."""

    calibration_interval: float
    """The number of years that may pass between a calibration or a performance check.

    For equipment that do not have a required and periodic interval, but are calibrated on demand,
    the value is `0`.
    """

    components: tuple[Component, ...] = ()
    """The components of the equipment that measure the `quantity`."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> Measurand:
        """Convert an XML element into a [Measurand][msl.equipment.schema.Measurand] instance.

        Args:
            element: A [measurand][type_measurand] XML element from an equipment register.

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
    """Represents the [qualityManual][type_qualityManual] element in an equipment register.

    Args:
        accessories: Additional accessories that may be required to use the equipment.
        documentation: Information (such as URLs) about the manuals, datasheets, etc. for the equipment.
        financial: Financial information about the equipment.
        personnel_restrictions: Information about the people (or team) who are qualified to use the equipment.
        service_agent: Information about the people or company that are qualified to perform alterations and/or
            maintenance to the equipment.
        technical_procedures: The technical procedures that depend on this equipment.
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
    """The technical procedures that depend on this equipment."""

    @classmethod
    def from_xml(cls, element: Element[str]) -> QualityManual:
        """Convert an XML element into an [QualityManual][msl.equipment.schema.QualityManual] instance.

        Args:
            element: A [qualityManual][type_qualityManual] XML element from an equipment register.

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

    Since this class is currently represented by the [any][type_any] type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element].
    It may be updated to be a more specific class at a later date.
    """

    tag: str = "referenceMaterials"
    """The element's name."""


class Specifications(Any):
    """Specifications provided by the manufacturer of the equipment.

    Typically, the specifications are specified on the website, datasheet and/or technical notes that a
    manufacturer provides.

    Since this class is currently represented by the [any][type_any] type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element].
    It may be updated to be a more specific class at a later date.
    """

    tag: str = "specifications"
    """The element's name."""


class SpecifiedRequirements(Any):
    """Verification that equipment conforms with specified requirements before being placed or returned into service.

    Since this class is currently represented by the [any][type_any] type in the
    XML Schema Definition, it is simply a subclass of [Element][xml.etree.ElementTree.Element].
    It may be updated to be a more specific class at a later date.
    """

    tag: str = "specifiedRequirements"
    """The element's name."""


@dataclass(frozen=True)
class Latest:
    """Base class for [LatestReport][msl.equipment.schema.LatestReport] and [LatestPerformanceCheck][msl.equipment.schema.LatestPerformanceCheck]."""  # noqa: E501

    calibration_interval: float
    """The number of years that may pass between a calibration or a performance check.

    For equipment that do not have a required and periodic interval, but are calibrated on demand,
    the value is `0`.
    """

    name: str
    """The [Component][msl.equipment.schema.Component] name."""

    next_calibration_date: _date
    """The date that the equipment is due for a re-calibration.

    If the [calibration_interval][msl.equipment.schema.Latest.calibration_interval] is `0`,
    i.e., the equipment is calibrated on demand, this date is equal to the date that
    the equipment was last calibrated.
    """

    quantity: str
    """The [Measurand][msl.equipment.schema.Measurand] quantity."""

    def is_calibration_due(self, months: int = 0) -> bool:
        """Determine if the equipment needs to be re-calibrated.

        Args:
            months: The number of months to add to today's date to determine if
                the equipment needs to be re-calibrated.

        Returns:
            Whether a calibration is due within the specified number of `months`.
        """
        if self.calibration_interval <= 0:
            return False  # calibrate on-demand

        ask_date = _future_date(_date.today(), max(0.0, months / 12.0))  # noqa: DTZ011
        return ask_date >= self.next_calibration_date


@dataclass(frozen=True)
class LatestReport(Latest):
    """Latest calibration report."""

    report: Report
    """Latest calibration report."""


@dataclass(frozen=True)
class LatestPerformanceCheck(Latest):
    """Latest performance check."""

    performance_check: PerformanceCheck
    """Latest performance check."""


@dataclass(frozen=True, repr=False)
class Equipment:
    """Represents the [equipment][type_equipment] element in an equipment register.

    Args:
        entered_by: The name of the person who initially entered the `<equipment>` element in the register.
        checked_by: The name of the person who checked the information in the `<equipment>` element.
        checked_date: The date that the information in the `<equipment>` element was last checked.
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
        connection: The connection to the equipment for computer control.
    """

    entered_by: str = ""
    """The name of the person who initially entered the `<equipment>` element in the register."""

    checked_by: str = ""
    """The name of the person who checked the information in the `<equipment>` element."""

    checked_date: _date | None = None
    """The date that the information in the `<equipment>` element was last checked."""

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

    connection: Connection | None = None
    """The connection to use for computer control."""

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        items: list[str] = []

        na = sum(1 for m in self.calibrations for c in m.components for _ in c.adjustments)
        if na > 0:
            plural = "" if na == 1 else "s"
            items.append(f"{na} adjustment{plural}")

        ndr = sum(1 for m in self.calibrations for c in m.components for _ in c.digital_reports)
        if ndr > 0:
            plural = "" if ndr == 1 else "s"
            items.append(f"{ndr} digital report{plural}")

        npc = sum(1 for m in self.calibrations for c in m.components for _ in c.performance_checks)
        if npc > 0:
            plural = "" if npc == 1 else "s"
            items.append(f"{npc} performance check{plural}")

        nr = sum(1 for m in self.calibrations for c in m.components for _ in c.reports)
        if nr > 0:
            plural = "" if nr == 1 else "s"
            items.append(f"{nr} report{plural}")

        summary = "" if not items else " (" + ", ".join(items) + ")"
        return (
            f"<{self.__class__.__name__} manufacturer={self.manufacturer!r}, "
            f"model={self.model!r}, serial={self.serial!r}{summary}>"
        )

    def connect(self) -> _Any:  # noqa: ANN401
        """Connect to the equipment."""
        if self.connection is None:
            super().__setattr__("connection", connections[self.id])
            assert self.connection is not None  # noqa: S101

        for backend in backends:
            if backend.handles(self.connection):
                return backend.cls(self)

        for resource in resources:
            if resource.handles(self):
                return resource.cls(self)

        address = self.connection.address
        for interface in interfaces:
            if interface.handles(address):
                return interface.cls(self)

        msg = f"Cannot determine the interface from the address {address!r}"
        raise ValueError(msg)

    @classmethod
    def from_xml(cls, element: Element[str]) -> Equipment:
        """Convert an XML element into an [Equipment][msl.equipment.schema.Equipment] instance.

        Args:
            element: An [equipment][type_equipment] XML element from an equipment register.

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

        The [connection][msl.equipment.schema.Equipment.connection] attribute is not included
        as an XML element.

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

    def latest_performance_checks(self) -> Iterator[LatestPerformanceCheck]:
        """Yields the latest performance check for every _measurand_ and _component_.

        Yields:
            The latest performance check.
        """
        default = _date(1875, 5, 20)
        for m in self.calibrations:
            for c in m.components:
                latest = default
                check: PerformanceCheck | None = None
                for pc in c.performance_checks:
                    if pc.completed_date > latest:
                        check = pc
                        latest = pc.completed_date

                if check is not None:
                    yield LatestPerformanceCheck(
                        calibration_interval=m.calibration_interval,
                        name=c.name,
                        next_calibration_date=_future_date(latest, m.calibration_interval),
                        performance_check=check,
                        quantity=m.quantity,
                    )

    def latest_performance_check(self, *, quantity: str = "", name: str = "") -> LatestPerformanceCheck | None:
        """Returns the latest performance check.

        Args:
            quantity: The measurand [quantity][msl.equipment.schema.Measurand.quantity].
            name: The component [name][msl.equipment.schema.Component.name].

        Returns:
            The [LatestPerformanceCheck][msl.equipment.schema.LatestPerformanceCheck] for the specified
                `quantity` and `name`. If the equipment has only one _measurand_ and only one _component_
                then you do not need to specify a value for the `quantity` and `name`. Returns `None` if
                there are no performance checks that match the `quantity` and `name` criteria or if
                the equipment does not have performance checks entered in the register.
        """
        return _latest(items=list(self.latest_performance_checks()), quantity=quantity, name=name)

    def latest_reports(self, date: Literal["issue", "start", "stop"] = "stop") -> Iterator[LatestReport]:
        """Yields the latest calibration report for every _measurand_ and _component_.

        Args:
            date: Which date in a report to use to determine what _latest_ refers to:

                * `issue`: Report issue date
                * `start`: Measurement start date
                * `stop`: Measurement stop date

        Yields:
            The latest calibration report.
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
                    yield LatestReport(
                        calibration_interval=m.calibration_interval,
                        name=c.name,
                        next_calibration_date=_future_date(latest, m.calibration_interval),
                        report=report,
                        quantity=m.quantity,
                    )

    def latest_report(
        self, *, quantity: str = "", name: str = "", date: Literal["issue", "start", "stop"] = "stop"
    ) -> LatestReport | None:
        """Returns the latest calibration report.

        Args:
            quantity: The measurand [quantity][msl.equipment.schema.Measurand.quantity].
            name: The component [name][msl.equipment.schema.Component.name].
            date: Which date in a report to use to determine what _latest_ refers to:

                * `issue`: Report issue date
                * `start`: Measurement start date
                * `stop`: Measurement stop date

        Returns:
            The [LatestReport][msl.equipment.schema.LatestReport] for the specified `quantity` and `name`.
                If the equipment has only one _measurand_ and only one _component_ then you do not need
                to specify a value for the `quantity` and `name`. Returns `None` if there are no calibration
                reports that match the `quantity` and `name` criteria or if the equipment does not have
                calibration reports entered in the register.
        """
        return _latest(items=list(self.latest_reports(date=date)), quantity=quantity, name=name)


class Register:
    """Represents the [register][element_register] element in an equipment register."""

    NAMESPACE: str = "https://measurement.govt.nz/equipment-register"
    """Default XML namespace."""

    def __init__(self, *sources: XMLSource | Element[str]) -> None:
        """Represents the [register][element_register] element in an equipment register.

        Specifying multiple sources allows for storing an equipment register across multiple
        files for the same team. Not specifying a source creates a new (empty) register.

        Args:
            sources: The [path-like][path-like object],
                [file-like][file-like object] or
                [Element][xml.etree.ElementTree.Element]
                objects that are equipment registers.
        """
        team = ""
        self._elements: list[Element[str]] = []
        for source in sources:
            root = source if isinstance(source, Element) else ElementTree().parse(source)
            t = root.attrib.get("team", "")
            if not team:
                team = t

            if team != t:
                msg = f"Cannot merge equipment registers from different teams, {team!r} != {t!r}"
                raise ValueError(msg)

            self._elements.extend(root)

        self._team: str = team
        self._equipment: list[Equipment | None] = [None] * len(self._elements)

        # a mapping between the alias/id and the index number in the register
        self._index_map: dict[str, int] = {str(e[0].text): i for i, e in enumerate(self._elements)}  # e[0] is the ID
        self._index_map.update({e.attrib["alias"]: i for i, e in enumerate(self._elements) if e.attrib.get("alias")})

    def __getitem__(self, item: str | int) -> Equipment:
        """Returns an Equipment item from the register."""
        if isinstance(item, str):
            index = self._index_map.get(item)
            if index is None:
                msg = f"No equipment exists with the alias or id {item!r}"
                raise ValueError(msg)
        else:
            index = item

        e = self._equipment[index]  # this will raise IndexError if out of bounds
        if e is None:
            e = Equipment.from_xml(self._elements[index])
            self._equipment[index] = e
        return e

    def __iter__(self) -> Iterator[Equipment]:
        """Yields the Equipment elements in the register."""
        for i, e in enumerate(self._equipment):
            if e is None:
                e = Equipment.from_xml(self._elements[i])  # noqa: PLW2901
                self._equipment[i] = e
            yield e

    def __len__(self) -> int:
        """Returns the number of Equipment elements in the register."""
        return len(self._equipment)

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return f"<{self.__class__.__name__} team={self.team!r} ({len(self)} equipment)>"

    def add(self, equipment: Equipment) -> None:
        """Add equipment to the register.

        Args:
            equipment: The equipment to add.
        """
        if equipment.id:
            self._index_map[equipment.id] = len(self._equipment)
        if equipment.alias:
            self._index_map[equipment.alias] = len(self._equipment)
        self._equipment.append(equipment)

    def find(self, pattern: str | re.Pattern[str], *, flags: int = 0) -> Iterator[Equipment]:  # noqa: C901
        """Find equipment in the register.

        The following attributes are used in the search:

        * keywords: [Equipment][msl.equipment.schema.Equipment]
        * description: [Equipment][msl.equipment.schema.Equipment]
        * manufacturer: [Equipment][msl.equipment.schema.Equipment]
        * model: [Equipment][msl.equipment.schema.Equipment]
        * serial: [Equipment][msl.equipment.schema.Equipment]
        * id: [Equipment][msl.equipment.schema.Equipment], [Report][msl.equipment.schema.Report], [DigitalReport][msl.equipment.schema.DigitalReport]
        * location: [Equipment][msl.equipment.schema.Equipment]
        * quantity: [Measurand][msl.equipment.schema.Measurand]
        * name: [Component][msl.equipment.schema.Component]
        * entered_by: [Equipment][msl.equipment.schema.Equipment], [PerformanceCheck][msl.equipment.schema.PerformanceCheck], [Report][msl.equipment.schema.Report]
        * checked_by: [Equipment][msl.equipment.schema.Equipment], [PerformanceCheck][msl.equipment.schema.PerformanceCheck], [Report][msl.equipment.schema.Report]
        * performed_by: [Alteration][msl.equipment.schema.Alteration], [CompletedTask][msl.equipment.schema.CompletedTask], [PlannedTask][msl.equipment.schema.PlannedTask]
        * comment: [CVDEquation][msl.equipment.schema.CVDEquation], [Equation][msl.equipment.schema.Equation], [File][msl.equipment.schema.File], [Table][msl.equipment.schema.Table], [Deserialised][msl.equipment.schema.Deserialised], [DigitalReport][msl.equipment.schema.DigitalReport]
        * format: [DigitalReport][msl.equipment.schema.DigitalReport]
        * details: [Alteration][msl.equipment.schema.Alteration], [Adjustment][msl.equipment.schema.Adjustment]
        * task: [CompletedTask][msl.equipment.schema.CompletedTask], [PlannedTask][msl.equipment.schema.PlannedTask]
        * asset_number: [CapitalExpenditure][msl.equipment.schema.CapitalExpenditure]
        * service_agent: [QualityManual][msl.equipment.schema.QualityManual]
        * technical_procedures: [QualityManual][msl.equipment.schema.QualityManual]

        Args:
            pattern: A [regular-expression pattern](https://regexr.com/) to use to find equipment.
            flags: The flags to use to compile the `pattern`. See [re.compile][] for more details.

        Yields:
            Equipment that match the `pattern`.
        """  # noqa: E501

        def comment_search(item: Report | PerformanceCheck) -> bool:
            for cvd_equation in item.cvd_equations:
                if regex.search(cvd_equation.comment) is not None:
                    return True
            for equation in item.equations:
                if regex.search(equation.comment) is not None:
                    return True
            for file in item.files:
                if regex.search(file.comment) is not None:
                    return True
            for table in item.tables:
                if regex.search(table.comment) is not None:
                    return True
            return any(regex.search(deserialised.comment) is not None for deserialised in item.deserialised)

        def task_search(m: Maintenance) -> bool:
            for c in m.completed:
                if regex.search(c.task) is not None:
                    return True
                if regex.search(c.performed_by) is not None:
                    return True
            for p in m.planned:
                if regex.search(p.task) is not None:
                    return True
                if regex.search(p.performed_by) is not None:
                    return True
            return False

        def alteration_search(alterations: tuple[Alteration, ...]) -> bool:
            for a in alterations:
                if regex.search(a.details) is not None:
                    return True
                if regex.search(a.performed_by) is not None:
                    return True
            return False

        def calibrations_search(e: Equipment) -> bool:  # noqa: C901, PLR0911, PLR0912
            for m in e.calibrations:
                if regex.search(m.quantity) is not None:
                    return True
                for c in m.components:
                    if regex.search(c.name) is not None:
                        return True
                    for r in c.reports:
                        if regex.search(r.entered_by) is not None:
                            return True
                        if regex.search(r.checked_by) is not None:
                            return True
                        if comment_search(r):
                            return True
                        if regex.search(r.id) is not None:
                            return True
                    for pc in c.performance_checks:
                        if regex.search(pc.entered_by) is not None:
                            return True
                        if regex.search(pc.checked_by) is not None:
                            return True
                        if comment_search(pc):
                            return True
                    for a in c.adjustments:
                        if regex.search(a.details) is not None:
                            return True
                    for dr in c.digital_reports:
                        if regex.search(dr.format.value) is not None:
                            return True
                        if regex.search(dr.id) is not None:
                            return True
                        if regex.search(dr.comment) is not None:
                            return True
            return False

        def asset_number_search(f: Financial) -> bool:
            if f.capital_expenditure is None:
                return False
            return regex.search(f.capital_expenditure.asset_number) is not None

        regex = re.compile(pattern, flags=flags)
        for equipment in self:
            if (
                regex.search(" ".join(equipment.keywords)) is not None
                or regex.search(equipment.description) is not None
                or regex.search(equipment.manufacturer) is not None
                or regex.search(equipment.model) is not None
                or regex.search(equipment.serial) is not None
                or regex.search(equipment.id) is not None
                or regex.search(equipment.location) is not None
                or regex.search(equipment.entered_by) is not None
                or regex.search(equipment.checked_by) is not None
                or calibrations_search(equipment)
                or alteration_search(equipment.alterations)
                or task_search(equipment.maintenance)
                or asset_number_search(equipment.quality_manual.financial)
                or regex.search(equipment.quality_manual.service_agent) is not None
                or regex.search(" ".join(equipment.quality_manual.technical_procedures)) is not None
            ):
                yield equipment

    def get(self, item: int | str) -> Equipment | None:
        """Get an [Equipment][msl.equipment.schema.Equipment] item from the register.

        This method will ignore all errors if the register does not contain the requested
        [Equipment][msl.equipment.schema.Equipment] item.

        !!! tip
            You can also treat a _register_ instance as a sequence of [Equipment][msl.equipment.schema.Equipment] items.

        <!--
        >>> from msl.equipment import Register
        >>> register = Register("tests/resources/mass/register.xml")

        -->

        Using the _indexable_ notation on a _register_ instance to access an [Equipment][msl.equipment.schema.Equipment]
        item by using the alias of the equipment or the index within the register could raise an exception

        ```pycon
        >>> register["unknown-alias"]
        Traceback (most recent call last):
        ...
        ValueError: No equipment exists with an alias or id of 'unknown-alias'

        >>> register[243]
        Traceback (most recent call last):
        ...
        IndexError: list index out of range

        ```

        whereas these errors can be silenced by using the [get][msl.equipment.schema.Register.get] method

        ```pycon
        >>> assert register.get("unknown") is None
        >>> assert register.get(243) is None

        ```

        Args:
            item: The index number, equipment id value or the equipment alias value in the register.

        Returns:
            The [Equipment][msl.equipment.schema.Equipment] item if `item` is valid, otherwise `None`.
        """
        try:
            return self[item]
        except (ValueError, IndexError):
            return None

    @property
    def team(self) -> str:
        """[str][] &mdash; The name of the team that is responsible for the equipment register."""
        return self._team

    @team.setter
    def team(self, value: str) -> None:
        self._team = value

    def tree(self, namespace: str | None = "DEFAULT", indent: int = 4) -> ElementTree[Element[str]]:
        """Convert the [Register][msl.equipment.schema.Register] class into an XML element tree.

        Args:
            namespace: The namespace to associate with the root element. If the value is
                `DEFAULT`, uses the value of [NAMESPACE][msl.equipment.schema.Register.NAMESPACE]
                as the namespace. If `None`, or an empty string, no namespace is associated
                with the root element.
            indent: The number of spaces to indent sub elements. The value must be &ge; 0.
                This parameter is ignored if the version of Python is &lt; 3.9.

        Returns:
            The [Register][msl.equipment.schema.Register] as an
                [ElementTree][xml.etree.ElementTree.ElementTree].
        """
        if indent < 0:
            msg = f"Indentation must be >= 0, got {indent}"
            raise ValueError(msg)

        attrib = {"team": self.team}
        if namespace:
            if namespace == "DEFAULT":
                namespace = self.NAMESPACE
            attrib["xmlns"] = namespace

        # The <table><data> element is 7 levels deep from <register>
        _Indent.table_data = (7 * indent) + len("<data>")

        e = Element("register", attrib=attrib)
        e.extend(equipment.to_xml() for equipment in self)
        tree: ElementTree[Element[str]] = ElementTree(element=e)

        if indent > 0 and sys.version_info >= (3, 9):
            from xml.etree.ElementTree import indent as pretty  # noqa: PLC0415

            pretty(tree, space=" " * indent)

        return tree


class Connection:
    """Information about how to interface with equipment."""

    __slots__: tuple[str, ...] = (
        "address",
        "backend",
        "eid",
        "manufacturer",
        "model",
        "properties",
        "serial",
    )

    def __init__(  # noqa: PLR0913
        self,
        address: str,
        *,
        backend: Literal["MSL", "PyVISA", "NIDAQ"] | Backend = Backend.MSL,
        eid: str = "",
        manufacturer: str = "",
        model: str = "",
        serial: str = "",
        **properties: _Any,  # noqa: ANN401
    ) -> None:
        """Information about how to interface with equipment.

        Args:
            address: The VISA-style address of the connection (see [here][address-syntax] for examples).
            backend: The [backend][msl.equipment.enumerations.Backend] to use to communicate with the equipment.
            eid: The [equipment id][msl.equipment.schema.Equipment.id] to associate with the [Connection][] instance.
            manufacturer: The name of the manufacturer of the equipment.
            model: The model number of the equipment.
            serial: The serial number (or unique identifier) of the equipment.
            properties: Additional key-value pairs to use when communicating with the equipment.
                For example, the _baud_rate_ and _parity_ values for an _RS-232_ connection.
        """
        self.address: str = address
        """The VISA-style address of the connection (see [here][address-syntax] for examples)."""

        self.backend: Backend = Backend(backend)
        """The [backend][msl.equipment.enumerations.Backend] that is used to communicate with the equipment."""

        self.eid: str = eid
        """The [equipment id][msl.equipment.schema.Equipment.id] associated with the [Connection][] instance."""

        self.manufacturer: str = manufacturer
        """The name of the manufacturer of the equipment."""

        self.model: str = model
        """The model number of the equipment."""

        # check for a properties key being explicitly defined and the value is a dict
        properties = (  # pyright: ignore[reportUnknownVariableType]
            properties["properties"]
            if ("properties" in properties and isinstance(properties["properties"], dict))
            else properties
        )

        self.properties: dict[str, _Any] = properties
        """Additional key-value pairs to use when communicating with the equipment.

        For example, the _baud_rate_ and _parity_ values for an _RS-232_ connection.
        """

        self.serial: str = serial
        """The serial number (or unique identifier) of the equipment."""

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return f"{self.__class__.__name__}(eid={self.eid!r} address={self.address!r})"

    def connect(self) -> _Any:  # noqa: ANN401
        """Connect to the equipment."""
        equipment = Equipment(
            id=self.eid,
            manufacturer=self.manufacturer,
            model=self.model,
            serial=self.serial,
            connection=self,
        )
        return equipment.connect()


class Connections:
    """Singleton class containing an eid:Connection mapping from <connections> defined in a configuration file."""

    def __init__(self) -> None:
        """Singleton class containing an eid:Connection mapping from <connections> defined in a configuration file."""
        self._connections: dict[str, Connection | Element[str]] = {}

    def __contains__(self, eid: str) -> bool:
        """Check whether an eid is in the mapping."""
        return eid in self._connections

    def __getitem__(self, eid: str) -> Connection:
        """Returns a Connection instance."""
        item = self._connections.get(eid)
        if isinstance(item, Connection):
            return item

        if item is None:
            msg = (
                f"A <connection> element with eid={eid!r} cannot be found in the "
                f"connections that are specified in the configuration file"
            )
            raise KeyError(msg)

        connection = self._from_xml(item)
        self._connections[eid] = connection
        return connection

    def __len__(self) -> int:
        """Returns the size of the mapping."""
        return len(self._connections)

    def add(self, *sources: PathLike | Element[str]) -> None:
        """Add the sources from the <connections> element in a configuration file."""
        for source in sources:
            root = source if isinstance(source, Element) else ElementTree().parse(source)

            # schema requires that the eid is the first child element
            self._connections.update({e[0].text: e for e in root if e[0].text})

    def clear(self) -> None:
        """Remove all connections from the mapping."""
        self._connections.clear()

    def _from_xml(self, element: Element[str]) -> Connection:
        """Convert a <connection> from a connections XML file."""
        # schema requires that eid and address are the first two elements
        eid = element[0].text or ""
        address = element[1].text or ""
        # the other elements are optional (minOccurs="0")
        backend, manufacturer, model, serial = Backend.MSL, "", "", ""
        properties: dict[str, bool | float | str | None] = {}
        for e in element[2:]:
            if e.tag == "backend":
                backend = Backend[e.text or "MSL"]
            elif e.tag == "manufacturer":
                manufacturer = e.text or ""
            elif e.tag == "model":
                model = e.text or ""
            elif e.tag == "serial":
                serial = e.text or ""
            else:
                for child in e:
                    if child.tag.endswith("termination"):
                        if child.text:
                            properties[child.tag] = child.text.replace("\\r", "\r").replace("\\n", "\n")
                    else:
                        properties[child.tag] = None if child.text is None else to_primitive(child.text)

        return Connection(
            eid=eid,
            address=address,
            backend=backend,
            manufacturer=manufacturer,
            model=model,
            serial=serial,
            **properties,
        )


class Interface:
    """Base class for all interfaces."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for all interfaces.

        Args:
            equipment: An [Equipment][] instance.
        """
        assert equipment.connection is not None  # noqa: S101
        self._equipment: Equipment = equipment

        # __str__ and __repr__ can be called often for logging message, cache values
        self.__str: str = f"{self.__class__.__name__}<{equipment.manufacturer}|{equipment.model}|{equipment.serial}>"
        self.__repr: str = (
            f"{self.__class__.__name__}"
            f"<{equipment.manufacturer}|{equipment.model}|{equipment.serial} at {equipment.connection.address}>"
        )

        logger.debug("Connecting to %r", self)

    def __del__(self) -> None:
        """Calls disconnect()."""
        self.disconnect()

    def __enter__(self: Self) -> Self:  # noqa: PYI019
        """Enter a context manager."""
        return self

    def __exit__(self, *ignore: object) -> None:
        """Exit the context manager."""
        self.disconnect()

    def __init_subclass__(  # noqa: PLR0913
        cls,
        *,
        manufacturer: str = "",
        model: str = "",
        flags: int = 0,
        backend: Backend | None = None,
        regex: re.Pattern[str] | None = None,
        append: bool = True,
    ) -> None:
        """This method is called whenever the Interface is sub-classed.

        Args:
            manufacturer: The name of the manufacturer (supports a regex pattern string).
            model: The model number of the equipment (supports a regex pattern string).
            flags: The flags to use for the regex pattern string.
            backend: The backend to use for communication.
            regex: The compiled regex to use when matching the Connection address.
            append: Whether to append the subclass to the appropriate `backends`, `interfaces`
                or `resources` list.
        """
        if not append:
            return

        if backend is not None:
            backends.append(_Backend(cls, backend))
            logger.debug("added backend: %s", cls)
        elif regex is not None:
            interfaces.append(_Interface(cls, regex))
            logger.debug("added interface: %s", cls)
        else:
            resources.append(_Resource(cls, manufacturer, model, flags))
            logger.debug("added resource: %s", cls)

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the representation."""
        return self.__repr

    def __str__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return self.__str

    @property
    def equipment(self) -> Equipment:
        """The [Equipment][] associated with the interface."""
        return self._equipment

    def disconnect(self) -> None:
        """Disconnect from the equipment.

        This method can be overridden in the subclass if the subclass must implement
        tasks that need to be performed in order to safely disconnect from the equipment.

        For example,

        * to clean up system resources from memory (e.g., if using a manufacturer's SDK)
        * to configure the equipment to be in a state that is safe for people
          working in the lab when the equipment is not in use

        !!! tip
            This method gets called automatically when the [Interface][msl.equipment.schema.Interface]
            instance gets garbage collected, which happens when the reference count is 0.
        """
        logger.debug("Disconnected from %r", self)


class _Backend:
    def __init__(self, cls: type[Interface], backend: Backend) -> None:
        """Keep track of the backend classes."""
        self.cls: type[Interface] = cls
        self.backend: Backend = backend

    def handles(self, connection: Connection) -> bool:
        """Checks if the backend handles communication with the equipment."""
        return connection.backend == self.backend


class _Interface:
    def __init__(self, cls: type[Interface], regex: re.Pattern[str]) -> None:
        """Keep track of the base interface classes."""
        self.cls: type[Interface] = cls
        self.regex: re.Pattern[str] = regex

    def handles(self, address: str) -> bool:
        """Checks if the interface class handles communication with the equipment."""
        return self.regex.match(address) is not None


class _Resource:
    def __init__(self, cls: type[Interface], manufacturer: str, model: str, flags: int) -> None:
        """Keep track of resource classes."""
        self.cls: type[Interface] = cls
        self.manufacturer: re.Pattern[str] | None = re.compile(manufacturer, flags=flags) if manufacturer else None
        self.model: re.Pattern[str] | None = re.compile(model, flags=flags) if model else None

    def handles(self, equipment: Equipment) -> bool:
        """Checks if the resource handles communication with the equipment."""
        # both manufacturer and model must match (if specified) to be a match
        if not (self.manufacturer or self.model):
            return False
        if self.manufacturer and not self.manufacturer.search(equipment.manufacturer):
            return False
        return not (self.model and not self.model.search(equipment.model))


resources: list[_Resource] = []
backends: list[_Backend] = []
interfaces: list[_Interface] = []
connections = Connections()
