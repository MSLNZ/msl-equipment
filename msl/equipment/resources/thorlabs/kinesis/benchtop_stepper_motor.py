"""
This module provides all the functionality required to control a
**Benchtop Stepper Motor** including:

* BSC101
* BSC102
* BSC103
* BSC201
* BSC202
* BSC203
"""
import os
from ctypes import c_short, c_int, c_uint, c_int64, c_double, byref, create_string_buffer

from msl.equipment.resources import register
from msl.equipment.resources.utils import WORD, DWORD
from msl.equipment.resources.thorlabs.kinesis.motion_control import MotionControl
from msl.equipment.resources.thorlabs.kinesis.api_functions import Benchtop_StepperMotor_FCNS
from msl.equipment.resources.thorlabs.kinesis.structs import (
    TLI_HardwareInformation,
    MOT_HomingParameters,
    MOT_JogParameters,
    MOT_JoystickParameters,
    MOT_LimitSwitchParameters,
    MOT_PIDLoopEncoderParams,
    MOT_PowerParameters,
    MOT_VelocityParameters,
)
from msl.equipment.resources.thorlabs.kinesis.enums import (
    UnitType,
    MOT_JogModes,
    MOT_StopModes,
    MOT_LimitSwitchModes,
    MOT_LimitSwitchSWModes,
    MOT_TravelModes,
    MOT_LimitsSoftwareApproachPolicy,
    MOT_TravelDirection,
    MOT_HomeLimitSwitchDirection,
    MOT_PID_LoopMode,
    MOT_MovementModes,
    MOT_MovementDirections,
)


