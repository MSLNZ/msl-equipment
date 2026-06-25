"""Communicate with a SpectraPro Series spectrograph/monochromator from Princeton Instruments."""

# cSpell: ignore SHOME FHOME
from __future__ import annotations

from enum import Enum
from time import sleep
from typing import TYPE_CHECKING, NamedTuple

from msl.equipment.interfaces.message import MSLConnectionError
from msl.equipment.interfaces.serial import Serial
from msl.equipment.utils import to_enum

if TYPE_CHECKING:
    from typing import Callable, Literal

    from msl.equipment.schema import Equipment


class SpectraProInfo(NamedTuple):
    """Information about a SpectraPro spectrograph/monochromator.

    Attributes:
        model (str): Model number.
        serial (str): Serial number.
        firmware_version (str): Firmware version number.
    """

    model: str
    serial: str
    firmware_version: str


class SpectraProGrating(NamedTuple):
    """Information about a SpectraPro grating.

    Attributes:
        position (int): Grating position number.
        description (str): Information about the groove density and blaze wavelength.
        selected (bool): Whether this grating is the grating that is currently selected.
    """

    position: int
    description: str
    selected: bool


class SpectraPro(Serial, manufacturer=r"Princeton Instruments", model=r"^(SpectraPro|HRS)"):
    """Communicate with a SpectraPro Series spectrograph/monochromator from Princeton Instruments."""

    class Slit(Enum):
        """A motorised slit.

        Attributes:
            FRONT_EXIT (str): `FRONT-EXIT-SLIT`
            FRONT_ENTRANCE (str): `FRONT-ENT-SLIT`
            SIDE_EXIT (str): `SIDE-EXIT-SLIT`
            SIDE_ENTRANCE (str): `SIDE-ENT-SLIT`
        """

        FRONT_EXIT = "FRONT-EXIT-SLIT"
        FRONT_ENTRANCE = "FRONT-ENT-SLIT"
        SIDE_EXIT = "SIDE-EXIT-SLIT"
        SIDE_ENTRANCE = "SIDE-ENT-SLIT"

    class Mirror(Enum):
        """A diverter mirror.

        Attributes:
            EXIT (str): `EXIT-MIRROR`
            ENTRANCE (str): `ENT-MIRROR`
        """

        EXIT = "EXIT-MIRROR"
        ENTRANCE = "ENT-MIRROR"

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a SpectraPro Series spectrograph/monochromator from Princeton Instruments.

        Windows FTDI driver version `2.12.16.0` (released 2016-03-09) has been shown to work,
        newer drivers may not be compatible.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Princeton Instruments"
        model=r"^(SpectraPro|HRS)"
        ```

        Args:
            equipment: An [Equipment][] instance.
        """
        super().__init__(equipment)
        self._write_termination: bytes | None = b"\r"
        self._callback: Callable[[float], None] | None = None
        self._filter_changed: bool = False
        self._grating_changed: bool = False
        self._wavelength_scanning: bool = False
        self._mirror_changed: SpectraPro.Mirror | None = None
        self._slit_changed: SpectraPro.Slit | None = None

    def _check_ok(self, reply: str, msg: str) -> None:
        """Check that a `reply` endswith `ok`."""
        if not reply.endswith("ok\r\n"):
            msg = f"Did not receive 'ok' when {msg}"
            raise MSLConnectionError(self, msg)

    def get_filter_wheel_position(self) -> int:
        """Get the position of the filter wheel.

        Returns:
            The filter-wheel position.
        """
        value, remaining = self.query(b"?FILTER").split(maxsplit=1)
        self._check_ok(remaining, "getting the filter-wheel position")
        return int(value)

    def get_grating_position(self) -> int:
        """Get the grating position.

        Returns:
            The grating position.
        """
        value, remaining = self.query(b"?GRATING").split(maxsplit=1)
        self._check_ok(remaining, "getting the grating position")
        return int(value)

    def get_mirror_position(self, mirror: str | SpectraPro.Mirror) -> Literal["front", "side"]:
        """Get the position of a diverter mirror.

        Args:
            mirror: The mirror to get the position of. Can be an enum member name (case insensitive) or value.

        Returns:
            The position (either `front` or `side`).
        """
        m = to_enum(mirror, SpectraPro.Mirror, to_upper=True)
        reply = self.query(f"{m.value} ?MIR").lstrip()
        if reply.startswith("no motor"):
            # Received "no motor", need to read another line to consume the " ok\r\n"
            _ = self.read()
            msg = f"{m} is not motorised"
            raise MSLConnectionError(self, msg)

        value, remaining = reply.split(maxsplit=1)
        self._check_ok(remaining, "getting the diverter mirror position")
        return "front" if int(value) == 0 else "side"

    def get_slit_width(self, slit: str | SpectraPro.Slit) -> int:
        """Get the width of a slit.

        Args:
            slit: The slit to get the width of. Can be an enum member name (case insensitive) or value.

        Returns:
            The slit width (in um).
        """
        s = to_enum(slit, SpectraPro.Slit, to_upper=True)
        reply = self.query(f"{s.value} ?MICRONS").lstrip()
        if reply.startswith("no motor"):
            # Received "no motor", need to read another line to consume the " ok\r\n"
            _ = self.read()
            msg = f"{s} is not motorised"
            raise MSLConnectionError(self, msg)

        value, remaining = reply.split(maxsplit=1)
        self._check_ok(remaining, "getting the slit width")
        return int(value)

    def gratings(self) -> list[SpectraProGrating]:
        """Get information about the installed gratings.

        Returns:
            The grating information.
        """
        gratings: list[SpectraProGrating] = []
        _ = self.query(b"?GRATINGS")
        while True:
            reply = self.read().strip()
            if reply == "ok":
                return gratings

            selected = False
            if reply.startswith("\x1a"):  # current grating in use is marked with an arrow
                selected = True
                reply = reply[1:]

            position, description = reply.split(maxsplit=1)
            if description != "Not Installed":
                gratings.append(SpectraProGrating(int(position), description, selected))

    def home_filter_wheel(self, *, wait: bool = True) -> None:
        """Move the filter wheel to the home position.

        !!! note
            It can take up to 3 seconds for the filter wheel to home.

        Args:
            wait: Whether to wait for the move to complete before returning to the calling program.
                If `False`, the next method you must call is [wait_until_ready][..wait_until_ready]
                to ensure the move has finished. Do not call other methods in this class until the
                move has finished, since the spectrograph/monochromator cannot respond to other
                requests while homing the filter wheel.
        """
        self._filter_changed = True
        _ = self.write(b"FHOME")
        if wait:
            self.wait_until_ready()

    def home_slit(self, slit: str | SpectraPro.Slit, *, wait: bool = True) -> None:
        """Move a slit to the home position.

        !!! note
            It can take up to 45 seconds for a slit to home.

        Args:
            slit: The slit to home. Can be an enum member name (case insensitive) or value.
            wait: Whether to wait for the move to complete before returning to the calling program.
                If `False`, the next method you must call is [wait_until_ready][..wait_until_ready]
                to ensure the move has finished. Do not call other methods in this class until the
                move has finished, since the spectrograph/monochromator cannot respond to other
                requests while homing a slit.
        """
        s = to_enum(slit, SpectraPro.Slit, to_upper=True)

        # It is more reliable to set the slit width to a value close to home and then send the
        # SHOME command instead of trying to home when the slit is near the maximum width.
        # Had lots of serial communication issues when homing the slit when it was at 3000 um.
        self.set_slit_width(s, 50)

        self._slit_changed = s  # must come after setting the slit width
        _ = self.write(f"{s.value} SHOME")
        if wait:
            self.wait_until_ready()

    def info(self) -> SpectraProInfo:
        """Get information about the spectrograph/monochromator.

        Returns:
            The `(model, serial, firmware-version)` numbers of the device.
        """
        model, _ = self.query(b"MODEL").split()
        serial, _ = self.query(b"SERIAL").split()
        version, _ = self.query(b"VER").split()
        return SpectraProInfo(model, serial, version)

    def is_wavelength_scanning(self) -> bool:
        """Check if the wavelength is in the process of scanning to the target value."""
        return self.query(b"MONO-?DONE\r", decode=False).startswith(b" 0")

    def motorised_slits(self) -> list[SpectraPro.Slit]:
        """Get the slits that are motorised.

        Returns:
            The motorised slits.
        """
        out: list[SpectraPro.Slit] = []
        for item in SpectraPro.Slit:
            reply = self.query(item.value).strip()
            if reply == "ok":
                out.append(item)
            else:
                # Received "no motor", need to read another line to consume the " ok\r\n"
                _ = self.read()
        return out

    def motorised_mirrors(self) -> list[SpectraPro.Mirror]:
        """Get the diverter mirrors that are motorised.

        Returns:
            The motorised diverter mirrors.
        """

        def check_reply(reply: str) -> bool:
            reply = reply.strip()
            if reply == "ok":
                return True

            # Received "no motor", need to read another line to consume the " ok\r\n"
            _ = self.read()
            return False

        out: list[SpectraPro.Mirror] = []
        if check_reply(self.query(b"EXIT-MIRROR")):
            out.append(SpectraPro.Mirror.EXIT)
        if check_reply(self.query(b"ENT-MIRROR")):
            out.append(SpectraPro.Mirror.ENTRANCE)
        return out

    def reset(self, *, wait: bool = True, init_wavelength: float = 0.0) -> None:
        """Reset the spectrograph/monochromator to the start-up settings.

        Sets the TURRET, GRATING, WAVELENGTH and SCAN-RATE to the initial (start-up) settings.

        !!! note
            If using a [callback][..set_callback] function while waiting, the wavelength
            value that is passed to the callback can be both positive and negative.

        Args:
            wait: Whether to wait for resetting to complete before returning to the calling program.
            init_wavelength: The value of the start-up wavelength to compare with the current
                wavelength to decide if resetting has completed.
        """
        reply = self.query(b"MONO-RESET")
        self._check_ok(reply, "resetting the spectrograph/monochromator")
        if wait:
            # sleeping for a bit seems to be required, otherwise reading the wavelength
            # will either raise an error (invalid reply) or immediately returns 0.0
            sleep(1)
            while True:
                w = self.wavelength
                if self._callback is not None:
                    self._callback(w)
                if w == init_wavelength:
                    return

    @property
    def scan_rate(self) -> float:
        """Get/Set the scan rate (in nm/minute) that a wavelength scan occurs at (see [scan_to][..scan_to]).

        The allowed scan-rate range may depend on the model, but typically the range is
        between 0.01 and 2000 nm/minute. Specifying a value outside this range may not
        raise an exception so it is best to get the scan rate after setting it to know
        what the actual value is.
        """
        value, remaining = self.query(b"?NM/MIN").split(maxsplit=1)
        self._check_ok(remaining, "getting the scan rate")
        return float(value)

    @scan_rate.setter
    def scan_rate(self, rate: float) -> None:
        reply = self.query(f"{rate:.3f} NM/MIN")
        self._check_ok(reply, "setting the scan rate")

    def scan_to(self, nm: float, *, wait: bool = True) -> None:
        """Scan to a wavelength at the specified [scan_rate][..scan_rate].

        Args:
            nm: The target wavelength (in nm).
            wait: Whether to wait for the move to complete before returning to the calling program.
                The [callback][..set_callback] function is called if waiting for the move to complete.
                If `False`, the only methods you can call are [wavelength][..wavelength],
                [is_wavelength_scanning][..is_wavelength_scanning], [wait_until_ready][..wait_until_ready],
                or [stop][..stop]. Do not call other methods in this class until the scan has finished, since
                the spectrograph/monochromator cannot respond to other requests while scanning the wavelength.
        """
        reply = self.query(f"{nm:.3f} >NM")
        self._check_ok(reply, "setting the scan-to wavelength")
        self._wavelength_scanning = True
        if wait:
            self.wait_until_ready()

    def set_callback(self, callback: Callable[[float], None] | None) -> None:
        """Set a callback function to receive the current wavelength value.

        The callback function is called automatically while waiting for a wavelength move to
        complete in the [reset][..reset] and [scan_to][..scan_to] methods only.

        Args:
            callback: A callback function. Set to `None` to disable callbacks.
                The callback function receives one argument, the current wavelength value (in nm).
        """
        self._callback = callback

    def set_filter_wheel_position(self, position: int, *, wait: bool = True) -> None:
        """Set the filter-wheel position.

        !!! note
            It can take up to 2 seconds for the filter wheel to change position.

        Args:
            position: The filter-wheel position to move to. The value must be between 1 and 6 (inclusive).
            wait: Whether to wait for the move to complete before returning to the calling program.
                If `False`, the next method you must call is [wait_until_ready][..wait_until_ready]
                to ensure the move has finished. Do not call other methods in this class until the
                move has finished, since the spectrograph/monochromator cannot respond to other
                requests while changing the filter-wheel position.
        """
        if position < 1 or position > 6:  # noqa: PLR2004
            msg = f"Invalid filter-wheel position {position}, must be between 1 and 6 (inclusive)"
            raise ValueError(msg)

        self._filter_changed = True
        _ = self.write(f"{position} FILTER")
        if wait:
            self.wait_until_ready()

    def set_grating_position(self, position: int, *, wait: bool = True) -> None:
        """Set the grating to use.

        !!! note
            It can take approximately 20 seconds for a different grating to come in to position.

        Args:
            position: The grating to select. The value must be between 1 and 9 (inclusive).
            wait: Whether to wait for the move to complete before returning to the calling program.
                If `False`, the next method you must call is [wait_until_ready][..wait_until_ready]
                to ensure the move has finished. Do not call other methods in this class until the
                move has finished, since the spectrograph/monochromator cannot respond to other
                requests while changing the grating position.
        """
        if position < 1 or position > 9:  # noqa: PLR2004
            msg = f"Invalid grating position {position}, must be between 1 and 9 (inclusive)"
            raise ValueError(msg)

        self._grating_changed = True
        _ = self.write(f"{position} GRATING")
        if wait:
            self.wait_until_ready()

    def set_mirror_position(
        self, mirror: str | SpectraPro.Mirror, position: Literal["front", "side"], *, wait: bool = True
    ) -> None:
        """Set the position of a diverter mirror.

        Args:
            mirror: The mirror to set the position of. Can be an enum member name (case insensitive) or value.
            position: The position to set the `mirror` to (either `front` or `side`).
            wait: Whether to wait for the move to complete before returning to the calling program.
                If `False`, the next method you must call is [wait_until_ready][..wait_until_ready]
                to ensure the move has finished. Do not call other methods in this class until the
                move has finished, since the spectrograph/monochromator cannot respond to other
                requests while changing the mirror position.
        """
        m = to_enum(mirror, SpectraPro.Mirror, to_upper=True)
        self._mirror_changed = m
        p = "FRONT" if position == "front" else "SIDE"
        _ = self.write(f"{m.value} {p}")
        if wait:
            self.wait_until_ready()

    def set_slit_width(self, slit: str | SpectraPro.Slit, um: int, *, wait: bool = True) -> None:
        """Set the width of a slit.

        !!! note
            It can take up to 10 seconds for a slit to reach the target width.

        Args:
            slit: The slit to set the width of. Can be an enum member name (case insensitive) or value.
            um: The width (in um). The range is typically from 10 to 3000 or 12000 microns and the
                resolution is either 1 or 5 microns depending on the slit that is installed in the system.
                Specifying a value that is outside the supported range or resolution automatically sets
                the slit width to a supported value. Call [get_slit_width][..get_slit_width] to get the
                actual slit width after the move is complete.
            wait: Whether to wait for the move to complete before returning to the calling program.
                If `False`, the next method you must call is [wait_until_ready][..wait_until_ready]
                to ensure the move has finished. Do not call other methods in this class until the
                move has finished, since the spectrograph/monochromator cannot respond to other
                requests while changing the slit width.
        """
        s = to_enum(slit, SpectraPro.Slit, to_upper=True)
        self._slit_changed = s
        _ = self.write(f"{s.value} {int(um)} MICRONS")
        if wait:
            self.wait_until_ready()

    def stop(self) -> None:
        """Stop the wavelength scan from moving.

        !!! warning
            This method must always be called after [scan_to][..scan_to], otherwise the
            spectrograph/monochromator does not retain the final wavelength position in its firmware.
            This method cannot be used to stop a grating position change.
        """
        reply = self.query(b"MONO-STOP")
        self._check_ok(reply, "requesting the wavelength to stop scanning")

    @property
    def turret(self) -> int:
        """Get/Set the turret number that is installed.

        The value must be either 1, 2 or 3.
        """
        value, remaining = self.query(b"?TURRET").split(maxsplit=1)
        self._check_ok(remaining, "getting the turret number")
        return int(value)

    @turret.setter
    def turret(self, number: int) -> None:
        if number not in {1, 2, 3}:
            msg = f"Invalid turret number {number}, must be 1, 2 or 3"
            raise ValueError(msg)

        reply = self.query(f"{number} TURRET")
        self._check_ok(reply, "setting the turret number")

    def wait_until_ready(self) -> None:
        """Wait until the wavelength, grating, slit or filter wheel has reached the target value.

        While the spectrograph/monochromator is busy it cannot respond to other requests.
        After calling this method, the device is ready to handle another request.
        """
        if self._grating_changed or self._filter_changed:
            text = "grating" if self._grating_changed else "filter-wheel"
            self._grating_changed = False
            self._filter_changed = False
            self._check_ok(self.read(), f"setting the {text} position")
        elif self._slit_changed is not None or self._mirror_changed is not None:
            item = self._slit_changed or self._mirror_changed
            self._slit_changed = None
            self._mirror_changed = None
            reply = self.read(decode=False).strip()
            if reply == b"no motor":
                # Received "no motor", need to read another line to consume the " ok\r\n"
                _ = self.read()
                msg = f"{item} is not motorised"
                raise MSLConnectionError(self, msg)
        elif self._wavelength_scanning:
            self._wavelength_scanning = False
            while True:
                done = not self.is_wavelength_scanning()
                if self._callback is not None:
                    self._callback(self.wavelength)
                if done:
                    self.stop()
                    return

    @property
    def wavelength(self) -> float:
        """Get/Set the wavelength (in nm).

        Moves to the target wavelength at the maximum motor speed. Only 3 digits
        after the decimal point is supported by the spectrograph/monochromator. If
        extra precision is specified, the value will be rounded to 3 decimal places.

        !!! note
            The [callback][..set_callback] function is not called while moving.
            Setting the wavelength will block the calling program until the move
            is finished.
        """
        value, remaining = self.query(b"?NM").split(maxsplit=1)
        self._check_ok(remaining, "getting the wavelength")
        return float(value)

    @wavelength.setter
    def wavelength(self, nm: float) -> None:
        """Set the wavelength (in nm)."""
        reply = self.query(f"{nm:.3f} <GOTO>")
        self._check_ok(reply, "setting the wavelength")
