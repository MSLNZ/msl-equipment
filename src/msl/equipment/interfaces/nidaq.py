"""Use [NI-DAQmx] as the backend to communicate with the equipment.

[NI-DAQmx]: https://nidaqmx-python.readthedocs.io/en/stable/index.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    import nidaqmx  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
    import nidaqmx.stream_readers  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs, reportUnusedImport]
    import nidaqmx.stream_writers  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs, reportUnusedImport]
except ImportError:  # pragma: no cover
    nidaqmx = None

from msl.equipment.enumerations import Backend
from msl.equipment.schema import Interface

if TYPE_CHECKING:
    from typing import Any

    from msl.equipment.schema import Equipment


class NIDAQ(Interface, backend=Backend.NIDAQ):
    """Use [NI-DAQmx]{:target="_blank"} to establish a connection to the equipment.

    [NI-DAQmx]: https://nidaqmx-python.readthedocs.io/en/stable/index.html
    """

    def __init__(self, equipment: Equipment) -> None:
        """Use [NI-DAQmx]{:target="_blank"} to establish a connection to the equipment.

        The [backend][msl.equipment.connections.Connection.backend]
        value must be equal to `NIDAQ` to use this class for the communication backend.

        The returned object from calling the [connect][msl.equipment.schema.Equipment.connect]
        method is equivalent to importing the [NI-DAQmx]{:target="_blank"} package, e.g.,

        ```python
        from msl.equipment import Backend, Connection, Equipment

        equipment = Equipment(connection=Connection(address="Dev1", backend=Backend.NIDAQ))
        nidaqmx = equipment.connect()
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(f"{nidaqmx.address}/ai0")
            voltage = task.read()
        ```

        is equivalent to

        ```python
        import nidaqmx
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
            voltage = task.read()
        ```

        You can also combine the packages, use `msl-equipment` for managing information
        about the equipment and directly use `nidaqmx` for the connection

        ```python
        import nidaqmx
        from msl.equipment import Config

        # config.xml contains <equipment eid="MSLE.0.142" name="daq" manufacturer="NI"/>
        # and specifies where the equipment registers are and the connections file.
        cfg = Config("config.xml")

        address = cfg.equipment["daq"].connection.address
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(f"{address}/ai0")
            voltage = task.read()
        ```

        See the [examples](https://github.com/ni/nidaqmx-python/tree/master/examples){:target="_blank"}
        on the [NI-DAQmx repository](https://github.com/ni/nidaqmx-python){:target="_blank"} to learn
        how to use the `nidaqmx` package.

        [NI-DAQmx]: https://nidaqmx-python.readthedocs.io/en/stable/index.html

        Args:
            equipment: An [Equipment][] instance.
        """
        super().__init__(equipment)

        if nidaqmx is None:  # pragma: no branch
            msg = "nidaqmx is not installed, run: pip install nidaqmx"
            raise RuntimeError(msg)

    def __getattr__(self, attr: str) -> Any:  # noqa: ANN401
        """Returns any attribute from the nidaqmx package."""
        return getattr(nidaqmx, attr)

    @property
    def address(self) -> str:
        """Returns the [address][msl.equipment.connections.Connection.address] of the [Connection][]."""
        return self.equipment.connection.address  # type: ignore[union-attr]  # pyright: ignore[reportOptionalMemberAccess]
