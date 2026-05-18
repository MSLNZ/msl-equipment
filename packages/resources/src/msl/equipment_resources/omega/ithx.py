"""[OMEGA](https://www.omega.co.uk/){:target="_blank"} iTHX Series Temperature and Humidity Chart Recorder.

This class is compatible with the following model numbers:

* iTHX-W3
* iTHX-D3
* iTHX-SD
* iTHX-M
* iTHX-W
* iTHX-2
"""

# cSpell: ignore DMSW ECONNRESET SRYRST
from __future__ import annotations

import re
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

    def reset(self, *, password: str | None = None, port: int = 2002, wait: bool = True) -> None:
        """Power reset (reboot) the iServer.

        Some iServers accept the reset command to be sent via the TCP/UDP protocol and
        some require the reset command to be sent via the Telnet protocol.

        Args:
            password: The administrator's password of the iServer. If not specified then uses the
                default manufacturer's password. Only used if the iServer needs to be reset via
                the Telnet protocol.
            port: The Telnet port number.
            wait: Whether to wait for the connection to the iServer to be re-established before
                returning to the calling program. Rebooting an iServer takes about 10 to 15 seconds.
        """

        def use_telnet() -> None:
            import socket  # noqa: PLC0415

            with socket.socket() as sock:
                sock.settimeout(self.timeout)
                sock.connect((self._info.host, port))

                # wait until a password request is received
                reply = b""
                while not reply.endswith((b":", b"?")):
                    reply = sock.recv(256)

                pw = password or "00000000"
                _ = sock.send(pw.encode() + b"\r")
                reply = sock.recv(256)
                if b"failure" in reply or b"Invalid" in reply:
                    reply = "Invalid iTHX telnet password"
                    raise MSLConnectionError(self, reply)

                _ = sock.send(b"reset\r")
                reply = sock.recv(256)
                if reply.startswith(b"WRONG_CMD"):
                    reply = "iTHX device does support the RESET command"
                    raise MSLConnectionError(self, reply)

        # The manual indicates that iTHX-W3, iTHX-D3, iTHX-SD and iTHX-M accept the *SRYRST command
        reply = self.query("*SRYRST").strip()
        if reply == "Reset":
            # this was the reply that was received with an iTHX-W3
            # which accepts the reset command via TCP/UDP
            pass
        elif reply == "Serial Time Out":
            # this was the reply that was received with an iTHX-W
            # which does not recognize the *SRYRST command
            use_telnet()
        else:
            msg = f"Received an unexpected reply, {reply!r}, for the *SRYRST command"
            raise MSLConnectionError(self, msg)

        if wait:
            self.reconnect(max_attempts=-1)

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
