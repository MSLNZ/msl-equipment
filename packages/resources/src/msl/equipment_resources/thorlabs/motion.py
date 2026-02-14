"""Thorlabs Motion Controller."""

# cSpell: ignore HBBBB HHBB HHHII Hiii MGMSG STATUSUPDATE USTATUSUPDATE POSCOUNTER ENCCOUNTER
# cSpell: ignore GENMOVEPARAMS VELPARAMS HOMEPARAMS UPDATEMSGS STATUSBITS CHANENABLESTATE LIMSWITCHPARAMS
from __future__ import annotations

import contextlib
import os
import sys
from dataclasses import dataclass
from struct import pack, unpack
from time import sleep
from typing import TYPE_CHECKING, NamedTuple

from msl.equipment.interfaces.ftdi import FTDI
from msl.equipment.interfaces.message_based import MSLConnectionError
from msl.equipment.schema import Interface

if TYPE_CHECKING:
    from typing import Callable, Literal

    from msl.equipment.schema import Equipment

MOVING_CLOCKWISE = 0x00000010
MOVING_COUNTER_CLOCKWISE = 0x00000020
JOGGING_CLOCKWISE = 0x00000040
JOGGING_COUNTER_CLOCKWISE = 0x00000080
HOMING = 0x00000200
HOMED = 0x00000400
MOVING = MOVING_CLOCKWISE | MOVING_COUNTER_CLOCKWISE | JOGGING_CLOCKWISE | JOGGING_COUNTER_CLOCKWISE | HOMING


