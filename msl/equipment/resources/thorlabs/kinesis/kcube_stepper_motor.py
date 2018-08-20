"""
This module provides all the functionality required to control a
KCube Stepper Motor (KST101).
"""
import os
from ctypes import c_short, c_int16, c_int, c_uint, c_int32, c_int64, c_double, byref, create_string_buffer

from msl.equipment.resources import register
from msl.equipment.resources.utils import WORD, DWORD
from msl.equipment.resources.thorlabs.kinesis.motion_control import MotionControl
from msl.equipment.resources.thorlabs.kinesis.api_functions import KCube_StepperMotor_FCNS
from msl.equipment.resources.thorlabs.kinesis.structs import (
    TLI_HardwareInformation,
    MOT_VelocityParameters,
    MOT_HomingParameters,
    MOT_JogParameters,
    MOT_LimitSwitchParameters,
    MOT_PowerParameters,
    MOT_PIDLoopEncoderParams,
    KMOT_MMIParams,
    KMOT_TriggerConfig,
    KMOT_TriggerParams,
)
from msl.equipment.resources.thorlabs.kinesis.enums import (
    MOT_JogModes,
    MOT_StopModes,
    MOT_TravelDirection,
    MOT_LimitSwitchModes,
    MOT_LimitSwitchSWModes,
    MOT_LimitsSoftwareApproachPolicy,
    MOT_HomeLimitSwitchDirection,
    MOT_TravelModes,
    UnitType,
    KMOT_WheelMode,
    KMOT_WheelDirectionSense,
    KMOT_TriggerPortMode,
    KMOT_TriggerPortPolarity,
    MOT_MovementModes,
    MOT_MovementDirections,
)


