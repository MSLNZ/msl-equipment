"""
Establishes a connection to an MX100QP, MX100TP or MX180TP DC power supply
from `Aim and Thurlby Thandar Instruments`_

.. _Aim and Thurlby Thandar Instruments: https://www.aimtti.com/
"""
import re
import time

from msl.equipment.constants import Interface
from msl.equipment.exceptions import AimTTiError
from msl.equipment.resources import register
from msl.equipment.connection_socket import ConnectionSocket
from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.connection_prologix import ConnectionPrologix

EXECUTION_ERROR_CODES = {
    0: ('OK',
        'No error has occurred since this register was last read.'),
    100: ('NumericError',
          'The parameter value sent was outside the permitted range for the command in the present circumstances.'),
    102: ('RecallError',
          'A recall of set up data has been requested but the store specified does not contain any data.'),
    103: ('CommandInvalid',
          'The command is recognised but is not valid in the current circumstances. '
          'Typical examples would be trying to change V2 directly while the outputs are '
          'in voltage tracking mode with V1 as the master.'),
    104: ('RangeChangeError',
          'An operation requiring a range change was requested but could not be completed. '
          'Typically this occurs because >0.5V was still present on output 1 and/or output 2 '
          'terminals at the time the command was executed.'),
    200: ('AccessDenied',
          'An attempt was made to change the instrument\'s settings from an interface which is '
          'locked out of write privileges by a lock held by another interface.')
}


