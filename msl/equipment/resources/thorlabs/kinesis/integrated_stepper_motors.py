"""
This module provides all the functionality required to control a number 
of **Integrated Stepper Motors** including:

* Long Travel Stages (LTS150 and LTS300)
* Lab Jack (MLJ050, MLJ150)
* Cage Rotator (K10CR1)

"""
import os
from ctypes import c_short, c_int, c_uint, c_int64, c_double, byref, create_string_buffer

from msl.equipment.resources import register
from msl.equipment.resources.utils import WORD, DWORD
from msl.equipment.resources.thorlabs.kinesis.motion_control import MotionControl
from msl.equipment.resources.thorlabs.kinesis.api_functions import IntegratedStepperMotors_FCNS
from msl.equipment.resources.thorlabs.kinesis.structs import (
    TLI_HardwareInformation,
    MOT_VelocityParameters,
    MOT_HomingParameters,
    MOT_JogParameters,
    MOT_LimitSwitchParameters,
    MOT_ButtonParameters,
    MOT_PotentiometerSteps,
    MOT_PowerParameters,
)
from msl.equipment.resources.thorlabs.kinesis.enums import (
    MOT_JogModes,
    MOT_StopModes,
    MOT_TravelDirection,
    MOT_LimitSwitchModes,
    MOT_LimitSwitchSWModes,
    MOT_LimitsSoftwareApproachPolicy,
    MOT_ButtonModes,
    MOT_HomeLimitSwitchDirection,
    MOT_TravelModes,
    UnitType,
    MOT_MovementModes,
    MOT_MovementDirections,
)


