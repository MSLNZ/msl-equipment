"""Use [PyVISA] as the backend to communicate with the equipment.

[PyVISA]: https://pyvisa.readthedocs.io/en/stable/
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

try:
    import pyvisa
except ImportError:
    pyvisa = None  # type: ignore[assignment]

from msl.equipment.constants import Parity, StopBits
from msl.equipment.utils import logger, to_enum

from . import Interface

if TYPE_CHECKING:
    from typing import Any, ClassVar

    from pyvisa.highlevel import ResourceManager, VisaLibraryBase
    from pyvisa.resources.resource import Resource

    from msl.equipment.connections import Connection
    from msl.equipment.schema import Equipment


class PyVISA(Interface):
    """Use PyVISA as the backend to communicate with the equipment."""

    _resource_classes: ClassVar[dict[str, type[Resource]]] = {}

    def __init__(self, equipment: Equipment) -> None:  # noqa: C901
        """Use [PyVISA] as the backend to communicate with the equipment.

        The [Connection.backend][msl.equipment.record_types.Connection.backend]
        value must be equal to `PyVISA` to use this class for the communication backend.

        The returned object from calling the [connect][msl.equipment.schema.Equipment.connect]
        method is equivalent to calling [open_resource][pyvisa.highlevel.ResourceManager.open_resource].

        For example,

        ```python
        from msl.equipment import Backend, Connection, Equipment

        equipment = Equipment(connection=Connection(address="GPIB::12", backend=Backend.PyVISA))
        inst = equipment.connect()
        ```

        is equivalent to

        ```python
        import pyvisa

        rm = pyvisa.ResourceManager()
        inst = rm.open_resource("GPIB::12")
        ```

        Args:
            equipment: The [Equipment][] instance.

        [PyVISA]: https://pyvisa.readthedocs.io/en/stable/
        """
        self._resource: Resource | None = None
        super().__init__(equipment)

        rm: ResourceManager = PyVISA.resource_manager()

        assert equipment.connection is not None  # noqa: S101
        assert pyvisa is not None  # noqa: S101

        props = equipment.connection.properties

        # In PyVISA, Parity and StopBits must be integers
        if "parity" in props:
            parity = props["parity"]
            if isinstance(parity, str):
                parity = to_enum(parity, Parity, to_upper=True)
            if isinstance(parity, Parity):
                parity = parity.name.lower()
                props["parity"] = to_enum(parity, pyvisa.constants.Parity)  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType, reportAttributeAccessIssue]

        if "stop_bits" in props:
            stop_bits = props["stop_bits"]
            if isinstance(stop_bits, StopBits):
                stop_bits = int(stop_bits.value * 10)
            elif isinstance(stop_bits, (int, float)) and stop_bits < 10:  # noqa: PLR2004
                stop_bits = int(stop_bits * 10)
            props["stop_bits"] = to_enum(stop_bits, pyvisa.constants.StopBits)  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType, reportAttributeAccessIssue]

        # PyVISA requires the read/write termination data type to be str not bytes
        def ensure_term(term: bytes) -> str | bytes:
            try:
                return term.decode()
            except AttributeError:
                return term

        # "termination" is a shortcut used by the MSL backend to set both
        # write_termination and read_termination to the same value
        rw_term = props.pop("termination", None)
        r_term = props.pop("read_termination", rw_term)
        w_term = props.pop("write_termination", rw_term)
        if r_term is not None:
            props["read_termination"] = ensure_term(r_term)
        if w_term is not None:
            props["write_termination"] = ensure_term(w_term)

        # the "timeout" value is in seconds for MSL backend
        # PyVISA uses a timeout in milliseconds
        timeout: float | None = props.get("timeout")
        if timeout and timeout < 100:  # noqa: PLR2004
            # if timeout < 100 then it's value is probably in seconds
            props["timeout"] = timeout * 1000

        self._resource = rm.open_resource(equipment.connection.address, **props)

    def __getattr__(self, item: str) -> Any:  # noqa: ANN401
        """Get a pyvisa attribute."""
        attr = getattr(self._resource, item)
        if callable(attr):

            def wrapper(*args: Any, **kwargs: Any) -> object:  # noqa: ANN401
                return attr(*args, **kwargs)

            return wrapper
        return attr

    def __setattr__(self, item: str, value: Any) -> None:  # pyright: ignore[reportImplicitOverride]  # noqa: ANN401
        """Set a pyvisa attribute."""
        if item[0] == "_":
            # handles all private attributes, like:
            #   self._resource
            #   self._equipment
            #   self.__repr
            #   self.__str
            self.__dict__[item] = value
        else:
            setattr(self._resource, item, value)

    def __delattr__(self, item: str) -> None:  # pyright: ignore[reportImplicitOverride]
        """Delete a pyvisa attribute."""
        delattr(self._resource, item)

    @property
    def resource(self) -> Resource | None:
        """:class:`~pyvisa.resources.Resource`: The PyVISA_ resource that is used for the connection.

        This is the :class:`~pyvisa.resources.Resource` that would have
        been returned if you did the following in a script::

            import pyvisa
            rm = pyvisa.ResourceManager()
            resource = rm.open_resource('ASRL3::INSTR')

        """
        return self._resource

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Calls [pyvisa.resources.Resource.close][]."""
        if self._resource is not None:
            self._resource.close()
            logger.debug("Disconnected from %s", self)
            self._resource = None

    @staticmethod
    def resource_manager(visa_library: str | VisaLibraryBase | None = None) -> ResourceManager:  # noqa: C901, PLR0912
        """Returns the PyVISA Resource Manager.

        Args:
            visa_library: The library to use for PyVISA_. For example:

                * `@ivi` &mdash; use [IVI][intro-configuring]
                * `@ni` &mdash; use [NI-VISA](https://www.ni.com/visa/) (only supported in PyVISA <1.11)
                * `@py` &mdash; use [PyVISA-py](https://pyvisa.readthedocs.io/projects/pyvisa-py/en/stable/)
                * `@sim` &mdash; use [PyVISA-sim](https://pyvisa.readthedocs.io/projects/pyvisa-sim/en/stable/)

                If `None`, the `PYVISA_LIBRARY` environment variable is used. This environment
                variable can be set in a [configuration file][configuration-files].

        Returns:
            The PyVISA Resource Manager.
        """
        if pyvisa is None:
            msg = "pyvisa is not installed, run: pip install pyvisa"  # type: ignore[unreachable]
            raise ImportError(msg)

        if not PyVISA._resource_classes:
            for item in dir(pyvisa.resources):
                if item.endswith("Instrument"):
                    key = item[: -len("Instrument")]
                    PyVISA._resource_classes[key] = getattr(pyvisa.resources, item)
                elif item == "GPIBInterface":
                    PyVISA._resource_classes["GPIB_INTFC"] = pyvisa.resources.GPIBInterface
                elif item == "VXIBackplane":
                    PyVISA._resource_classes["VXI_BACKPLANE"] = pyvisa.resources.VXIBackplane
                elif item == "VXIMemory":
                    PyVISA._resource_classes["VXI_MEMACC"] = pyvisa.resources.VXIMemory
                elif item == "TCPIPSocket":
                    PyVISA._resource_classes["TCPIP_SOCKET"] = pyvisa.resources.TCPIPSocket
                elif item == "USBRaw":
                    PyVISA._resource_classes["USB_RAW"] = pyvisa.resources.USBRaw
                elif item == "PXIMemory":
                    PyVISA._resource_classes["PXI_MEMACC"] = getattr(pyvisa.resources, item)
            for item in ("COM", "ASRL", "LPT1", "ASRLCOM"):
                PyVISA._resource_classes[item] = pyvisa.resources.SerialInstrument

        if visa_library is None:
            visa_library = os.getenv("PYVISA_LIBRARY", "@ivi")

        try:
            return pyvisa.ResourceManager(visa_library)
        except ValueError as err:
            # as of PyVISA 1.11 the @ni backend was renamed to @ivi
            msg = str(err)
            if msg.endswith("ni"):
                return pyvisa.ResourceManager("@ivi")
            if msg.endswith("ivi"):
                return pyvisa.ResourceManager("@ni")
            raise

    @staticmethod
    def resource_class(item: Equipment | Connection) -> type[Resource]:  # noqa: C901, PLR0911
        """Get the PyVISA [Resource class][api_resources].

        Args:
            item: An equipment or connection item.

        Returns:
            The PyVISA Resource class that can open the `item`.
        """
        address = str(item.address) if hasattr(item, "address") else str(item.connection.address)  # type: ignore[union-attr]  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportOptionalMemberAccess, reportUnknownArgumentType]
        if not address:
            msg = "The Connection.address has not been set"
            raise ValueError(msg)

        rm = PyVISA.resource_manager()
        try:
            info = rm.resource_info(address, extended=True)
            return rm._resource_classes[(info.interface_type, info.resource_class)]  # type: ignore[index]  # noqa: SLF001  # pyright: ignore[reportArgumentType, reportPrivateUsage]
        except:  # noqa: E722
            # try to figure out the resource class...
            a = str(address.upper())

            if a.startswith("GPIB") and a.endswith("INTFC"):
                return PyVISA._resource_classes["GPIB_INTFC"]

            if a.startswith("VXI") and a.endswith("BACKPLANE"):
                return PyVISA._resource_classes["VXI_BACKPLANE"]

            if a.startswith("VXI") and a.endswith("MEMACC"):
                return PyVISA._resource_classes["VXI_MEMACC"]

            if a.startswith("TCPIP") and a.endswith("SOCKET"):
                return PyVISA._resource_classes["TCPIP_SOCKET"]

            if a.startswith("USB") and a.endswith("RAW"):
                return PyVISA._resource_classes["USB_RAW"]

            if a.startswith("PXI") and a.endswith("MEMACC"):
                return PyVISA._resource_classes["PXI_MEMACC"]

            for key, value in PyVISA._resource_classes.items():
                if a.startswith(key):
                    return value

            msg = f"Cannot find a PyVISA resource class for {address}"
            raise ValueError(msg) from None
