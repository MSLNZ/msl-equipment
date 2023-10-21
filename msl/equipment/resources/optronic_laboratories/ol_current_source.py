"""
Communicate with a DC current source from Optronic Laboratories.
"""
from __future__ import annotations

import re
import struct
import time

from msl.equipment.connection_gpib import ConnectionGPIB
from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.constants import Interface
from msl.equipment.exceptions import OptronicLaboratoriesError
from msl.equipment.record_types import EquipmentRecord
from msl.equipment.resources import register

EOT = 0xFF
ACK = 0x06
NAK = 0x15
STX = 0x02
ETX = 0x03


class OLCurrentSource:

    def __init__(self, record: EquipmentRecord) -> None:
        """Communicate with a DC current source from Optronic Laboratories.

        .. attention::

           The connection interface must be selected (using the buttons on the
           front panel) to be either RS-232 or IEEE-488 after the Current Source
           is initially powered on. Even if this is the default power-on interface,
           it must be manually re-selected before communication will work.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for the connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'address': int, the internal address of the device [default: 1]
            'delay': float, the number of seconds to wait between a write-read transaction [default: 0.1]

        as well as the key-value pairs supported by
        :class:`~msl.equipment.connection_serial.ConnectionSerial` if using RS-232
        as the interface or by :class:`~msl.equipment.connection_gpib.ConnectionGPIB` if
        using IEEE-488 as the interface.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        :param record: A record from an :ref:`equipment-database`.
        """
        self._system_status_byte = 0
        self._options = (40, 50, 60, 70, 80, 90, 95)
        self._str_options = (60, 90, 95)

        p = record.connection.properties
        self._address = int(p.get('address', 1))
        self._delay = float(p.get('delay', 0.1))

    def _check_lamp_number(self, lamp: int) -> None:
        if lamp < 0 or lamp > 9:
            self.raise_exception(f'Invalid lamp number {lamp}')  # noqa

    def _receive(self, message: bytes) -> bytes:
        raise NotImplementedError

    def _send(self, message: bytes) -> None:
        raise NotImplementedError

    def get_current(self) -> float:
        """Get the output current."""
        self._send(b'c')
        return float(self._receive(b'c'))

    def get_option(self, lamp: int, option: int) -> str | float:
        """Get the value of a lamp configuration option.

        :param lamp: The lamp number (between 0 and 9, inclusive).

        :param option: The option type to read.
            Must be one of the following values

                * 40: Lamp Hours :math:`\\rightarrow` :class:`float`
                * 50: Recalibration interval (hours) :math:`\\rightarrow` :class:`float`
                * 60: Target units (A, V or W) :math:`\\rightarrow` :class:`str`
                * 70: Target value :math:`\\rightarrow` :class:`float`
                * 80: Current limit :math:`\\rightarrow` :class:`float`
                * 90: Lamp description text :math:`\\rightarrow` :class:`str`
                * 95: Wattage (L or H) :math:`\\rightarrow` :class:`str`

        :return: The value of the `option` that was requested.
        """
        self._check_lamp_number(lamp)

        if option not in self._options:
            self.raise_exception(f'Invalid option value {option}')  # noqa

        msg = f'Y {lamp:.0f} {option:.0f}'
        self._send(msg.encode('ascii'))
        reply = self._receive(b'Y')

        if len(reply) == 3:
            num, dt, dv = reply
        else:
            num, dt = reply[:2]
            dv = b''.join(reply[2:])

        n = int(num)
        if n != lamp:
            self.raise_exception(f'Lamp number mismatch, {n} != {lamp}')  # noqa

        t = int(dt)
        if t != option:
            self.raise_exception(f'Data type mismatch, {t} != {option}')  # noqa

        if t in self._str_options:
            return dv.decode('ascii').strip('|')
        return float(dv)

    def get_voltage(self) -> float:
        """Get the output voltage."""
        self._send(b'v')
        return float(self._receive(b'v'))

    def get_wattage(self) -> float:
        """Get the output wattage."""
        self._send(b'w')
        return float(self._receive(b'w'))

    def reset(self) -> None:
        """Reset the communication buffers."""
        self._send(b'Z')
        self._receive(b'Z')

    def select_lamp(self, lamp: int) -> None:
        """Select a lamp.

        :param lamp: The lamp number (between 0 and 9, inclusive).
        """
        self._check_lamp_number(lamp)
        msg = f'S {lamp:.0f}'.encode('ascii')

        # selecting a lamp is buggy, so try to do it twice
        try:
            self._send(msg)
            self._receive(b'S')
        except OptronicLaboratoriesError:
            self._send(msg)
            self._receive(b'S')

    def set_current(self, amps: float) -> float:
        """Set the target output current.

        :param amps: The target current, in Amps. If the value is above the
            target current limit for the presently selected lamp setup or if
            the value is less than the minimum supported current, the target
            current will not change.

        :return: The actual value of the output current after it was set.
        """
        msg = f'C {amps:.5f}'
        self._send(msg.encode('ascii'))
        return float(self._receive(b'C'))

    def set_option(self, lamp: int, option: int, value: str | float) -> None:
        """Set a value for one of the lamp configuration options.

        :param lamp: The lamp number (between 0 and 9, inclusive).

        :param option: The option type to update.
            Must be one of the following values

                * 40: Lamp Hours
                * 50: Recalibration interval (hours)
                * 60: Target units (A, V or W)
                * 70: Target value
                * 80: Current limit
                * 90: Lamp description text
                * 95: Wattage (L or H)

        :param value: The value to write for `option`.
        """
        self._check_lamp_number(lamp)
        if option not in self._options:
            self.raise_exception(f'Invalid option value {option}')  # noqa

        msg = f'X {lamp:.0f} {option:.0f} {value}'
        self._send(msg.encode('ascii'))
        self._receive(b'X')

    def set_voltage(self, volts: float) -> float:
        """Set the target output voltage.

        :param volts: The target voltage, in Volts. If the value is above the
            target voltage limit for the presently selected lamp setup or if
            the value is less than the minimum supported voltage, the target
            voltage will not change.

        :return: The actual value of the output voltage after it was set.
        """
        msg = f'V {volts:.5f}'
        self._send(msg.encode('ascii'))
        return float(self._receive(b'V'))

    def set_wattage(self, watts: float) -> float:
        """Set the target output wattage.

        :param watts: The target wattage, in Watts. If the value is above the
            target wattage limit for the presently selected lamp setup or if
            the value is less than the minimum supported wattage, the target
            wattage will not change.

        :return: The actual value of the output wattage after it was set.
        """
        msg = f'W {watts:.5f}'
        self._send(msg.encode('ascii'))
        return float(self._receive(b'W'))

    def state(self) -> bool:
        """Returns whether the output is on or off."""
        self._send(b'b')
        return self._receive(b'b') == b'1'

    @property
    def system_status_byte(self) -> int:
        """The system status byte that is returned in every reply.

        It is constructed as follows:

            * bit 7: Busy flag (the device is performing a function)
            * bit 6: Reserved
            * bit 5: Reserved
            * bit 4: Lamp status (0=off, 1=on)
            * bit 3: Reserved
            * bit 2: Reserved
            * bit 1: Seeking current (1=current is ramping)
            * bit 0: Reserved

        """
        return self._system_status_byte

    def target_info(self) -> dict[str, int | float | str]:
        """Get the target information of the currently-selected lamp.

        :return: The lamp number, target value and target unit.
            The key-value pairs are::

              {'lamp': int, 'value': float, 'unit': str}

        """
        self._send(b't')
        number, value, unit = self._receive(b't')
        return {'lamp': int(number),
                'value': float(value),
                'unit': unit.decode('ascii')}

    def turn_off(self) -> None:
        """Turn the output off."""
        self._send(b'B 0')
        self._receive(b'B')

    def turn_on(self) -> None:
        """Turn the output on."""
        self._send(b'B 1')
        self._receive(b'B')

    def zero_voltage_monitor(self) -> None:
        """Zero the voltage monitor."""
        self._send(b'D')
        self._receive(b'D')


