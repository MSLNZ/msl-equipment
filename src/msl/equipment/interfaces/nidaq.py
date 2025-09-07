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

from . import Interface

if TYPE_CHECKING:
    from typing import Any

    from msl.equipment.schema import Equipment


class NIDAQ(Interface):
    """Use NI-DAQmx to establish a connection to the equipment."""

    def __init__(self, equipment: Equipment) -> None:
        """Use [NI-DAQmx] to establish a connection to the equipment.

        The [Connection.backend][msl.equipment.record_types.Connection.backend]
        value must be equal to `NIDAQ` to use this class for the communication backend.

        The returned object from calling the [connect][msl.equipment.schema.Equipment.connect]
        method is equivalent to importing the [NI-DAQmx] package.

        For example,

        ```python
        nidaqmx = equipment.connect()
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
            voltage = task.read()
        ```

        is equivalent to

        ```python
        import nidaqmx
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
            voltage = task.read()
        ```

        See the [examples](https://github.com/ni/nidaqmx-python/tree/master/examples){:target="_blank"}
        for how to use [NI-DAQmx].

        Args:
            equipment: The [Equipment][] instance.

        [NI-DAQmx]: https://nidaqmx-python.readthedocs.io/en/stable/index.html
        """
        super().__init__(equipment)

        if nidaqmx is None:  # pragma: no branch
            msg = "nidaqmx is not installed, run: pip install nidaqmx"
            raise RuntimeError(msg)

    def __getattr__(self, attr: str) -> Any:  # noqa: ANN401
        """Returns any attribute from the nidaqmx package."""
        return getattr(nidaqmx, attr)