@register(
    manufacturer=r'(Aim)?\s*[-&_]?\s*(and)?\s*T(hurlby)?\s*T(handar)?\s*I(nstruments)?',
    model=r'MX1[80]0[TQ]P',
    flags=re.IGNORECASE
)
class MXSeries(object):

    def __new__(cls, record):
        """
        Establishes a connection to an MX100QP, MX100TP or MX180TP DC power supply
        from `Aim and Thurlby Thandar Instruments`_ for different interfaces:

        * :obj:`.Interface.PROLOGIX`
        * :obj:`.Interface.SERIAL`
        * :obj:`.Interface.SOCKET`

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        interface = record.connection.interface
        if interface == Interface.SOCKET:
            base = ConnectionSocket
        elif interface == Interface.SERIAL:
            base = ConnectionSerial
        elif interface == Interface.PROLOGIX:
            base = ConnectionPrologix
        else:
            raise AimTTiError('Unsupported interface {!r}'.format(interface))

        dict_ = dict((k, v) for k, v in vars(cls).items() if not k.startswith('__'))
        type_ = type(cls.__name__, (base,), dict_)
        instance = type_(record)
        instance.set_exception_class(AimTTiError)
        return instance

    def clear(self):
        """Send the clear, ``*CLS``, command."""
        self.write('*CLS')

    def decrement_current(self, channel):
        """Decrement the current limit by step size of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        See Also
        --------
        :meth:`.set_current_step_size`
        """
        self._write_and_check('DECI{}'.format(channel))

    def decrement_voltage(self, channel, verify=True):
        """Decrement the voltage by step size of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        verify : :class:`bool`, optional
            Whether to verify that the output voltage has stabilized at
            the decremented voltage before returning to the calling program.

        See Also
        --------
        :meth:`.set_voltage_step_size`
        """
        command = 'DECV{}{}'.format(channel, 'V' if verify else '')
        self._write_and_check(command)

    def event_status_register(self, as_integer=True):
        """Read and clear the standard event status register.

        Parameters
        ----------
        as_integer : :class:`bool`, optional
            Whether to return the value as an :class:`int`.

        Returns
        -------
        :class:`int` or :class:`str`
            The event status register value. The data type depends on the
            value of `as_integer`. If a :class:`str` is returned then it
            will have a length of 8. For example,

            * '10000000' or the integer value 128
            * '00100000' or the integer value 32

        """
        value = int(self.query('*ESR?'))
        if as_integer:
            return value
        return format(value, '08b')

    def get_current(self, channel):
        """Get the output current of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        Returns
        -------
        :class:`float`
            The output current, in Amps.
        """
        reply = self._query_and_check('I{}O?'.format(channel))
        return float(reply[:-1])

    def get_current_limit(self, channel):
        """Get the current limit of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        Returns
        -------
        :class:`float`
            The current limit, in Amps.
        """
        reply = self._query_and_check('I{}?'.format(channel))
        return float(reply[2:])

    def get_current_step_size(self, channel):
        """Get the current limit step size of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        Returns
        -------
        :class:`float`
            The current limit step size, in Amps.
        """
        reply = self._query_and_check('DELTAI{}?'.format(channel))
        return float(reply[7:])

    def get_over_current_protection(self, channel):
        """Get the over-current protection trip point of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        Returns
        -------
        :class:`float` or :data:`None`
            If the trip point is enabled then returns the trip point value, in Amps.
            Returns :data:`None` if the over-current protection is disabled.
        """
        reply = self._query_and_check('OCP{}?'.format(channel))
        if reply.endswith('OFF'):
            return
        return float(reply[3:])

    def get_over_voltage_protection(self, channel):
        """Get the over-voltage protection trip point of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        Returns
        -------
        :class:`float` or :data:`None`
            If the trip point is enabled then returns the trip point value, in Volts.
            Returns :data:`None` if the over-voltage protection is disabled.
        """
        reply = self._query_and_check('OVP{}?'.format(channel))
        if reply.endswith('OFF'):
            return
        return float(reply[3:])

    def get_voltage(self, channel):
        """Get the output voltage of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        Returns
        -------
        :class:`float`
            The output voltage, in Volts.
        """
        reply = self._query_and_check('V{}O?'.format(channel))
        return float(reply[:-1])

    def get_voltage_range(self, channel):
        """Get the output voltage range index of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        Returns
        -------
        :class:`int`
            The output voltage range index. See the manual for more details.
            For example, 2 = 35V/3A.
        """
        return int(self._query_and_check('VRANGE{}?'.format(channel)))

    def get_voltage_setpoint(self, channel):
        """Get the set-point voltage of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        Returns
        -------
        :class:`float`
            The set-point voltage, in Volts.
        """
        reply = self._query_and_check('V{}?'.format(channel))
        return float(reply[2:])

    def get_voltage_step_size(self, channel):
        """Get the voltage step size of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        Returns
        -------
        :class:`float`
            The voltage step size, in Volts.
        """
        reply = self._query_and_check('DELTAV{}?'.format(channel))
        return float(reply[7:])

    def get_voltage_tracking_mode(self):
        """Get the voltage tracking mode of the unit.

        Returns
        -------
        :class:`int`
            The voltage tracking mode. See the manual for more details.
        """
        return int(self._query_and_check('CONFIG?'))

    def increment_current(self, channel):
        """Increment the current limit by step size of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        See Also
        --------
        :meth:`.set_current_step_size`
        """
        self._write_and_check('INCI{}'.format(channel))

    def increment_voltage(self, channel, verify=True):
        """Increment the voltage by step size of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        verify : :class:`bool`, optional
            Whether to verify that the output voltage has stabilized at
            the incremented voltage before returning to the calling program.

        See Also
        --------
        :meth:`.set_voltage_step_size`
        """
        command = 'INCV{}{}'.format(channel, 'V' if verify else '')
        self._write_and_check(command)

    def is_output_on(self, channel):
        """Check if the output channel is on or off.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).

        Returns
        -------
        :class:`bool`
            Whether the output channel is on (:data:`True`) or off (:data:`False`).
        """
        reply = self._query_and_check('OP{}?'.format(channel))
        return reply == '1'

    def turn_on(self, channel):
        """Turn the output channel on.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        """
        self._write_and_check('OP{} 1'.format(channel))

    def turn_on_multi(self, options=None):
        """Turn multiple output channels on (the Multi-On feature).

        Parameters
        ----------
        options : :class:`dict`, optional
            Set the Multi-On option for each output channel before setting Multi-On.
            If not specified then uses the pre-programmed options.
            If a particular output channel is not included in `options` then
            uses the pre-programmed option for that channel.
            The keys are the output channel number and the value can be :data:`False`
            (set the channel to ``NEVER``, see the manual for more details), :data:`True`
            (set the channel to ``QUICK``, see the manual for more details) or a
            delay in milliseconds (as an :class:`int`).

            Examples:

            * ``{1: False}`` :math:`\\rightarrow` channel 1 does not turn on
            * ``{2: 100}`` :math:`\\rightarrow` channel 2 has a 100-ms delay
            * ``{1: 100, 3: True}`` :math:`\\rightarrow` channel 1 has a 100-ms delay
              and channel 3 turns on immediately
            * ``{1: 100, 2: 200, 3: 300}`` :math:`\\rightarrow` channel 1 has a 100-ms delay,
              channel 2 has a 200-ms delay and channel 3 has a 300-ms delay

        See Also
        --------
        :meth:`.set_multi_on_delay`
        :meth:`.set_multi_on_action`
        """
        if options:
            if not isinstance(options, dict):
                self.raise_exception('The Multi-On options must be a dict, got {}'.format(type(options)))
            for channel, value in options.items():
                if isinstance(value, bool):
                    self.set_multi_on_action(channel, 'QUICK' if value else 'NEVER')
                else:
                    self.set_multi_on_action(channel, 'DELAY')
                    self.set_multi_on_delay(channel, value)
                    time.sleep(0.1)  # otherwise the power supply may not set the delay properly
        self._write_and_check('OPALL 1')

    def turn_off(self, channel):
        """Turn the output channel off.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        """
        self._write_and_check('OP{} 0'.format(channel))

    def turn_off_multi(self, options=None):
        """Turn multiple output channels off (the Multi-Off feature).

        Parameters
        ----------
        options : :class:`dict`, optional
            Set the Multi-Off option for each output channel before setting Multi-Off.
            If not specified then uses the pre-programmed options.
            If a particular output channel is not included in `options` then
            uses the pre-programmed option for that channel.
            The keys are the output channel number and the value can be :data:`False`
            (set the channel to ``NEVER``, see the manual for more details), :data:`True`
            (set the channel to ``QUICK``, see the manual for more details) or a
            delay in milliseconds (as an :class:`int`).

            Examples:

            * ``{1: False}`` :math:`\\rightarrow` channel 1 does not turn off
            * ``{2: 100}`` :math:`\\rightarrow` channel 2 has a 100-ms delay
            * ``{1: 100, 3: True}`` :math:`\\rightarrow` channel 1 has a 100-ms delay
              and channel 3 turns off immediately
            * ``{1: 100, 2: 200, 3: 300}`` :math:`\\rightarrow` channel 1 has a 100-ms delay,
              channel 2 has a 200-ms delay and channel 3 has a 300-ms delay

        See Also
        --------
        :meth:`.set_multi_off_delay`
        :meth:`.set_multi_off_action`
        """
        if options:
            if not isinstance(options, dict):
                self.raise_exception('The Multi-Off options must be a dict, got {}'.format(type(options)))
            for channel, value in options.items():
                if isinstance(value, bool):
                    self.set_multi_off_action(channel, 'QUICK' if value else 'NEVER')
                else:
                    self.set_multi_off_action(channel, 'DELAY')
                    self.set_multi_off_delay(channel, value)
                    time.sleep(0.1)  # otherwise the power supply may not set the delay properly
        self._write_and_check('OPALL 0')

    def recall(self, channel, index):
        """Recall the settings of the output channel from the store.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        index : :class:`int`
            The store index number, can be 0-49.

        See Also
        --------
        :meth:`.save`
        """
        self._write_and_check('RCL{} {}'.format(channel, index))

    def recall_all(self, index):
        """Recall the settings for all output channels from the store.

        Parameters
        ----------
        index : :class:`int`
            The store index number, can be 0-49.

        See Also
        --------
        :meth:`.save_all`
        """
        self._write_and_check('*SAV {}'.format(index))

    def reset(self):
        """Send the reset, ``*RST``, command."""
        self.write('*RST')

    def reset_trip(self):
        """Attempt to clear all trip conditions."""
        self.write('TRIPRST')

    def save(self, channel, index):
        """Save the present settings of the output channel to the store.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        index : :class:`int`
            The store index number, can be 0-49.

        See Also
        --------
        :meth:`.recall`
        """
        self._write_and_check('SAV{} {}'.format(channel, index))

    def save_all(self, index):
        """Save the settings of all output channels to the store.

        Parameters
        ----------
        index : :class:`int`
            The store index number, can be 0-49.

        See Also
        --------
        :meth:`.recall_all`
        """
        self._write_and_check('*RCL {}'.format(index))

    def set_current_limit(self, channel, value):
        """Set the current limit of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        value : :class:`float`
            The current limit, in Amps.
        """
        self._write_and_check('I{} {}'.format(channel, value))

    def set_current_meter_averaging(self, channel, value):
        """Set the current meter measurement averaging of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        value : :class:`str`
            Can be ``ON``, ``OFF``, ``LOW``, ``MED`` or ``HIGH``.
        """
        self._write_and_check('DAMPING{} {}'.format(channel, value))

    def set_current_step_size(self, channel, size):
        """Set the current limit step size of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        size : :class:`float`
            The current limit step size, in Amps.
        """
        self._write_and_check('DELTAI{} {}'.format(channel, size))

    def set_multi_on_action(self, channel, action):
        """Set the Multi-On action of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        action : :class:`str`
            The Multi-On action, one of ``QUICK``, ``NEVER`` or ``DELAY``.
        """
        self._write_and_check('ONACTION{} {}'.format(channel, action))

    def set_multi_on_delay(self, channel, delay):
        """Set the Multi-On delay, in milliseconds, of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        delay : :class:`int`
            The delay, in milliseconds.
        """
        self._write_and_check('ONDELAY{} {}'.format(channel, delay))

    def set_multi_off_action(self, channel, action):
        """Set the Multi-Off action of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        action : :class:`str`
            The Multi-Off action, one of ``QUICK``, ``NEVER`` or ``DELAY``.
        """
        self._write_and_check('OFFACTION{} {}'.format(channel, action))

    def set_multi_off_delay(self, channel, delay):
        """Set the Multi-Off delay, in milliseconds, of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        delay : :class:`int`
            The delay, in milliseconds.
        """
        self._write_and_check('OFFDELAY{} {}'.format(channel, delay))

    def set_over_current_protection(self, channel, enable, value=None):
        """Set the over-current protection trip point of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        enable : :class:`bool`
            Whether to enable (:data:`True`) or disable (:data:`False`)
            the over-current protection trip point.
        value : :class:`float`, optional
            If the trip point is enabled then you must specify a value, in Amps.
        """
        if enable:
            if value is None:
                self.raise_exception('Must specify the trip point value if the trip point is enabled')
            command = 'OCP{channel} ON;OCP{channel} {value}'.format(channel=channel, value=value)
        else:
            command = 'OCP{} OFF'.format(channel)
        self._write_and_check(command)

    def set_over_voltage_protection(self, channel, enable, value=None):
        """Set the over-voltage protection trip point of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        enable : :class:`bool`
            Whether to enable (:data:`True`) or disable (:data:`False`)
            the over-voltage protection trip point.
        value : :class:`float`, optional
            If the trip point is enabled then you must specify a value, in Volts.
        """
        if enable:
            if value is None:
                self.raise_exception('Must specify the trip point value if the trip point is enabled')
            command = 'OVP{channel} ON;OVP{channel} {value}'.format(channel=channel, value=value)
        else:
            command = 'OVP{} OFF'.format(channel)
        self._write_and_check(command)

    def set_voltage(self, channel, value, verify=True):
        """Set the output voltage of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        value : :class:`float`
            The value, in Volts.
        verify : :class:`bool`, optional
            Whether to verify that the output voltage has stabilized at
            `value` before returning to the calling program.
        """
        if verify:
            command = 'V{}V {}'.format(channel, value)
        else:
            command = 'V{} {}'.format(channel, value)
        self._write_and_check(command)

    def set_voltage_range(self, channel, index):
        """Set the output voltage range of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        index : :class:`int`
            The output voltage range index. See the manual for more details.
            For example, 2 = 35V/3A.
        """
        self._write_and_check('VRANGE{} {}'.format(channel, index))

    def set_voltage_step_size(self, channel, size):
        """Set the voltage step size of the output channel.

        Parameters
        ----------
        channel : :class:`int`
            The output channel. The first output channel is 1 (not 0).
        size : :class:`float`
            The voltage step size, in Volts.
        """
        self._write_and_check('DELTAV{} {}'.format(channel, size))

    def set_voltage_tracking_mode(self, mode):
        """Set the voltage tracking mode of the unit.

        Parameters
        ----------
        mode : :class:`int`
            The voltage tracking mode. See the manual for more details.
        """
        self._write_and_check('CONFIG {}'.format(mode))

    def _check_event_status_register(self, command):
        """Check the value of the standard event status register for an error.

        Parameters
        ----------
        command : :class:`str`
            The command that was sent prior to checking for an error.
        """
        status = self.event_status_register(as_integer=False)
        # Bit 7 - Power On. Set when power is first applied to the instrument.
        # Bit 1 and 6 - Not used, permanently 0.
        # Bit 0 - Operation Complete. Set in response to the *OPC command.
        bit5, bit4, bit3, bit2 = status[2:-2]
        if bit5 == '1':  # Bit 5 - Command Error
            err_type = 'CommandError'
            err_msg = 'A syntax error is detected in a command or parameter'
        elif bit4 == '1':  # Bit 4 - Execution Error
            error_code = int(self.query('EER?').rstrip())
            try:
                err_type, err_msg = EXECUTION_ERROR_CODES[error_code]
            except KeyError:
                err_type = 'UndefinedError'
                err_msg = 'The error code {} has not been defined in the Python dict'.format(error_code)
        elif bit3 == '1':  # Bit 3 - Verify Timeout Error
            err_type = 'VerifyTimeoutError'
            err_msg = 'A parameter has been set with "verify" specified ' \
                      'and the value has not been reached within 5 seconds, ' \
                      'e.g. the output voltage is slowed by a load with a large capacitance'
        elif bit2 == '1':  # Bit 2 - Query Error
            err_type = 'QueryError'
            err_msg = 'The controller has not issued commands and read ' \
                      'response messages in the correct sequence'
        else:
            return

        self.raise_exception('{}: {} -> command={!r}'.format(err_type, err_msg, command))

    def _query_and_check(self, command):
        """
        Query the command. If there is an error when querying then
        check the event status register for an error.
        """
        try:
            return self.query(command).rstrip()
        except:
            self._check_event_status_register(command)
            # if checking the event status register does not raise an exception
            # then raise the query exception
            raise

    def _write_and_check(self, command):
        """Write the command and check the event status register for an error."""
        self.write(command)
        self._check_event_status_register(command)
