"""Use [PyVISA] as the backend to communicate with the equipment.

[PyVISA]: https://pyvisa.readthedocs.io/en/stable/
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    import pyvisa
except ImportError:
    pyvisa = None  # type: ignore[assignment]

from msl.equipment.enumerations import Backend, Parity, StopBits
from msl.equipment.schema import Interface
from msl.equipment.utils import logger, to_enum

if TYPE_CHECKING:
    from typing import Any, ClassVar

    from pyvisa.highlevel import ResourceManager, VisaLibraryBase
    from pyvisa.resources.resource import Resource

    from msl.equipment.schema import Connection, Equipment


class PyVISA(Interface, backend=Backend.PyVISA):
    """Use [PyVISA]{:target="_blank"} as the backend to communicate with the equipment.

    [PyVISA]: https://pyvisa.readthedocs.io/en/stable/
    """

    _resource_classes: ClassVar[dict[str, type[Resource]]] = {}

    def __init__(self, equipment: Equipment) -> None:  # noqa: C901
        """Use [PyVISA] as the backend to communicate with the equipment.

        The [backend][msl.equipment.connections.Connection.backend]
        value must be equal to `PyVISA` to use this class for the communication backend.

        The returned object from calling the [connect][msl.equipment.schema.Equipment.connect]
        method is equivalent to calling
        [open_resource][pyvisa.highlevel.ResourceManager.open_resource]{:target="_blank"}, e.g.,

        ```python
        from msl.equipment import Backend, Connection, Equipment

        equipment = Equipment(connection=Connection(address="GPIB::12", backend=Backend.PyVISA))
        inst = equipment.connect()
        print(inst.query("*IDN?"))
        ```

        is equivalent to

        ```python
        import pyvisa

        rm = pyvisa.ResourceManager()
        inst = rm.open_resource("GPIB::12")
        print(inst.query("*IDN?"))
        ```

        You can also combine the packages, use `msl-equipment` for managing information
        about the equipment and directly use `pyvisa` for the connection

        ```python
        import pyvisa
        from msl.equipment import Config

        # config.xml contains <equipment eid="MSLE.0.063" name="dmm"/>
        # and specifies where the equipment registers are and the connections file.
        cfg = Config("config.xml")

        address = cfg.equipment["dmm"].connection.address

        rm = pyvisa.ResourceManager()
        inst = rm.open_resource(address)
        print(inst.query("*IDN?"))
        ```

        [PyVISA]: https://pyvisa.readthedocs.io/en/stable/

        Args:
            equipment: An [Equipment][] instance.
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
        """The PyVISA resource that is used for the connection.

        This is the [Resource][pyvisa.resources.Resource]{:target="_blank"} instance
        that would have been returned if you did the following

        ```python
        import pyvisa
        rm = pyvisa.ResourceManager()
        resource = rm.open_resource("ASRL3::INSTR")
        ```
        """
        return self._resource

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Calls [pyvisa.resources.Resource.close][]{:target="_blank"}."""
        if self._resource is not None:
            self._resource.close()
            logger.debug("Disconnected from %s", self)
            self._resource = None

    @staticmethod
    def resource_manager(visa_library: str | VisaLibraryBase = "") -> ResourceManager:  # noqa: C901
        """Returns the PyVISA Resource Manager.

        Args:
            visa_library: The library to use for PyVISA, for example,

                * `@ivi` &mdash; PyVISA &ge; 1.11
                * `@ni` &mdash; PyVISA &lt; 1.11
                * `@py` &mdash; use [PyVISA-py](https://pyvisa.readthedocs.io/projects/pyvisa-py/en/stable/){:target="_blank"}
                * `@sim` &mdash; use [PyVISA-sim](https://pyvisa.readthedocs.io/projects/pyvisa-sim/en/stable/){:target="_blank"}

                If unspecified, the `PYVISA_LIBRARY` environment variable is used (if it exists).
                This environment variable can be defined in a [configuration file][config-xml-example].
                The default library is `@ivi` if not specified elsewhere.

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

        return pyvisa.ResourceManager(visa_library)

    @staticmethod
    def resource_class(connection: Connection) -> type[Resource]:  # noqa: C901, PLR0911
        """Get the PyVISA [Resource][pyvisa.resources.Resource]{:target="_blank"} class for the [Connection][].

        Args:
            connection: A [Connection][] instance.

        Returns:
            The type of PyVISA Resource class for `connection`.
        """
        address = str(connection.address)
        if not address:
            msg = "The Connection.address attribute has not been set"
            raise ValueError(msg)

        rm = PyVISA.resource_manager()
        info = rm.resource_info(address, extended=True)
        if info.resource_class is not None:
            return rm._resource_classes[(info.interface_type, info.resource_class)]  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

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