@register(manufacturer='Thorlabs', model='KST101')
class KCubeStepperMotor(MotionControl):

    def __init__(self, record):
        """A wrapper around ``Thorlabs.MotionControl.KCube.StepperMotor.dll``.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a KCubeStepperMotor connection supports the following key-value pairs in the
        :ref:`connections_database`::

            'device_name': str, the device name found in ThorlabsDefaultSettings.xml [default: None]

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~msl.equipment.record_types.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        super(KCubeStepperMotor, self).__init__(record, KCube_StepperMotor_FCNS)

    def can_device_lock_front_panel(self):
        """Determine if the device front panel can be locked.

        Returns
        -------
        :class:`bool`
            :data:`True` if the front panel of the device can be locked, :data:`False` if not.
        """
        return self.sdk.SCC_CanDeviceLockFrontPanel(self._serial)

    def can_home(self):
        """Can the device perform a :meth:`home`?

        Returns
        -------
        :class:`bool`
            Whether the device can be homed.
        """
        return self.sdk.SCC_CanHome(self._serial)

    def can_move_without_homing_first(self):
        """Does the device need to be :meth:`home`\'d before a move can be performed?

        Returns
        -------
        :class:`bool`
            Whether the device needs to be homed.
        """
        return self.sdk.SCC_CanMoveWithoutHomingFirst(self._serial)

    def check_connection(self):
        """Check connection.

        Returns
        -------
        :class:`bool`
            Whether the USB is listed by the FTDI controller.
        """
        return self.sdk.SCC_CheckConnection(self._serial)

    def clear_message_queue(self):
        """Clears the device message queue."""
        self.sdk.SCC_ClearMessageQueue(self._serial)

    def close(self):
        """Disconnect and close the device."""
        self.sdk.SCC_Close(self._serial)

    def disable_channel(self):
        """Disable the channel so that motor can be moved by hand.

        When disabled, power is removed from the motor and it can be freely moved.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_DisableChannel(self._serial)

    def enable_channel(self):
        """Enable channel for computer control.

        When enabled, power is applied to the motor so it is fixed in position.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_EnableChannel(self._serial)

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
        self.sdk.SCC_EnableLastMsgTimer(self._serial, enable, last_msg_timeout)

    def get_backlash(self):
        """Get the backlash distance setting (used to control hysteresis).

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The backlash distance in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SCC_GetBacklash(self._serial)

    def get_bow_index(self):
        """Gets the stepper motor bow index.

        Returns
        -------
        :class:`int`
            The bow index.
        """
        return self.sdk.SCC_GetBowIndex(self._serial)

    def get_calibration_file(self):
        """Get calibration file for this motor.

        Returns
        -------
        :class:`str`
            The filename of the calibration file.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        size = 256
        filename = create_string_buffer(size)
        self.sdk.SCC_GetCalibrationFile(self._serial, filename, size)
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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        device_unit = c_int()
        unit = self.convert_to_enum(unit_type, UnitType)
        self.sdk.SCC_GetDeviceUnitFromRealValue(self._serial, real_value, byref(device_unit), unit)
        return device_unit.value

    def get_digital_outputs(self):
        """Gets the digital output bits.

        Returns
        -------
        :class:`bytes`
            Bit mask of states of the 4 digital output pins.
        """
        return self.sdk.SCC_GetDigitalOutputs(self._serial)

    def get_encoder_counter(self):
        """Get the encoder counter.

        For devices that have an encoder, the current encoder position can be read.

        Returns
        -------
        :class:`int`
            The encoder count in encoder units.
        """
        return self.sdk.SCC_GetEncoderCounter(self._serial)

    def get_front_panel_locked(self):
        """Query if the device front panel locked.

        Returns
        -------
        :class:`bool`
            :data:`True` if the device front panel is locked, :data:`False` if not.
        """
        return self.sdk.SCC_GetFrontPanelLocked(self._serial)

    def get_hardware_info(self):
        """Gets the hardware information from the device.

        Returns
        -------
        :class:`.structs.TLI_HardwareInformation`
            The hardware information.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        return self._get_hardware_info(self.sdk.SCC_GetHardwareInfo)

    def get_hardware_info_block(self):
        """Gets the hardware information in a block.

        Returns
        -------
        :class:`.structs.TLI_HardwareInformation`
            The hardware information.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        info = TLI_HardwareInformation()
        self.sdk.SCC_GetHardwareInfoBlock(self._serial, byref(info))
        return info

    def get_homing_params_block(self):
        """Get the homing parameters.

        Returns
        -------
        :class:`.structs.MOT_HomingParameters`
            The homing parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_HomingParameters()
        self.sdk.SCC_GetHomingParamsBlock(self._serial, byref(params))
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
        return self.sdk.SCC_GetHomingVelocity(self._serial)

    def get_hub_bay(self):
        """Gets the hub bay number this device is fitted to.

        Returns
        -------
        :class:`bytes`
            The number, 0x00 if unknown or 0xff if not on a hub.
        """
        return self.sdk.SCC_GetHubBay(self._serial)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        mode = c_short()
        stop_mode = c_short()
        self.sdk.SCC_GetJogMode(self._serial, byref(mode), byref(stop_mode))
        return MOT_JogModes(mode.value), MOT_StopModes(stop_mode.value)

    def get_jog_params_block(self):
        """Get the jog parameters.

        Returns
        -------
        :class:`.structs.MOT_JogParameters`
            The jog parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_JogParameters()
        self.sdk.SCC_GetJogParamsBlock(self._serial, byref(params))
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
        return self.sdk.SCC_GetJogStepSize(self._serial)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        acceleration = c_int()
        max_velocity = c_int()
        self.sdk.SCC_GetJogVelParams(self._serial, byref(acceleration), byref(max_velocity))
        return max_velocity.value, acceleration.value

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        cw_lim = WORD()
        ccw_lim = WORD()
        cw_pos = c_uint()
        ccw_pos = c_uint()
        soft = WORD()
        self.sdk.SCC_GetLimitSwitchParams(self._serial, byref(cw_lim), byref(ccw_lim),
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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_LimitSwitchParameters()
        self.sdk.SCC_GetLimitSwitchParamsBlock(self._serial, byref(params))
        return params

    def get_mmi_params(self):
        """Get the MMI Parameters for the KCube Display Interface.

        Deprecated calls by :meth:`get_mmi_params_ext`
        """
        return self.get_mmi_params_ext()

    def get_mmi_params_block(self):
        """Gets the MMI parameters for the device.

        Returns
        -------
        :class:`.structs.KMOT_MMIParams`
            The MMI parameters for the device.
        """
        mmi_params = KMOT_MMIParams()
        self.sdk.SCC_GetMMIParamsBlock(self._serial, byref(mmi_params))
        return mmi_params

    def get_mmi_params_ext(self):
        """Get the MMI Parameters for the KCube Display Interface.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`.enums.KMOT_WheelMode`
            The device joystick mode.
        :class:`int`
            The joystick maximum velocity in ``DeviceUnits``.
        :class:`int`
            The joystick acceleration in ``DeviceUnits``.
        :class:`.enums.KMOT_WheelDirectionSense`
            The joystick direction sense.
        :class:`int`
            The first preset position in ``DeviceUnits``.
        :class:`int`
            The second preset position in ``DeviceUnits``.
        :class:`int`
            The display intensity, range 0 to 100%.
        :class:`int`
            The display timeout, range 0 to 480 in minutes (0 is off, otherwise
            the inactivity period before dimming the display).
        :class:`int`
            The display dimmed intensity, range 0 to 10 (after the timeout
            period the device display will dim).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        mode = c_int16()
        vmax = c_int32()
        acc = c_int32()
        sense = c_int16()
        preset1 = c_int32()
        preset2 = c_int32()
        intensity = c_int16()
        timeout = c_int16()
        dim_intensity = c_int16()
        self.sdk.SCC_GetMMIParamsExt(self._serial, byref(mode), byref(vmax), byref(acc), byref(sense), byref(preset1),
                                     byref(preset2), byref(intensity), byref(timeout), byref(dim_intensity))
        return (KMOT_WheelMode(mode.value), vmax.value, acc.value, KMOT_WheelDirectionSense(sense.value),
                preset1.value, preset2.value, intensity.value, timeout.value, dim_intensity.value)

    def get_motor_params(self):
        """Gets the motor stage parameters.

        Deprecated: calls :meth:`get_motor_params_ext`

        These parameters, when combined define the stage motion in terms of
        ``RealWorldUnits`` [millimeters or degrees]. The real-world unit
        is defined from ``steps_per_rev * gear_box_ratio / pitch``.

        Returns
        ----------
        :class:`float`
            The steps per revolution.
        :class:`float`
            The gear box ratio.
        :class:`float`
            The pitch.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        return self.get_motor_params_ext()

    def get_motor_params_ext(self):
        """Gets the motor stage parameters.

        These parameters, when combined define the stage motion in terms of
        ``RealWorldUnits`` [millimeters or degrees]. The real-world unit
        is defined from ``steps_per_rev * gear_box_ratio / pitch``.

        Returns
        ----------
        :class:`float`
            The steps per revolution.
        :class:`float`
            The gear box ratio.
        :class:`float`
            The pitch.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        steps_per_rev = c_double()
        gear_box_ratio = c_double()
        pitch = c_double()
        self.sdk.SCC_GetMotorParamsExt(self._serial, byref(steps_per_rev), byref(gear_box_ratio), byref(pitch))
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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        min_position = c_double()
        max_position = c_double()
        self.sdk.SCC_GetMotorTravelLimits(self._serial, byref(min_position), byref(max_position))
        return min_position.value, max_position.value

    def get_motor_travel_mode(self):
        """Get the motor travel mode.

        Returns
        -------
        :class:`.enums.MOT_TravelModes`
            The travel mode.
        """
        return MOT_TravelModes(self.sdk.SCC_GetMotorTravelMode(self._serial))

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        max_velocity = c_double()
        max_acceleration = c_double()
        self.sdk.SCC_GetMotorVelocityLimits(self._serial, byref(max_velocity), byref(max_acceleration))
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
        return self.sdk.SCC_GetMoveAbsolutePosition(self._serial)

    def get_move_relative_distance(self):
        """Gets the move relative distance.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The move relative position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SCC_GetMoveRelativeDistance(self._serial)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        message_type = WORD()
        message_id = WORD()
        message_data = DWORD()
        self.sdk.SCC_GetNextMessage(self._serial, byref(message_type), byref(message_id), byref(message_data))
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
        return self.sdk.SCC_GetNumberPositions(self._serial)

    def get_pid_loop_encoder_coeff(self):
        """Gets the encoder PID loop coefficient.

        This is the encoder coefficient.  Use 0.0 to disable the encoder or if no
        encoder is present otherwise a positive encoder coefficient.

        Returns
        -------
        :class:`float`
            The encoder PID loop coefficient.
        """
        return self.sdk.SCC_GetPIDLoopEncoderCoeff(self._serial)

    def get_pid_loop_encoder_params(self):
        """Gets the Encoder PID loop parameters.

        Returns
        -------
        :class:`.structs.MOT_PIDLoopEncoderParams`
            The Encoder PID loop parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_PIDLoopEncoderParams()
        self.sdk.SCC_GetPIDLoopEncoderParams(self._serial, byref(params))
        return params

    def get_position(self):
        """Get the current position.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        index : :class:`int`
            The position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SCC_GetPosition(self._serial)

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
        return self.sdk.SCC_GetPositionCounter(self._serial)

    def get_power_params(self):
        """Gets the power parameters for the stepper motor.

        Returns
        -------
        :class:`.structs.MOT_PowerParameters`
            The power parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_PowerParameters()
        self.sdk.SCC_GetPowerParams(self._serial, byref(params))
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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        real_unit = c_double()
        unit = self.convert_to_enum(unit_type, UnitType)
        self.sdk.SCC_GetRealValueFromDeviceUnit(self._serial, device_value, byref(real_unit), unit)
        return real_unit.value

    def get_soft_limit_mode(self):
        """Gets the software limits mode.

        Returns
        -------
        :class:`.enums.MOT_LimitsSoftwareApproachPolicy`
            The software limits mode.
        """
        return MOT_LimitsSoftwareApproachPolicy(self.sdk.SCC_GetSoftLimitMode(self._serial))

    def get_software_version(self):
        """Gets version number of the device software.

        Returns
        -------
        :class:`str`
            The device software version.
        """
        return self.to_version(self.sdk.SCC_GetSoftwareVersion(self._serial))

    def get_stage_axis_max_pos(self):
        """Gets the Stepper Motor maximum stage position.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The maximum position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SCC_GetStageAxisMaxPos(self._serial)

    def get_stage_axis_min_pos(self):
        """Gets the Stepper Motor minimum stage position.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The minimum position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SCC_GetStageAxisMinPos(self._serial)

    def get_status_bits(self):
        """Get the current status bits.

        This returns the latest status bits received from the device.
        To get new status bits, use :meth:`request_status_bits` or use
        the polling functions, :meth:`start_polling`.

        Returns
        -------
        :class:`int`
            The status bits from the device.
        """
        return self.sdk.SCC_GetStatusBits(self._serial)

    def get_trigger_config_params(self):
        """Get the Trigger Configuration Parameters.

        Returns
        -------
        :class:`.enums.KMOT_TriggerPortMode`
            The trigger 1 mode.
        :class:`.enums.KMOT_TriggerPortPolarity`
            The trigger 1 polarity.
        :class:`.enums.KMOT_TriggerPortMode`
            The trigger 2 mode.
        :class:`.enums.KMOT_TriggerPortPolarity`
            The trigger 2 polarity.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        mode1 = c_int16()
        pol1 = c_int16()
        mode2 = c_int16()
        pol2 = c_int16()
        self.sdk.SCC_GetTriggerConfigParams(self._serial, byref(mode1), byref(pol1), byref(mode2), byref(pol2))
        return (KMOT_TriggerPortMode(mode1.value), KMOT_TriggerPortPolarity(pol1.value),
                KMOT_TriggerPortMode(mode2.value), KMOT_TriggerPortPolarity(pol2.value))

    def get_trigger_config_params_block(self):
        """Gets the trigger configuration parameters block.

        Returns
        -------
        :class:`.structs.KMOT_TriggerConfig`
            Options for controlling the trigger configuration.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = KMOT_TriggerConfig()
        self.sdk.SCC_GetTriggerConfigParamsBlock(self._serial, byref(params))
        return params

    def get_trigger_params_params(self):
        """Get the Trigger Parameters parameters.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Returns
        -------
        :class:`int`
            The trigger start position, forward, in ``DeviceUnits`` (see manual).
        :class:`int`
            The trigger interval, forward, in ``DeviceUnits`` (see manual).
        :class:`int`
            Number of trigger pulses, forward.
        :class:`int`
            The trigger start position, reverse, in ``DeviceUnits`` (see manual).
        :class:`int`
            The trigger interval, reverse, in ``DeviceUnits`` (see manual).
        :class:`int`
            Number of trigger pulses., reverse.
        :class:`int`
            Width of the trigger pulse in milliseconds, range 10 (10us) to 650000 (650ms).
        :class:`int`
            Number of cycles to perform triggering.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        trigger_start_position_fwd = c_int32()
        trigger_interval_fwd = c_int32()
        trigger_pulse_count_fwd = c_int32()
        trigger_start_position_rev = c_int32()
        trigger_interval_rev = c_int32()
        trigger_pulse_count_rev = c_int32()
        trigger_pulse_width = c_int32()
        cycle_count = c_int32()
        self.sdk.SCC_GetTriggerParamsParams(self._serial, byref(trigger_start_position_fwd),
                                            byref(trigger_interval_fwd), byref(trigger_pulse_count_fwd),
                                            byref(trigger_start_position_rev), byref(trigger_interval_rev),
                                            byref(trigger_pulse_count_rev), byref(trigger_pulse_width),
                                            byref(cycle_count))
        return (trigger_start_position_fwd.value, trigger_interval_fwd.value, trigger_pulse_count_fwd.value,
                trigger_start_position_rev.value, trigger_interval_rev.value, trigger_pulse_count_rev.value,
                trigger_pulse_width.value, cycle_count.value)

    def get_trigger_params_params_block(self):
        """Gets the trigger parameters block.

        Returns
        -------
        :class:`.structs.KMOT_TriggerParams`
            Options for controlling the trigger.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = KMOT_TriggerParams()
        self.sdk.SCC_GetTriggerParamsParamsBlock(self._serial, byref(params))
        return params

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        acceleration = c_int()
        max_velocity = c_int()
        self.sdk.SCC_GetVelParams(self._serial, byref(acceleration), byref(max_velocity))
        return max_velocity.value, acceleration.value

    def get_vel_params_block(self):
        """Get the move velocity parameters.

        Returns
        -------
        :class:`.structs.MOT_VelocityParameters`
            The velocity parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_VelocityParameters()
        self.sdk.SCC_GetVelParamsBlock(self._serial, byref(params))
        return params

    def has_last_msg_timer_overrun(self):
        """Queries if the time since the last message has exceeded the
        ``lastMsgTimeout`` set by :meth:`.enable_last_msg_timer`.

        This can be used to determine whether communications with the device is
        still good.

        Returns
        -------
        :class:`bool`
            :data:`True` if last message timer has elapsed or
            :data:`False` if monitoring is not enabled or if time of last message
            received is less than ``lastMsgTimeout``.
        """
        return self.sdk.SCC_HasLastMsgTimerOverrun(self._serial)

    def home(self):
        """Home the device.

        Homing the device will set the device to a known state and determine
        the home position.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_Home(self._serial)

    def identify(self):
        """Sends a command to the device to make it identify itself."""
        return self.sdk.SCC_Identify(self._serial)

    def is_calibration_active(self):
        """Is a calibration file active for this motor?

        Returns
        -------
        :class:`bool`
            Whether a calibration file is active.
        """
        return self.sdk.SCC_IsCalibrationActive(self._serial)

    def load_settings(self):
        """Update device with stored settings.

        The settings are read from ``ThorlabsDefaultSettings.xml``, which
        gets created when the Kinesis software is installed.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_LoadSettings(self._serial)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_LoadNamedSettings(self._serial, settings_name)

    def message_queue_size(self):
        """Gets the size of the message queue.

        Returns
        -------
        :class:`int`
            The number of messages in the queue.
        """
        return self.sdk.SCC_MessageQueueSize(self._serial)

    def move_absolute(self):
        """Moves the device to the position defined in :meth:`set_move_absolute_position`.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_MoveAbsolute(self._serial)

    def move_at_velocity(self, direction):
        """Start moving at the current velocity in the specified direction.

        Parameters
        ----------
        direction : :class:`.enums.MOT_TravelDirection`
            The required direction of travel as a :class:`.enums.MOT_TravelDirection`
            enum value or member name.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        direction_ = self.convert_to_enum(direction, MOT_TravelDirection, prefix='MOT_')
        self.sdk.SCC_MoveAtVelocity(self._serial, direction_)

    def move_jog(self, jog_direction):
        """Perform a jog.

        Parameters
        ----------
        jog_direction : :class:`.enums.MOT_TravelDirection`
            The jog direction as a :class:`.enums.MOT_TravelDirection` enum value
            or member name.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        direction = self.convert_to_enum(jog_direction, MOT_TravelDirection, prefix='MOT_')
        self.sdk.SCC_MoveJog(self._serial, direction)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_MoveRelative(self._serial, displacement)

    def move_relative_distance(self):
        """Moves the device by a relative distance defined by :meth:`set_move_relative_distance`.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_MoveRelativeDistance(self._serial)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_MoveToPosition(self._serial, index)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_Open(self._serial)

    def persist_settings(self):
        """Persist the devices current settings.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_PersistSettings(self._serial)

    def polling_duration(self):
        """Gets the polling loop duration.

        Returns
        -------
        :class:`int`
            The time between polls in milliseconds or 0 if polling is not active.
        """
        return self.sdk.SCC_PollingDuration(self._serial)

    def register_message_callback(self, callback):
        """Registers a callback on the message queue.

        Parameters
        ----------
        callback : :class:`~msl.equipment.resources.thorlabs.kinesis.callbacks.MotionControlCallback`
            A function to be called whenever messages are received.
        """
        self.sdk.SCC_RegisterMessageCallback(self._serial, callback)

    def request_backlash(self):
        """Requests the backlash.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestBacklash(self._serial)

    def request_bow_index(self):
        """Requests the stepper motor bow index.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestBowIndex(self._serial)

    def request_digital_outputs(self):
        """Requests the digital output bits.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestDigitalOutputs(self._serial)

    def request_encoder_counter(self):
        """Requests the encoder counter.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestEncoderCounter(self._serial)

    def request_front_panel_locked(self):
        """Ask the device if its front panel is locked.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestFrontPanelLocked(self._serial)

    def request_homing_params(self):
        """Requests the homing parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestHomingParams(self._serial)

    def request_jog_params(self):
        """Requests the jog parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestJogParams(self._serial)

    def request_limit_switch_params(self):
        """Requests the limit switch parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestLimitSwitchParams(self._serial)

    def request_mmi_params(self):
        """Requests the MMI Parameters for the KCube Display Interface.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestMMIParams(self._serial)

    def request_move_absolute_position(self):
        """Requests the position of next absolute move.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestMoveAbsolutePosition(self._serial)

    def request_move_relative_distance(self):
        """Requests the relative move distance.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestMoveRelativeDistance(self._serial)

    def request_pid_loop_encoder_params(self):
        """Requests the Encoder PID loop parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestPIDLoopEncoderParams(self._serial)

    def request_pos_trigger_params(self):
        """Requests the position trigger parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestPosTriggerParams(self._serial)

    def request_position(self):
        """Requests the current position.

        This needs to be called to get the device to send it's current position.
        Note, this is called automatically if ``Polling`` is enabled for the device
        using :meth:`start_polling`.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestPosition(self._serial)

    def request_power_params(self):
        """Requests the power parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestPowerParams(self._serial)

    def request_settings(self):
        """Requests that all settings are downloaded from the device.

        This function requests that the device upload all it's settings to the
        DLL.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestSettings(self._serial)

    def request_status_bits(self):
        """Request the status bits which identify the current motor state.

        This needs to be called to get the device to send it's current status bits.
        Note, this is called automatically if ``Polling`` is enabled for the device
        using :meth:`start_polling`.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestStatusBits(self._serial)

    def request_trigger_config_params(self):
        """Requests the Trigger Configuration Parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestTriggerConfigParams(self._serial)

    def request_vel_params(self):
        """Requests the velocity parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_RequestVelParams(self._serial)

    def reset_rotation_modes(self):
        """Reset the rotation modes for a rotational device.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_ResetRotationModes(self._serial)

    def resume_move_messages(self):
        """Resume suspended move messages.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_ResumeMoveMessages(self._serial)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetBacklash(self._serial, distance)

    def set_bow_index(self, bow_index):
        """Sets the stepper motor bow index.

        Parameters
        ----------
        bow_index : :class:`int`
            The bow index.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetBowIndex(self._serial, bow_index)

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
        self.sdk.SCC_SetCalibrationFile(self._serial, path.encode(), enabled)

    def set_digital_outputs(self, outputs_bits):
        """Sets the digital output bits.

        Parameters
        ----------
        outputs_bits : :class:`int`
            Bit mask to set the states of the 4 digital output pins.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetDigitalOutputs(self._serial, outputs_bits)

    def set_direction(self, reverse):
        """Sets the motor direction sense.

        This function is used because some actuators have directions of motion
        reversed. This parameter will tell the system to reverse the direction sense
        when moving, jogging etc.

        Parameters
        ----------
        reverse : :class:`bool`
            If :data:`True` then directions will be swapped on these moves.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetDirection(self._serial, reverse)

    def set_encoder_counter(self, count):
        """Set the Encoder Counter values.

        Setting the encoder counter to zero, effectively defines a home position on the encoder strip.
        Note, setting this value does not move the device.

        Parameters
        ----------
        count : :class:`int`
            The encoder count in encoder units.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetEncoderCounter(self._serial, count)

    def set_front_panel_lock(self, locked):
        """Sets the device front panel lock state.

        Parameters
        ----------
        locked : :class:`bool`
            :data:`True` to lock the device, :data:`False` to unlock

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetFrontPanelLock(self._serial, locked)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_HomingParameters()
        params.direction = self.convert_to_enum(direction, MOT_TravelDirection, prefix='MOT_')
        params.limitSwitch = self.convert_to_enum(limit, MOT_HomeLimitSwitchDirection, prefix='MOT_')
        params.velocity = velocity
        params.offsetDistance = offset
        self.sdk.SCC_SetHomingParamsBlock(self._serial, byref(params))

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetHomingVelocity(self._serial, velocity)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        mode_ = self.convert_to_enum(mode, MOT_JogModes, prefix='MOT_')
        stop_mode_ = self.convert_to_enum(stop_mode, MOT_StopModes, prefix='MOT_')
        self.sdk.SCC_SetJogMode(self._serial, mode_, stop_mode_)

    def set_jog_params_block(self, jog_params):
        """Set the jog parameters.

        Parameters
        ----------
        jog_params : :class:`.structs.MOT_JogParameters`
            The jog parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        TypeError
            If the data type of `jog_params` is not :class:`.structs.MOT_JogParameters`
        """
        if not isinstance(jog_params, MOT_JogParameters):
            raise TypeError('The jog parameter must be a MOT_JogParameters struct')
        self.sdk.SCC_SetJogParamsBlock(self._serial, byref(jog_params))

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetJogStepSize(self._serial, step_size)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetJogVelParams(self._serial, acceleration, max_velocity)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        cw_lim_ = self.convert_to_enum(cw_lim, MOT_LimitSwitchModes, prefix='MOT_')
        ccw_lim_ = self.convert_to_enum(ccw_lim, MOT_LimitSwitchModes, prefix='MOT_')
        sw = self.convert_to_enum(soft_limit_mode, MOT_LimitSwitchSWModes, prefix='MOT_')
        self.sdk.SCC_SetLimitSwitchParams(self._serial, cw_lim_, ccw_lim_, cw_pos, ccw_pos, sw)

    def set_limit_switch_params_block(self, params):
        """Set the limit switch parameters.

        Parameters
        ----------
        params : :class:`.structs.MOT_LimitSwitchParameters`
            The limit switch parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        if not isinstance(params, MOT_LimitSwitchParameters):
            raise TypeError('The limit switch parameter must be a MOT_LimitSwitchParameters struct')
        self.sdk.SCC_SetLimitSwitchParamsBlock(self._serial, byref(params))

    def set_limits_software_approach_policy(self, policy):
        """Sets the software limits mode.

        Parameters
        ----------
        policy : :class:`.enums.MOT_LimitsSoftwareApproachPolicy`
            The soft limit mode as a :class:`.enums.MOT_LimitsSoftwareApproachPolicy` enum
            value or member name.
        """
        policy_ = self.convert_to_enum(policy, MOT_LimitsSoftwareApproachPolicy)
        self.sdk.SCC_SetLimitsSoftwareApproachPolicy(self._serial, policy_)

    def set_mmi_params(self, joystick_mode, joystick_max_velocity, joystick_acceleration,
                       direction_sense, preset_position1, preset_position2, display_intensity):
        """Set the MMI Parameters for the KCube Display Interface.

        Deprecated calls :meth:`set_mmi_params_ext` setting the `display_timeout` to 1 minute
        and the `display_dim_intensity` to 8.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        return self.set_mmi_params_ext(joystick_mode, joystick_max_velocity, joystick_acceleration, direction_sense,
                                       preset_position1, preset_position2, display_intensity, 1, 8)

    def set_mmi_params_block(self, mmi_params):
        """Sets the MMI parameters for the device.

        Parameters
        ----------
        mmi_params : :class:`.structs.KMOT_MMIParams`
            Options for controlling the mmi.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        if not isinstance(mmi_params, KMOT_MMIParams):
            self.raise_exception('Must pass in a KMOT_MMIParams structure')
        self.sdk.SCC_SetMMIParamsBlock(self._serial, byref(mmi_params))

    def set_mmi_params_ext(self, joystick_mode, joystick_max_velocity, joystick_acceleration, direction_sense,
                           preset_position1, preset_position2, display_intensity, display_timeout,
                           display_dim_intensity):
        """Set the MMI Parameters for the KCube Display Interface.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        joystick_mode : :class:`.enums.KMOT_WheelMode`
            The device joystick mode as a :class:`.enums.KMOT_WheelMode` enum value or member name.
        joystick_max_velocity : :class:`int`
            The joystick maximum velocity in ``DeviceUnits``.
        joystick_acceleration : :class:`int`
            The joystick acceleration in ``DeviceUnits``.
        direction_sense : :class:`.enums.KMOT_WheelDirectionSense`
            The joystick direction sense as a :class:`.enums.KMOT_WheelDirectionSense` enum value or member name.
        preset_position1 : :class:`int`
            The first preset position in ``DeviceUnits``.
        preset_position2 : :class:`int`
            The second preset position in ``DeviceUnits``.
        display_intensity : :class:`int`
            The display intensity, range 0 to 100%.
        display_timeout : :class:`int`
            The display timeout, range 0 to 480 in minutes (0 is off, otherwise
            the inactivity period before dimming the display).
        display_dim_intensity : :class:`int`
            The display dimmed intensity, range 0 to 10 (after the timeout
            period the device display will dim).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        mode = self.convert_to_enum(joystick_mode, KMOT_WheelMode, prefix='KMOT_JS_')
        sense = self.convert_to_enum(direction_sense, KMOT_WheelDirectionSense, prefix='KMOT_JS_')
        self.sdk.SCC_SetMMIParamsExt(self._serial, mode, joystick_max_velocity, joystick_acceleration, sense,
                                     preset_position1, preset_position2, display_intensity, display_timeout,
                                     display_dim_intensity)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetMotorParamsExt(self._serial, steps_per_rev, gear_box_ratio, pitch)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetMotorTravelLimits(self._serial, min_position, max_position)

    def set_motor_travel_mode(self, travel_mode):
        """Set the motor travel mode.

        Parameters
        ----------
        travel_mode : :class:`.enums.MOT_TravelModes`
            The travel mode as a :class:`.enums.MOT_TravelModes` enum value or
            member name.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        mode = self.convert_to_enum(travel_mode, MOT_TravelModes, prefix='MOT_')
        self.sdk.SCC_SetMotorTravelMode(self._serial, mode)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetMotorVelocityLimits(self._serial, max_velocity, max_acceleration)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetMoveAbsolutePosition(self._serial, position)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetMoveRelativeDistance(self._serial, distance)

    def set_pid_loop_encoder_coeff(self, coeff):
        """Sets the encoder PID loop coefficient.

        This is the encoder coefficient.  Use 0.0 to disable the encoder or if no encoder is
        present otherwise a positive encoder coefficient.

        Parameters
        ----------
        coeff : :class:`float`
             The encoder PID loop coefficient.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetPIDLoopEncoderCoeff(self._serial, coeff)

    def set_pid_loop_encoder_params(self, params):
        """Sets the encoder PID loop parameters.

        Parameters
        ----------
        params : :class:`.structs.MOT_PIDLoopEncoderParams`
            The encoder PID loop parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        :exc:`TypeError`
            If `params` is not a :class:`.structs.MOT_PIDLoopEncoderParams`.
        """
        if not isinstance(params, MOT_PIDLoopEncoderParams):
            self.raise_exception('Must pass in a MOT_PIDLoopEncoderParams structure')
        return self.sdk.SCC_SetPIDLoopEncoderParams(self._serial, byref(params))

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetPositionCounter(self._serial, count)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        if rest < 0 or rest > 100:
            raise ValueError('The rest power parameter is {}. Must be 0 <= rest <=100'.format(rest))
        if move < 0 or move > 100:
            raise ValueError('The move power parameter is {}. Must be 0 <= move <=100'.format(move))
        params = MOT_PowerParameters()
        params.restPercentage = rest
        params.movePercentage = move
        self.sdk.SCC_SetPowerParams(self._serial, byref(params))

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        mode = self.convert_to_enum(mode, MOT_MovementModes)
        direction = self.convert_to_enum(direction, MOT_MovementDirections)
        self.sdk.SCC_SetRotationModes(self._serial, mode, direction)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetStageAxisLimits(self._serial, min_position, max_position)

    def set_trigger_config_params(self, mode1, polarity1, mode2, polarity2):
        """Set the trigger configuration parameters.

        Parameters
        ----------
        mode1 : :class:`.enums.KMOT_TriggerPortMode`
            The trigger 1 mode as a :class:`~.enums.KMOT_TriggerPortMode` enum
            value or member name.
        polarity1 : :class:`.enums.KMOT_TriggerPortPolarity`
            The trigger 1 polarity as a :class:`~.enums.KMOT_TriggerPortPolarity`
            enum value or member name.
        mode2 : :class:`.enums.KMOT_TriggerPortMode`
            The trigger 2 mode as a :class:`~.enums.KMOT_TriggerPortMode` enum
            value or member name.
        polarity2 : :class:`.enums.KMOT_TriggerPortPolarity`
            The trigger 2 polarity as a :class:`~.enums.KMOT_TriggerPortPolarity`
            enum value or member name.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        m1 = self.convert_to_enum(mode1, KMOT_TriggerPortMode, prefix='KMOT_')
        p1 = self.convert_to_enum(polarity1, KMOT_TriggerPortPolarity, prefix='KMOT_')
        m2 = self.convert_to_enum(mode2, KMOT_TriggerPortMode, prefix='KMOT_')
        p2 = self.convert_to_enum(polarity2, KMOT_TriggerPortPolarity, prefix='KMOT_')
        self.sdk.SCC_SetTriggerConfigParams(self._serial, m1, p1, m2, p2)

    def set_trigger_config_params_block(self, trigger_config_params):
        """Sets the trigger configuration parameters block.

        Parameters
        ----------
        trigger_config_params : :class:`.structs.KMOT_TriggerConfig`
            Options for controlling the trigger configuration.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        :exc:`TypeError`
            If `trigger_config_params` is not a :class:`.structs.KMOT_TriggerConfig`.
        """
        if not isinstance(trigger_config_params, KMOT_TriggerConfig):
            self.raise_exception('Must pass in a KMOT_TriggerConfig structure')
        self.sdk.SCC_SetTriggerConfigParamsBlock(self._serial, byref(trigger_config_params))

    def set_trigger_params_params(self, trigger_start_position_fwd, trigger_interval_fwd, trigger_pulse_count_fwd,
                                  trigger_start_position_rev, trigger_interval_rev, trigger_pulse_count_rev,
                                  trigger_pulse_width, cycle_count):
        """Set the Trigger Parameters parameters.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        trigger_start_position_fwd : :class:`int`
            The trigger start position, forward, in ``DeviceUnits`` (see manual).
        trigger_interval_fwd : :class:`int`
            The trigger interval, forward, in ``DeviceUnits`` (see manual).
        trigger_pulse_count_fwd : :class:`int`
            Number of trigger pulses, forward.
        trigger_start_position_rev : :class:`int`
            The trigger start position, reverse, in ``DeviceUnits`` (see manual).
        trigger_interval_rev : :class:`int`
            The trigger interval, reverse, in ``DeviceUnits`` (see manual).
        trigger_pulse_count_rev : :class:`int`
            Number of trigger pulses, reverse.
        trigger_pulse_width : :class:`int`
            Width of the trigger pulse in milliseconds, range 10 (10us) to 650000 (650ms).
        cycle_count : :class:`int`
            Number of cycles to perform triggering.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetTriggerParamsParams(self._serial, trigger_start_position_fwd, trigger_interval_fwd,
                                            trigger_pulse_count_fwd, trigger_start_position_rev, trigger_interval_rev,
                                            trigger_pulse_count_rev, trigger_pulse_width, cycle_count)

    def set_trigger_params_params_block(self, trigger_params_params):
        """Set the Trigger Parameters parameters.

        Parameters
        ----------
        trigger_params_params : :class:`.structs.KMOT_TriggerParams`
            Options for controlling the trigger.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        :exc:`TypeError`
            If `trigger_params_params` is not a :class:`.structs.KMOT_TriggerParams`.
        """
        if not isinstance(trigger_params_params, KMOT_TriggerParams):
            self.raise_exception('Must pass in a KMOT_TriggerParams structure')
        self.sdk.SCC_SetTriggerParamsParamsBlock(self._serial, byref(trigger_params_params))

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SetVelParams(self._serial, acceleration, max_velocity)

    def set_vel_params_block(self, min_velocity, max_velocity, acceleration):
        """Set the move velocity parameters.

        Parameters
        ----------
        min_velocity : :class:`int`
            The minimum velocity.
        max_velocity : :class:`int`
            The maximum velocity.
        acceleration : :class:`int`
            The acceleration.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_VelocityParameters()
        params.minVelocity = min_velocity
        params.acceleration = acceleration
        params.maxVelocity = max_velocity
        self.sdk.SCC_SetVelParamsBlock(self._serial, byref(params))

    def start_polling(self, milliseconds):
        """Starts the internal polling loop.

        This function continuously requests position and status messages.

        Parameters
        ----------
        milliseconds : :class:`int`
            The polling rate, in milliseconds.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_StartPolling(self._serial, milliseconds)

    def stop_immediate(self):
        """Stop the current move immediately (with the risk of losing track of the position).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_StopImmediate(self._serial)

    def stop_polling(self):
        """Stops the internal polling loop."""
        self.sdk.SCC_StopPolling(self._serial)

    def stop_profiled(self):
        """Stop the current move using the current velocity profile.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_StopProfiled(self._serial)

    def suspend_move_messages(self):
        """Suspend automatic messages at ends of moves.

        Useful to speed up part of real-time system with lots of short moves.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SCC_SuspendMoveMessages(self._serial)

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
        ret = self.sdk.SCC_TimeSinceLastMsgReceived(self._serial, byref(ms))
        return ms.value, ret

    def uses_pid_loop_encoding(self):
        """Determines if we can uses PID loop encoding.

        This is true if the stage supports PID Loop Encoding. Requires :meth:`get_pid_loop_encoder_coeff`
        to have a positive non zero coefficient.

        Returns
        -------
        :class:`bool`
            Whether PID loop encoding is supported.
        """
        return self.sdk.SCC_UsesPIDLoopEncoding(self._serial)

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
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        message_type = WORD()
        message_id = WORD()
        message_data = DWORD()
        self.sdk.SCC_WaitForMessage(self._serial, byref(message_type), byref(message_id), byref(message_data))
        return message_type.value, message_id.value, message_data.value


if __name__ == '__main__':
    from msl.equipment.resources.thorlabs.kinesis import _print
    _print(KCubeStepperMotor, KCube_StepperMotor_FCNS, 'Thorlabs.MotionControl.KCube.StepperMotor.h')