class ThorlabsMotion(Interface):
    """Thorlabs Motion Controller."""

    unit: str = "mm"
    """The physical unit."""

    def __init__(self, equipment: Equipment) -> None:
        """Thorlabs Motion Controller.

        Implements the Host-Controller Communication Protocol.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following
        _properties_ for the `ThorlabsMotion` class, as well as the _properties_ defined
        in [FTDI][msl.equipment.interfaces.ftdi.FTDI]. The default baud rate is 115200
        and RTS/CTS flow control is enabled.

        Attributes: Connection Properties:
            init (bool): Whether to initialise the motion controller to default parameters.
                These parameters are specific to each motion controller. If `False`, the
                parameters that are persisted in the firmware of the controller are kept.
                You may change these parameters at runtime, `init` just changes the
                initialisation procedure. _Default: `False`_
        """
        self._is_connected: bool = False
        super().__init__(equipment)

        # These should be redefined in the subclass (if necessary)
        self._position: Convert = Convert(1)
        self._velocity: Convert = Convert(1)
        self._acceleration: Convert = Convert(1)
        self._is_slot_system: bool = False
        self._has_encoder: bool = False

        assert equipment.connection is not None  # noqa: S101
        equipment.connection.properties.setdefault("baud_rate", 115200)

        try:
            ftdi = FTDI(equipment)
        except MSLConnectionError as e:
            if str(e).endswith(("FT_DEVICE_NOT_FOUND", "not found")):
                raise

            if sys.maxsize > (1 << 32):
                path = r"C:\Program Files\Thorlabs\Kinesis\ftd2xx.dll"
            else:
                path = r"C:\Program Files (x86)\Thorlabs\Kinesis\ftd2xx.dll"

            if not os.path.isfile(path):  # noqa: PTH113
                raise

            os.environ["D2XX_LIBRARY"] = path
            ftdi = FTDI(equipment)

        self._ftdi: FTDI = ftdi
        self._is_connected = True
        self._callback: Callable[[float, int, int], None] | None = None
        self._auto_updates: bool = False
        self._init_defaults: bool = equipment.connection.properties.get("init", False)

        # Host-Controller Communications Protocol Issue 44.1
        # Section 2.1: USB Interface

        # Pre purge dwell 50ms
        sleep(0.05)

        # Purge the device
        self._ftdi.purge_buffers()

        # Post purge dwell 50ms
        sleep(0.05)

        # Reset device
        self._ftdi.reset_device()

        # Set RTS
        self._ftdi.set_rts(state=equipment.connection.properties.setdefault("rts_cts", True))

        _ = self.write(0x0018)  # MGMSG_HW_NO_FLASH_PROGRAMMING
        self.stop_auto_updates()

    def _maybe_handle_auto_update(self, response: ThorlabsResponse) -> bool:
        """Maybe handle an automatic update response, if the message ID is correct for an automatic update.

        Returns:
            Whether the response was from an automatic update.
        """
        if response.message_id == 0x0481:  # MGMSG_MOT_GET_STATUSUPDATE  # noqa: PLR2004
            if self._callback is not None:
                # Some 0x0481 messages have 14 bytes but other messages (from BSC20x controllers) have 28 bytes
                # If 28 bytes, the last 14 bytes are reserved for future use so only consider the first 14 bytes
                _, position, encoder, status = unpack("<HiiI", response.data[:14])
                value: int = encoder if self._has_encoder else position
                self._callback(self._position.to_mm_or_degree(value), value, status)
            return True
        if response.message_id == 0x0491:  # MGMSG_MOT_GET_USTATUSUPDATE  # noqa: PLR2004
            if self._callback is not None:
                _, position, _, _, status = unpack("<HiHhI", response.data)
                self._callback(self._position.to_mm_or_degree(position), position, status)
            return True
        return False

    def _wait(self, channel: int) -> None:
        """Wait for an actuator or a stage to stop moving."""
        auto = self._auto_updates
        if not auto:
            self.start_auto_updates()

        # MGMSG_MOT_MOVE_HOMED, MGMSG_MOT_MOVE_COMPLETED, MGMSG_MOT_MOVE_STOPPED
        move_complete = {0x0444, 0x0464, 0x0466}

        while True:
            response = self.read()
            _ = self._maybe_handle_auto_update(response)
            if response.message_id in move_complete:
                break

        if not auto:
            self.stop_auto_updates()

        if self._callback is not None:
            counts = self.encoder(channel=channel)
            self._callback(self._position.to_mm_or_degree(counts), counts, self.status(channel=channel))

    def disable(self, channel: int = 1) -> None:
        """Disable a channel.

        When disabled, power is removed from the motor and it can be freely moved by hand.

        Args:
            channel: The channel to disable.
        """
        _ = self.write(0x0210, param1=channel, param2=0x02)  # MGMSG_MOD_SET_CHANENABLESTATE

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the Thorlabs motion controller."""
        if self._is_connected:
            dest = 0x11 if self._is_slot_system else 0x50
            with contextlib.suppress(MSLConnectionError):
                if self._auto_updates:
                    self.stop_auto_updates()
                _ = self.write(0x0002, dest=dest)  # MGMSG_HW_DISCONNECT

            self._ftdi.disconnect()
            super().disconnect()
            self._is_connected = False

    def enable(self, channel: int = 1) -> None:
        """Enable a channel.

        When enabled, power is applied to the motor so it is fixed in position.

        Args:
            channel: The channel to enable.
        """
        _ = self.write(0x0210, param1=channel, param2=0x01)  # MGMSG_MOD_SET_CHANENABLESTATE

    def encoder(self, channel: int = 1) -> int:
        """Get the position of the actuator or stage in encoder counts.

        Args:
            channel: The channel to get the encoder counts of.

        Returns:
            Encoder counts (number of pulses).
        """
        # MGMSG_MOT_REQ_ENCCOUNTER or MGMSG_MOT_REQ_POSCOUNTER
        msg_id = 0x040A if self._has_encoder else 0x0411
        _, counts = unpack("<Hi", self.query(msg_id, param1=channel))
        return counts

    @property
    def ftdi(self) -> FTDI:
        """Returns the underlying interface instance."""
        return self._ftdi

    def get_backlash(self, channel: int = 1) -> float:
        """Get the backlash value (to control hysteresis).

        Args:
            channel: The channel to get the backlash of.

        Returns:
            The backlash value (in millimetres or degrees).
        """
        data = self.query(0x043B, param1=channel)  # MGMSG_MOT_REQ_GENMOVEPARAMS
        _, encoder = unpack("<Hi", data)
        return self._position.to_mm_or_degree(encoder)

    def get_home_parameters(self, channel: int = 1) -> ThorlabsHomeParameters:
        """Get the parameters that are used to home the motion controller.

        Args:
            channel: The channel to get the home parameters of.

        Returns:
            The homing parameters.
        """
        reply = self.query(0x0441, param1=channel)  # MGMSG_MOT_REQ_HOMEPARAMS
        ch, direction, limit_switch, velocity, offset = unpack("<HHHii", reply)
        return ThorlabsHomeParameters(
            channel=ch,
            direction="forward" if direction == 1 else "reverse",
            limit_switch="forward" if limit_switch == 4 else "reverse",  # noqa: PLR2004
            velocity=self._velocity.to_mm_or_degree(velocity),
            offset=self._position.to_mm_or_degree(offset),
        )

    def get_limit_parameters(self, channel: int = 1) -> ThorlabsLimitParameters:
        """Get the limit-switch parameters that are used for the motion controller.

        Args:
            channel: The channel to get the limit-switch parameters of.

        Returns:
            The limit-switch parameters.
        """
        reply = self.query(0x0424, param1=channel)  # MGMSG_MOT_REQ_LIMSWITCHPARAMS
        ch, cw_hard, ccw_hard, cw_soft, ccw_soft, mode = unpack("<HHHiiH", reply)
        return ThorlabsLimitParameters(
            channel=ch,
            cw_hardware=cw_hard,
            ccw_hardware=ccw_hard,
            cw_software=self._position.to_mm_or_degree(cw_soft),
            ccw_software=self._position.to_mm_or_degree(ccw_soft),
            mode=mode,
        )

    def get_move_parameters(self, channel: int = 1) -> ThorlabsMoveParameters:
        """Get the parameters that are used to move the motion controller.

        Args:
            channel: The channel to get the move parameters of.

        Returns:
            The move parameters.
        """
        reply = self.query(0x0414, param1=channel)  # MGMSG_MOT_REQ_VELPARAMS
        ch, minimum, acceleration, maximum = unpack("<Hiii", reply)
        return ThorlabsMoveParameters(
            channel=ch,
            min_velocity=self._velocity.to_mm_or_degree(minimum),
            max_velocity=self._velocity.to_mm_or_degree(maximum),
            acceleration=self._acceleration.to_mm_or_degree(acceleration),
        )

    def hardware_info(self) -> ThorlabsHardwareInfo:
        """Get the hardware information.

        Returns:
            The hardware information about the Thorlabs motion controller.
        """
        serial, model, typ, fw, notes, data, hw, state, n = unpack("<I8sH4s48s12sHHH", self.query(0x0005))

        # "notes" sometimes has non \x00 characters at the end, so cannot reliably use rstrip(b"\x00")
        index = notes.find(b"\x00")
        if index > 0:
            notes = notes[:index]

        return ThorlabsHardwareInfo(
            serial=str(serial),
            model=model.rstrip(b"\x00").decode(),
            type=typ,
            firmware_version=f"{fw[2]}.{fw[1]}.{fw[0]}",
            notes=notes.decode(),
            data=data.strip(b"\x00").decode().rstrip(),
            hardware_version=hw,
            modification_state=state,
            num_channels=n,
        )

    def home(self, *, channel: int = 1, wait: bool = True) -> None:
        """Move to the home position.

        Args:
            channel: The channel to home.
            wait: Whether to wait for homing to complete before returning to the calling program.
        """
        _ = self.write(0x0443, param1=channel)  # MGMSG_MOT_MOVE_HOME
        if wait:
            self._wait(channel)

    def identify(self, channel: int = 1) -> None:
        """Instruct hardware unit to identify itself by flashing its front panel LEDs.

        Args:
            channel: The channel to identify.
        """
        dest = 0x11 if self._is_slot_system else 0x50
        _ = self.write(0x0223, param1=channel, dest=dest)

    def is_enabled(self, channel: int = 1) -> bool:
        """Check if a motor is enabled.

        If enabled, power is applied to the motor so it is fixed in position.

        Args:
            channel: The channel to check.

        Returns:
            Whether the motor is enabled or disabled.
        """
        reply = self.query(0x0211, param1=channel)
        return reply[1] == 0x01

    def is_homed(self, channel: int = 1) -> bool:
        """Check if the actuator or stage has been homed.

        Args:
            channel: The channel to check.

        Returns:
            Whether the actuator or stage has been homed.
        """
        return bool(self.status(channel) & HOMED)

    def is_moving(self, channel: int = 1) -> bool:
        """Check if the actuator or stage is moving.

        Args:
            channel: The channel to check.

        Returns:
            Whether the actuator or stage is moving.
        """
        return bool(self.status(channel=channel) & MOVING)

    def move_by(self, distance: float, *, channel: int = 1, convert: bool = True, wait: bool = True) -> None:
        """Move by a relative distance.

        Args:
            distance: The distance to move by. Can be a negative or a positive value. The unit of the
                value depends on the whether `convert` is `True` or `False`. If `True`, the unit must
                be in millimetres (for a translation) or degrees (for a rotation), otherwise the
                distance must be specified as encoder counts.
            channel: The channel to move.
            convert: Whether to convert `distance` to encoder counts.
            wait: Whether to wait for the move to complete before returning to the calling program.
        """
        counts = self._position.to_encoder(distance) if convert else int(distance)
        _ = self.write(0x0448, data=pack("<Hi", channel, counts))  # MGMSG_MOT_MOVE_RELATIVE
        if wait:
            self._wait(channel)

    def move_to(self, position: float, *, channel: int = 1, convert: bool = True, wait: bool = True) -> None:
        """Move to an absolute position.

        Args:
            position: The position to move to. The unit of the value depends on the whether `convert` is
                `True` or `False`. If `True`, the unit must be in millimetres (for a translation) or degrees
                (for a rotation), otherwise the position must be specified as encoder counts.
            channel: The channel to move.
            convert: Whether to convert `position` to encoder counts.
            wait: Whether to wait for the move to complete before returning to the calling program.
        """
        counts = self._position.to_encoder(position) if convert else int(position)
        data = pack("<Hi", channel, counts)
        _ = self.write(0x0453, data=data)  # MGMSG_MOT_MOVE_ABSOLUTE
        if wait:
            self._wait(channel)

    def position(self, channel: int = 1) -> float:
        """Get the position of the actuator or stage.

        Args:
            channel: The channel to get the position of.

        Returns:
            The position (in millimetres or degrees).
        """
        return self._position.to_mm_or_degree(self.encoder(channel=channel))

    def query(
        self,
        message_id: int,
        *,
        param1: int = 0,
        param2: int = 0,
        data: bytes | None = None,
        dest: int | None = None,
        delay: float = 0,
    ) -> bytes:
        """Query data from a Thorlabs motion controller.

        Args:
            message_id: The message ID of the request.
            param1: First parameter required for the query.
            param2: Second parameter required for the query.
            data: The optional data to include with the message. If specified, `param1` and `param2` are not used.
            dest: Destination module that the query is for, e.g., `0x50` for a generic controller,
                `0x11` for a rack controller, motherboard in a card-slot system or a router board,
                `0x21` for Bay 0 in a card-slot system, `0x22` for Bay 1 in a card-slot system, etc.
                If not specified, the destination module is automatically determined.
            delay: The number of seconds to wait between
                [write][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.write]
                and [read][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.read] operations.

        Returns:
            The data of the response.
        """
        _ = self.write(message_id, param1=param1, param2=param2, data=data, dest=dest)
        if delay > 0:
            sleep(delay)

        # Could get automatic update messages in between requested data
        while True:
            response = self.read()
            if response.message_id == message_id + 1:
                return response.data

            if self._maybe_handle_auto_update(response):
                continue

            msg = f"Expected a response with message ID 0x{message_id + 1:04X}, got {response!r}"
            raise MSLConnectionError(self, msg)

    def read(self) -> ThorlabsResponse:
        """Read a response from a Thorlabs motion controller.

        Returns:
            A response instance.
        """
        msg_id, p1, p2, d, s = unpack("<HBBBB", self._ftdi.read(size=6, decode=False))
        data = self._ftdi.read(size=p1 | (p2 << 8), decode=False) if d & 0x80 else bytes([p1, p2])
        return ThorlabsResponse(message_id=msg_id, module=s, data=data)

    def set_backlash(self, backlash: float, *, channel: int = 1, convert: bool = True) -> None:
        """Set the backlash value (to control hysteresis).

        Args:
            backlash: The backlash value. The unit of the value depends on the whether `convert` is
                `True` or `False`. If `True`, the unit must be in millimetres (for a translation) or degrees
                (for a rotation), otherwise the backlash must be specified as encoder counts.
            channel: The channel to set the backlash of.
            convert: Whether to convert `backlash` to encoder counts.
        """
        counts = self._position.to_encoder(backlash) if convert else int(backlash)
        _ = self.write(0x043A, data=pack("<Hi", channel, counts))  # MGMSG_MOT_SET_GENMOVEPARAMS

    def set_callback(self, callback: Callable[[float, int, int], None] | None) -> None:
        """Set a callback function to receive position, encoder counts and status information.

        The callback function is called while waiting for an actuator or a stage to stop moving.

        Args:
            callback: A callback function. Set to `None` to disable callbacks.

                The callback function receives three arguments:

                * Position (in millimetres or degrees)
                * Encoder counts (as an integer)
                * Status of the motion controller. A 32-bit integer that represents the
                    current status of the motion controller. Each of the 32 bits acts as
                    a flag (0 or 1), simultaneously indicating 32 distinct operating
                    conditions of the motion controller.
        """
        self._callback = callback

    def set_home_parameters(self, parameters: ThorlabsHomeParameters) -> None:
        """Set the parameters that are used to home the motion controller.

        Args:
            parameters: Homing parameters. It is recommended to call
                [get_home_parameters][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.get_home_parameters]
                first and then update the appropriate attributes.
        """
        direction = 1 if parameters.direction == "forward" else 2
        limit_switch = 4 if parameters.limit_switch == "forward" else 1
        velocity = self._velocity.to_encoder(parameters.velocity)
        offset = self._position.to_encoder(parameters.offset)
        data = pack("<HHHii", parameters.channel, direction, limit_switch, velocity, offset)
        _ = self.write(0x0440, data=data)  # MGMSG_MOT_SET_HOMEPARAMS

    def set_limit_parameters(self, parameters: ThorlabsLimitParameters) -> None:
        """Set the limit-switch parameters for the motion controller.

        Args:
            parameters: Limit-switch parameters. It is recommended to call
                [get_limit_parameters][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.get_limit_parameters]
                first and then update the appropriate attributes.
        """
        cw_soft = self._position.to_encoder(parameters.cw_software)
        ccw_soft = self._position.to_encoder(parameters.ccw_software)
        data = pack(
            "<HHHiiH",
            parameters.channel,
            parameters.cw_hardware,
            parameters.ccw_hardware,
            cw_soft,
            ccw_soft,
            parameters.mode,
        )
        _ = self.write(0x0423, data=data)  # MGMSG_MOT_SET_LIMSWITCHPARAMS

    def set_move_parameters(self, parameters: ThorlabsMoveParameters) -> None:
        """Set the parameters that are used to move the motion controller.

        Args:
            parameters: Move parameters. It is recommended to call
                [get_move_parameters][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.get_move_parameters]
                first and then update the appropriate attributes.
        """
        minimum = self._velocity.to_encoder(parameters.min_velocity)
        maximum = self._velocity.to_encoder(parameters.max_velocity)
        acceleration = self._acceleration.to_encoder(parameters.acceleration)
        data = pack("<Hiii", parameters.channel, minimum, acceleration, maximum)
        _ = self.write(0x0413, data=data)  # MGMSG_MOT_SET_VELPARAMS

    def start_auto_updates(self) -> None:
        """Start automatic updates from the Thorlabs motion controller.

        Update messages contain information about the position and status of the controller.
        The messages will be sent by the controller every 100 milliseconds until
        [stop_auto_updates][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.stop_auto_updates] is called.

        If you want to receive position and status updates from the controller, call
        [set_callback][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.set_callback] with a function
        to handle the updates.

        Automatic updates are temporarily enabled while waiting for an actuator or a stage to stop moving.

        You must periodically call [read][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.read] to handle
        the automatic updates if you explicitly call this method, otherwise the read buffer may overflow.
        """
        self._auto_updates = True
        _ = self.write(0x0011)  # MGMSG_HW_START_UPDATEMSGS

    def status(self, channel: int = 1) -> int:
        """Get the status of the motion controller.

        Args:
            channel: The channel to get the status of.

        Returns:
            The status. A 32-bit value that represents the current status of the motion controller.
                Each of the 32 bits acts as a flag (0 or 1), simultaneously indicating 32 distinct
                operating conditions of the motion controller.
        """
        status: int
        _, status = unpack("<HI", self.query(0x0429, param1=channel))  # MGMSG_MOT_REQ_STATUSBITS
        return status

    def stop(self, *, channel: int = 1, immediate: bool = False) -> None:
        """Stop the actuator or stage from moving.

        Args:
            channel: The channel of the motion controller to stop.
            immediate: Whether to stop immediately (`True`) or use a gradual stop (`False`).
                Stopping immediately may risk losing track of the position.
        """
        mode = 0x01 if immediate else 0x02
        _ = self.write(0x0465, param1=channel, param2=mode)  # MGMSG_MOT_MOVE_STOP
        self._wait(channel)

    def stop_auto_updates(self) -> None:
        """Stop automatic updates from the Thorlabs motion controller."""
        self._auto_updates = False
        _ = self.write(0x0012)  # MGMSG_HW_STOP_UPDATEMSGS

    @property
    def timeout(self) -> float | None:
        """The timeout, in seconds, for [read][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.read]
        and [write][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.write] operations.

        A value &lt;0 will set the timeout to be `None` (blocking mode).
        """  # noqa: D205
        return self._ftdi.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self._ftdi.timeout = value

    def wait_until_moved(self, channel: int = 1) -> None:
        """Wait until the motion controller indicates that a move is complete.

        !!! warning
            Some motion controllers indicate that a move is complete but upon reading the position
            of the actuator (or stage) the returned value indicates that it is still a few
            _encoder counts_ away from the target position. It has been observed that it could take
            up to 600 ms for the indicated position to equal the target position.

            This method will block forever if the motion controller is not moving.

        Args:
            channel: The channel to wait for.
        """
        self._wait(channel)

    def write(
        self, message_id: int, *, param1: int = 0, param2: int = 0, data: bytes | None = None, dest: int | None = None
    ) -> int:
        """Write a message to the Thorlabs motion controller.

        Args:
            message_id: Message ID.
            param1: First parameter required for the message.
            param2: Second parameter required for the message.
            data: The optional data to include with the message. If specified, `param1` and `param2` are not used.
            dest: Destination module that the message is for, e.g., `0x50` for a single-channel controller,
                `0x11` for a rack controller, motherboard in a card slot system or a router board,
                `0x21` for Bay 0 in a card slot system, `0x22` for Bay 1 in a card slot system, etc.
                If not specified, the destination module is automatically determined.

        Returns:
            The number of bytes written.
        """
        if dest is None:
            dest = (0x11 if param1 == 0 else 0x20 + param1) if self._is_slot_system else 0x50

        # `source` is always 0x01 for a message sent from a computer
        if data is None:
            msg = pack("<HBBBB", message_id, param1, param2, dest, 0x01)
        else:
            msg = pack("<HHBB", message_id, len(data), dest | 0x80, 0x01) + data

        return self._ftdi.write(msg)


class Convert:
    """Convert between encoder counts and a physical value (millimetres or degree)."""

    def __init__(self, factor: float, decimals: int = 6) -> None:
        """Convert between encoder counts and a physical value.

        Args:
            factor: The scaling factor. Must be `physical / encoder`.
            decimals: The number of decimals to round the physical value to.
        """
        self._factor: float = factor
        self._decimals: int = decimals

    def to_encoder(self, mm_or_degree: float) -> int:
        """Convert a value in millimetres or degrees to encoder counts."""
        return round(mm_or_degree / self._factor)

    def to_mm_or_degree(self, encoder: int) -> float:
        """Convert encoder counts to a value in millimetres or degrees."""
        return round(encoder * self._factor, self._decimals)


class ThorlabsResponse(NamedTuple):
    """A response from a Thorlabs motion controller.

    Attributes:
        message_id (int): The message ID of the response.
        module (int): The module in the motion controller that sent the response.
        data (bytes): The response data.
    """

    message_id: int
    module: int
    data: bytes

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return f"ThorlabsResponse(message_id=0x{self.message_id:04X}, module=0x{self.module:02X}, data={self.data!r})"


class ThorlabsHardwareInfo(NamedTuple):
    """Information about Thorlabs motion-controller hardware.

    Attributes:
        serial (str): Unique 8-digit serial number.
        model (str): Alphanumeric model number.
        type (int): Hardware type.
        firmware_version (str): Firmware version number.
        notes (str): Device-dependant notes.
        data (str): Device-dependant data.
        hardware_version (int): The hardware version number.
        modification_state (int): The modification state of the hardware.
        num_channels (int): The number of channels the hardware has.
    """

    serial: str
    model: str
    type: int
    firmware_version: str
    notes: str
    data: str
    hardware_version: int
    modification_state: int
    num_channels: int


@dataclass
class ThorlabsHomeParameters:
    """Parameters used when homing a Thorlabs motion controller.

    Attributes:
        channel (int): The channel associated with the homing parameters.
        direction (Literal["forward", "reverse"]): The direction sense for a move to home.
        limit_switch (Literal["forward", "reverse"]): The hardware-limit switch associated with the home position.
        velocity (float): The homing velocity, in millimetres/second or degrees/second.
        offset (float): The distance (in millimetres or degrees) of the home position from the Home Limit Switch.
    """

    channel: int
    direction: Literal["forward", "reverse"]
    limit_switch: Literal["forward", "reverse"]
    velocity: float
    offset: float


@dataclass
class ThorlabsMoveParameters:
    """Parameters used when moving a Thorlabs motion controller.

    Attributes:
        channel (int): The channel associated with the move parameters.
        min_velocity (float): The minimum velocity, in millimetres/second or degrees/second.
            Currently not used, must be 0.
        max_velocity (float): The maximum velocity, in millimetres/second or degrees/second.
        acceleration (float): The acceleration, in millimetres/second/second or degrees/second/second.
    """

    channel: int
    min_velocity: float
    max_velocity: float
    acceleration: float


@dataclass
class ThorlabsLimitParameters:
    """Limit-switch parameters.

    Attributes:
        channel (int): The channel associated with the parameters.
        cw_hardware (int): The operation of the clockwise hardware limit switch when contact is made.
        ccw_hardware (int): The operation of the counter-clockwise hardware limit switch when contact is made.
        cw_software (float): Clockwise software limit (in millimetres or degrees).
        ccw_software (float): Counter-clockwise software limit (in millimetres or degrees).
        mode (int): Software limit-switch mode.
    """

    channel: int
    cw_hardware: int
    ccw_hardware: int
    cw_software: float
    ccw_software: float
    mode: int


def find_device(equipment: Equipment) -> str | None:
    """Parse C:/ProgramData/Thorlabs/MotionControl/ThorlabsDeviceConfiguration.xml for a device."""
    assert equipment.connection is not None  # noqa: S101
    p = equipment.connection.properties
    device = p.get("actuator", p.get("stage", ""))
    if device:
        return device

    from xml.etree import ElementTree as ET  # noqa: PLC0415

    try:
        tree = ET.parse(r"C:\ProgramData\Thorlabs\MotionControl\ThorlabsDeviceConfiguration.xml")  # noqa: S314
    except FileNotFoundError:
        return None

    serial = equipment.serial
    if not serial:
        *_, serial = equipment.connection.address.split("::")

    element = tree.find(f".//Device[@Name={serial!r}]")
    if element is None:
        return None

    return element[0].text
