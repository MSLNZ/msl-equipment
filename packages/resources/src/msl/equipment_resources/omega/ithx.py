"""[OMEGA](https://www.omega.co.uk/){:target="_blank"} iTHX Series Temperature and Humidity Chart Recorder.

This class is compatible with the following model numbers:

* iTHX-W3
* iTHX-D3
* iTHX-SD
* iTHX-M
* iTHX-W
* iTHX-2
"""

# cSpell: ignore DMSW SRBF ECONNRESET SRYRST
from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from msl.equipment.interfaces import MSLConnectionError, Socket

if TYPE_CHECKING:
    from typing import Literal

    from msl.equipment.schema import Equipment


class ITHX(Socket, manufacturer=r"OMEGA", model=r"iTHX-[2DMSW][3D]?", flags=re.IGNORECASE):
    """[OMEGA](https://www.omega.co.uk/){:target="_blank"} iTHX Series Temperature and Humidity Chart Recorder."""

    def __init__(self, equipment: Equipment) -> None:
        r"""OMEGA iTHX Series Temperature and Humidity Chart Recorder.

        The default termination character for read and write operations is `\r`.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"OMEGA"
        model=r"iTHX-[2DMSW][3D]?"
        flags=IGNORECASE
        ```

        Args:
            equipment: An [Equipment][] instance.
        """
        super().__init__(equipment)
        self.read_termination: bytes = b"\r"
        self.write_termination: bytes = b"\r"

    def dewpoint(self, probe: Literal[1, 2] = 1, *, celsius: bool = True) -> float:
        """Read the dewpoint.

        Args:
            probe: The probe number to read the dewpoint of (for iTHX's that contain multiple probes).
            celsius: `True` to return the dewpoint in celsius, `False` for fahrenheit.

        Returns:
            The dewpoint for the specified probe.
        """
        return self._get("DC" if celsius else "DF", probe)

    def humidity(self, probe: Literal[1, 2] = 1) -> float:
        """Read the percent humidity.

        Args:
            probe: The probe number to read the humidity of (for iTHX's that contain multiple probes).

        Returns:
            The percent humidity for the specified probe.
        """
        return self._get("H", probe)

    def reset(self, *, wait: bool = True, password: str | None = None, port: int = 2002, timeout: float = 10) -> None:
        """Power reset the iServer.

        Some iServers accept the reset command (`*SRYRST`) to be sent via the TCP/UDP protocol and
        some require the reset command to be sent via the Telnet protocol.

        !!! info
            The `telnetlib` module was removed from the standard library in Python 3.13.
            If you need Telnet support consider using a third-party library from PyPI.
            You can review the source code of this method to see how Telnet messages
            are sent to the device to perform the reset.

        Args:
            wait: Whether to wait for the connection to the iServer to be re-established before
                returning to the calling program. Rebooting an iServer takes about 10 to 15 seconds.
            password: The administrator's password of the iServer. If not specified then uses the
                default manufacturer's password. Only used if the iServer needs to be reset via
                the Telnet protocol.
            port: The port to use for the Telnet connection.
            timeout: The timeout value to use during the Telnet session.
        """

        def use_telnet() -> None:
            try:
                # telnetlib was removed in Python 3.13
                from telnetlib import Telnet  # type: ignore[import-not-found]  # pyright: ignore[reportUnknownVariableType, reportMissingImports]  # noqa: I001, PLC0415
            except ImportError:
                msg = "iTHX reset requires telnet, which is no longer part of the Python standard library"
                raise MSLConnectionError(self, msg) from None

            pw = password or "00000000"
            with Telnet(self._info.host, port, timeout=timeout) as tn:  # pyright: ignore[reportUnknownVariableType]  # noqa: S312
                tn.read_until(b"Password:", timeout=timeout)  # pyright: ignore[reportUnknownMemberType]
                tn.write(pw.encode() + b"\n")  # pyright: ignore[reportUnknownMemberType]
                tn.read_until(b"Login Successful", timeout=timeout)  # pyright: ignore[reportUnknownMemberType]
                tn.write(b"reset\n")  # pyright: ignore[reportUnknownMemberType]
                tn.read_until(b"The unit will reset in 5 seconds.", timeout=timeout)  # pyright: ignore[reportUnknownMemberType]

            if wait:
                # 5 seconds from the Telnet message
                # 10 seconds for the time it takes to reboot
                time.sleep(15)
                self.reconnect(max_attempts=-1)

        # according to the manual, these models require Telnet
        if self.equipment.model in ["iTHX-W", "iTHX-2"]:
            return use_telnet()

        # The manual indicates that iTHX-W3, iTHX-D3, iTHX-SD and iTHX-M
        # all accept the *SRYRST command
        reply = self.query("*SRYRST").strip()
        if reply == "Reset":
            # this was the reply that was received with an iTHX-W3
            # which accepts the reset command via TCP/UDP
            if wait:
                time.sleep(10)
                self.reconnect(max_attempts=-1)
        elif reply == "Serial Time Out":
            # this was the reply that was received with an iTHX-W
            # which does not recognize the *SRYRST command
            use_telnet()
        else:
            msg = f"Received an unexpected reply, {reply!r}, for the *SRYRST command"
            raise MSLConnectionError(self, msg)

        return None

    def _get(self, message: str, probe: int) -> float:
        if probe not in {1, 2}:
            # iTHX-SD supports probe=3 but we don't have one of those devices to test
            msg = f"Invalid probe number {probe}. Must be either 1 or 2"
            raise ValueError(msg)

        command = f"*SR{message}{probe}" if probe > 1 else f"*SR{message}"

        try:
            return float(self.query(command))
        except ConnectionResetError:
            # for some reason the socket closes if a certain amount of time passes and no
            # messages have been sent. For example, querying the temperature, humidity and
            # dew point every >60 seconds raised:
            #   [Errno errno.ECONNRESET] An existing connection was forcibly closed by the remote host
            self.reconnect(max_attempts=1)
            return self._get(message, probe)  # retry

    def temperature(self, probe: Literal[1, 2] = 1, *, celsius: bool = True) -> float:
        """Read the temperature.

        Args:
            probe: The probe number to read the temperature of (for iTHX's that contain multiple probes).
            celsius: `True` to return the temperature in celsius, `False` for fahrenheit.

        Returns:
            The temperature for the specified probe.
        """
        return self._get("TC" if celsius else "TF", probe)
