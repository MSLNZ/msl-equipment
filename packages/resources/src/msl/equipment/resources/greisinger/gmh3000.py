"""
Communicate with a Greisinger GMH 3000 Series thermometer.
"""
from __future__ import annotations

from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.exceptions import GreisingerError
from msl.equipment.record_types import EquipmentRecord
from msl.equipment.resources import register

ERROR_CODES = {
    16352: 'Measuring range exceeded',
    16353: 'Measuring range undercut',
    16362: 'Calculation not possible',
    16363: 'System error',
    16364: 'Battery dead',
    16365: 'No sensor',
    16366: 'Recording error: EEPROM error',
    16367: 'EEPROM checksum error',
    16368: 'Recording error: system restarted',
    16369: 'Recording error: data pointer',
    16370: 'Recording error: marker, data invalid',
    16371: 'Data invalid',
}


@register(manufacturer=r'Greisinger', model=r'GMH\s*3\d{3}')
class GMH3000(ConnectionSerial):
    
    def __init__(self, record: EquipmentRecord) -> None:
        """Communicate with a Greisinger GMH 3000 Series thermometer.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a thermometer connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'gmh_address': int, The GMH address of the device [default: 1]

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        props = record.connection.properties
        props.setdefault('baud_rate', 4800)
        super().__init__(record)

        self.set_exception_class(GreisingerError)

        # termination characters are not used
        self.read_termination = None
        self.write_termination = None

        self._address = self._invert(int(props.get('gmh_address', 1)))

    def _check_crc(self, reply: bytes) -> None:
        # check CRC values in the reply
        for i in range(len(reply) // 3):
            i *= 3
            if self._crc(*reply[i:i+2]) != reply[i+2]:
                self.raise_exception(f'Invalid CRC checksum in reply: {reply}')

    @staticmethod
    def _crc(a: int, b: int) -> int:
        """Calculate the CRC byte."""
        # See section "8.5 Code zur CRC-Berechnung" from the document
        # "Schnittstellenbeschreibung fur EASYBus Sensormodule und GMH Handmessgerate V1.0"
        byte = (a << 8) | b
        for _ in range(16):
            if (byte & 0x8000) == 0x8000:
                byte = (byte << 1) ^ 0x0700
            else:
                byte = byte << 1
        return ~(byte >> 8) & 0xFF

    def _decode(self, reply) -> float:
        if len(reply) == 3:
            return self._decode16(*reply[:2])
        return self._decode32(*reply[:2], *reply[3:5])

    def _decode16(self, a: int, b: int) -> float:
        """Decode two bytes as a float."""
        uint16 = self._to_uint16(a, b)
        exponent = (uint16 & 0xC000) >> 14
        uint16 &= 0x3FFF
        if 0x3FE0 <= uint16 <= 0x3FFF:
            self.raise_exception(ERROR_CODES.get(uint16, f'Unknown EASYBus error code {uint16}'))
        return (float(uint16) - 2048.0) / (10. ** exponent)

    def _decode32(self, a: int, b: int, c: int, d: int) -> float:
        """Decode four bytes as a float."""
        # Section "8.1 Codes zur Decodierung" from the document
        # "Schnittstellenbeschreibung fur EASYBus Sensormodule und GMH Handmessgerate V1.0"
        exponent = (self._invert(a) >> 3) - 15
        e = self._to_uint16(a, b)
        f = self._to_uint16(c, d)
        uint32 = self._to_uint32(e, f)
        uint32 &= 0x07FFFFFF
        if 0x07F5E100 > uint32:
            if 0x04000000 == (uint32 & 0x04000000):
                uint32 |= 0xF8000000
            uint32 += 0x02000000
        else:
            err = uint32 - 0x07F5E100
            self.raise_exception(ERROR_CODES.get(err, f'Unknown EASYBus error code {err}'))
        uint32 &= 0xFFFFFFFF
        int32 = (uint32 ^ 0x80000000) - 0x80000000  # convert to signed int32
        return float(int32) / (10. ** exponent)

    def _get(self, *, code: int) -> bytes:
        """Send a Get transaction. Checks all CRC values in the reply."""
        if code > 15:
            code = self._invert(code)
            request = [self._address, 0xF2, self._crc(self._address, 0xF2),
                       code, 0, self._crc(code, 0)]
        else:
            code <<= 4
            request = [self._address, code, self._crc(self._address, code)]

        self.write(bytes(request))
        header = self.read(size=3, decode=False)
        if self._crc(*header[:2]) != header[2]:
            self.raise_exception(f'Invalid CRC checksum in header: {header}')

        # bit 1 and 2 represent the message length (including the header) in bytes
        size = 3 * ((header[1] & 0b00000110) >> 1)
        if size == 0:
            return header
        reply = self.read(size=size, decode=False)
        self._check_crc(reply)
        return reply

    @staticmethod
    def _invert(b: int) -> int:
        """Invert byte (1 -> 254, 2 -> 253, ...)."""
        return ~b & 0xFF

    def _to_uint16(self, a: int, b: int) -> int:
        """Convert two bytes to uint16."""
        # See section "8.1 Codes zur Decodierung" from the document
        # "Schnittstellenbeschreibung fur EASYBus Sensormodule und GMH Handmessgerate V1.0"
        return (self._invert(a) << 8) | b

    @staticmethod
    def _to_uint32(a: int, b: int) -> int:
        """Convert two uint16 to uint32."""
        # See section "8.1 Codes zur Decodierung" from the document
        # "Schnittstellenbeschreibung fur EASYBus Sensormodule und GMH Handmessgerate V1.0"
        return (a << 16) | b

    def channel_count(self) -> int:
        """Get the number of channels.

        Returns
        -------
        :class:`int`
            The channel count.
        """
        reply = self._get(code=208)
        return self._to_uint16(*reply[3:5])

    def clear_max_value(self) -> float:
        """Clear the maximum value stored in the device memory.

        Returns
        -------
        :class:`float`
            The current value.
        """
        # used Wireshark with the USBPcap plugin to eavesdrop on the
        # GMH_Transmit(1, 175, 0, 0.0, 1) call of the DLL to get the
        # hex values and message lengths
        code, value = self._invert(175), 1
        self.write(bytes([self._address, 0xF6, self._crc(self._address, 0xF6),
                          code, value, self._crc(code, value),
                          0x00, 0xFF, 0x0C, 0x00, 0xFF, 0x0C]))
        reply = self.read(size=12, decode=False)
        self._check_crc(reply)
        return self._decode32(*reply[6:8], *reply[9:11])

    def clear_min_value(self) -> float:
        """Clear the minimum value stored in the device memory.

        Returns
        -------
        :class:`float`
            The current value.
        """
        # used Wireshark with the USBPcap plugin to eavesdrop on the
        # GMH_Transmit(1, 174, 0, 0.0, 1) call of the DLL to get the
        # hex values and message lengths
        code, value = self._invert(174), 1
        self.write(bytes([self._address, 0xF6, self._crc(self._address, 0xF6),
                          code, value, self._crc(code, value),
                          0x00, 0xFF, 0x0C, 0x00, 0xFF, 0x0C]))
        reply = self.read(size=12, decode=False)
        self._check_crc(reply)
        return self._decode32(*reply[6:8], *reply[9:11])

    def display_range(self) -> tuple[float, float]:
        """Get the range of the display.

        Returns
        -------
        :class:`float`
            The minimum value that the device can display.
        :class:`float`
            The maximum value that the device can display.
        """
        reply = self._get(code=200)
        minimum = self._decode32(*reply[3:5], *reply[6:8])
        reply = self._get(code=201)
        maximum = self._decode32(*reply[3:5], *reply[6:8])
        return minimum, maximum

    def firmware_version(self) -> tuple[int, int]:
        """Get the version information of the firmware.

        Returns
        -------
        :class:`int`
            The version number.
        :class:`int`
            The version identifier.
        """
        reply = self._get(code=254)
        return reply[4], self._invert(reply[3])

    def id_number(self) -> str:
        """Get the device ID (serial) number.

        Returns
        -------
        :class:`str`
            The ID (serial) number of the device.
        """
        reply = self._get(code=12)
        a = self._to_uint16(*reply[:2])
        b = self._to_uint16(*reply[3:5])
        return f'{self._to_uint32(a, b):x}'

    def max_value(self) -> float:
        """Get the maximum value that has been read.

        Returns
        -------
        :class:`float`
            The maximum value that has been read since the device was turn on
            or since :meth:`~.clear_max_value` was called.
        """
        return self._decode(self._get(code=7))

    def measurement_range(self) -> tuple[float, float]:
        """Get the measurement range.

        Returns
        -------
        :class:`float`
            The minimum value that the device can measure.
        :class:`float`
            The maximum value that the device can measure.
        """
        reply = self._get(code=176)
        minimum = self._decode16(*reply[3:5])
        reply = self._get(code=177)
        maximum = self._decode16(*reply[3:5])
        return minimum, maximum

    def min_value(self) -> float:
        """Get the minimum value that has been read.

        Returns
        -------
        :class:`float`
            The minimum value that has been read since the device was turn on
            or since :meth:`~.clear_min_value` was called.
        """
        return self._decode(self._get(code=6))

    def offset_correction(self) -> float:
        """Get the offset-correction value.

        The zero point (intercept in a linear calibration equation) of the
        measurement will be displaced by this value to compensate for
        deviations in the temperature probe or in the measuring device.

        Returns
        -------
        :class:`float`
            The offset-correction value.
        """
        reply = self._get(code=216)
        return self._decode16(*reply[3:5])

    def power_off_time(self) -> int:
        """Get the power-off time.

        Returns
        -------
        :class:`int`
            The number of minutes that the device will automatically power off
            as soon as this time has elapsed if no key is pressed or if no
            interface communication takes place. A value of 0 means that
            power off is disabled.
        """
        reply = self._get(code=222)
        return self._to_uint16(*reply[3:5])

    def resolution(self) -> int:
        """Get the measurement resolution.

        Returns
        -------
        :class:`int`
            The number of digits after the decimal point that is acquired for
            the measured value.
        """
        # The manual says to use code=204, however, using Wireshark to eavesdrop
        # on the GMH_Transmit(address, 204, ...) DLL call the actual code sent
        # is 0, which is the code to read the nominal value
        reply = self._get(code=0)
        return (self._invert(reply[0]) >> 3) - 15

    def scale_correction(self) -> float:
        """Get the scale-correction factor.

        The scale (slope in a linear calibration equation) of the measurement
        will be changed by this factor to compensate for deviations in the
        temperature probe or in the measuring device.

        Returns
        -------
        :class:`float`
            The scale-correction factor.
        """
        reply = self._get(code=214)
        return self._decode16(*reply[3:5])

    def set_power_off_time(self, minutes: int) -> int:
        """Set the power-off time.

        Parameters
        ----------
        minutes : :class:`int`
            The number of minutes that the device will automatically power off
            as soon as this time has elapsed if no key is pressed or if no
            interface communication takes place. A value of 0 means that
            power off is disabled.

        Returns
        -------
        :class:`int`
            The actual power-off time that the device was set to. If you set
            the power-off time to a value greater than the maximum time allowed,
            the device automatically coerces the value to be the maximum time.
        """
        # used Wireshark with the USBPcap plugin to eavesdrop on the
        # GMH_Transmit(1, 223, 0, 0.0, minutes) call of the DLL to get the
        # hex values and message lengths
        code = self._invert(223)
        self.write(bytes([self._address, 0xF4, self._crc(self._address, 0xF4),
                          code, 0x00, self._crc(code, 0x00),
                          0xFF, minutes, self._crc(0xFF, minutes)]))
        reply = self.read(size=9, decode=False)
        self._check_crc(reply)
        # do not check if reply[7]==minutes and raise an exception if not equal
        # because if, for example, minutes=121 the device will automatically
        # set the power-off time to the maximum value that it supports (120) and
        # raising an exception would be very confusing to the end user because
        # the power-off value has changed, but not to the expected value. It's
        # better to mention in the docstring that the returned value is what
        # actually happened so the end user can do their own checks.
        return reply[7]

    def status(self) -> int:
        """Get the system status.

        The status value represents a bit mask:

        +-------+-------+--------------------------+
        | Index | Value | Description              |
        +=======+=======+==========================+
        |   0   |     1 | Max. alarm               |
        +-------+-------+--------------------------+
        |   1   |     2 | Min. alarm               |
        +-------+-------+--------------------------+
        |   2   |     4 | Display range overrun    |
        +-------+-------+--------------------------+
        |   3   |     8 | Display range underrun   |
        +-------+-------+--------------------------+
        |   4   |    16 | Reserved                 |
        +-------+-------+--------------------------+
        |   5   |    32 | Reserved                 |
        +-------+-------+--------------------------+
        |   6   |    64 | Reserved                 |
        +-------+-------+--------------------------+
        |   7   |   128 | Reserved                 |
        +-------+-------+--------------------------+
        |   8   |   256 | Measuring range overrun  |
        +-------+-------+--------------------------+
        |   9   |   512 | Measuring range underrun |
        +-------+-------+--------------------------+
        |   10  |  1024 | Sensor error             |
        +-------+-------+--------------------------+
        |   11  |  2048 | Reserved                 |
        +-------+-------+--------------------------+
        |   12  |  4096 | System fault             |
        +-------+-------+--------------------------+
        |   13  |  8192 | Calculation not possible |
        +-------+-------+--------------------------+
        |   14  | 16384 | Reserved                 |
        +-------+-------+--------------------------+
        |   15  | 32768 | Low battery              |
        +-------+-------+--------------------------+

        Returns
        -------
        :class:`int`
            The system status.
        """
        reply = self._get(code=3)
        return self._to_uint16(*reply[:2])

    def unit(self) -> str:
        """Get the measurement unit.

        Returns
        -------
        :class:`str`
            The measurement unit.
        """
        reply = self._get(code=202)
        unit = self._to_uint16(*reply[3:5])
        if unit == 1:
            return '\u00B0C'
        if unit == 2:
            return '\u00B0F'
        self.raise_exception(f'Unimplemented unit ID {unit}')

    def value(self) -> float:
        """Get the current measurement value.

        Returns
        -------
        :class:`float`
            The current value.
        """
        return self._decode(self._get(code=0))