@register(manufacturer='Thorlabs', model='BSC(101|102|103|201|202|203)')
class BenchtopStepperMotor(MotionControl):

    def __init__(self, record):
        """A wrapper around ``Thorlabs.MotionControl.Benchtop.StepperMotor.dll``.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a BenchtopStepperMotor connection supports the following key-value pairs in the
        :ref:`connections_database`::

            'device_name': str, the device name found in ThorlabsDefaultSettings.xml [default: None]

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~msl.equipment.record_types.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        super(BenchtopStepperMotor, self).__init__(record, Benchtop_StepperMotor_FCNS)

        self._num_channels = self.get_num_channels()

    def can_home(self, channel):
        """Can the device perform a :meth:`home`?

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`bool`
            :data:`True` if the device can perform a home.
        """
        return self.sdk.SBC_CanHome(self._serial, self._ch(channel))

    def can_move_without_homing_first(self, channel):
        """Does the device need to be :meth:`home`\'d before a move can be performed?

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`bool`
            :data:`True` if the device does not need to be :meth:`home`\'d before a move can be commanded.
        """
        return self.sdk.SBC_CanMoveWithoutHomingFirst(self._serial, self._ch(channel))

    def check_connection(self):
        """Check connection.

        Returns
        -------
        :class:`bool`
            :data:`True` if the USB is listed by the FTDI controller.
        """
        return self.sdk.SBC_CheckConnection(self._serial)

    def clear_message_queue(self, channel):
        """Clears the device message queue.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_ClearMessageQueue(self._serial, self._ch(channel))

    def close(self):
        """Disconnect and close the device.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_Close(self._serial)

    def disable_channel(self, channel):
        """Disable the channel so that the motor can be moved by hand.

        When disabled, power is removed from the motor and it can be freely moved.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_DisableChannel(self._serial, self._ch(channel))

    def enable_channel(self, channel):
        """Enable channel for computer control.

        When enabled, power is applied to the motor so it is fixed in position.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_EnableChannel(self._serial, self._ch(channel))

    def enable_last_msg_timer(self, channel, enable, last_msg_timeout):
        """Enables the last message monitoring timer.

        This can be used to determine whether communications with the device is
        still good.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        enable : :class:`bool`
            :data:`True` to enable monitoring otherwise :data:`False` to disable.
        last_msg_timeout : :class:`int`
            The last message error timeout in ms. Set to 0 to disable.
        """
        self.sdk.SBC_EnableLastMsgTimer(self._serial, self._ch(channel), enable, last_msg_timeout)

    def get_backlash(self, channel):
        """Get the backlash distance setting (used to control hysteresis).

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The backlash distance in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SBC_GetBacklash(self._serial, self._ch(channel))

    def get_bow_index(self, channel):
        """Gets the stepper motor bow index.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The bow index.
        """
        return self.sdk.SBC_GetBowIndex(self._serial, self._ch(channel))

    def get_calibration_file(self, channel):
        """Get the calibration file for this motor.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        self.sdk.SBC_GetCalibrationFile(self._serial, self._ch(channel), filename, size)
        return filename.raw.decode('utf-8').rstrip('\x00')

    def get_device_unit_from_real_value(self, channel, real_value, unit_type):
        """Converts a real-world value to a device value.

        Either :meth:`load_settings`, :meth:`load_named_settings` or :meth:`set_motor_params_ext`
        must be called before calling this function, otherwise the returned value will always be 0.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
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
        device = c_int()
        unit = self.convert_to_enum(unit_type, UnitType)
        self.sdk.SBC_GetDeviceUnitFromRealValue(self._serial, self._ch(channel), real_value, byref(device), unit)
        return device.value

    def get_digital_outputs(self, channel):
        """Gets the digital output bits.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            Bit mask of states of the 4 digital output pins.
        """
        return self.sdk.SBC_GetDigitalOutputs(self._serial, self._ch(channel))

    def get_encoder_counter(self, channel):
        """Get the Encoder Counter.

        For devices that have an encoder, the current encoder position can be read.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            Encoder count of encoder units.
        """
        return self.sdk.SBC_GetEncoderCounter(self._serial, self._ch(channel))

    def get_firmware_version(self, channel):
        """Gets the version number of the device firmware.

        Returns
        -------
        :class:`str`
            The firmware version.
        """
        return self.to_version(self.sdk.SBC_GetFirmwareVersion(self._serial, self._ch(channel)))

    def get_hardware_info(self, channel):
        """Gets the hardware information from the device.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`.structs.TLI_HardwareInformation`
            The hardware information.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        return self._get_hardware_info(self.sdk.SBC_GetHardwareInfo, channel=self._ch(channel))

    def get_hardware_info_block(self, channel):
        """Gets the hardware information in a block.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        self.sdk.SBC_GetHardwareInfoBlock(self._serial, self._ch(channel), byref(info))
        return info

    def get_homing_params_block(self, channel):
        """Get the homing parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        self.sdk.SBC_GetHomingParamsBlock(self._serial, self._ch(channel), byref(params))
        return params

    def get_homing_velocity(self, channel):
        """Gets the homing velocity.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The homing velocity in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SBC_GetHomingVelocity(self._serial, self._ch(channel))

    def get_input_voltage(self, channel):
        """Gets the analogue input voltage reading.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The input voltage 0-32768 corresponding to 0-5V.
        """
        return self.sdk.SBC_GetInputVoltage(self._serial, self._ch(channel))

    def get_jog_mode(self, channel):
        """Gets the jog mode.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        self.sdk.SBC_GetJogMode(self._serial, self._ch(channel), byref(mode), byref(stop_mode))
        return MOT_JogModes(mode.value), MOT_StopModes(stop_mode.value)

    def get_jog_params_block(self, channel):
        """Get the jog parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        self.sdk.SBC_GetJogParamsBlock(self._serial, self._ch(channel), byref(params))
        return params

    def get_jog_step_size(self, channel):
        """Gets the distance to move when jogging.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The step size in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SBC_GetJogStepSize(self._serial, self._ch(channel))

    def get_jog_vel_params(self, channel):
        """Gets the jog velocity parameters.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        self.sdk.SBC_GetJogVelParams(self._serial, self._ch(channel), byref(acceleration), byref(max_velocity))
        return max_velocity.value, acceleration.value

    def get_joystick_params(self, channel):
        """Gets the joystick parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`.structs.MOT_JoystickParameters`
            The joystick parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_JoystickParameters()
        self.sdk.SBC_GetJoystickParams(self._serial, self._ch(channel), byref(params))
        return params

    def get_limit_switch_params(self, channel):
        """Gets the limit switch parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        cw_limit = MOT_LimitSwitchModes()
        ccw_limit = MOT_LimitSwitchModes()
        cw_pos = c_uint()
        ccw_pos = c_uint()
        soft_limit = MOT_LimitSwitchSWModes()
        self.sdk.SBC_GetLimitSwitchParams(self._serial, self._ch(channel), byref(cw_limit), byref(ccw_limit),
                                          byref(cw_pos), byref(ccw_pos), byref(soft_limit))
        return cw_limit, ccw_limit, cw_pos.value, ccw_pos.value, soft_limit

    def get_limit_switch_params_block(self, channel):
        """Get the limit switch parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        self.sdk.SBC_GetLimitSwitchParamsBlock(self._serial, self._ch(channel), byref(params))
        return params

    def get_motor_params(self, channel):
        """Gets the motor stage parameters.

        Deprecated: calls :meth:`get_motor_params_ext`
        """
        return self.get_motor_params_ext(channel)

    def get_motor_params_ext(self, channel):
        """Gets the motor stage parameters.

        These parameters, when combined define the stage motion in terms of
        ``RealWorldUnits`` [millimeters or degrees]. The real-world unit
        is defined from ``steps_per_rev * gear_box_ratio / pitch``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
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
        steps = c_double()
        gear = c_double()
        pitch = c_double()
        self.sdk.SBC_GetMotorParamsExt(self._serial, self._ch(channel), byref(steps), byref(gear), byref(pitch))
        return steps.value, gear.value, pitch.value

    def get_motor_travel_limits(self, channel):
        """Gets the motor stage min and max position.

        These define the range of travel for the stage.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        self.sdk.SBC_GetMotorTravelLimits(self._serial, self._ch(channel), byref(min_position), byref(max_position))
        return min_position.value, max_position.value

    def get_motor_travel_mode(self, channel):
        """Get the motor travel mode.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`.enums.MOT_TravelModes`
            The travel mode.
        """
        return MOT_TravelModes(self.sdk.SBC_GetMotorTravelMode(self._serial, self._ch(channel)))

    def get_motor_velocity_limits(self, channel):
        """Gets the motor stage maximum velocity and acceleration.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        vel = c_double()
        acc = c_double()
        self.sdk.SBC_GetMotorVelocityLimits(self._serial, self._ch(channel), byref(vel), byref(acc))
        return vel.value, acc.value

    def get_move_absolute_position(self, channel):
        """Gets the move absolute position.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The move absolute position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SBC_GetMoveAbsolutePosition(self._serial, self._ch(channel))

    def get_move_relative_distance(self, channel):
        """Gets the move relative distance.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The move relative position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SBC_GetMoveRelativeDistance(self._serial, self._ch(channel))

    def get_next_message(self, channel):
        """Get the next Message Queue item, if it is available. See :mod:`.messages`.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        msg_type = WORD()
        msg_id = WORD()
        msg_data = DWORD()
        self.sdk.SBC_GetNextMessage(self._serial, self._ch(channel), byref(msg_type), byref(msg_id), byref(msg_data))
        return msg_type.value, msg_id.value, msg_data.value

    def get_num_channels(self):
        """Gets the number of channels in the device.

        Returns
        -------
        :class:`int`
            The number of channels.
        """
        return self.sdk.SBC_GetNumChannels(self._serial)

    def get_number_positions(self, channel):
        """Get the number of positions.

        This function will get the maximum position reachable by the device.
        The motor may need to be set to its :meth:`home` position before this
        parameter can be used.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The number of positions.
        """
        return self.sdk.SBC_GetNumberPositions(self._serial, self._ch(channel))

    def get_pid_loop_encoder_coeff(self, channel):
        """Gets the Encoder PID loop encoder coefficient.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`float`
            The Encoder PID loop encoder coefficient.
        """
        return self.sdk.SBC_GetPIDLoopEncoderCoeff(self._serial, self._ch(channel))

    def get_pid_loop_encoder_params(self, channel):
        """Gets the Encoder PID loop parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`.structs.MOT_PIDLoopEncoderParams`
            The parameters used to define the Encoder PID Loop.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_PIDLoopEncoderParams()
        self.sdk.SBC_GetPIDLoopEncoderParams(self._serial, self._ch(channel), byref(params))
        return params

    def get_position(self, channel):
        """Get the current position.

        The current position is the last recorded position. The current position is updated either by the
        polling mechanism or by calling :meth:`request_position`.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        index : :class:`int`
            The current position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SBC_GetPosition(self._serial, self._ch(channel))

    def get_position_counter(self, channel):
        """Get the position counter.

        The position counter is identical to the position parameter.
        The position counter is set to zero when homing is complete.
        The position counter can also be set using :meth:`set_position_counter` if homing is not to be performed.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The position counter in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SBC_GetPositionCounter(self._serial, self._ch(channel))

    def get_power_params(self, channel):
        """Gets the power parameters for the stepper motor.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        self.sdk.SBC_GetPowerParams(self._serial, self._ch(channel), byref(params))
        return params

    def get_rack_digital_outputs(self):
        """Gets the rack digital output bits.

        Returns
        -------
        :class:`int`
            Bit mask of states of the 4 digital output pins.
        """
        return self.sdk.SBC_GetRackDigitalOutputs(self._serial)

    def get_rack_status_bits(self):
        """Gets the Rack status bits.

        Returns
        -------
        :class:`int`
            The status bits including 4 with one per electronic input pin.
        """
        return self.sdk.SBC_GetRackStatusBits(self._serial)

    def get_real_value_from_device_unit(self, channel, device_value, unit_type):
        """Converts a device value to a real-world value.

        Either :meth:`load_settings`, :meth:`load_named_settings` or :meth:`set_motor_params_ext`
        must be called before calling this function, otherwise the returned value will always be 0.0.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
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
        real = c_double()
        unit = self.convert_to_enum(unit_type, UnitType)
        self.sdk.SBC_GetRealValueFromDeviceUnit(self._serial, self._ch(channel), device_value, byref(real), unit)
        return real.value

    def get_soft_limit_mode(self, channel):
        """Gets the software limits mode.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`.enums.MOT_LimitsSoftwareApproachPolicy`
            The software limits mode.
        """
        return MOT_LimitsSoftwareApproachPolicy(self.sdk.SBC_GetSoftLimitMode(self._serial, self._ch(channel)))

    def get_software_version(self):
        """Gets version number of the device software.

        Returns
        -------
        :class:`str`
            The device software version.
        """
        return self.to_version(self.sdk.SBC_GetSoftwareVersion(self._serial))

    def get_stage_axis_max_pos(self, channel):
        """Gets the Stepper Motor maximum stage position.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The maximum position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SBC_GetStageAxisMaxPos(self._serial, self._ch(channel))

    def get_stage_axis_min_pos(self, channel):
        """Gets the Stepper Motor minimum stage position.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The minimum position in ``DeviceUnits`` (see manual).
        """
        return self.sdk.SBC_GetStageAxisMinPos(self._serial, self._ch(channel))

    def get_status_bits(self, channel):
        """Get the current status bits.

        This returns the latest status bits received from the device.
        To get new status bits, use :meth:`request_status_bits` or use
        the polling function, :meth:`start_polling`.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The status bits from the device.
        """
        return self.sdk.SBC_GetStatusBits(self._serial, self._ch(channel))

    def get_trigger_switches(self, channel):
        """Gets the trigger switch parameter.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            Trigger mask where:

            * Bit 0 - Input trigger enabled.
            * Bit 1 - Output trigger enabled.
            * Bit 2 - Output Passthrough mode enabled where Output Trigger mirrors Input Trigger.
            * Bit 3 - Output trigger high when moving.
            * Bit 4 - Performs relative move when input trigger goes high.
            * Bit 5 - Performs absolute move when input trigger goes high.
            * Bit 6 - Perfgorms home when input trigger goes high.
            * Bit 7 - Output triggers when motor moved by software command.

        """
        return self.sdk.SBC_GetTriggerSwitches(self._serial, self._ch(channel))

    def get_vel_params(self, channel):
        """Gets the move velocity parameters.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        self.sdk.SBC_GetVelParams(self._serial, self._ch(channel), byref(acceleration), byref(max_velocity))
        return max_velocity.value, acceleration.value

    def get_vel_params_block(self, channel):
        """Get the move velocity parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        self.sdk.SBC_GetVelParamsBlock(self._serial, self._ch(channel), byref(params))
        return params

    def has_last_msg_timer_overrun(self, channel):
        """Queries if the time since the last message has exceeded the
        ``lastMsgTimeout`` set by :meth:`enable_last_msg_timer`.

        This can be used to determine whether communications with the device is
        still good.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`bool`
            :data:`True` if last message timer has elapsed, :data:`False` if monitoring is
            not enabled or if time of last message received is less than ``lastMsgTimeout``.
        """
        return self.sdk.SBC_HasLastMsgTimerOverrun(self._serial, self._ch(channel))

    def home(self, channel):
        """Home the device.

        Homing the device will set the device to a known state and determine
        the home position.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_Home(self._serial, self._ch(channel))

    def identify(self, channel):
        """Sends a command to the device to make it identify itself.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_Identify(self._serial, self._ch(channel))

    def is_calibration_active(self, channel):
        """Is a calibration file active for this motor?

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`bool`
            Whether a calibration file is active.
        """
        return self.sdk.SBC_IsCalibrationActive(self._serial, self._ch(channel))

    def is_channel_valid(self, channel):
        """Verifies that the specified channel is valid.

        Parameters
        ----------
        channel : :class:`int`
            The requested channel number (1 to n).

        Returns
        -------
        :class:`bool`
            Whether the channel is valid.
        """
        return self.sdk.SBC_IsChannelValid(self._serial, channel)

    def load_settings(self, channel):
        """Update device with stored settings.

        The settings are read from ``ThorlabsDefaultSettings.xml``, which
        gets created when the Kinesis software is installed.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_LoadSettings(self._serial, self._ch(channel))

    def load_named_settings(self, channel, settings_name):
        """Update device with named settings.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        settings_name : :class:`str`
            The name of the device to load the settings for. Examples for the value
            of `setting_name` can be found in `ThorlabsDefaultSettings.xml``, which
            gets created when the Kinesis software is installed.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_LoadNamedSettings(self._serial, self._ch(channel), settings_name)

    def max_channel_count(self):
        """Gets the number of channels available to this device.

        This function returns the number of available bays, not the number of bays filled.

        Returns
        -------
        :class:`int`
            The number of channels available on this device.
        """
        return self.sdk.SBC_MaxChannelCount(self._serial)

    def message_queue_size(self, channel):
        """Gets the size of the message queue.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The number of messages in the queue.
        """
        return self.sdk.SBC_MessageQueueSize(self._serial, self._ch(channel))

    def move_absolute(self, channel):
        """Moves the device to the position defined in the :meth:`set_move_absolute_position` command.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_MoveAbsolute(self._serial, self._ch(channel))

    def move_at_velocity(self, channel, direction):
        """Start moving at the current velocity in the specified direction.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        direction : :class:`.enums.MOT_TravelDirection`
            The required direction of travel as a :class:`.enums.MOT_TravelDirection`
            enum value or member name.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        direction_ = self.convert_to_enum(direction, MOT_TravelDirection, prefix='MOT_')
        self.sdk.SBC_MoveAtVelocity(self._serial, self._ch(channel), direction_)

    def move_jog(self, channel, jog_direction):
        """Perform a jog.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        jog_direction : :class:`.enums.MOT_TravelDirection`
            The jog direction as a :class:`.enums.MOT_TravelDirection` enum value
            or member name.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        direction = self.convert_to_enum(jog_direction, MOT_TravelDirection, prefix='MOT_')
        self.sdk.SBC_MoveJog(self._serial, self._ch(channel), direction)

    def move_relative(self, channel, displacement):
        """Move the motor by a relative amount.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        displacement : :class:`int`
            Signed displacement in ``DeviceUnits`` (see manual).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_MoveRelative(self._serial, self._ch(channel), displacement)

    def move_relative_distance(self, channel):
        """Moves the device by a relative distance defined by :meth:`set_move_relative_distance`.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_MoveRelativeDistance(self._serial, self._ch(channel))

    def move_to_position(self, channel, index):
        """Move the device to the specified position (index).

        The motor may need to be set to its :meth:`home` position before a
        position can be set.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        index : :class:`int`
            The position in ``DeviceUnits`` (see manual).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_MoveToPosition(self._serial, self._ch(channel), index)

    def needs_homing(self, channel):
        """Does the device need to be :meth:`home`\'d before a move can be performed?

        Deprecated: calls :meth:`can_move_without_homing_first` instead.

        Returns
        -------
        :class:`bool`
            Whether the device needs to be homed.
        """
        return self.can_move_without_homing_first(channel)

    def open(self):
        """Open the device for communication.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_Open(self._serial)

    def persist_settings(self, channel):
        """Persist device settings to device.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        """
        self.sdk.SBC_PersistSettings(self._serial, self._ch(channel))

    def polling_duration(self, channel):
        """Gets the polling loop duration.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The time between polls in milliseconds or 0 if polling is not active.
        """
        return self.sdk.SBC_PollingDuration(self._serial, self._ch(channel))

    def register_message_callback(self, channel, callback):
        """Registers a callback on the message queue.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        callback : :class:`~msl.equipment.resources.thorlabs.kinesis.callbacks.MotionControlCallback`
            A function to be called whenever messages are received.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RegisterMessageCallback(self._serial, self._ch(channel), callback)

    def request_backlash(self, channel):
        """Requests the backlash.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestBacklash(self._serial, self._ch(channel))

    def request_bow_index(self, channel):
        """Requests the stepper motor bow index.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestBowIndex(self._serial, self._ch(channel))

    def request_digital_outputs(self, channel):
        """Requests the digital output bits.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestDigitalOutputs(self._serial, self._ch(channel))

    def request_encoder_counter(self, channel):
        """Requests the encoder counter.

        For devices that have an encoder, the current encoder position can be read.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestEncoderCounter(self._serial, self._ch(channel))

    def request_homing_params(self, channel):
        """Requests the homing parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestHomingParams(self._serial, self._ch(channel))

    def request_input_voltage(self, channel):
        """Requests the analogue input voltage reading.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestInputVoltage(self._serial, self._ch(channel))

    def request_jog_params(self, channel):
        """Requests the jog parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestJogParams(self._serial, self._ch(channel))

    def request_joystick_params(self, channel):
        """Requests the joystick parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestJoystickParams(self._serial, self._ch(channel))

    def request_limit_switch_params(self, channel):
        """Requests the limit switch parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestLimitSwitchParams(self._serial, self._ch(channel))

    def request_move_absolute_position(self, channel):
        """Requests the position of next absolute move.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestMoveAbsolutePosition(self._serial, self._ch(channel))

    def request_move_relative_distance(self, channel):
        """Requests the relative move distance.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestMoveRelativeDistance(self._serial, self._ch(channel))

    def request_pid_loop_encoder_params(self, channel):
        """Requests the Encoder PID loop parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestPIDLoopEncoderParams(self._serial, self._ch(channel))

    def request_position(self, channel):
        """Requests the current position.

        This needs to be called to get the device to send its current position.
        Note, this is called automatically if ``Polling`` is enabled for the device
        using :meth:`start_polling`.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestPosition(self._serial, self._ch(channel))

    def request_power_params(self, channel):
        """Requests the power parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestPowerParams(self._serial, self._ch(channel))

    def request_rack_digital_outputs(self):
        """Requests the rack digital output bits.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestRackDigitalOutputs(self._serial)

    def request_rack_status_bits(self):
        """Requests the Rack status bits be downloaded.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestRackStatusBits(self._serial)

    def request_settings(self, channel):
        """Requests that all settings are downloaded from the device.

        This function requests that the device upload all its settings to the DLL.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestSettings(self._serial, self._ch(channel))

    def request_status_bits(self, channel):
        """Request the status bits which identify the current motor state.

        This needs to be called to get the device to send its current status bits.
        Note, this is called automatically if ``Polling`` is enabled for the device
        using :meth:`start_polling`.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestStatusBits(self._serial, self._ch(channel))

    def request_trigger_switches(self, channel):
        """Requests the trigger switch parameter.

        .. warning::
           This function is currently not in the DLL, as of v1.14.8, but it is in the header file.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestTriggerSwitches(self._serial, self._ch(channel))

    def request_vel_params(self, channel):
        """Requests the velocity parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_RequestVelParams(self._serial, self._ch(channel))

    def reset_rotation_modes(self, channel):
        """Reset the rotation modes for a rotational device.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_ResetRotationModes(self._serial, self._ch(channel))

    def resume_move_messages(self, channel):
        """Resume suspended move messages.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_ResumeMoveMessages(self._serial, self._ch(channel))

    def set_backlash(self, channel, distance):
        """Sets the backlash distance (used to control hysteresis).

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        distance : :class:`int`
            The backlash distance in ``DeviceUnits`` (see manual).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetBacklash(self._serial, self._ch(channel), distance)

    def set_bow_index(self, channel, bow_index):
        """Sets the stepper motor bow index.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        bow_index : :class:`int`
            The bow index.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetBowIndex(self._serial, self._ch(channel), bow_index)

    def set_calibration_file(self, channel, path, enabled):
        """Set the calibration file for this motor.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
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
        self.sdk.SBC_SetCalibrationFile(self._serial, self._ch(channel), path.encode('utf-8'), enabled)

    def set_digital_outputs(self, channel, outputs_bits):
        """Sets the digital output bits.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        outputs_bits : :class:`int`
            Bit mask to set states of the 4 digital output pins.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetDigitalOutputs(self._serial, self._ch(channel), outputs_bits)

    def set_direction(self, channel, reverse):
        """Sets the motor direction sense.

        This function is used because some actuators use have directions of motion
        reversed. This parameter will tell the system to reverse the direction sense
        when moving, jogging etc.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        reverse : :class:`bool`
            If :data:`True` then directions will be swapped on these moves.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetDirection(self._serial, self._ch(channel), reverse)

    def set_encoder_counter(self, channel, count):
        """Set the Encoder Counter values.

        Setting the encoder counter to zero, effectively defines a home position on the encoder strip.
        Setting this value does not move the device.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        count : :class:`int`
            The encoder count in encoder units.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetEncoderCounter(self._serial, self._ch(channel), count)

    def set_homing_params_block(self, channel, direction, limit, velocity, offset):
        """Set the homing parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
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
        self.sdk.SBC_SetHomingParamsBlock(self._serial, self._ch(channel), byref(params))

    def set_homing_velocity(self, channel, velocity):
        """Sets the homing velocity.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        velocity : :class:`int`
            The homing velocity in ``DeviceUnits`` (see manual).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetHomingVelocity(self._serial, self._ch(channel), velocity)

    def set_jog_mode(self, channel, mode, stop_mode):
        """Sets the jog mode.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
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
        self.sdk.SBC_SetJogMode(self._serial, self._ch(channel), mode_, stop_mode_)

    def set_jog_params_block(self, channel, jog_params):
        """Set the jog parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        jog_params : :class:`.structs.MOT_JogParameters`
            The jog parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        if not isinstance(jog_params, MOT_JogParameters):
            self.raise_exception('The jog parameter must be a MOT_JogParameters struct')
        self.sdk.SBC_SetJogParamsBlock(self._serial, self._ch(channel), byref(jog_params))

    def set_jog_step_size(self, channel, step_size):
        """Sets the distance to move on jogging.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        step_size : :class:`int`
            The step size in ``DeviceUnits`` (see manual).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetJogStepSize(self._serial, self._ch(channel), step_size)

    def set_jog_vel_params(self, channel, max_velocity, acceleration):
        """Sets jog velocity parameters.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        max_velocity : :class:`int`
            The maximum velocity in ``DeviceUnits`` (see manual).
        acceleration : :class:`int`
            The acceleration in ``DeviceUnits`` (see manual).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetJogVelParams(self._serial, self._ch(channel), acceleration, max_velocity)

    def set_joystick_params(self, channel, joystick_params):
        """Sets the joystick parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        joystick_params : :class:`.structs.MOT_JoystickParameters`
            The joystick parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        if not isinstance(joystick_params, MOT_JoystickParameters):
            self.raise_exception('The joystick parameter must be a MOT_JoystickParameters struct')
        self.sdk.SBC_SetJoystickParams(self._serial, self._ch(channel), byref(joystick_params))

    def set_limit_switch_params(self, channel, cw_lim, ccw_lim, cw_pos, ccw_pos, soft_limit_mode):
        """Sets the limit switch parameters.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
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
        self.sdk.SBC_SetLimitSwitchParams(self._serial, self._ch(channel), cw_lim_, ccw_lim_, cw_pos, ccw_pos, sw)

    def set_limit_switch_params_block(self, channel, params):
        """Set the limit switch parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        params : :class:`.structs.MOT_LimitSwitchParameters`
            The new limit switch parameters.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        if not isinstance(params, MOT_LimitSwitchParameters):
            self.raise_exception('The limit switch parameter must be a MOT_LimitSwitchParameters struct')
        self.sdk.SBC_SetLimitSwitchParamsBlock(self._serial, self._ch(channel), byref(params))

    def set_limits_software_approach_policy(self, channel, policy):
        """Sets the software limits policy.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        policy : :class:`.enums.MOT_LimitsSoftwareApproachPolicy`
            The soft limit mode as a :class:`.enums.MOT_LimitsSoftwareApproachPolicy` enum
            value or member name.
        """
        policy_ = self.convert_to_enum(policy, MOT_LimitsSoftwareApproachPolicy)
        self.sdk.SBC_SetLimitsSoftwareApproachPolicy(self._serial, self._ch(channel), policy_)

    def set_motor_params(self, channel, steps_per_rev, gear_box_ratio, pitch):
        """Sets the motor stage parameters.

        Deprecated: calls :meth:`set_motor_params_ext`
        """
        self.set_motor_params_ext(channel, steps_per_rev, gear_box_ratio, pitch)

    def set_motor_params_ext(self, channel, steps_per_rev, gear_box_ratio, pitch):
        """Sets the motor stage parameters.

        These parameters, when combined, define the stage motion in terms of
        ``RealWorldUnits`` [millimeters or degrees]. The real-world unit
        is defined from ``steps_per_rev * gear_box_ratio / pitch``.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
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
        self.sdk.SBC_SetMotorParamsExt(self._serial, self._ch(channel), steps_per_rev, gear_box_ratio, pitch)

    def set_motor_travel_limits(self, channel, min_position, max_position):
        """Sets the motor stage min and max position.

        These define the range of travel for the stage.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        min_position : :class:`float`
            The minimum position in ``RealWorldUnits`` [millimeters or degrees].
        max_position : :class:`float`
            The maximum position in ``RealWorldUnits`` [millimeters or degrees].

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetMotorTravelLimits(self._serial, self._ch(channel), min_position, max_position)

    def set_motor_travel_mode(self, channel, travel_mode):
        """Set the motor travel mode.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        travel_mode : :class:`.enums.MOT_TravelModes`
            The travel mode as a :class:`.enums.MOT_TravelModes` enum value or
            member name.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        mode = self.convert_to_enum(travel_mode, MOT_TravelModes, prefix='MOT_')
        self.sdk.SBC_SetMotorTravelMode(self._serial, self._ch(channel), mode)

    def set_motor_velocity_limits(self, channel, max_velocity, max_acceleration):
        """Sets the motor stage maximum velocity and acceleration.

        See :meth:`get_real_value_from_device_unit` for converting from a
        ``DeviceUnit`` to a ``RealValue``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        max_velocity : :class:`float`
            The maximum velocity in ``RealWorldUnits`` [millimeters or degrees].
        max_acceleration : :class:`float`
            The maximum acceleration in ``RealWorldUnits`` [millimeters or degrees].

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetMotorVelocityLimits(self._serial, self._ch(channel), max_velocity, max_acceleration)

    def set_move_absolute_position(self, channel, position):
        """Sets the move absolute position.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        position : :class:`int`
            The absolute position in ``DeviceUnits`` (see manual).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetMoveAbsolutePosition(self._serial, self._ch(channel), position)

    def set_move_relative_distance(self, channel, distance):
        """Sets the move relative distance.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        distance : :class:`int`
            The relative position in ``DeviceUnits`` (see manual).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetMoveRelativeDistance(self._serial, self._ch(channel), distance)

    def set_pid_loop_encoder_coeff(self, channel, coeff):
        """Sets the Encoder PID loop encoder coefficient.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        coeff : :class:`float`
            The Encoder PID loop encoder coefficient. Set to 0.0 to disable the encoder or if no encoder is
            present otherwise the positive encoder coefficient.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetPIDLoopEncoderCoeff(self._serial, self._ch(channel), coeff)

    def set_pid_loop_encoder_params(self, channel, mode, prop_gain, int_gain, diff_gain, limit, tol):
        """Sets the Encoder PID loop parameters.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        mode : :class:`.enums.MOT_PID_LoopMode`
            The Encoder PID loop mode as a :class:`.enums.MOT_PID_LoopMode` enum value or member name.
        prop_gain : :class:`int`
            The Encoder PID Loop proportional gain. Range 0 to 2^24.
        int_gain : :class:`int`
            The Encoder PID Loop integral gain. Range 0 to 2^24.
        diff_gain : :class:`int`
            The Encoder PID Loop differential gain. Range 0 to 2^24.
        limit : :class:`int`
            The Encoder PID Loop output limit. Range 0 to 2^15.
        tol : :class:`int`
            The Encoder PID Loop tolerance. Range 0 to 2^15.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_PIDLoopEncoderParams()
        params.loopMode = self.convert_to_enum(mode, MOT_PID_LoopMode, prefix='MOT_')
        params.proportionalGain = prop_gain
        params.integralGain = int_gain
        params.differentialGain = diff_gain
        params.PIDOutputLimit = limit
        params.PIDTolerance = tol
        self.sdk.SBC_SetPIDLoopEncoderParams(self._serial, self._ch(channel), byref(params))

    def set_position_counter(self, channel, count):
        """Set the position counter.

        Setting the position counter will locate the current position.
        Setting the position counter will effectively define the home position
        of a motor.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        count : :class:`int`
            The position counter in ``DeviceUnits`` (see manual).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetPositionCounter(self._serial, self._ch(channel), count)

    def set_power_params(self, channel, rest, move):
        """Sets the power parameters for the stepper motor.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
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
            self.raise_exception('The rest power parameter is {}. Must be 0 <= rest <=100'.format(rest))
        if move < 0 or move > 100:
            self.raise_exception('The move power parameter is {}. Must be 0 <= move <=100'.format(move))
        params = MOT_PowerParameters()
        params.restPercentage = int(rest)
        params.movePercentage = int(move)
        self.sdk.SBC_SetPowerParams(self._serial, self._ch(channel), byref(params))

    def set_rack_digital_outputs(self, outputs_bits):
        """Sets the rack digital output bits.

        Parameters
        ----------
        outputs_bits : :class:`int`
            Bit mask to set states of the 4 digital output pins.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetRackDigitalOutputs(self._serial, outputs_bits)

    def set_rotation_modes(self, channel, mode, direction):
        """Set the rotation modes for a rotational device.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
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
        self.sdk.SBC_SetRotationModes(self._serial, self._ch(channel), mode, direction)

    def set_stage_axis_limits(self, channel, min_position, max_position):
        """Sets the stage axis position limits.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        min_position : :class:`int`
            The minimum position in ``DeviceUnits`` (see manual).
        max_position : :class:`int`
            The maximum position in ``DeviceUnits`` (see manual).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetStageAxisLimits(self._serial, self._ch(channel), min_position, max_position)

    def set_trigger_switches(self, channel, indicator_bits):
        """Sets the trigger switch bits.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        indicator_bits : :class:`int`
            Sets the 8 bits indicating action on trigger input and events to trigger electronic output.

            * Bit 0 - Input trigger enabled.
            * Bit 1 - Output trigger enabled.
            * Bit 2 - Output pass-through mode enabled where Output Trigger mirrors Input Trigger.
            * Bit 3 - Output trigger high when moving.
            * Bit 4 - Performs relative move when input trigger goes high.
            * Bit 5 - Performs absolute move when input trigger goes high.
            * Bit 6 - Performs home when input trigger goes high.
            * Bit 7 - Output triggers when motor moved by software command.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetTriggerSwitches(self._serial, self._ch(channel), indicator_bits)

    def set_vel_params(self, channel, max_velocity, acceleration):
        """Sets the move velocity parameters.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        max_velocity : :class:`int`
            The maximum velocity in ``DeviceUnits`` (see manual).
        acceleration : :class:`int`
            The acceleration in ``DeviceUnits`` (see manual).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SetVelParams(self._serial, self._ch(channel), acceleration, max_velocity)

    def set_vel_params_block(self, channel, min_velocity, max_velocity, acceleration):
        """Set the move velocity parameters.

        See :meth:`get_device_unit_from_real_value` for converting from a
        ``RealValue`` to a ``DeviceUnit``.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        min_velocity : :class:`int`
            The minimum velocity in ``DeviceUnits`` (see manual).
        max_velocity : :class:`int`
            The maximum velocity in ``DeviceUnits`` (see manual)..
        acceleration : :class:`int`
            The acceleration in ``DeviceUnits`` (see manual)..

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        params = MOT_VelocityParameters()
        params.minVelocity = min_velocity
        params.acceleration = acceleration
        params.maxVelocity = max_velocity
        self.sdk.SBC_SetVelParamsBlock(self._serial, self._ch(channel), byref(params))

    def start_polling(self, channel, milliseconds):
        """Starts the internal polling loop.

        This function continuously requests position and status messages.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        milliseconds : :class:`int`
            The polling rate, in milliseconds.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_StartPolling(self._serial, self._ch(channel), int(milliseconds))

    def stop_immediate(self, channel):
        """Stop the current move immediately (with the risk of losing track of the position).

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_StopImmediate(self._serial, self._ch(channel))

    def stop_polling(self, channel):
        """Stops the internal polling loop.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        """
        self.sdk.SBC_StopPolling(self._serial, self._ch(channel))

    def stop_profiled(self, channel):
        """Stop the current move using the current velocity profile.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_StopProfiled(self._serial, self._ch(channel))

    def suspend_move_messages(self, channel):
        """Suspend automatic messages at ends of moves.

        Useful to speed up part of real-time system with lots of short moves.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Raises
        ------
        :exc:`~msl.equipment.exceptions.ThorlabsError`
            If not successful.
        """
        self.sdk.SBC_SuspendMoveMessages(self._serial, self._ch(channel))

    def time_since_last_msg_received(self, channel):
        """Gets the time, in milliseconds, since the last message was received.

        This can be used to determine whether communications with the device is
        still good.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

        Returns
        -------
        :class:`int`
            The time, in milliseconds, since the last message was received.
        :class:`bool`
            :data:`True` if monitoring is enabled otherwise :data:`False`.
        """
        ms = c_int64()
        ret = self.sdk.SBC_TimeSinceLastMsgReceived(self._serial, self._ch(channel), byref(ms))
        return ms.value, ret

    def uses_pid_loop_encoding(self, channel):
        """Determines if we can uses PID loop encoding.

        This is true if the stage supports PID Loop Encoding. Requires :meth:`get_pid_loop_encoder_coeff`
        to have a positive non-zero coefficient, see also :meth:`set_pid_loop_encoder_coeff`.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).
        """
        self.sdk.SBC_UsesPIDLoopEncoding(self._serial, self._ch(channel))

    def wait_for_message(self, channel):
        """Wait for next Message Queue item if it is available. See :mod:`.messages`.

        Parameters
        ----------
        channel : :class:`int`
            The channel number (1 to n).

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
        msg_type = WORD()
        msg_id = WORD()
        msg_data = DWORD()
        self.sdk.SBC_WaitForMessage(self._serial, self._ch(channel), byref(msg_type), byref(msg_id), byref(msg_data))
        return msg_type.value, msg_id.value, msg_data.value

    def _ch(self, channel):
        """checks that the channel number is valid"""
        ch = int(channel)
        if ch < 1 or ch > self._num_channels:
            msg = 'Invalid channel number {}. '.format(channel)
            if self._num_channels == 1:
                self.raise_exception(msg + 'The channel number must be set to 1')
            else:
                self.raise_exception(msg + 'Must be 1 <= channel <= ' + str(self._num_channels))
        return ch


if __name__ == '__main__':
    from msl.equipment.resources.thorlabs.kinesis import _print
    _print(BenchtopStepperMotor, Benchtop_StepperMotor_FCNS, 'Thorlabs.MotionControl.Benchtop.StepperMotor.h')