class OLCurrentSourceASRL(OLCurrentSource, ConnectionSerial):

    def __init__(self, record):
        super(OLCurrentSourceASRL, self).__init__(record)
        super(OLCurrentSource, self).__init__(record)
        self.set_exception_class(OptronicLaboratoriesError)
        self.read_termination = struct.pack('B', ETX)
        self.write_termination = None

    @staticmethod
    def _checksum(buffer: bytes) -> bytes:
        """Convert bytes to a checksum."""
        s = sum(struct.unpack(f'{len(buffer)}B', buffer))
        return struct.pack('B', s & 0x7F)

    def _receive(self, expected: bytes, iteration: int = 0) -> bytes:
        """Receive a message."""
        time.sleep(self._delay)

        # initiate
        msg = struct.pack('BB', EOT, self._address | 0x80)
        reply = self.query(msg, size=1, decode=False)
        r = struct.unpack('B', reply)[0]
        if r != ACK:
            msg = 'The power supply does not have data to send'
            if iteration < 3:
                self.log_debug('%s, read again', msg)
                return self._receive(expected, iteration=iteration+1)
            else:
                self.raise_exception(msg)

        # read until the ETX character
        reply = self.read(decode=False)

        # read the checksum
        chk = self.read(size=1, decode=False)

        # send the ACK/NAK reply based on whether the checksums match
        if self._checksum(reply) == chk:
            self.write(struct.pack('B', ACK))
        else:
            self.write(struct.pack('B', NAK))
            self.raise_exception('The checksum is invalid')

        values = reply[1:-1].split()

        # all replies start with the command character that was sent,
        # sometimes the reply is from a previous request so read again
        if values[0] != expected:
            msg = f'Invalid reply character, {bytes(values[0])} != {expected}'
            if iteration < 3:
                self.log_debug('%s, read again', msg)
                return self._receive(expected, iteration=iteration+1)
            else:
                self.raise_exception(msg)

        # update the cached system status byte for this command
        self._system_status_byte = int(bytes(values[-1]), 16)

        data = values[1:-1]
        if len(data) == 1:
            return data[0]
        return data

    def _send(self, message: bytes) -> None:
        """Send a message."""
        # initiate
        init = struct.pack('BB', EOT, self._address)
        reply = self.query(init, size=1, decode=False)
        r = struct.unpack('B', reply)[0]
        if r != ACK:
            self.raise_exception('The power supply cannot receive data')

        # send request
        buffer = struct.pack(f'B{len(message)}sB', STX, message, ETX)
        buffer += self._checksum(buffer)
        reply = self.query(buffer, size=1, decode=False)
        r = struct.unpack('B', reply)[0]
        if r != ACK:
            self.raise_exception('The checksum is invalid')


