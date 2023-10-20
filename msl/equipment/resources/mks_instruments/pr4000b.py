"""
Flow and Pressure controller, PR4000B, from MKS Instruments.
"""
from __future__ import annotations

import re

from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.exceptions import MKSInstrumentsError
from msl.equipment.resources import register


@register(manufacturer=r'^MKS', model=r'PR4000B', flags=re.IGNORECASE)
class PR4000B(ConnectionSerial):

    ERROR_CODES = {
        '#E010': 'Syntax Error',
        '#E020': 'Failed to execute command',
        '#E001': 'Communication Error',
        '#E002': 'ADC Overflow or Underflow',
        '#E003': 'Range Error, Setpoint < 0 or out of range',
        '#W001': 'Offset > 250 mV'
    }

    UNITS = {
        0: 'ubar',
        1: 'mbar',
        2: 'bar',
        3: 'mTor',
        4: 'Torr',
        5: 'KTor',
        6: 'Pa',
        7: 'kPa',
        8: 'mH2O',
        9: 'cH2O',
        10: 'PSI',
        11: 'N/qm',
        12: 'SCCM',
        13: 'SLM',
        14: 'SCM',
        15: 'SCFH',
        16: 'SCFM',
        17: 'mA',
        18: 'V',
        19: '%',
        20: 'C'
    }

    SIGNAL_MODES = {
        0: 'METER',
        1: 'OFF',
        2: 'INDEP',
        3: 'EXTRN',
        4: 'SLAVE',
        5: 'RTD'
    }

    LIMIT_MODES = {
        0: 'SLEEP',
        1: 'LIMIT',
        2: 'BAND',
        3: 'MLIMIT',
        4: 'MBAND'
    }

    TAGS = {
        0: 'SP',
        1: 'VA',
        2: 'CH',
        3: 'FL',
        4: 'PR',
        5: 'EX'
    }

    def __init__(self, record):
        """Flow and Pressure controller, PR4000B, from MKS Instruments.

        The default settings for the RS232 connection are:

        * Baud rate = 9600
        * Data bits = 7
        * Stop bits = 1
        * Parity = ODD
        * Flow control = None

        The baud rate and parity can be changed on the controller. The data bits,
        stop bits, and flow control cannot be changed. A null modem (cross over)
        cable is required when using a USB to RS232 converter. RS485 support is
        not implemented.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        super(PR4000B, self).__init__(record)
        self.set_exception_class(MKSInstrumentsError)

    def _check(self, reply):
        """Check a reply for an error.

        Parameters
        ----------
        reply : :class:`str`
            The reply to check.

        Returns
        -------
        :class:`str`
            The reply if the there was no error, otherwise raises an exception.
        """
        if reply.startswith('#'):
            msg = self.ERROR_CODES.get(reply, 'Undefined error code')
            self.raise_exception('{}: {}'.format(reply, msg))
        return reply

    def _check_channel(self, channel):
        if channel < 1 or channel > 2:
            self.raise_exception('Invalid channel {}'.format(channel))

    def _get_index_from_value(self, string, dictionary):
        string_lower = string.lower()
        for key, value in dictionary.items():
            if value.lower() == string_lower:
                return key

    def auto_zero(self, channel):
        """Auto zero a channel

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`int`
            The offset.
        """
        self._check_channel(channel)
        return int(self.query('AZ{}'.format(channel)))

    def default(self, mode):
        """Reset to the default configuration.

        Parameters
        ----------
        mode : :class:`str`
            The mode to reset. One of ``Pressure``, ``Flow``, ``P`` or ``F`` (case insensitive).
        """
        upper = mode.upper()
        if upper not in ['P', 'F', 'PRESSURE', 'FLOW']:
            self.raise_exception('Invalid default mode {!r}, must one of: Pressure, Flow, P or F'.format(mode))
        self._check(self.query('DF,{}'.format(upper[0])))

    def displays_enable(self, display, enable):
        """Turn a display on or off.

        Parameters
        ----------
        display : :class:`int`
            The display number [1, 4].
        enable : :class:`bool`
            Whether to turn the display on, :data:`True`, or off, :data:`False`.
        """
        if display < 1 or display > 4:
            self.raise_exception('Invalid display number {}, must be between [1, 4]'.format(display))
        state = 'ON' if enable else 'OFF'
        self._check(self.query('DP{},{}'.format(display, state)))

    def displays_setup(self, display, line, tag, channel):
        """Configure a display.

        Parameters
        ----------
        display : :class:`int`
            The display number [1, 4].
        line : :class:`int`
            The line number, 1 or 2.
        tag : :class:`int` or :class:`str`
            The tag to use (0=SP, 1=VA, 2=CH, 3=FL, 4=PR, 5=EX). For example,
            setting tag to 4 or ``'PR'`` are equivalent.
        channel : :class:`int`
            The channel, either 1 or 2.
        """
        if display < 1 or display > 4:
            self.raise_exception('Invalid display number {}, must be between [1, 4]'.format(display))
        if line < 1 or line > 2:
            self.raise_exception('Invalid line number {}, must be 1 or 2'.format(line))
        self._check_channel(channel)
        if isinstance(tag, str):
            index = self._get_index_from_value(tag, self.TAGS)
            if index is None:
                self.raise_exception('Invalid tag {!r}'.format(tag))
        else:
            index = int(tag)
        self._check(self.query('DP{},{},{},{}'.format(display, line, index, channel)))

    def display_4(self, enable):
        """Whether to enable or disable display 4.

        Parameters
        ----------
        enable : :class:`bool`
            Whether to enable or disable display 4.
        """
        state = 'ON' if enable else 'OFF'
        self._check(self.query('DP4,{}'.format(state)))

    def external_input(self, channel):
        """Return the external input of a channel

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`float`
            The external input.
        """
        self._check_channel(channel)
        return float(self.query('EX{}'.format(channel)))

    def get_access_channel(self, channel):
        """Get the setpoint and the state of the valve of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`float`
            The setpoint value.
        :class:`bool`
            Whether the valve is on, :data:`True`, or off, :data:`False`.
        """
        self._check_channel(channel)
        split = self.query('?AC{}'.format(channel)).rstrip().split(',')
        return float(split[0]), split[1] == 'ON'

    def get_actual_value(self, channel):
        """Get the actual value of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`float`
            The value.
        """
        self._check_channel(channel)
        return float(self.query('AV{}'.format(channel)))

    def get_address(self):
        """Get the address.

        Returns
        -------
        :class:`int`
            The address.
        """
        return int(self.query('?AD'))

    def get_dead_band(self, channel):
        """Get the dead band of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`float`
            The dead band.
        """
        self._check_channel(channel)
        return float(self.query('?DB{}'.format(channel)))

    def get_dialog(self):
        """Get the current dialog index that is displayed.

        Returns
        -------
        :class:`int`
            The dialog index.
        """
        return int(self.query('?DG'))

    def get_display_text(self):
        """Get the display text.

        Returns
        -------
        :class:`str`
            The display text.
        """
        return self.query('?DT').rstrip()

    def get_external_input_range(self, channel):
        """Get the external input range of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`int`
            The external input range.
        """
        self._check_channel(channel)
        return int(self.query('?EI{}'.format(channel)))

    def get_external_output_range(self, channel):
        """Get the external output range of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`int`
            The external output range.
        """
        self._check_channel(channel)
        return int(self.query('?EO{}'.format(channel)))

    def get_formula_relay(self, channel):
        """Get the relay formula of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`str`
            The formula.
        """
        self._check_channel(channel)
        return self.query('?FR{}'.format(channel)).strip()

    def get_formula_temporary(self, channel):
        """Get the temporary formula of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`str`
            The formula.
        """
        self._check_channel(channel)
        return self.query('?FT{}'.format(channel)).strip()

    def get_gain(self, channel):
        """Get the gain of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`float`
            The gain.
        """
        self._check_channel(channel)
        return float(self.query('?GN{}'.format(channel)))

    def get_input_range(self, channel):
        """Get the input range of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`int`
            The input range.
        """
        self._check_channel(channel)
        return int(self.query('?IN{}'.format(channel)))

    def get_interface_mode(self):
        """Get the interface mode.

        Returns
        -------
        :class:`int`
            The interface mode.
        """
        return int(self.query('?IM'))

    def get_limit_mode(self, channel):
        """Get the limit mode of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`int`
            The index of the limit mode.
        :class:`str`
            The name of the limit mode.
        """
        self._check_channel(channel)
        mode = int(self.query('?LM{}'.format(channel)))
        return mode, self.LIMIT_MODES[mode]

    def get_linearization_point(self, channel, point):
        """Get the point in the linearization table of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        point : :class:`int`
            The point in the table [0, 10].

        Returns
        -------
        :class:`float`
            The x value.
        :class:`float`
            The y value.
        """
        self._check_channel(channel)
        if point < 0 or point > 10:
            self.raise_exception('Invalid point {}, must be between [0, 10]'.format(point))
        split = self.query('?LN{},{}'.format(channel, point)).split(',')
        return float(split[0]), float(split[1])

    def get_linearization_size(self, channel):
        """Get the size of the linearization table of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`int`
            The size of the table.
        """
        self._check_channel(channel)
        return int(self.query('?LS{}'.format(channel)))

    def get_lower_limit(self, channel):
        """Get the lower limit of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`float`
            The lower limit.
        """
        self._check_channel(channel)
        return float(self.query('?LL{}'.format(channel)))

    def get_offset(self, channel):
        """Get the offset of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`int`
            The offset.
        """
        self._check_channel(channel)
        return int(self.query('?OF{}'.format(channel)))

    def get_output_range(self, channel):
        """Get the output range of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`int`
            The output range.
        """
        self._check_channel(channel)
        return int(self.query('?OT{}'.format(channel)))

    def get_range(self, channel):
        """Get the range and unit of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`float`
            The range.
        :class:`int`
            The unit index.
        :class:`str`
            The unit name.
        """
        self._check_channel(channel)
        split = self.query('?RG{}'.format(channel)).rstrip().split(',')
        unit = int(split[1])
        return float(split[0]), unit, self.UNITS[unit]

    def get_relays(self, channel):
        """Get the relay state of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`bool`
            Whether the relay is enabled or disabled.
        """
        self._check_channel(channel)
        return self.query('?RL{}'.format(channel)).rstrip() == 'ON'

    def get_remote_mode(self):
        """Get the remote operation mode.

        Returns
        -------
        :class:`bool`
            Whether the remote operation mode is enabled, :data:`True`,
            or disabled, :data:`False`.
        """
        return self.query('?RT').rstrip() == 'ON'

    def get_resolution(self):
        """Get whether 16-bit resolution is enabled.

        Returns
        -------
        :class:`bool`
            Whether 16-bit resolution is enabled, :data:`True`, or disabled, :data:`False`.
        """
        return self.query('?RS').rstrip() == 'ON'

    def get_rtd_offset(self, channel):
        """Get the RTD offset of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`int`
            The offset.
        """
        self._check_channel(channel)
        return int(self.query('?RO{}'.format(channel)))

    def get_scale(self, channel):
        """Get the scale of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`float`
            The scale.
        """
        return float(self.query('?SC{}'.format(channel)))

    def get_setpoint(self, channel):
        """Get the setpoint of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`float`
            The setpoint.
        """
        self._check_channel(channel)
        return float(self.query('?SP{}'.format(channel)))

    def get_signal_mode(self, channel):
        """Get the signal mode of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`int`
            The index number of the signal mode.
        :class:`str`
            The name of the signal mode.
        """
        self._check_channel(channel)
        mode = int(self.query('?SM{}'.format(channel)))
        return mode, self.SIGNAL_MODES[mode]

    def get_upper_limit(self, channel):
        """Get the upper limit of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`float`
            The upper limit.
        """
        self._check_channel(channel)
        return float(self.query('?UL{}'.format(channel)))

    def get_valves(self, channel):
        """Get the state of the valve of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.

        Returns
        -------
        :class:`bool`
            Whether the valve is enabled or disabled.
        """
        self._check_channel(channel)
        return self.query('?VL{}'.format(channel)).rstrip() == 'ON'

    def identity(self):
        """Returns the identity.

        Returns
        -------
        :class:`str`
            The identity (e.g., ``PR42vvrrsssss``, where vv is the version,
            rr is the release and sssss is the serial number).
        """
        return self.query('?ID')

    def lock(self):
        """Lock setup."""
        self._check(self.query('#1'))

    def request_key(self):
        """Requests most recent key that was pressed.

        Returns
        -------
        :class:`int`
            The key that was most recently pressed.
        :class:`int`
            The number of key presses that occurred since the last time this
            method was called.
        """
        split = self.query('?KY').split(',')
        return int(split[0]), int(split[1])

    def reset_status(self):
        """Send the reset/status command."""
        self._check(self.query('RE'))

    def set_access_channel(self, channel, setpoint, valve):
        """Set the setpoint and the state of the valve for a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        setpoint : :class:`float`
            The setpoint value.
        valve : :class:`bool`
            Whether to enable or disable the valve.

        Returns
        -------
        :class:`float`
            The actual setpoint value.
        """
        self._check_channel(channel)
        state = 'ON' if valve else 'OFF'
        return float(self._check(self.query('AC{},{},{}'.format(channel, setpoint, state))))

    def set_actual_value(self, channel, setpoint):
        """Set the actual value of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        setpoint : :class:`float`
            The setpoint.

        Returns
        -------
        :class:`float`
            The actual value.
        """
        self._check_channel(channel)
        return float(self.query('AV{},{}'.format(channel, setpoint)))

    def set_address(self, address):
        """Set the address.

        Parameters
        ----------
        address : :class:`int`
            The address [0, 31].
        """
        if address < 0 or address > 31:
            self.raise_exception('Invalid address {}, must be between [0, 31]'.format(address))
        self._check(self.query('AD,{}'.format(address)))

    def set_dead_band(self, channel, band):
        """Set the dead band of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        band : :class:`float`
            The dead band [0.0% to 9.9% of full scale].
        """
        self._check_channel(channel)
        self._check(self.query('DB{},{}'.format(channel, band)))

    def set_dialog(self, index):
        """Set the display dialog.

        Parameters
        ----------
        index : :class:`int`
            The dialog index (between 0 and 29 inclusive). See Appendix D
            of the manual for more information.
        """
        if index < 0 or index > 29:
            self.raise_exception('Invalid dialog index {}, must be in the range [0, 29]'.format(index))
        self._check(self.query('DG,{}'.format(index)))

    def set_display_text(self, text, clear=True):
        """Set the display text.

        To view the text on the display you must call :meth:`.set_dialog`
        with the index equal to 3.

        Parameters
        ----------
        text : :class:`str`
            The text to display. Maximum 32 characters.
        clear : :class:`bool`, optional
            Whether to clear the current display text before setting the new text.
        """
        if len(text) > 32:
            self.raise_exception('The display text must be <= 32 characters, got {!r}'.format(text))
        if clear:
            self._check(self.query('!DT'))
        self._check(self.query('DT,{}'.format(text)))

    def set_external_input_range(self, channel, range):
        """Set the external input range of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        range : :class:`int`
            The external input range [1, 10] in Volts.
        """
        self._check_channel(channel)
        if range < 1 or range > 10:
            self.raise_exception('Invalid external input range {}'.format(range))
        self._check(self.query('EI{},{}'.format(channel, range)))

    def set_external_output_range(self, channel, range):
        """Set the external output range of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        range : :class:`int`
            The external output range [1, 10] in Volts.
        """
        self._check_channel(channel)
        if range < 1 or range > 10:
            self.raise_exception('Invalid external output range {}'.format(range))
        self._check(self.query('EO{},{}'.format(channel, range)))

    def set_formula_relay(self, channel, formula):
        """Set the relay formula of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        formula : :class:`str`
            The relay formula.
        """
        self._check_channel(channel)
        self._check(self.query('FR{},{}'.format(channel, formula)))

    def set_formula_temporary(self, channel, formula):
        """Set the temporary formula of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        formula : :class:`str`
            The temporary formula.
        """
        self._check_channel(channel)
        self._check(self.query('FT{},{}'.format(channel, formula)))

    def set_gain(self, channel, gain):
        """Set the gain of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        gain : :class:`float`
            The gain [0.001, 2.000].
        """
        self._check_channel(channel)
        self._check(self.query('GN{},{}'.format(channel, gain)))

    def set_input_range(self, channel, range):
        """Set the input range of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        range : :class:`int`
            The input range [1, 10] in Volts.
        """
        self._check_channel(channel)
        if range < 1 or range > 10:
            self.raise_exception('Invalid input range {}'.format(range))
        self._check(self.query('IN{},{}'.format(channel, range)))

    def set_interface_mode(self, mode):
        """Set the interface mode.

        Parameters
        ----------
        mode : :class:`int`
            The interface mode.
        """
        self._check(self.query('IM,{}'.format(mode)))

    def set_limit_mode(self, channel, mode):
        """Set the limit mode of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        mode : :class:`int` or :class:`str`
            The limit mode as either an index number [0, 4] or a name (e.g., ``SLEEP``).
        """
        self._check_channel(channel)
        if isinstance(mode, str):
            index = self._get_index_from_value(mode, self.LIMIT_MODES)
            if index is None:
                self.raise_exception('Invalid limit mode {!r}'.format(mode))
        else:
            index = int(mode)

        if index < 0 or index > 4:
            self.raise_exception('Invalid limit mode index {}, must be between [0, 4]'.format(index))
        self._check(self.query('LM{},{}'.format(channel, index)))

    def set_linearization_point(self, channel, point, x, y):
        """Set a point in the linearization table of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        point : :class:`int`
            The point in the table [0, 10].
        x : :class:`float`
            The x value [-5% to 100% of full scale].
        y : :class:`float`
            The y value [-5% to 100% of full scale].
        """
        self._check_channel(channel)
        if point < 0 or point > 10:
            self.raise_exception('Invalid point {}, must be between [0, 10]'.format(point))
        self._check(self.query('LN{},{},{},{}'.format(channel, point, x, y)))

    def set_linearization_size(self, channel, size):
        """Set the size of the linearization table of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        size : :class:`int`
            The size of the table.
        """
        self._check_channel(channel)
        if size < 0 or size > 10:
            self.raise_exception('Invalid size {}, must be between [0, 10]'.format(size))
        self._check(self.query('LS{},{}'.format(channel, size)))

    def set_lower_limit(self, channel, limit):
        """Set the lower limit of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        limit : :class:`float`
            The lower limit [-5% to 110% of full scale].
        """
        self._check_channel(channel)
        self._check(self.query('LL{},{}'.format(channel, limit)))

    def set_offset(self, channel, offset):
        """Set the offset of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        offset : :class:`int`
            The offset [-250, 250].
        """
        self._check_channel(channel)
        if offset < -250 or offset > 250:
            self.raise_exception('Invalid offset {}, must be between [-250, 250]'.format(offset))
        self._check(self.query('OF{},{}'.format(channel, offset)))

    def set_output_range(self, channel, range):
        """Set the output range of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        range : :class:`int`
            The output range [1, 10] in Volts.
        """
        self._check_channel(channel)
        if range < 1 or range > 10:
            self.raise_exception('Invalid output range {}'.format(range))
        self._check(self.query('OT{},{}'.format(channel, range)))

    def set_range(self, channel, range, unit):
        """Set the range and unit of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        range : :class:`float`
            The range value.
        unit : :class:`int` or :class:`str`
            The unit as either an index number [0, 20] or a name (e.g., ``kPa``).
        """
        self._check_channel(channel)
        if isinstance(unit, str):
            index = self._get_index_from_value(unit, self.UNITS)
            if index is None:
                self.raise_exception('Invalid unit {!r}'.format(unit))
        else:
            index = int(unit)

        if index < 0 or index > 20:
            self.raise_exception('Invalid unit index {}, must be between [0, 20]'.format(index))
        self._check(self.query('RG{},{},{}'.format(channel, range, index)))

    def set_relays(self, channel, enable):
        """Set the relay state of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        enable : :class:`bool`
            Whether to enable or disable the relay.
        """
        self._check_channel(channel)
        state = 'ON' if enable else 'OFF'
        self._check(self.query('RL{},{}'.format(channel, state)))

    def set_remote_mode(self, enable):
        """Set the remote operation mode to be enable or disabled.

        Parameters
        ----------
        enable : :class:`bool`
            Whether to enable or disable remote operation.
        """
        mode = 'ON' if enable else 'OFF'
        self._check(self.query('RT,{}'.format(mode)))

    def set_resolution(self, enable):
        """Set the 16-bit resolution to be enable or disabled.

        Parameters
        ----------
        enable : :class:`bool`
            Whether to enable or disable 16-bit resolution.
        """
        state = 'ON' if enable else 'OFF'
        self._check(self.query('RS,{}'.format(state)))

    def set_rtd_offset(self, channel, offset):
        """Set the RTD offset of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        offset : :class:`int`
            The RTD offset [-250, 250].
        """
        self._check_channel(channel)
        if offset < -250 or offset > 250:
            self.raise_exception('Invalid RTD offset {}, must be between [-250, 250]'.format(offset))
        self._check(self.query('RO{},{}'.format(channel, offset)))

    def set_scale(self, channel, scale):
        """Set the scale of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        scale : :class:`float`
            The scale.
        """
        self._check_channel(channel)
        self._check(self.query('SC{},{}'.format(channel, scale)))

    def set_setpoint(self, channel, setpoint):
        """Set the setpoint of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        setpoint : :class:`float`
            The setpoint.
        """
        self._check_channel(channel)
        self._check(self.query('SP{},{}'.format(channel, setpoint)))

    def set_signal_mode(self, channel, mode):
        """Set the range and unit of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        mode : :class:`int` or :class:`str`
            The signal mode as either an index number (e.g., between 0 and 5 inclusive)
             or a name (e.g., ``INDEP``).
        """
        self._check_channel(channel)
        if isinstance(mode, str):
            index = self._get_index_from_value(mode, self.SIGNAL_MODES)
            if index is None:
                self.raise_exception('Invalid signal mode {!r}'.format(mode))
        else:
            index = int(mode)

        if index < 0 or index > 5:
            self.raise_exception('Invalid signal mode index {}, must be between [0, 5]'.format(index))
        self._check(self.query('SM{},{}'.format(channel, index)))

    def set_tweak_control(self, enable):
        """Set tweak control.

        Parameters
        ----------
        enable : :class:`bool`
            Whether to switch tweak control on or off.
        """
        command = '$1' if enable else '$0'
        self._check(self.query(command))

    def set_upper_limit(self, channel, limit):
        """Set the upper limit of a particular channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        limit : :class:`float`
            The upper limit [-5% to 110% of full scale].
        """
        self._check_channel(channel)
        self._check(self.query('UL{},{}'.format(channel, limit)))

    def set_valves(self, channel, enable):
        """Set the state of the valve of a channel.

        Parameters
        ----------
        channel : :class:`int`
            The channel, either 1 or 2.
        """
        if channel == 0:
            self.raise_exception('The manual indicates that you can specify channel=0 '
                                 'to set both valves simultaneously, but that does not work')
        self._check_channel(channel)
        state = 'ON' if enable else 'OFF'
        self._check(self.query('VL{},{}'.format(channel, state)))

    def status(self):
        """Request status bits.

        Returns
        -------
        :class:`int`
            The status value.
        :class:`str`
            The binary representation of the value.
        """
        value = int(self.query('ST'))
        return value, '{:08b}'.format(value)

    def unlock(self):
        """Unlock setup."""
        self._check(self.query('#0'))