@register(manufacturer=r'Thorlabs', model=r'(LTS(150|300)|MLJ(050|150)|K10CR1)')
class IntegratedStepperMotors(MotionControl):

    def __init__(self, record):
        """A wrapper around ``Thorlabs.MotionControl.IntegratedStepperMotors.dll``.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for an IntegratedStepperMotors connection supports the following key-value pairs in the
        :ref:`connections_database`::

            'device_name': str, the device name found in ThorlabsDefaultSettings.xml [default: None]

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~msl.equipment.record_types.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        super(IntegratedStepperMotors, self).__init__(
            record, IntegratedStepperMotors_FCNS, build_device_list=True
        )

    def can_home(self):
        """Can the device perform a :meth:`home`?

        Returns
        -------
        :class:`bool`
            Whether the device can be homed.
        """
        return self.sdk.ISC_CanHome(self._serial)

    def can_move_without_homing_first(self):
        """Does the device need to be :meth:`home`\'d before a move can be performed?

        Returns
        -------
        :class:`bool`
            Whether the device needs to be homed.
        """
        return self.sdk.ISC_CanMoveWithoutHomingFirst(self._serial)

    def check_connection(self):
        """Check connection.

        Returns
        -------
        :class:`bool`
            Whether the USB is listed by the FTDI controller.
        """
        return self.sdk.ISC_CheckConnection(self._serial)

    def clear_message_queue(self):
        """Clears the device message queue."""
        self.sdk.ISC_ClearMessageQueue(self._serial)

    def close(self):
        """Disconnect and close the device."""
        self.sdk.ISC_Close(self._serial)

    def disable_channel(self):
        """Disable the channel so that motor can be moved by hand.

        When disabled, power is removed from the motor and it can be freely moved.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_DisableChannel(self._serial)

    def enable_channel(self):
        """Enable channel for computer control.

        When enabled, power is applied to the motor so it is fixed in position.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_EnableChannel(self._serial)

    def enable_last_msg_timer(self, enable, last_msg_timeout):
        """Enables the last message monitoring timer.

        This can be used to determine whether communications with the device is
        still good.

        Parameters
        ----------
        enable : :class:`bool`
            :data:`True` to enable monitoring otherwise :data:`False` to disable.
        last_msg_timeout : :class:`int`
            The last message error timeout in ms. Set to 0 to disable.
        """
        return self.sdk.ISC_EnableLastMsgTimer(self._serial, enable, last_msg_timeout)

    def get_backlash(self):
        """Get the backlash distance setting (used to control hysteresis).

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The backlash distance in ``DeviceUnits`` (see manual).
        """
        return self.sdk.ISC_GetBacklash(self._serial)

    def get_bow_index(self):
        """Gets the stepper motor bow index.

        Returns
        -------
        :class:`int`
            The bow index.
        """
        return self.sdk.ISC_GetBowIndex(self._serial)

    def get_button_params(self):
        """Gets the LTS button parameters.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`.enums.MOT_ButtonModes`
            The button mode.
        :class:`int`
            The Preset position in ``DeviceUnits`` for the left button (when in preset mode).
        :class:`int`
            The Preset position in ``DeviceUnits`` for the right button (when in preset mode).
        :class:`int`
            The time that buttons need to be pressed in order to go home or to record a
            preset buttons defined position.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        mode = WORD()
        left = c_int()
        right = c_int()
        timeout = c_short()
        self.sdk.ISC_GetButtonParams(self._serial, byref(mode), byref(left), byref(right), byref(timeout))
        return MOT_ButtonModes(mode.value), left.value, right.value, timeout.value

    def get_button_params_block(self):
        """Get the button parameters.

        Returns
        -------
        :class:`.structs.MOT_ButtonParameters`
            The button parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        params = MOT_ButtonParameters()
        self.sdk.ISC_GetButtonParamsBlock(self._serial, byref(params))
        return params

    def get_calibration_file(self):
        """Get the calibration file for this motor.

        Returns
        -------
        :class:`str`
            The filename of the calibration file.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        size = 256
        filename = create_string_buffer(size)
        self.sdk.ISC_GetCalibrationFile(self._serial, filename, size)
        return filename.raw.decode('utf-8').rstrip('\x00')

    def get_device_unit_from_real_value(self, real_value, unit_type):
        """Converts a real-world value to a device value.

        Either :meth:`load_settings`, :meth:`load_named_settings` or :meth:`set_motor_params_ext`
        must be called before calling this function, otherwise the returned value will always be 0.

        Parameters
        ----------
        real_value : :class:`float`
            The real-world value.
        unit_type : :class:`.enums.UnitType`
            The unit of the real-world value.

        Returns
        -------
        :class:`int`
            The device value.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        device_unit = c_int()
        unit = self.convert_to_enum(unit_type, UnitType)
        self.sdk.ISC_GetDeviceUnitFromRealValue(self._serial, real_value, byref(device_unit), unit)
        return device_unit.value

    def get_firmware_version(self):
        """Gets version number of the device firmware.

        Returns
        -------
        :class:`str`
            The firmware version.
        """
        return self.to_version(self.sdk.ISC_GetFirmwareVersion(self._serial))

    def get_hardware_info(self):
        """Gets the hardware information from the device.

        Returns
        -------
        :class:`.structs.TLI_HardwareInformation`
            The hardware information.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        return self._get_hardware_info(self.sdk.ISC_GetHardwareInfo)

    def get_hardware_info_block(self):
        """Gets the hardware information in a block.

        Returns
        -------
        :class:`.structs.TLI_HardwareInformation`
            The hardware information.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        info = TLI_HardwareInformation()
        self.sdk.ISC_GetHardwareInfoBlock(self._serial, byref(info))
        return info

    def get_homing_params_block(self):
        """Get the homing parameters.

        Returns
        -------
        :class:`.structs.MOT_HomingParameters`
            The homing parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        params = MOT_HomingParameters()
        self.sdk.ISC_GetHomingParamsBlock(self._serial, byref(params))
        return params

    def get_homing_velocity(self):
        """Gets the homing velocity.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The homing velocity in ``DeviceUnits`` (see manual).
        """
        return self.sdk.ISC_GetHomingVelocity(self._serial)

    def get_jog_mode(self):
        """Gets the jog mode.

        Returns
        -------
        :class:`.enums.MOT_JogModes`
            The jog mode.
        :class:`.enums.MOT_StopModes`
            The stop mode.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        mode = c_short()
        stop_mode = c_short()
        self.sdk.ISC_GetJogMode(self._serial, byref(mode), byref(stop_mode))
        return MOT_JogModes(mode.value), MOT_StopModes(stop_mode.value)

    def get_jog_params_block(self):
        """Get the jog parameters.

        Returns
        -------
        :class:`.structs.MOT_JogParameters`
            The jog parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        params = MOT_JogParameters()
        self.sdk.ISC_GetJogParamsBlock(self._serial, byref(params))
        return params

    def get_jog_step_size(self):
        """Gets the distance to move when jogging.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The step size in ``DeviceUnits`` (see manual).
        """
        return self.sdk.ISC_GetJogStepSize(self._serial)

    def get_jog_vel_params(self):
        """Gets the jog velocity parameters.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The maximum velocity in ``DeviceUnits`` (see manual).
        :class:`int`
            The acceleration in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        acceleration = c_int()
        max_velocity = c_int()
        self.sdk.ISC_GetJogVelParams(self._serial, byref(acceleration), byref(max_velocity))
        return max_velocity.value, acceleration.value

    def get_led_switches(self):
        """Get the LED indicator bits on the device.

        Returns
        -------
        :class:`int`
            Sum of: 8 to indicate moving 2 to indicate end of track and 1 to
            flash on identify command.
        """
        return self.sdk.ISC_GetLEDswitches(self._serial)

    def get_limit_switch_params(self):
        """ Gets the limit switch parameters.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`.enums.MOT_LimitSwitchModes`
            The clockwise hardware limit mode.
        :class:`.enums.MOT_LimitSwitchModes`
            The anticlockwise hardware limit mode.
        :class:`int`
            The position of the clockwise software limit in ``DeviceUnits`` (see manual).
        :class:`int`
            The position of the anticlockwise software limit in ``DeviceUnits`` (see manual).
        :class:`.enums.MOT_LimitSwitchSWModes`
            The soft limit mode.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        cw_lim = WORD()
        ccw_lim = WORD()
        cw_pos = c_uint()
        ccw_pos = c_uint()
        soft = WORD()
        self.sdk.ISC_GetLimitSwitchParams(self._serial, byref(cw_lim), byref(ccw_lim),
                                          byref(cw_pos), byref(ccw_pos), byref(soft))
        try:
            cw_mode = MOT_LimitSwitchModes(cw_lim.value)
        except ValueError:
            cw_mode = MOT_LimitSwitchModes(cw_lim.value | 0x0080)
        try:
            ccw_mode = MOT_LimitSwitchModes(ccw_lim.value)
        except ValueError:
            ccw_mode = MOT_LimitSwitchModes(ccw_lim.value | 0x0080)
        try:
            s_mode = MOT_LimitSwitchSWModes(soft.value)
        except ValueError:
            s_mode = MOT_LimitSwitchSWModes(soft.value | 0x0080)
        return cw_mode, ccw_mode, cw_pos.value, ccw_pos.value, s_mode

    def get_limit_switch_params_block(self):
        """Get the limit switch parameters.

        Returns
        -------
        :class:`.structs.MOT_LimitSwitchParameters`
            The limit switch parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        params = MOT_LimitSwitchParameters()
        self.sdk.ISC_GetLimitSwitchParamsBlock(self._serial, byref(params))
        return params

    def get_motor_params(self):
        """Gets the motor stage parameters.

        Deprecated: calls :meth:`get_motor_params_ext`
        """
        return self.get_motor_params_ext()

    def get_motor_params_ext(self):
        """Gets the motor stage parameters.

        These parameters, when combined define the stage motion in terms of
        ``RealWorldUnits`` [millimeters or degrees]. The real-world unit
        is defined from ``steps_per_rev * gear_box_ratio / pitch``.

        Returns
        -------
        class`float`
            The steps per revolution.
        :class:`float`
            The gear box ratio.
        :class:`float`
            The pitch.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        steps_per_rev = c_double()
        gear_box_ratio = c_double()
        pitch = c_double()
        self.sdk.ISC_GetMotorParamsExt(self._serial, byref(steps_per_rev), byref(gear_box_ratio), byref(pitch))
        return steps_per_rev.value, gear_box_ratio.value, pitch.value

    def get_motor_travel_limits(self):
        """Gets the motor stage min and max position.

        Returns
        -------
        :class:`float`
            The minimum position in ``RealWorldUnits`` [millimeters or degrees].
        :class:`float`
            The maximum position in ``RealWorldUnits`` [millimeters or degrees].

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        min_position = c_double()
        max_position = c_double()
        self.sdk.ISC_GetMotorTravelLimits(self._serial, byref(min_position), byref(max_position))
        return min_position.value, max_position.value

    def get_motor_travel_mode(self):
        """Get the motor travel mode.

        Returns
        -------
        :class:`.enums.MOT_TravelModes`
            The travel mode.
        """
        return MOT_TravelModes(self.sdk.ISC_GetMotorTravelMode(self._serial))

    def get_motor_velocity_limits(self):
        """Gets the motor stage maximum velocity and acceleration.

        Returns
        -------
        :class:`float`
            The maximum velocity in ``RealWorldUnits`` [millimeters or degrees].
        :class:`float`
            The maximum acceleration in ``RealWorldUnits`` [millimeters or degrees].

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        max_velocity = c_double()
        max_acceleration = c_double()
        self.sdk.ISC_GetMotorVelocityLimits(self._serial, byref(max_velocity), byref(max_acceleration))
        return max_velocity.value, max_acceleration.value

    def get_move_absolute_position(self):
        """Gets the move absolute position.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The move absolute position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.ISC_GetMoveAbsolutePosition(self._serial)

    def get_move_relative_distance(self):
        """Gets the move relative distance.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The move relative position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.ISC_GetMoveRelativeDistance(self._serial)

    def get_next_message(self):
        """Get the next Message Queue item. See :mod:`.messages`.

        Returns
        -------
        :class:`int`
            The message type.
        :class:`int`
            The message ID.
        :class:`int`
            The message data.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        message_type = WORD()
        message_id = WORD()
        message_data = DWORD()
        self.sdk.ISC_GetNextMessage(self._serial, byref(message_type), byref(message_id), byref(message_data))
        return message_type.value, message_id.value, message_data.value

    def get_number_positions(self):
        """Get the number of positions.

        This function will get the maximum position reachable by the device.
        The motor may need to be set to its :meth:`home` position before this
        parameter can be used.

        Returns
        -------
        :class:`int`
            The number of positions.
        """
        return self.sdk.ISC_GetNumberPositions(self._serial)

    def get_position(self):
        """Get the current position.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        index : :class:`int`
            The position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.ISC_GetPosition(self._serial)

    def get_position_counter(self):
        """Get the position counter.

        The position counter is identical to the position parameter.
        The position counter is set to zero when homing is complete.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The position counter in ``DeviceUnits`` (see manual).
        """
        return self.sdk.ISC_GetPositionCounter(self._serial)

    def get_potentiometer_params(self, index):
        """Gets the potentiometer parameters for the LTS.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        index : :class:`int`
            The potentiometer index to be read.

        Returns
        -------
        :class:`int`
            The potentiometer threshold, range 0 to 127.
        :class:`int`
            The velocity in ``DeviceUnits`` for the current potentiometer threshold.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        threshold = c_int()
        velocity = c_int()
        self.sdk.ISC_GetPotentiometerParams(self._serial, index, byref(threshold), byref(velocity))
        return threshold.value, velocity.value

    def get_potentiometer_params_block(self):
        """Get the potentiometer parameters.

        Returns
        -------
        :class:`.structs.MOT_PotentiometerSteps`
            The potentiometer parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        params = MOT_PotentiometerSteps()
        self.sdk.ISC_GetPotentiometerParamsBlock(self._serial, byref(params))
        return params

    def get_power_params(self):
        """Gets the power parameters for the stepper motor.

        Returns
        -------
        :class:`.structs.MOT_PowerParameters`
            The power parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        params = MOT_PowerParameters()
        self.sdk.ISC_GetPowerParams(self._serial, byref(params))
        return params

    def get_real_value_from_device_unit(self, device_value, unit_type):
        """Converts a device value to a real-world value.

        Either :meth:`load_settings`, :meth:`load_named_settings` or :meth:`set_motor_params_ext`
        must be called before calling this function, otherwise the returned value will always be 0.

        Parameters
        ----------
        device_value : :class:`int`
            The device value.
        unit_type : :class:`.enums.UnitType`
            The unit of the device value.

        Returns
        -------
        :class:`float`
            The real-world value.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        real_unit = c_double()
        unit = self.convert_to_enum(unit_type, UnitType)
        self.sdk.ISC_GetRealValueFromDeviceUnit(self._serial, device_value, byref(real_unit), unit)
        return real_unit.value

    def get_soft_limit_mode(self):
        """Gets the software limits mode.

        Returns
        -------
        :class:`.enums.MOT_LimitsSoftwareApproachPolicy`
            The software limits mode.
        """
        return MOT_LimitsSoftwareApproachPolicy(self.sdk.ISC_GetSoftLimitMode(self._serial))

    def get_software_version(self):
        """Gets version number of the device software.

        Returns
        -------
        :class:`str`
            The device software version.
        """
        return self.to_version(self.sdk.ISC_GetSoftwareVersion(self._serial))

    def get_stage_axis_max_pos(self):
        """Gets the LTS Motor maximum stage position.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The maximum position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.ISC_GetStageAxisMaxPos(self._serial)

    def get_stage_axis_min_pos(self):
        """Gets the LTS Motor minimum stage position.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The minimum position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.ISC_GetStageAxisMinPos(self._serial)

    def get_status_bits(self):
        """Get the current status bits.

        This returns the latest status bits received from the device.
        To get new status bits, use :meth:`request_status_bits` or use
        :meth:`request_status` or use the polling function, :meth:`start_polling`.

        Returns
        -------
        :class:`int`
            The status bits from the device.
        """
        return self.sdk.ISC_GetStatusBits(self._serial)

    def get_trigger_switches(self):
        """Gets the trigger switch bits.

        Returns
        -------
        :class:`int`
            8 bits indicating action on trigger input and events to trigger
            electronic output.
        """
        return self.sdk.ISC_GetTriggerSwitches(self._serial)

    def get_vel_params(self):
        """Gets the move velocity parameters.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        max_velocity : :class:`int`
            The maximum velocity in ``DeviceUnits`` (see manual).
        acceleration : :class:`int`
            The acceleration in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        acceleration = c_int()
        max_velocity = c_int()
        self.sdk.ISC_GetVelParams(self._serial, byref(acceleration), byref(max_velocity))
        return max_velocity.value, acceleration.value

    def get_vel_params_block(self):
        """Get the move velocity parameters.

        Returns
        -------
        :class:`.structs.MOT_VelocityParameters`
            The velocity parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        params = MOT_VelocityParameters()
        self.sdk.ISC_GetVelParamsBlock(self._serial, byref(params))
        return params

    def has_last_msg_timer_overrun(self):
        """Queries if the time since the last message has exceeded the
        ``lastMsgTimeout`` set by :meth:`.enable_last_msg_timer`.

        This can be used to determine whether communications with the device is
        still good.

        Returns
        -------
        :class:`bool`
            :data:`True` if last message timer has elapsed, :data:`False` if monitoring is
            not enabled or if time of last message received is less than ``lastMsgTimeout``.
        """
        return self.sdk.ISC_HasLastMsgTimerOverrun(self._serial)

    def home(self):
        """Home the device.

        Homing the device will set the device to a known state and determine
        the home position.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_Home(self._serial)

    def identify(self):
        """Sends a command to the device to make it identify itself.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_Identify(self._serial)

    def is_calibration_active(self):
        """Is a calibration file active for this motor?

        Returns
        -------
        :class:`bool`
            Whether a calibration file is active.
        """
        return self.sdk.ISC_IsCalibrationActive(self._serial)

    def load_settings(self):
        """Update device with stored settings.

        The settings are read from ``ThorlabsDefaultSettings.xml``, which
        gets created when the Kinesis software is installed.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_LoadSettings(self._serial)

    def load_named_settings(self, settings_name):
        """Update device with named settings.

        Parameters
        ----------
        settings_name : :class:`str`
            The name of the device to load the settings for. Examples for the value
            of `setting_name` can be found in `ThorlabsDefaultSettings.xml``, which
            gets created when the Kinesis software is installed.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_LoadNamedSettings(self._serial, settings_name.encode())

    def message_queue_size(self):
        """Gets the size of the message queue.

        Returns
        -------
        :class:`int`
            The number of messages in the queue.
        """
        return self.sdk.ISC_MessageQueueSize(self._serial)

    def move_absolute(self):
        """Moves the device to the position defined in :meth:`set_move_absolute_position`.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_MoveAbsolute(self._serial)

    def move_at_velocity(self, direction):
        """Start moving at the current velocity in the specified direction.

        Parameters
        ----------
        direction : :class:`.enums.MOT_TravelDirection`
            The required direction of travel as a :class:`.enums.MOT_TravelDirection`
            enum value or member name.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        direction_ = self.convert_to_enum(direction, MOT_TravelDirection, prefix='MOT_')
        self.sdk.ISC_MoveAtVelocity(self._serial, direction_)

    def move_jog(self, jog_direction):
        """Perform a jog.

        Parameters
        ----------
        jog_direction : :class:`.enums.MOT_TravelDirection`
            The jog direction as a :class:`.enums.MOT_TravelDirection` enum value
            or member name.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        direction = self.convert_to_enum(jog_direction, MOT_TravelDirection, prefix='MOT_')
        self.sdk.ISC_MoveJog(self._serial, direction)

    def move_relative(self, displacement):
        """Move the motor by a relative amount.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        displacement : :class:`int`
            Signed displacement in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_MoveRelative(self._serial, displacement)

    def move_relative_distance(self):
        """Moves the device by a relative distance defined by :meth:`set_move_relative_distance`.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_MoveRelativeDistance(self._serial)

    def move_to_position(self, index):
        """Move the device to the specified position (index).

        The motor may need to be set to its :meth:`home` position before a
        position can be set.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        index : :class:`int`
            The position in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_MoveToPosition(self._serial, index)

    def needs_homing(self):
        """Does the device need to be :meth:`home`\'d before a move can be performed?

        Deprecated: calls :meth:`can_move_without_homing_first` instead.

        Returns
        -------
        :class:`bool`
            Whether the device needs to be homed.
        """
        return self.can_move_without_homing_first()

    def open(self):
        """Open the device for communication.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_Open(self._serial)

    def persist_settings(self):
        """Persist the devices current settings.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_PersistSettings(self._serial)

    def polling_duration(self):
        """Gets the polling loop duration.

        Returns
        -------
        :class:`int`
            The time between polls in milliseconds or 0 if polling is not active.
        """
        return self.sdk.ISC_PollingDuration(self._serial)

    def register_message_callback(self, callback):
        """Registers a callback on the message queue.

        Parameters
        ----------
        callback : :class:`~msl.equipment.resources.thorlabs.kinesis.callbacks.MotionControlCallback`
            A function to be called whenever messages are received.
        """
        self.sdk.ISC_RegisterMessageCallback(self._serial, callback)

    def request_backlash(self):
        """Requests the backlash.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestBacklash(self._serial)

    def request_bow_index(self):
        """Requests the stepper motor bow index.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestBowIndex(self._serial)

    def request_button_params(self):
        """Requests the LTS button parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestButtonParams(self._serial)

    def request_homing_params(self):
        """Requests the homing parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestHomingParams(self._serial)

    def request_jog_params(self):
        """Requests the jog parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestJogParams(self._serial)

    def request_limit_switch_params(self):
        """Requests the limit switch parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestLimitSwitchParams(self._serial)

    def request_move_absolute_position(self):
        """Requests the position of next absolute move.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestMoveAbsolutePosition(self._serial)

    def request_move_relative_distance(self):
        """Requests the relative move distance.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestMoveRelativeDistance(self._serial)

    def request_position(self):
        """Requests the current position.

        This needs to be called to get the device to send its current position.
        Note, this is called automatically if ``Polling`` is enabled for the device
        using :meth:`start_polling`.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestPosition(self._serial)

    def request_potentiometer_params(self):
        """Requests the potentiometer parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestPotentiometerParams(self._serial)

    def request_power_params(self):
        """Requests the power parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestPowerParams(self._serial)

    def request_settings(self):
        """Requests that all settings are downloaded from the device.

        This function requests that the device upload all its settings to the DLL.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestSettings(self._serial)

    def request_status(self):
        """Request position and status bits.

        This needs to be called to get the device to send it's current status.
        Note, this is called automatically if ``Polling`` is enabled for the device
        using :meth:`start_polling`.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestStatus(self._serial)

    def request_status_bits(self):
        """Request the status bits which identify the current motor state.

        This needs to be called to get the device to send its current status bits.
        Note, this is called automatically if ``Polling`` is enabled for the device
        using :meth:`start_polling`.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestStatusBits(self._serial)

    def request_trigger_switches(self):
        """Requests the trigger switch bits.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestTriggerSwitches(self._serial)

    def request_vel_params(self):
        """Requests the velocity parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_RequestVelParams(self._serial)

    def reset_rotation_modes(self):
        """Reset the rotation modes for a rotational device.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_ResetRotationModes(self._serial)

    def reset_stage_to_defaults(self):
        """Reset the stage settings to defaults.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_ResetStageToDefaults(self._serial)

    def set_backlash(self, distance):
        """Sets the backlash distance (used to control hysteresis).

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        distance : :class:`int`
            The backlash distance in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetBacklash(self._serial, distance)

    def set_bow_index(self, bow_index):
        """Sets the stepper motor bow index.

        Parameters
        ----------
        bow_index : :class:`int`
            The bow index.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetBowIndex(self._serial, bow_index)

    def set_button_params(self, button_mode, left_button_position, right_button_position):
        """Sets the LTS button parameters.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        button_mode : :class:`.enums.MOT_ButtonModes`
            The button mode as a :class:`.enums.MOT_ButtonModes` enum value or member name.
        left_button_position : :class:`int`
            The Preset position in ``DeviceUnits`` for the left button (when in preset mode).
        right_button_position : :class:`int`
            The Preset position in ``DeviceUnits`` for the right button (when in preset mode).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetButtonParams(self._serial, button_mode, left_button_position, right_button_position)

    def set_button_params_block(self, mode, left_button, right_button, timeout):
        """Set the button parameters.

        Parameters
        ----------
        mode : :class:`.enums.MOT_ButtonModes`
            The mode of operation of the device buttons as a :class:`.enums.MOT_ButtonModes`
            enum value or member name.
        left_button : :class:`int`
            Position in encoder counts to go to when left button is pressed.
        right_button : :class:`int`
            Position in encoder counts to go to when right button is pressed.
        timeout : :class:`int`
            The Time a button needs to be held down for to record the position as a preset.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        params = MOT_ButtonParameters()
        params.buttonMode = self.convert_to_enum(mode, MOT_ButtonModes, prefix='MOT_')
        params.leftButtonPosition = left_button
        params.rightButtonPosition = right_button
        params.timeout = timeout
        params.unused = 0
        self.sdk.ISC_SetButtonParamsBlock(self._serial, byref(params))

    def set_calibration_file(self, path, enabled):
        """Set the calibration file for this motor.

        Parameters
        ----------
        path : :class:`str`
            The path to a calibration file to load.
        enabled : :class:`bool`
            :data:`True` to enable, :data:`False` to disable.

        Raises
        ------
        IOError
            If the `path` does not exist.
        """
        if not os.path.isfile(path):
            raise IOError('Cannot find {}'.format(path))
        self.sdk.ISC_SetCalibrationFile(self._serial, path.encode('utf-8'), enabled)

    def set_direction(self, reverse):
        """Sets the motor direction sense.

        This function is used because some actuators use have directions of motion
        reversed. This parameter will tell the system to reverse the direction sense
        when moving, jogging etc.

        Parameters
        ----------
        reverse : :class:`bool`
            If :data:`True` then directions will be swapped on these moves.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetDirection(self._serial, reverse)

    def set_homing_params_block(self, direction, limit, velocity, offset):
        """Set the homing parameters.

        Parameters
        ----------
        direction : :class:`.enums.MOT_TravelDirection`
            The Homing direction sense as a :class:`.enums.MOT_TravelDirection`
            enum value or member name.
        limit : :class:`.enums.MOT_HomeLimitSwitchDirection`
            The limit switch direction as a :class:`.enums.MOT_HomeLimitSwitchDirection`
            enum value or member name.
        velocity : :class:`int`
            The velocity in small indivisible units.
        offset : :class:`int`
            Distance of home from limit in small indivisible units.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        params = MOT_HomingParameters()
        params.direction = self.convert_to_enum(direction, MOT_TravelDirection, prefix='MOT_')
        params.limitSwitch = self.convert_to_enum(limit, MOT_HomeLimitSwitchDirection, prefix='MOT_')
        params.velocity = velocity
        params.offsetDistance = offset
        self.sdk.ISC_SetHomingParamsBlock(self._serial, byref(params))

    def set_homing_velocity(self, velocity):
        """Sets the homing velocity.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        velocity : :class:`int`
            The homing velocity in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetHomingVelocity(self._serial, velocity)

    def set_jog_mode(self, mode, stop_mode):
        """Sets the jog mode.

        Parameters
        ----------
        mode : :class:`.enums.MOT_JogModes`
            The jog mode, as a :class:`.enums.MOT_JogModes` enum value or member name.
        stop_mode : :class:`.enums.MOT_StopModes`
            The stop mode, as a :class:`.enums.MOT_StopModes` enum value or member name.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        mode_ = self.convert_to_enum(mode, MOT_JogModes, prefix='MOT_')
        stop_mode_ = self.convert_to_enum(stop_mode, MOT_StopModes, prefix='MOT_')
        self.sdk.ISC_SetJogMode(self._serial, mode_, stop_mode_)

    def set_jog_params_block(self, jog_params):
        """Set the jog parameters.

        Parameters
        ----------
        jog_params : :class:`.structs.MOT_JogParameters`
            The jog parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        TypeError
            If the data type of `jog_params` is not :class:`.structs.MOT_JogParameters`
        """
        if not isinstance(jog_params, MOT_JogParameters):
            raise TypeError('The jog parameter must be a MOT_JogParameters struct')
        self.sdk.ISC_SetJogParamsBlock(self._serial, byref(jog_params))

    def set_jog_step_size(self, step_size):
        """Sets the distance to move on jogging.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        step_size : :class:`int`
            The step size in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetJogStepSize(self._serial, step_size)

    def set_jog_vel_params(self, max_velocity, acceleration):
        """Sets jog velocity parameters.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        max_velocity : :class:`int`
            The maximum velocity in ``DeviceUnits`` (see manual).
        acceleration : :class:`int`
            The acceleration in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetJogVelParams(self._serial, acceleration, max_velocity)

    def set_led_switches(self, led_switches):
        """Set the LED indicator bits on the device.
        
        Parameters
        ----------
        led_switches : :class:`int`
            Sum of: 8 to indicate moving 2 to indicate end of track and 1 to 
            flash on identify command.            

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetLEDswitches(self._serial, led_switches)

    def set_limit_switch_params(self, cw_lim, ccw_lim, cw_pos, ccw_pos, soft_limit_mode):
        """Sets the limit switch parameters.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        cw_lim : :class:`.enums.MOT_LimitSwitchModes`
            The clockwise hardware limit mode as a :class:`.enums.MOT_LimitSwitchModes`
            enum value or member name.
        ccw_lim : :class:`.enums.MOT_LimitSwitchModes`
            The anticlockwise hardware limit mode as a :class:`.enums.MOT_LimitSwitchModes`
            enum value or member name.
        cw_pos : :class:`int`
            The position of the clockwise software limit in ``DeviceUnits`` (see manual).
        ccw_pos : :class:`int`
            The position of the anticlockwise software limit in ``DeviceUnits`` (see manual).
        soft_limit_mode : :class:`.enums.MOT_LimitSwitchSWModes`
            The soft limit mode as a :class:`.enums.MOT_LimitSwitchSWModes` enum
            value or member name.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        cw_lim_ = self.convert_to_enum(cw_lim, MOT_LimitSwitchModes, prefix='MOT_')
        ccw_lim_ = self.convert_to_enum(ccw_lim, MOT_LimitSwitchModes, prefix='MOT_')
        sw = self.convert_to_enum(soft_limit_mode, MOT_LimitSwitchSWModes, prefix='MOT_')
        self.sdk.ISC_SetLimitSwitchParams(self._serial, cw_lim_, ccw_lim_, cw_pos, ccw_pos, sw)

    def set_limit_switch_params_block(self, params):
        """Set the limit switch parameters.

        Parameters
        ----------
        params : :class:`.structs.MOT_LimitSwitchParameters`
            The new limit switch parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        TypeError
            If the data type of `joystick_params` is not :class:`.structs.MOT_JoystickParameters`
        """
        if not isinstance(params, MOT_LimitSwitchParameters):
            raise TypeError('The limit switch parameter must be a MOT_LimitSwitchParameters struct')
        self.sdk.ISC_SetLimitSwitchParamsBlock(self._serial, byref(params))

    def set_limits_software_approach_policy(self, policy):
        """Sets the software limits policy.

        Parameters
        ----------
        policy : :class:`.enums.MOT_LimitsSoftwareApproachPolicy`
            The soft limit mode as a :class:`.enums.MOT_LimitsSoftwareApproachPolicy` enum
            value or member name.
        """
        policy_ = self.convert_to_enum(policy, MOT_LimitsSoftwareApproachPolicy)
        self.sdk.ISC_SetLimitsSoftwareApproachPolicy(self._serial, policy_)

    def set_motor_params(self, steps_per_rev, gear_box_ratio, pitch):
        """Sets the motor stage parameters.

        Deprecated: calls :meth:`set_motor_params_ext`

        These parameters, when combined, define the stage motion in terms of
        ``RealWorldUnits`` [millimeters or degrees]. The real-world unit
        is defined from ``steps_per_rev * gear_box_ratio / pitch``.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        steps_per_rev : :class:`float`
            The steps per revolution.
        gear_box_ratio : :class:`float`
            The gear box ratio.
        pitch : :class:`float`
            The pitch.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.set_motor_params_ext(steps_per_rev, gear_box_ratio, pitch)

    def set_motor_params_ext(self, steps_per_rev, gear_box_ratio, pitch):
        """Sets the motor stage parameters.

        These parameters, when combined, define the stage motion in terms of
        ``RealWorldUnits`` [millimeters or degrees]. The real-world unit
        is defined from ``steps_per_rev * gear_box_ratio / pitch``.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        steps_per_rev : :class:`float`
            The steps per revolution.
        gear_box_ratio : :class:`float`
            The gear box ratio.
        pitch : :class:`float`
            The pitch.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetMotorParamsExt(self._serial, steps_per_rev, gear_box_ratio, pitch)

    def set_motor_travel_limits(self, min_position, max_position):
        """Sets the motor stage min and max position.

        These define the range of travel for the stage.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        min_position : :class:`float`
            The minimum position in ``RealWorldUnits`` [millimeters or degrees].
        max_position : :class:`float`
            The maximum position in ``RealWorldUnits`` [millimeters or degrees].

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetMotorTravelLimits(self._serial, min_position, max_position)

    def set_motor_travel_mode(self, travel_mode):
        """Set the motor travel mode.

        Parameters
        ----------
        travel_mode : :class:`.enums.MOT_TravelModes`
            The travel mode as a :class:`.enums.MOT_TravelModes` enum value or
            member name.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        mode = self.convert_to_enum(travel_mode, MOT_TravelModes, prefix='MOT_')
        self.sdk.ISC_SetMotorTravelMode(self._serial, mode)

    def set_motor_velocity_limits(self, max_velocity, max_acceleration):
        """Sets the motor stage maximum velocity and acceleration.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        max_velocity : :class:`float`
            The maximum velocity in ``RealWorldUnits`` [millimeters or degrees].
        max_acceleration : :class:`float`
            The maximum acceleration in ``RealWorldUnits`` [millimeters or degrees].

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetMotorVelocityLimits(self._serial, max_velocity, max_acceleration)

    def set_move_absolute_position(self, position):
        """Sets the move absolute position.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        position : :class:`int`
            The absolute position in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetMoveAbsolutePosition(self._serial, position)

    def set_move_relative_distance(self, distance):
        """Sets the move relative distance.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        distance : :class:`int`
            The relative position in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetMoveRelativeDistance(self._serial, distance)

    def set_position_counter(self, count):
        """Set the position counter.

        Setting the position counter will locate the current position.
        Setting the position counter will effectively define the home position
        of a motor.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        count : :class:`int`
            The position counter in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetPositionCounter(self._serial, count)

    def set_potentiometer_params(self, index, threshold, velocity):
        """Sets the potentiometer parameters for the LTS.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        index : :class:`int`
            The potentiometer index to be stored.
        threshold : :class:`int`
            The potentiometer threshold, range 0 to 127.
        velocity : :class:`int`
            The velocity in ``DeviceUnits`` for the current potentiometer threshold.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        if threshold < 0 or threshold > 127:
            self.raise_exception('Invalid potentiometer threshold value of {}. '
                                 'Must be 0 <= threshold <= 127'.format(threshold))
        self.sdk.ISC_SetPotentiometerParams(self._serial, index, threshold, velocity)

    def set_potentiometer_params_block(self, params):
        """Set the potentiometer parameters.

        Parameters
        ----------
        params : :class:`.structs.MOT_PotentiometerSteps`
            The potentiometer parameters.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        if not isinstance(params, MOT_PotentiometerSteps):
            raise TypeError('Must pass in a MOT_PotentiometerSteps struct')
        self.sdk.ISC_SetPotentiometerParamsBlock(self._serial, byref(params))

    def set_power_params(self, rest, move):
        """Sets the power parameters for the stepper motor.

        Parameters
        ----------
        rest : :class:`int`
            Percentage of full power to give while not moving (0 - 100).
        move : :class:`int`
            Percentage of full power to give while moving (0 - 100).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        if rest < 0 or rest > 100:
            self.raise_exception('The rest power parameter is {}. Must be 0 <= rest <=100'.format(rest))
        if move < 0 or move > 100:
            self.raise_exception('The move power parameter is {}. Must be 0 <= move <=100'.format(move))
        params = MOT_PowerParameters()
        params.restPercentage = int(rest)
        params.movePercentage = int(move)
        self.sdk.ISC_SetPowerParams(self._serial, byref(params))

    def set_rotation_modes(self, mode, direction):
        """Set the rotation modes for a rotational device.

        Parameters
        ----------
        mode : :class:`.enums.MOT_MovementModes`
            The travel mode as a :class:`.enums.MOT_MovementModes` enum value or
            member name.
        direction : :class:`.enums.MOT_MovementDirections`
            The travel mode as a :class:`.enums.MOT_MovementDirections` enum value or
            member name.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        mode = self.convert_to_enum(mode, MOT_MovementModes)
        direction = self.convert_to_enum(direction, MOT_MovementDirections)
        self.sdk.ISC_SetRotationModes(self._serial, mode, direction)

    def set_stage_axis_limits(self, min_position, max_position):
        """Sets the stage axis position limits.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        min_position : :class:`int`
            The minimum position in ``DeviceUnits`` (see manual).
        max_position : :class:`int`
            The maximum position in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetStageAxisLimits(self._serial, min_position, max_position)

    def set_trigger_switches(self, indicator_bits):
        """Sets the trigger switch bits.

        Parameters
        ----------
        indicator_bits : :class:`int`
            Sets the 8 bits indicating action on trigger input and events
            to trigger electronic output.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetTriggerSwitches(self._serial, indicator_bits)

    def set_vel_params(self, max_velocity, acceleration):
        """Sets the move velocity parameters.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        max_velocity : :class:`int`
            The maximum velocity in ``DeviceUnits`` (see manual).
        acceleration : :class:`int`
            The acceleration in ``DeviceUnits`` (see manual).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_SetVelParams(self._serial, acceleration, max_velocity)

    def set_vel_params_block(self, min_velocity, max_velocity, acceleration):
        """Set the move velocity parameters.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        min_velocity : :class:`int`
            The minimum velocity in ``DeviceUnits`` (see manual)..
        max_velocity : :class:`int`
            The maximum velocity in ``DeviceUnits`` (see manual)..
        acceleration : :class:`int`
            The acceleration in ``DeviceUnits`` (see manual)..

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        params = MOT_VelocityParameters()
        params.minVelocity = min_velocity
        params.acceleration = acceleration
        params.maxVelocity = max_velocity
        self.sdk.ISC_SetVelParamsBlock(self._serial, byref(params))

    def start_polling(self, milliseconds):
        """Starts the internal polling loop.

        This function continuously requests position and status messages.

        Parameters
        ----------
        milliseconds : :class:`int`
            The polling rate, in milliseconds.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_StartPolling(self._serial, int(milliseconds))

    def stop_immediate(self):
        """Stop the current move immediately (with the risk of losing track of the position).

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_StopImmediate(self._serial)

    def stop_polling(self):
        """Stops the internal polling loop."""
        self.sdk.ISC_StopPolling(self._serial)

    def stop_profiled(self):
        """Stop the current move using the current velocity profile.
        
        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        self.sdk.ISC_StopProfiled(self._serial)

    def time_since_last_msg_received(self):
        """Gets the time, in milliseconds, since the last message was received.

        This can be used to determine whether communications with the device is
        still good.

        Returns
        -------
        :class:`int`
            The time, in milliseconds, since the last message was received.
        :class:`bool`
            :data:`True` if monitoring is enabled otherwise :data:`False`.
        """
        ms = c_int64()
        ret = self.sdk.ISC_TimeSinceLastMsgReceived(self._serial, byref(ms))
        return ms.value, ret

    def wait_for_message(self):
        """Wait for next Message Queue item. See :mod:`.messages`.

        Returns
        -------
        :class:`int`
            The message type.
        :class:`int`
            The message ID.
        :class:`int`
            The message data.

        Raises
        ------
        ~msl.equipment.exceptions.ThorlabsError
            If not successful.
        """
        message_type = WORD()
        message_id = WORD()
        message_data = DWORD()
        self.sdk.ISC_WaitForMessage(self._serial, byref(message_type), byref(message_id), byref(message_data))
        return message_type.value, message_id.value, message_data.value


if __name__ == '__main__':
    from msl.equipment.resources.thorlabs.kinesis import _print
    _print(IntegratedStepperMotors, IntegratedStepperMotors_FCNS, 'Thorlabs.MotionControl.IntegratedStepperMotors.h')