class OLCurrentSourceGPIB(OLCurrentSource, ConnectionGPIB):

    def __init__(self, record):
        super(OLCurrentSourceGPIB, self).__init__(record)
        super(OLCurrentSource, self).__init__(record)
        self.set_exception_class(OptronicLaboratoriesError)

    def _receive(self, expected: bytes, iteration: int = 0) -> bytes:
        """Receive a message."""
        time.sleep(self._delay)

        reply = self.read(decode=False).rstrip()
        values = reply[1:-1].split()

        # all replies start with the command character that was sent,
        # sometimes the reply is from a previous request so read again
        if values[0] != expected:
            msg = f'Invalid reply character, {bytes(values[0])} != {expected}'
            if iteration < 3:
                self.log_debug('%s, read again', msg)
                return self._receive(expected, iteration=iteration+1)
            else:
                self.raise_exception(msg)

        # update the cached system status byte for this command
        self._system_status_byte = int(bytes(values[-1]), 16)

        data = values[1:-1]
        if len(data) == 1:
            return data[0]
        return data

    def _send(self, message: bytes) -> None:
        """Send a message."""
        packed = struct.pack(f'B{len(message)}sB', STX, message, ETX)
        self.write(packed)


@register(manufacturer=r'Optronic', model=r'(OL)?\s*(16|65|83)A', flags=re.IGNORECASE)
def ol_current_source_factory(record: EquipmentRecord) -> OLCurrentSourceASRL | OLCurrentSourceGPIB:
    """Initiate the connection class based on the interface type."""
    if record.connection.interface == Interface.SERIAL:
        return OLCurrentSourceASRL(record)

    if record.connection.interface == Interface.GPIB:
        return OLCurrentSourceGPIB(record)

    raise OptronicLaboratoriesError('Only ASRL or GPIB interfaces are supported')
