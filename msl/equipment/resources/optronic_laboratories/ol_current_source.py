"""
Communicate with a DC current source from Optronic Laboratories.
"""
import re
import struct
import time

from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.exceptions import OptronicLaboratoriesError
from msl.equipment.resources import register

EOT = 0xFF
ACK = 0x06
NAK = 0x15
STX = 0x02
ETX = 0x03


@register(manufacturer=r'Optronic', model=r'(OL)?\s*(16|65|83)A', flags=re.IGNORECASE)
class OLCurrentSource(ConnectionSerial):

    def __init__(self, record):
        """Communicate with a DC current source from Optronic Laboratories.

        .. attention::

           The COM interface must be selected (using the buttons on the front panel)
           to be RS-232 after the Current Source is initially powered on. Even if
           this is the default power-on interface, it must be re-selected before
           communication will work. This is required for models with firmware
           revision 5.8, other firmware versions may be different.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for the connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'address': int, the internal address of the device [default: 1]
            'delay': float, the number of seconds to wait between send/receive commands [default: 0.05]

        as well as those key-value pairs supported by the parent
        :class:`~msl.equipment.connection_serial.ConnectionSerial` class.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        super(OLCurrentSource, self).__init__(record)
        self.read_termination = struct.pack('B', ETX)
        self.write_termination = None
        self.set_exception_class(OptronicLaboratoriesError)

        self._system_status_byte = 0
        self._types = (40, 50, 60, 70, 80, 90, 95)
        self._str_types = (60, 90, 95)

        p = record.connection.properties
        self._address = int(p.get('address', 1))

        # passing delay=self._delay as a kwarg to self.query does not appear to
        # be necessary, just a single delay between self._send and self._receive
        self._delay = float(p.get('delay', 0.05))

    def get_current(self):
        """Get the output current.

        Returns
        -------
        :class:`float`
            The value of the output current.
        """
        self._send(b'c')
        return float(self._receive(b'c'))

    def get_setup(self, lamp, typ):
        """Get the lamp setup.

        Parameters
        ----------
        lamp : :class:`int`
            The lamp number, between 0 and 9.
        typ : :class:`int`
            The type of data to read. Must be one of 40, 50, 60, 70, 80, 90, 95.

                * 40: Lamp Hours
                * 50: Recalibration interval (hours)
                * 60: Target units (A, V or W)
                * 70: Target value
                * 80: Current limit
                * 90: Lamp description text
                * 95: Wattage (L or H)

        Returns
        -------
        :class:`str` or :class:`float`
            The value of the data type that was requested.
        """
        self._check_lamp_number(lamp)

        if typ not in self._types:
            self.raise_exception('Invalid data type number {}'.format(typ))

        msg = 'Y {:.0f} {:.0f}'.format(lamp, typ)
        self._send(msg.encode('ascii'))
        reply = self._receive(b'Y')

        if len(reply) == 3:
            num, dt, dv = reply
        else:
            num, dt = reply[:2]
            dv = b''.join(reply[2:])

        n = int(num)
        if n != lamp:
            self.raise_exception('Lamp number mismatch, {} != {}'.format(n, lamp))

        t = int(dt)
        if t != typ:
            self.raise_exception('Data type mismatch, {} != {}'.format(t, typ))

        if t in self._str_types:
            return dv.decode('ascii').strip('|')

        return float(dv)

    def get_voltage(self):
        """Get the output voltage.

        Returns
        -------
        :class:`float`
            The value of the output voltage.
        """
        self._send(b'v')
        return float(self._receive(b'v'))

    def get_wattage(self):
        """Get the output wattage.

        Returns
        -------
        :class:`float`
            The value of the output wattage.
        """
        self._send(b'w')
        return float(self._receive(b'w'))

    def reset(self):
        """Reset the communication buffers."""
        self._send(b'Z')
        self._receive(b'Z')

    def select_lamp(self, number):
        """Select a lamp.

        Parameters
        ----------
        number : :class:`int`
            The lamp number to select, between 0 and 9.
        """
        self._check_lamp_number(number)
        msg = 'S {:.0f}'.format(number).encode('ascii')

        # selecting a lamp is buggy, so try to do it twice
        try:
            self._send(msg)
            self._receive(b'S')
        except OptronicLaboratoriesError:
            self._send(msg)
            self._receive(b'S')

    def set_current(self, amps):
        """Set the target output current.

        Parameters
        ----------
        amps : :class:`float`
           The target current, in Amps. If the value is above the target current
           limit for the presently selected lamp setup or if the value is less
           than the minimum supported current, the target current will not change.

        Returns
        -------
        :class:`float`
            The present value of the output current.
        """
        msg = 'C {:.5f}'.format(amps)
        self._send(msg.encode('ascii'))
        return float(self._receive(b'C'))

    def set_setup(self, lamp, typ, value):
        """Set the lamp setup.

        Parameters
        ----------
        lamp : :class:`int`
            The lamp number, between 0 and 9.
        typ : :class:`int`
            The type of data to write. Must be one of 40, 50, 60, 70, 80, 90, 95.

                * 40: Lamp Hours
                * 50: Recalibration interval (hours)
                * 60: Target units (A, V or W)
                * 70: Target value
                * 80: Current limit
                * 90: Lamp description text
                * 95: Wattage (L or H)

        value : :class:`str` or :class:`float`
            The value to write.
        """
        self._check_lamp_number(lamp)
        if typ not in self._types:
            self.raise_exception('Invalid data type number {}'.format(typ))

        msg = 'X {:.0f} {:.0f} {}'.format(lamp, typ, value)
        self._send(msg.encode('ascii'))
        self._receive(b'X')

    def set_voltage(self, volts):
        """Set the target output voltage.

        Parameters
        ----------
        volts : :class:`float`
           The target voltage, in Volts. If the value is above the target voltage
           limit for the presently selected lamp setup or if the value is less
           than the minimum supported voltage, the target voltage will not change.

        Returns
        -------
        :class:`float`
            The present value of the output voltage.
        """
        msg = 'V {:.5f}'.format(volts)
        self._send(msg.encode('ascii'))
        return float(self._receive(b'V'))

    def set_wattage(self, watts):
        """Set the target output wattage.

        Parameters
        ----------
        watts : :class:`float`
           The target wattage, in Volts. If the value is above the target wattage
           limit for the presently selected lamp setup or if the value is less
           than the minimum supported wattage, the target wattage will not change.

        Returns
        -------
        :class:`float`
            The present value of the output wattage.
        """
        msg = 'W {:.5f}'.format(watts)
        self._send(msg.encode('ascii'))
        return float(self._receive(b'W'))

    def state(self):
        """Returns whether the output is on or off.

        Returns
        -------
        :class:`bool`
            :data:`True` if the output is on, :data:`False` if the output is off.
        """
        self._send(b'b')
        return self._receive(b'b') == b'1'

    @property
    def system_status_byte(self):
        """:class:`int`: The system status byte that is returned in every reply.

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

    def target_info(self):
        """Get the target information of the currently-selected lamp.

        Returns
        -------
        :class:`dict`
            The lamp number, target value and target unit.
            The key-value pairs are::

              {'lamp': int, 'value': float, 'unit': str}

        """
        self._send(b't')
        number, value, unit = self._receive(b't')
        return {'lamp': int(number),
                'value': float(value),
                'unit': unit.decode('ascii')}

    def turn_off(self):
        """Turn the output off."""
        self._send(b'B 0')
        self._receive(b'B')

    def turn_on(self):
        """Turn the output on."""
        self._send(b'B 1')
        self._receive(b'B')

    def zero_voltage_monitor(self):
        """Zero the voltage monitor."""
        self._send(b'D')
        self._receive(b'D')

    @staticmethod
    def _checksum(buffer):
        """Convert bytes to a checksum."""
        s = sum(struct.unpack('{}B'.format(len(buffer)), buffer))
        return struct.pack('B', s & 0x7F)

    def _check_lamp_number(self, lamp):
        if lamp < 0 or lamp > 9:
            self.raise_exception('Invalid lamp number {}. '
                                 'Must be between 0 and 9'.format(lamp))

    def _receive(self, expected, iteration=0):
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

        # all replies start with the command character that was sent
        if values[0] != expected:
            msg = 'Invalid reply character, {} != {}'.format(bytes(values[0]), expected)
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

    def _send(self, message):
        """Send a message."""
        # initiate
        init = struct.pack('BB', EOT, self._address)
        reply = self.query(init, size=1, decode=False)
        r = struct.unpack('B', reply)[0]
        if r != ACK:
            self.raise_exception('The power supply cannot receive data')

        # send request
        buffer = struct.pack('B{}sB'.format(len(message)), STX, message, ETX)
        buffer += self._checksum(buffer)
        reply = self.query(buffer, size=1, decode=False)
        r = struct.unpack('B', reply)[0]
        if r != ACK:
            self.raise_exception('The checksum is invalid')
