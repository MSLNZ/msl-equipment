"""
Communicate with the EQ-99 Manager from Energetiq.
"""
from __future__ import annotations

import re

from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.exceptions import EnergetiqError
from msl.equipment.resources import register


@register(manufacturer=r'Energetiq', model=r'EQ-99(-MGR)?', flags=re.IGNORECASE)
class EQ99(ConnectionSerial):

    def __init__(self, record):
        """Communicate with the EQ-99 Manager from Energetiq.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        record.connection.properties.setdefault('baud_rate', 38400)
        super(EQ99, self).__init__(record)
        self.set_exception_class(EnergetiqError)

    def identity(self):
        """Query the instrument identification.

        Returns
        -------
        :class:`str`
            Returns the identification string for the instrument in
            the following format: *Energetiq Model SN Ver Build*
        """
        return self.query('*IDN?').rstrip()

    def reset(self):
        """Resets the instrument to factory defaults and the output is shut off.

         The unit remains in remote mode.
         """
        self._write_check('*RST')

    def get_beep(self):
        """Query whether beeps are enabled.

        Returns
        -------
        :class:`bool`
            Whether beeps are enabled.
        """
        return bool(int(self.query('BEEP?')))

    def set_beep(self, beep=2):
        """Set the beep value.

        Parameters
        ----------
        beep : :class:`int` or :class:`bool`, optional
            Causes the instrument to beep, or enables or disabled the beep
            sound for error messages and other events that generate and
            audible response. Possible values are

            * 0 or :data:`False` -- Disable the beep sound
            * 1 or :data:`True` -- Enable the beep sound
            * 2 -- Generate one beep

        """
        if beep not in [0, 1, 2, True, False]:
            self.raise_exception('Invalid beep value "{}"'.format(beep))
        self._write_check('BEEP {}'.format(beep))

    def get_brightness(self):
        """Query the display brightness.

        Returns
        -------
        :class:`int`
            Returns the value of the display brightness (between 0 and 100).
        """
        return int(self.query('BRIGHT?'))

    def set_brightness(self, brightness):
        """Set the display brightness.

        Parameters
        ----------
        brightness : :class:`int`
            Sets the display brightness level from 0 to 100 percent.
            There are only 8 brightness levels (each separated by about
            12.5 percent) and the brightness value is used to select an
            appropriate level.
        """
        self._write_check('BRIGHT {}'.format(int(brightness)))

    def delay(self, milliseconds):
        """Specify a delay to use in command processing.

        Parameters
        ----------
        milliseconds : :class:`int`
            Causes command processing to be delayed for the specified number
            of milliseconds. Valid range is from 1 to 30000 milliseconds.
        """
        if not (1 <= milliseconds <= 30000):
            self.raise_exception('Invalid delay of {} milliseconds'.format(milliseconds))
        self._write_check('DELAY {}'.format(milliseconds))

    def condition_register(self):
        """Query LDLS condition register.

        The condition register reflects the state of the instrument
        at the time the condition register is read.

        The bitmask sequence is as follows:

        +-------+-------+-------------------------+
        | Index | Value | Description             |
        +=======+=======+=========================+
        |   0   |    1  | Interlock               |
        +-------+-------+-------------------------+
        |   1   |    2  | Controller not detected |
        +-------+-------+-------------------------+
        |   2   |    4  | Controller fault        |
        +-------+-------+-------------------------+
        |   3   |    8  | Lamp fault              |
        +-------+-------+-------------------------+
        |   4   |   16  | Output on               |
        +-------+-------+-------------------------+
        |   5   |   32  | Lamp on                 |
        +-------+-------+-------------------------+
        |   6   |   64  | Laser on                |
        +-------+-------+-------------------------+
        |   7   |  128  | Laser stable            |
        +-------+-------+-------------------------+
        |   8   |  256  | Shutter open            |
        +-------+-------+-------------------------+

        Returns
        -------
        :class:`int`
            The condition register value.
        :class:`str`
            The condition register as a bitmask string. For example,
            a value of ``336`` is expressed as ``'000010101'``
            (meaning that the interlock is closed, there are no faults,
            the output is on, the lamp is off, the laser is on,
            the laser is not stable and the shutter is open).
        """
        value = int(self.query('LDLS:COND?'))
        return value, format(value, '09b')[::-1]

    def event_register(self):
        """Query LDLS event register.

        Returns the LDLS event register. The event register reflects the
        occurrence of any condition since the last time the event register
        was read. For example, if the output was turned on and then turned off,
        the Output on the bit in the condition register will be zero, but the
        same bit in the event register will be one.

        The bitmask sequence is as follows:

        +-------+-------+-------------------------+
        | Index | Value | Description             |
        +=======+=======+=========================+
        |   0   |    1  | Interlock               |
        +-------+-------+-------------------------+
        |   1   |    2  | Controller not detected |
        +-------+-------+-------------------------+
        |   2   |    4  | Controller fault        |
        +-------+-------+-------------------------+
        |   3   |    8  | Lamp fault              |
        +-------+-------+-------------------------+
        |   4   |   16  | Output on               |
        +-------+-------+-------------------------+
        |   5   |   32  | Lamp on                 |
        +-------+-------+-------------------------+
        |   6   |   64  | Laser on                |
        +-------+-------+-------------------------+
        |   7   |  128  | Laser stable            |
        +-------+-------+-------------------------+
        |   8   |  256  | Shutter open            |
        +-------+-------+-------------------------+

        Returns
        -------
        :class:`int`
            The event register value.
        :class:`str`
            The event register as a bitmask string. For example,
            a value of ``256`` is expressed as ``'000000001'``
            and ``32`` as ``'000001000'``.
        """
        value = int(self.query('LDLS:EVENT?'))
        return value, format(value, '09b')[::-1]

    def get_exposure_time(self):
        """Query the exposure time.

        Returns
        -------
        :class:`int`
            The exposure time, in milliseconds.
        """
        return int(self.query('LDLS:EXPOSURE?'))

    def set_exposure_time(self, milliseconds):
        """Set the exposure time.

        Exposure time is used when the shutter exposure mode is set to
        `Exposure mode` (see :meth:`.set_exposure_mode`). An exposure is
        triggered by a shutter button press or the shutter trigger input.

        Parameters
        ----------
        milliseconds : :class:`int`
            The exposure time, in milliseconds, from 100 to 30000 ms.
        """
        self._write_check('LDLS:EXPOSURE {}'.format(milliseconds))

    def get_exposure_mode(self):
        """Query the exposure mode.

        Returns
        -------
        :class:`int`
            The exposure mode (0=Manual, 1=Exposure).
        """
        return int(self.query('LDLS:EXPMODE?'))

    def set_exposure_mode(self, mode):
        """Set the exposure mode.

        Same as the Shutter setting in the menu.

        Parameters
        ----------
        mode : :class:`int` or :class:`bool`
            The exposure mode (0=Manual, 1=Exposure).
        """
        self._write_check('LDLS:EXPMODE {}'.format(mode))

    def get_output(self):
        """Query the output state.

        Returns
        -------
        :class:`bool`
            Whether the output is enabled.
        """
        return bool(int(self.query('LDLS:OUTPUT?')))

    def set_output(self, enable):
        """Turn the output on or off.

        Parameters
        ----------
        enable : :class:`int` or :class:`bool`
            Whether to enable the output.
        """
        self._write_check('LDLS:OUTPUT {}'.format(enable))

    def get_lamptime(self):
        """Query the lamp runtime.

        Returns
        -------
        :class:`float`
            The number of hours accumulated while the lamp was on.
        """
        return float(self.query('LDLS: LAMPTIME?'))

    def set_lamptime(self, hours):
        """Set the lamp runtime.

        Resets the runtime to the new value. Useful for resetting the runtime
        to zero when the lamp has been serviced or replaced, or when moving
        the manager to a new LDLS system.

        Parameters
        ----------
        hours : :class:`float`
            The lamp runtime, in hours, between 0 and 9999.
        """
        self._write_check('LDLS:LAMPTIME {}'.format(hours))

    def get_shutter_init(self):
        """Query the power-up shutter state.

        Returns
        -------
        :class:`int`
            The power-up shutter state.

            * 0 -- Shutter is closed on power-up
            * 1 -- Shutter is open on power-up

        """
        return int(self.query('LDLS:SHUTINIT?'))

    def set_shutter_init(self, state):
        """Set the power-up shutter state

        Parameters
        ----------
        state : :class:`int` or :class:`bool`
            Sets the initial state of the shutter on power-up of the manager

            * 0 or :data:`False` -- Shutter is closed on power-up
            * 1 or :data:`True` -- Shutter is open on power-up

        """
        self._write_check('LDLS:SHUTINIT {}'.format(state))

    def get_shutter_state(self):
        """Query the shutter state.

        Returns
        -------
        :class:`bool`
            The state of the shutter.

            * :data:`False` -- Shutter is closed
            * :data:`True` -- Shutter is open

        """
        return bool(int(self.query('LDLS:SHUTTER?')))

    def set_shutter_state(self, state):
        """Open, close, or trigger the shutter.

        A close command (state equals 0) will always close the shutter,
        regardless of exposure mode. An open command (state equals 1)
        will open the shutter if exposure mode is set to Manual, or
        trigger a shutter if exposure mode is set to Exposure.

        Parameters
        ----------
        state : :class:`int` or :class:`bool`
            The state of the shutter.

            * 0 or :data:`False` -- Close the shutter
            * 1 or :data:`True` -- Open or trigger the shutter

        """
        self._write_check('LDLS:SHUTTER {}'.format(state))

    def get_trigger_mode(self):
        """Query the trigger mode.

        Returns
        -------
        :class:`int`
            The trigger mode. See :meth:`.set_trigger_mode` for more details.
        """
        return int(self.query('LDLS:TRIGMODE?'))

    def set_trigger_mode(self, mode):
        """Set the trigger mode.

        The trigger mode controls how the shutter trigger input controls the
        operation of the shutter. For more information on trigger modes, see
        *Shutter Operation* in the *Operating the Instrument* section of the
        manual for more details.

        Parameters
        ----------
        mode : :class:`int`
            The trigger mode.

            * 0 -- Positive edge trigger
            * 1 -- Negative edge trigger
            * 2 -- Positive level trigger
            * 3 -- Negative level trigger
            * 4 -- Off (trigger disabled)

        """
        self._write_check('LDLS:TRIGMODE {}'.format(mode))

    def get_message_buffer(self):
        """Query the internal message buffer.

        Returns
        -------
        :class:`str`
            The value of the internal message buffer.
        """
        return self.query('MESSAGE?').rstrip()

    def set_message_buffer(self, message):
        """Set the message buffer.

        Parameters
        ----------
        message : :class:`str`
            Sets the internal message buffer, up to a maximum of 16 characters.
            If more than 16 characters are specified then the additional
            characters are silently ignored.
        """
        self._write_check('MESSAGE {}'.format(message))

    def get_remote_mode_error(self):
        """Query whether errors are displayed while in remote mode.

        Returns
        -------
        :class:`bool`
            Whether errors are displayed while in remote mode.
        """
        return bool(int(self.query('REMERR?')))

    def set_remote_mode_error(self, enable):
        """Set whether to display errors while in remote mode.

        This command controls if the instrument will display errors while in
        remote mode. If set to zero, then errors will not be displayed. If
        set to one, errors will be displayed. Errors will always accumulate
        in the error queue.

        Parameters
        ----------
        enable : :class:`int` or :class:`bool`
            Whether to display errors while in remote mode.

            * 0 or :data:`False` -- No not display errors in remote mode
            * 1 or :data:`True` -- Display errors in remote mode

        """
        self._write_check('REMERR {}'.format(enable))

    def serial_number(self):
        """Query the serial number of the instrument.

        Returns
        -------
        :class:`str`
            The serial number of the instrument. This is the same information
            that is part of the ``*IDN?`` query.
        """
        return self.query('SN?').rstrip()

    def get_termination(self):
        """Query response terminator.

        Returns the current response terminator setting. See
        :meth:`.set_termination` for a complete definition of
        possible return values.

        Returns
        -------
        :class:`int`
            The response terminator.
        """
        return int(self.query('TERM?'))

    def set_termination(self, value):
        """Set the response terminator character(s).

        This command controls the termination characters used for
        responses to queries.

        Parameters
        ----------
        value : :class:`int`
            The response terminator character(s)

            * 0 or 1 -- <CR><LF>
            * 2 or 3 -- <CR>
            * 4 or 5 -- <LF>
            * 6 or 7 -- no terminator

        """
        self._write_check('TERM {}'.format(value))

    def run_time(self):
        """Query run time.

        Returns
        -------
        :class:`str`
            Returns the elapsed time since the unit has been turned on.
            Format is in HH:MM:SS.ss, where HH is hours, MM is minutes,
            SS is seconds, and ss is hundredths of a second.
        """
        return self.query('TIME?').rstrip()

    def timer(self):
        """Query time since the last time this method was called.

        Returns
        -------
        :class:`str`
            Returns the elapsed time since the last time this method was
            called, or, if this is the first time calling this method
            then the time since unit has been turned on. Format is in
            HH:MM:SS.ss, where HH is hours, MM is minutes, SS is seconds,
            and ss is hundredths of a second.
        """
        return self.query('TIMER?').rstrip()

    def version(self):
        """Query the firmware version.

        Returns
        -------
        :class:`str`
            Returns the firmware version. This is the same information
            that is part of the ``*IDN?`` query.
        """
        return self.query('VER?').rstrip()

    def _write_check(self, command):
        self.write(command)
        message = self.query('ERRSTR?').rstrip()
        if message == '0':
            return
        self.raise_exception(message)
