"""
Establishes a connection to a TC Series Temperature Controller from Electron Dynamics Ltd.
"""
import re

from msl.equipment.resources import register
from msl.equipment.connection_serial import ConnectionSerial


@register(manufacturer=r'Electron Dynamics', model=r'TC\s*[M|L]', flags=re.IGNORECASE)
class TCSeries(ConnectionSerial):

    def __init__(self, record):
        """
        Establishes a connection to a TC Series Temperature Controller from Electron Dynamics Ltd.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        if not record.connection.properties:
            # then use the default connection properties
            record.connection.properties = {
                'baud_rate': 19200,
                'write_termination': None,
                'read_termination': self.CR+self.LF,
                'timeout': 10.0,
            }
        super(TCSeries, self).__init__(record)

    def _checksum(self, msg):
        return (sum(map(ord, msg)) + 1) & 0xFF

    def _send(self, command, data):
        msg = '%s%02d%s' % (command, len(data), data)
        self.write('\01%s%02X' % (msg, self._checksum(msg)))

    def _value(self, val):
        try:
            return int(val)
        except ValueError:
            try:
                return float(val)
            except ValueError:
                return val

    def _reply(self, command):
        self._send(command, '')
        reply = self.read()
        checksum = self._checksum(reply[1:-2])
        if int(reply[-2:], 16) != checksum:
            self.raise_exception("Checksum mismatch. Got %r, expect '%02X'" % (reply[-2:], checksum))
        return [self._value(item) for item in reply[4:-3].split(';')]

    def get_alarm(self):
        """Get the alarm parameters.

        Returns
        -------
        :class:`list`
            The alarm parameters. See :meth:`.set_alarm` for more details.
        """
        return self._reply('d')

    def get_control(self):
        """Get the control parameters.

        Returns
        -------
        :class:`list`
            The control parameters. See :meth:`.set_control` for more details.
        """
        return self._reply('b')

    def get_output(self):
        """Get the output parameters.

        Returns
        -------
        :class:`list`
            The output parameters. See :meth:`.set_output` for more details.
        """
        return self._reply('h')

    def get_sensor(self):
        """Get the sensor parameters.

        Returns
        -------
        :class:`list`
            The sensor parameters. See :meth:`.set_sensor` for more details.
        """
        return self._reply('f')

    def get_setpoint(self):
        """Get the setpoint parameters.

        Returns
        -------
        :class:`list`
            The setpoint parameters. See :meth:`.set_setpoint` for more details.
        """
        return self._reply('q')

    def get_status(self):
        """Get the status.

        Returns
        -------
        :class:`list`
            The status parameters.
        """
        return self._reply('j')

    # def get_test(self):
    #     """Get the test parameters.
    #
    #     This method is in the Commands manual, but it does not work.
    #
    #     Returns
    #     -------
    #     :class:`list`
    #         The alarm parameters. See :meth:`.set_test` for more details.
    #     """
    #     return self._reply('l')

    def set_alarm(self, alarm_type, minimum, maximum, ok_min, ok_max, limit_min, limit_max):
        """Set the alarm parameters.

        This corresponds to the ``c`` command in the Commands manual.

        Parameters
        ----------
        alarm_type : :class:`int`
            The alarm type. One of:

                * 0: None
                * 1: Minimum
                * 2: Maximum
                * 3: Both

        minimum : :class:`float`
            Sets the temperature below which the alarm is activated.
        maximum : :class:`float`
            Sets the temperature above which the alarm is activated.
        ok_min : :class:`float`
            Sets the lower temperature difference point from the setpoint for temperature OK.
        ok_max : :class:`float`
            Sets the higher temperature difference point from the setpoint for temperature OK.
        limit_min : :class:`float`
            Sets the temperature minimum, below which the drive output is disabled.
        limit_max : :class:`float`
            Sets the temperature maximum, above which the drive output is disabled.
        """
        if alarm_type < 0 or alarm_type > 3:
            self.raise_exception('Invalid alarm_type=%d. Must be 0, 1, 2 or 3' % alarm_type)
        data = '%d;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;' % (alarm_type, minimum, maximum,
                                                      ok_min, ok_max, limit_min, limit_max)
        self._send('c', data)

    def set_control(self, control_type, p, i, d, d_filter, dead_band, power_up_state):
        """Set the control type and the control parameters.

        This corresponds to the ``a`` command in the Commands manual.

        Parameters
        ----------
        control_type : :class:`int`
            The control type. One of:

                * 0: None
                * 1: On/Off - Output drive is only fully On (heating or cooling) or Off
                * 2: Proportional (P)
                * 3: Proportional and Integral (PI)
                * 4: Proportional, Integral and Derivative (PID)

        p : :class:`float`
            The proportional (gain) value. With proportional action, the controller output is
            proportional to the temperature error from the setpoint. The proportional terms
            sets the gain for this where: ``Output = (setpoint-actual temperature ) * proportional term``
        i : :class:`float`
            The integral value. With integral action, the controller output is proportional to
            the amount of time the error is present. Integral action eliminates offset. The integral
            term is a time unit in seconds. NB for larger effects of integration reduce the integral
            time, also for operation without integral, integral time can be set to a large number e.g. 1e6.
        d : :class:`float`
            The derivative value. With derivative action, the controller output is proportional to
            the rate of change of the measurement or error. The controller output is calculated by
            the rate of change of the measurement with time, in seconds. To increase the derivative
            action increase the derivative value. See also Derivative Filter (`d_filter`).
        d_filter : :class:`float`
            The derivative filter is a low pass filter function on the derivative value.
            This allows the filtration of noise components which are a problem with a pure
            derivative function. The filter value should be set to be between 0 and 1.
        dead_band : :class:`float`
            For use with On/Off control the dead band specifies the temperature range
            around the set point where the output is zero. For example:

                * Temperature > setpoint + dead_band (Fully Cooling)
                * Temperature < setpoint - dead_band (Fully Heating)
                * Temperature < setpoint + dead_band AND > setpoint-dead_band (Output off)

        power_up_state : :class:`int`
            This sets the temperature control state from power up. One of:

                * 0: Off
                * 1: On
                * 2: Same as the last setting prior to power off

        """
        if control_type < 0 or control_type > 4:
            self.raise_exception('Invalid control_type=%d. Must be 0, 1, 2, 3 or 4' % control_type)
        if power_up_state < 0 or power_up_state > 2:
            self.raise_exception('Invalid power_up_state=%d. Must be 0, 1 or 2' % power_up_state)
        data = '%d;%.3f;%.3f;%.3f;%.3f;%.3f;%d;' % (control_type, p, i, d, d_filter, dead_band, power_up_state)
        self._send('a', data)

    def set_output(self, polarity, minimum, maximum, frequency):
        """Set the output parameters.

        This corresponds to the ``g`` command in the Commands manual.

        Parameters
        ----------
        polarity : :class:`int`
            Sets the polarity of the output drive. One of:

                * 0: Negative
                * 1: Positive

        minimum : :class:`float`
            Sets the minimum value limit of the output. Range -100 to +100.
        maximum : :class:`float`
            Sets the maximum value limit of the output. Range -100 to +100.
        frequency : :class:`float`
            Sets the pulse-width modulation repetition frequency of the output drive.
            Range 20 to 1000 Hz.
        """
        if polarity < 0 or polarity > 1:
            self.raise_exception('Invalid polarity=%d. Must be 0 or 1' % polarity)
        if abs(minimum) > 100:
            self.raise_exception('Invalid minimum=%f. Must be between -100 and +100' % minimum)
        if abs(maximum) > 100:
            self.raise_exception('Invalid maximum=%f. Must be between -100 and +100' % maximum)
        if frequency < 20 or frequency > 1000:
            self.raise_exception('Invalid frequency=%f. Must be between 20 and 1000' % frequency)
        data = '%d;%.3f;%.3f;%.3f;' % (polarity, minimum, maximum, frequency)
        self._send('g', data)

    def set_output_drive(self, mode, value):
        """Set the output drive state and value.

        This corresponds to the ``m`` command in the Commands manual.

        Parameters
        ----------
        mode : :class:`int`
            The drive mode. Either 0 (Off) or 1 (On).
        value : :class:`int`
            Percent output.
        """
        if mode < 0 or mode > 1:
            self.raise_exception('Invalid mode=%d. Must be 0 or 1' % mode)
        data = '%d;%d;' % (mode, value)
        self._send('m', data)

    def set_sensor(self, sensor, x2, x, c, unit, averaging, rl=22000):
        """Set the sensor type and the sensor parameters.

        This corresponds to the ``e`` command in the Commands manual.

        Parameters
        ----------
        sensor : :class:`int`
            The sensor type. One of:

                * 0: Voltage
                * 1: PT100
                * 2: LM35
                * 3: LM50
                * 4: LM60
                * 5: LM61
                * 6: NTC Thermistor
                * 7: RES
                * 8: PT1000
                * 9: RTD

        x2 : :class:`float`
        x : :class:`float`
        c : :class:`float`
            The `x2`, `x` and `c` parameters are quadratic coefficients than can be used
            to convert the sensor voltage into a temperature, i.e.,
            ``temperature = (v * v * x2 ) + (v * x) + c``, where ``v`` is the measured sensor
            voltage.

            For ``NTC`` thermistors `x2` is the beta value as specified for the thermistor type,
            `x` is the resistance at 25 deg C, and, `c` is still the offset.
        unit : :class:`str`
            The temperature units. One of:

                * ``'C'``: Centigrade
                * ``'F'``: Fahrenheit
                * ``'K'``: Kelvin
                * ``'V'``: Voltage
                * ``'R'``: Resistance

        averaging : :class:`int`
            Set the averaging to be 0 (Off) or 1 (On).
        rl : :class:`float`, optional
            Used for ``NTC`` or ``RES`` sensors. This value corresponds to the RL drive resistance.
        """
        if sensor < 0 or sensor > 7:
            self.raise_exception('Invalid sensor=%d. Must be 0, 1, 2, 3, 4, 5, 6 or 7' % sensor)
        unit = unit.upper()
        if unit not in 'CFKVR':
            self.raise_exception('Invalid unit=%s. Must be C, F, K, V or R' % unit)
        data = '%d;%.3f;%.3f;%.3f;%s;%d;' % (sensor, x2, x, c, unit, int(bool(averaging)))
        if sensor == 6 or sensor == 7:
            data += '%.3f;' % rl
        self._send('e', data)

    def set_setpoint(self, method, value, pot_range, pot_offset):
        """Set the setpoint parameters.

        This corresponds to the ``i`` command in the Commands manual.

        Parameters
        ----------
        method : :class:`int`
            The temperature setpoint can be set via software or by altering the potentiometer
            on the temperature controller hardware. One of:

                * 0: Potentiometer
                * 1: Software
                * 2: Input

        value : :class:`float`
            The setpoint value.
        pot_range : :class:`float`
            The temperature range of the potentiometer.
        pot_offset : :class:`float`
            The minimum temperature point of the potentiometer.
        """
        if method < 0 or method > 2:
            self.raise_exception('Invalid method=%d. Must be 0, 1 or 2' % method)
        data = '%d;%.3f;%.3f;%.3f;' % (method, value, pot_range, pot_offset)
        self._send('i', data)

    def set_test(self, mode, arg1, arg2, arg3, arg4, arg5, arg6, arg7):
        """Set the test parameters.

        This corresponds to the ``k`` command in the Commands manual.

        Parameters
        ----------
        mode : :class:`int`
            The test mode. One of:

                * 0: Off
                * 1: Normal
                * 2: Temperature cycle
                * 3: Temperature ramp
                * 4: Auto tune

        arg1 : :class:`float`
            The maximum cycle value or the test time (in seconds).
        arg2 : :class:`float`
            The start temperature or setpoint value.
        arg3 : :class:`float`
            The end temperature or end peak test value.
        arg4 : :class:`float`
            The rate 1 or the calc PID value.
        arg5 : :class:`float`
            The rate 2 or the run PID value.
        arg6 : :class:`float`
            The time 1 or undo PID value.
        arg7 : :class:`float`
            The time 2 or auto cal value.
        """
        if mode < 0 or mode > 4:
            self.raise_exception('Invalid mode=%d. Must be 0, 1, 2, 3 or 4' % mode)
        data = '%d;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;' % (mode, arg1, arg2, arg3, arg4, arg5, arg6, arg7)
        self._send('k', data)
