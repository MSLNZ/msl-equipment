"""
Two-axis stage controller (SHOT-702) from OptoSigma.
"""
import re
import time

from msl.equipment.exceptions import OptoSigmaError
from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.resources import register


@register(manufacturer=r'Opto\s*Sigma|Sigma\s*Koki', model=r'SHOT-702')
class SHOT702(ConnectionSerial):

    def __init__(self, record):
        """Two-axis stage controller (SHOT-702) from OptoSigma.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        super(SHOT702, self).__init__(record)

        self._status_regex = re.compile(r'(-*)\s*(\d+),(-*)\s*(\d+),([XK]),([LMWK]),([BR])')
        self._speed_regex = re.compile(r'S(\d+)F(\d+)R(\d+)S(\d+)F(\d+)R(\d+)')
        self.set_exception_class(OptoSigmaError)

    def get_input_status(self):
        """Get the I/O input connector status.

        Returns
        -------
        status : :class:`int`
            Can either be 0 or 1 -- see manual.
        """
        return int(self.query('I:'))

    def get_speed(self):
        """Get the speed that each stage moves to a position.

        Returns
        -------
        :class:`dict`
            The speed of each stage. The returned value has the form::

            {
              'stage1' : (minimum, maximum, acceleration),
              'stage2' : (minimum, maximum, acceleration),
            }

        """
        values = re.match(self._speed_regex, self.query('?:DW')).groups()
        speed = dict()
        speed['stage1'] = (int(values[0]), int(values[1]), int(values[2]))
        speed['stage2'] = (int(values[3]), int(values[4]), int(values[5]))
        return speed

    def get_speed_origin(self):
        """Get the speed that each stage moves to the origin.

        Returns
        -------
        :class:`dict`
            The speed of each stage. The returned value has the form::

            {
              'stage1' : (minimum, maximum, acceleration),
              'stage2' : (minimum, maximum, acceleration),
            }

        """
        values = re.match(self._speed_regex, self.query('?:BW')).groups()
        speed = dict()
        speed['stage1'] = (int(values[0]), int(values[1]), int(values[2]))
        speed['stage2'] = (int(values[3]), int(values[4]), int(values[5]))
        return speed

    def get_steps(self):
        """Get the number of steps for each stage.

        Returns
        -------
        :class:`int`
            The number of steps for stage 1.
        :class:`int`
            The number of steps for stage 2.
        """
        values = self.query('?:SW').split(',')
        return int(values[0]), int(values[1])

    def get_travel_per_pulse(self):
        """Get the travels per pulse for each stage.

        Returns
        -------
        :class:`float`
            The travel per pulse for stage 1.
        :class:`float`
            The travel per pulse for stage 2.
        """
        values = self.query('?:PW').split(',')
        return float(values[0]), float(values[1])

    def get_version(self):
        """Get the version number.

        Returns
        -------
        :class:`str`
            The version number.
        """
        return self.query('?:V')

    def home(self, stage):
        """Move the stage(s) to the home position.

        Parameters
        ----------
        stage : :class:`int` or :class:`str`
            The stage(s) to home. Allowed values:

            * ``1`` (home stage 1),
            * ``2`` (home stage 2), or
            * ``'W'`` (home stages 1 and 2).

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        if self.query('H:{}'.format(stage)) != 'OK':
            self.raise_exception('cannot home stage {}'.format(stage))

    def is_moving(self):
        """Whether a stage is busy moving.

        Returns
        -------
        :class:`bool`
            Whether a stage is busy moving.
        """
        return self.query('!:') == 'B'

    def move(self, stage, direction):
        """Start moving the stage(s), at the minimum speed, in the specified direction.

        Parameters
        ----------
        stage : :class:`int` or :class:`str`
            The stage(s) to move. Allowed values:

            * ``1`` (start moving stage 1),
            * ``2`` (start moving stage 2), or
            * ``'W'`` (start moving stages 1 and 2).

        direction : :class:`str`
            The direction that the stage(s) should move. Allowed values are:

            * ``'+'`` or ``'-'`` (move a single stage in the specified direction)
            * ``'++'`` (move stage 1 in the + direction, stage 2 in the + direction)
            * ``'+-'`` (move stage 1 in the + direction, stage 2 in the - direction)
            * ``'-+'`` (move stage 1 in the - direction, stage 2 in the + direction)
            * ``'--'`` (move stage 1 in the - direction, stage 2 in the - direction)

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        ret = self.query('J:{}{}'.format(stage, direction))
        if ret != 'OK' or self.query('G:') != 'OK':
            self.raise_exception('cannot move stage {} in direction={}'.format(stage, direction))

    def move_absolute(self, stage, *position):
        """Move the stage(s) to the specified position.

        Examples:

        * move_absolute(1, 1000)

          - move stage 1 to position 1000 in the + direction

        * move_absolute(2, -5000)

          - move stage 2 to position 5000 in the - direction

        * move_absolute('W', 1000, -5000)

          - move stage 1 to position 1000 in the + direction, and
          - move stage 2 to position 5000 in the - direction

        Parameters
        ----------
        stage : :class:`int` or :class:`str`
            The stage(s) to move. Allowed values: ``1``, ``2``, ``'W'``.
        position : :class:`int` or :class:`tuple` of :class:`int`
            The position the stage(s) should move to.

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        self._move('A', stage, *position)

    def move_relative(self, stage, *num_pulses):
        """Move the stage(s) by a relative amount.

        Examples:

        * move_relative(1, 1000)

          - move stage 1 by 1000 pulses in the + direction

        * move_relative(2, -5000)

          - move stage 2 by 5000 pulses in the - direction

        * move_relative('W', 1000, -5000)

          - move stage 1 by 1000 pulses in the + direction, and
          - move stage 2 by 5000 pulses in the - direction

        Parameters
        ----------
        stage : :class:`int` or :class:`str`
            The stage(s) to move. Allowed values: ``1``, ``2``, ``'W'``.
        num_pulses : :class:`int` or :class:`tuple` of :class:`int`
            The number of pulses the stage(s) should move.

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        self._move('M', stage, *num_pulses)

    def set_mode(self, stage, mode):
        """Set whether the stage(s) can be moved by hand or by the motor.

        Parameters
        ----------
        stage : :class:`int` or :class:`str`
            The stage(s) to set the mode of. Allowed values:

            * ``1`` (set the mode for stage 1),
            * ``2`` (set the mode for stage 2), or
            * ``'W'`` (set the mode for stages 1 and 2).

        mode : :class:`int`
            Whether the stage(s) can be moved by hand (0) or motor (1).

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        if self.query('C:{}{}'.format(stage, mode)) != 'OK':
            self.raise_exception('cannot set stage {} to mode={}'.format(stage, mode))

    def set_origin(self, stage):
        """Set the origin of the stage(s) to its current position.

        Parameters
        ----------
        stage : :class:`int` or :class:`str`
            The stage(s) to set the home of. Allowed values:

            * ``1`` (set the home for stage 1),
            * ``2`` (set the home for stage 2), or
            * ``'W'`` (set the home for stages 1 and 2).

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        if self.query('R:{}'.format(stage)) != 'OK':
            self.raise_exception('cannot set the origin for stage {}'.format(stage))

    def set_output_status(self, status):
        """Set the I/O output status.

        Parameters
        ----------
        status : :class:`int`
            Can either be 0 or 1 -- see manual.

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        if self.query('O:{}'.format(status)) != 'OK':
            self.raise_exception('cannot set the output status to {}'.format(status))

    def set_speed(self, stage, minimum, maximum, acceleration):
        """Set the minimum, maximum and acceleration values when moving to a position.

        Examples:

        * set_speed(1, 100, 1000, 50)

          - set stage 1 to a minimum speed of 100 PPS, maximum speed of 1000 PPS
            and a 50 ms acceleration/deceleration time.

        * set_speed(2, 1000, 5000, 200)

          - set stage 2 to a minimum speed of 1000 PPS, maximum speed of 5000 PPS
            and a 200 ms acceleration/deceleration time.

        * set_speed('W', [100,1000], [1000,5000], [50,200])

          - set stage 1 to a minimum speed of 100 PPS, maximum speed of 1000 PPS
            and a 50 ms acceleration/deceleration time.
          - set stage 2 to a minimum speed of 1000 PPS, maximum speed of 5000 PPS
            and a 200 ms acceleration/deceleration time.

        Parameters
        ----------
        stage : :class:`int` or :class:`str`
            The stage(s) to set the setting for. Allowed values: ``1``, ``2``, ``'W'``.
        minimum : :class:`int` or :class:`list` of :class:`int`
            The minimum speed (allowed range 1 - 500k).
        maximum : :class:`int` or :class:`list` of :class:`int`
            The maximum speed (allowed range 1 - 500k).
        acceleration : :class:`int` or :class:`list` of :class:`int`
            The acceleration and deceleration time in milliseconds (allowed range 1 - 1000).

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        self._speed('D', stage, minimum, maximum, acceleration)

    def set_speed_origin(self, stage, minimum, maximum, acceleration):
        """Set the minimum, maximum and acceleration values when moving to the origin.

        Examples:

        * set_speed_origin(1, 100, 1000, 50)

          - set origin speed for stage 1 to a minimum speed of 100 PPS, maximum
            speed of 1000 PPS and a 50 ms acceleration/deceleration time.

        * set_speed_origin(2, 1000, 5000, 200)

          - set origin speed for stage 2 to a minimum speed of 1000 PPS, maximum
            speed of 5000 PPS and a 200 ms acceleration/deceleration time.

        * set_speed_origin('W', [100,1000], [1000,5000], [50,200])

          - set origin speed for stage 1 to a minimum speed of 100 PPS, maximum
            speed of 1000 PPS and a 50 ms acceleration/deceleration time.
          - set origin speed for stage 2 to a minimum speed of 1000 PPS, maximum
            speed of 5000 PPS and a 200 ms acceleration/deceleration time.

        Parameters
        ----------
        stage : :class:`int` or :class:`str`
            The stage(s) to set the setting for. Allowed values: ``1``, ``2``, ``'W'``.
        minimum : :class:`int` or :class:`list` of :class:`int`
            The minimum origin speed (allowed range 1 - 500k).
        maximum : :class:`int` or :class:`list` of :class:`int`
            The maximum origin speed (allowed range 1 - 500k).
        acceleration : :class:`int` or :class:`list` of :class:`int`
            The origin acceleration and deceleration time in milliseconds (allowed range 1 - 1000).

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        self._speed('V', stage, minimum, maximum, acceleration)

    def set_steps(self, stage, num_steps):
        """Set the number of steps that the stage motor will use.

        See the manual for more details -- the ``S`` command.

        Parameters
        ----------
        stage : :class:`int`
            The stage to set the steps of (must be ``1`` or ``2``).
        num_steps : :class:`int`
            The number of steps that the motor should use (must be one of
            ``1``, ``2``, ``4``, ``5``, ``8``, ``10``, ``20``, ``25``, ``40``,
            ``50``, ``80``, ``100``, ``125``, ``200``, ``250``).

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        if self.query('S:{}{}'.format(stage, num_steps)) != 'OK':
            self.raise_exception('cannot set stage {} to #steps={}'.format(stage, num_steps))

    def status(self):
        """Returns the current position and state of each stage.

        Returns
        -------
        pos1 : :class:`int`
            The current position of stage 1.
        pos2 : :class:`int`
            The current position of stage 2.
        state : :class:`str`
            The stopped state of the stage (one of ``'L'``, ``'M'``, ``'W'``, ``'K'``) --
            see the manual for more details.
        is_moving : :class:`bool`
            Whether a stage is busy moving.

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        reply = self.query('Q:')
        if reply == 'NG':  # then try again
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            return self.status()
        match = re.match(self._status_regex, reply)
        if not match:
            self.raise_exception('Invalid regex expression for the reply {!r}'.format(reply))
        negative1, position1, negative2, position2, ok, state, moving = match.groups()
        if ok != 'K':
            self.raise_exception('Error getting the status from the controller {!r}'.format(reply))
        pos1 = -int(position1) if negative1 else int(position1)
        pos2 = -int(position2) if negative2 else int(position2)
        return pos1, pos2, state, moving == 'B'

    def stop(self):
        """Immediately stop both stages from moving.

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        if self.query('L:E') != 'OK':
            self.raise_exception('cannot stop the stages')

    def stop_slowly(self, stage):
        """Slowly bring the stage(s) to a stop.

        Parameters
        ----------
        stage : :class:`int` or :class:`str`
            The stage(s) to slowly stop. Allowed values:

            * ``1`` (slowly stop stage 1),
            * ``2`` (slowly stop stage 2), or
            * ``'W'`` (slowly stop stages 1 and 2).

        Raises
        ------
        :exc:`.OptoSigmaError`
            If there was an error processing the command.
        """
        if self.query('L:{}'.format(stage)) != 'OK':
            self.raise_exception('cannot slowly stop stage {}'.format(stage))

    def wait(self, callback=None, sleep=0.05):
        """Wait for the stages to finish moving.

        This is a blocking call because it uses :func:`time.sleep`.

        Parameters
        ----------
        callback : :func:`callable`, optional
            A callable function. The function will receive 4 arguments -- the
            returned values from :meth:`.status`
        sleep : :class:`float`, optional
            The number of seconds to wait between calls to `callback`.
        """
        has_callback = callable(callback)
        while True:
            ret = self.status()
            if has_callback:
                callback(*ret)
            if not ret[3]:
                break
            time.sleep(sleep)

    def _move(self, letter, stage, *n_pulses):
        cmd = '{}:{}'.format(letter, stage)
        for val in n_pulses:
            if val < 0:
                cmd += '-P{}'.format(abs(val))
            else:
                cmd += '+P{}'.format(val)

        ret = self.query(cmd)
        if ret != 'OK' or self.query('G:') != 'OK':
            preposition = 'by' if letter == 'M' else 'to'
            if stage == 'W':
                self.raise_exception('cannot move stages {} {}'.format(preposition, n_pulses))
            else:
                self.raise_exception('cannot move stage {} {} {}'.format(stage, preposition, n_pulses[0]))

    def _speed(self, letter, stage, minimum, maximum, acceleration):
        cmd = '{}:{}'.format(letter, stage)
        if stage == 'W':
            for i in range(2):
                cmd += 'S{}F{}R{}'.format(minimum[i], maximum[i], acceleration[i])
        else:
            cmd += 'S{}F{}R{}'.format(minimum, maximum, acceleration)

        if self.query(cmd) != 'OK':
            self.raise_exception('cannot set stage {} to (min, max, acc) = '
                                 '({}, {}, {})'.format(stage, minimum, maximum, acceleration))
