"""Use [PyVISA] as the backend to communicate with the equipment.

[PyVISA]: https://pyvisa.readthedocs.io/en/stable/
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    import pyvisa
except ImportError:  # pragma: no branch
    pyvisa = None  # type: ignore[assignment]

from msl.equipment.enumerations import Backend, Parity, StopBits
from msl.equipment.schema import Interface
from msl.equipment.utils import logger, to_enum

if TYPE_CHECKING:
    from typing import Any

    from pyvisa.highlevel import ResourceManager
    from pyvisa.resources.resource import Resource

    from msl.equipment.schema import Equipment


class PyVISA(Interface, backend=Backend.PyVISA):
    """Use [PyVISA](https://pyvisa.readthedocs.io/en/stable/) as the backend to communicate with the equipment."""

    rm: ResourceManager | None = None
    """PyVISA Resource Manager."""

    def __init__(self, equipment: Equipment) -> None:
        """Use [PyVISA] as the backend to communicate with the equipment.

        The [backend][msl.equipment.connections.Connection.backend]
        value must be equal to `PyVISA` to use this class for the communication backend.

        The `PYVISA_LIBRARY` environment variable is used (if it exists) to create the
        [ResourceManager][pyvisa.highlevel.ResourceManager]. This environment variable
        can be defined in a [configuration file][config-xml-example] or by defining the
        environment variable in your code before connecting to the equipment using
        [PyVISA][msl.equipment.interfaces.pyvisa.PyVISA] for the first time. The default
        value is `@ivi` if this environment variable is not defined.

        The returned object using `msl-equipment` to connect to the equipment is equivalent
        to calling [open_resource][pyvisa.highlevel.ResourceManager.open_resource], e.g.,

        ```python
        from msl.equipment import Backend, Connection

        connection = Connection("GPIB::12", backend=Backend.PyVISA)
        inst = connection.connect()
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
        about the equipment and directly use `pyvisa` for the connection. If you use this
        method, the editor you use to develop your code will have better support for
        features like code completion and type checking.

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

        if pyvisa is None:  # pragma: no branch
            msg = "pyvisa is not installed, run: pip install pyvisa"  # type: ignore[unreachable]
            raise RuntimeError(msg)

        assert equipment.connection is not None  # noqa: S101
        kwargs = _prepare_kwargs(equipment.connection.properties)

        if PyVISA.rm is None:
            PyVISA.rm = pyvisa.ResourceManager()

        self._resource = PyVISA.rm.open_resource(equipment.connection.address, **kwargs)

    def __getattr__(self, item: str) -> Any:  # noqa: ANN401
        """Get a pyvisa attribute."""
        return getattr(self._resource, item)

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

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Calls [pyvisa.resources.Resource.close][]."""
        if self._resource is not None:
            self._resource.close()
            logger.debug("Disconnected from %s", self)
            self._resource = None


def _prepare_kwargs(props: dict[str, Any]) -> dict[str, Any]:  # noqa: C901
    assert pyvisa is not None  # noqa: S101

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
        if isinstance(stop_bits, str):
            stop_bits = int(to_enum(stop_bits, StopBits, to_upper=True).value * 10)
        elif isinstance(stop_bits, StopBits):
            stop_bits = int(stop_bits.value * 10)
        elif isinstance(stop_bits, (int, float)) and stop_bits < 10:  # noqa: PLR2004
            stop_bits = int(stop_bits * 10)
        props["stop_bits"] = to_enum(stop_bits, pyvisa.constants.StopBits)  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType, reportAttributeAccessIssue]

    # PyVISA requires the read/write termination type to be str not bytes
    def ensure_term(term: str | bytes) -> str:
        return term.decode() if isinstance(term, bytes) else term

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
    if timeout and timeout < 600:  # noqa: PLR2004
        # the value is probably in seconds
        props["timeout"] = max(0, timeout * 1000)

    return props
