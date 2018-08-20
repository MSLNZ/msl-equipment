"""
Structs defined in Thorlabs Kinesis v1.14.10
"""
from ctypes import c_byte, c_bool, c_char, c_ushort, c_uint16, c_short, \
    c_int16, c_uint, c_int, c_int32, c_uint32, c_float, Structure

from msl.equipment.resources.utils import BYTE, WORD, DWORD

NUM_TIA_RANGES = 16


class TLI_DeviceInfo(Structure):
    _fields_ = [
        ('typeID', DWORD),
        ('description', c_char * 65),
        ('serialNo', c_char * 9),
        ('PID', DWORD),
        ('isKnownType', c_bool),
        ('motorType', c_int),
        ('isPiezoDevice', c_bool),
        ('isLaser', c_bool),
        ('isCustomType', c_bool),
        ('isRack', c_bool),
        ('maxChannels', c_short),
    ]


class TLI_HardwareInformation(Structure):
    _fields_ = [
        ('serialNumber', DWORD),
        ('modelNumber', c_char * 8),
        ('type', WORD),
        ('firmwareVersion', DWORD),
        ('notes', c_char * 48),
        ('deviceDependantData', BYTE * 12),
        ('hardwareVersion', WORD),
        ('modificationState', WORD),
        ('numChannels', c_short),
    ]


class MOT_VelocityParameters(Structure):
    _fields_ = [
        ('minVelocity', c_int),
        ('acceleration', c_int),
        ('maxVelocity', c_int),
    ]


class MOT_JogParameters(Structure):
    _fields_ = [
        ('mode', c_short),
        ('stepSize', c_uint),
        ('velParams', MOT_VelocityParameters),
        ('stopMode', c_short),
    ]


class MOT_HomingParameters(Structure):
    _fields_ = [
        ('direction', c_short),
        ('limitSwitch', c_short),
        ('velocity', c_uint),
        ('offsetDistance', c_uint),
    ]


class MOT_VelocityProfileParameters(Structure):
    _fields_ = [
        ('mode', WORD),
        ('jerk', DWORD),
        ('notUsed', WORD),
        ('lastNotUsed', WORD),
    ]


class MOT_StageAxisParameters(Structure):
    _fields_ = [
        ('stageID', WORD),
        ('axisID', WORD),
        ('partNumber', c_char * 16),
        ('serialNumber', DWORD),
        ('countsPerUnit', DWORD),
        ('minPosition', c_int),
        ('maxPosition', c_int),
        ('maxAcceleration', c_int),
        ('maxDecceleration', c_int),
        ('maxVelocity', c_int),
        ('reserved1', WORD),
        ('reserved2', WORD),
        ('reserved3', WORD),
        ('reserved4', WORD),
        ('reserved5', DWORD),
        ('reserved6', DWORD),
        ('reserved7', DWORD),
        ('reserved8', DWORD),
    ]


class MOT_JoystickParameters(Structure):
    _fields_ = [
        ('lowGearMaxVelocity', DWORD),
        ('highGearMaxVelocity', DWORD),
        ('lowGearAcceleration', DWORD),
        ('highGearAcceleration', DWORD),
        ('directionSense', c_short),
    ]


class MOT_BrushlessPositionLoopParameters(Structure):
    _fields_ = [
        ('proportionalGain', WORD),
        ('integralGain', WORD),
        ('integralLimit', DWORD),
        ('differentialGain', WORD),
        ('derivativeRecalculationTime', WORD),
        ('factorForOutput', WORD),
        ('velocityFeedForward', WORD),
        ('accelerationFeedForward', WORD),
        ('positionErrorLimit', DWORD),
        ('notUsed', WORD),
        ('lastNotUsed', WORD),
    ]


class MOT_BrushlessTrackSettleParameters(Structure):
    _fields_ = [
        ('time', WORD),
        ('settledError', WORD),
        ('maxTrackingError', WORD),
        ('notUsed', WORD),
        ('lastNotUsed', WORD),
    ]


class MOT_BrushlessCurrentLoopParameters(Structure):
    _fields_ = [
        ('phase', WORD),
        ('proportionalGain', WORD),
        ('integralGain', WORD),
        ('integralLimit', WORD),
        ('deadErrorBand', WORD),
        ('feedForward', WORD),
        ('notUsed', WORD),
        ('lastNotUsed', WORD),
    ]


class MOT_BrushlessElectricOutputParameters(Structure):
    _fields_ = [
        ('continuousCurrentLimit', WORD),
        ('excessEnergyLimit', WORD),
        ('motorSignalLimit', c_short),
        ('motorSignalBias', c_short),
        ('notUsed', WORD),
        ('lastNotUsed', WORD),
    ]


class MOT_LimitSwitchParameters(Structure):
    _fields_ = [
        ('clockwiseHardwareLimit', WORD),
        ('anticlockwiseHardwareLimit', WORD),
        ('clockwisePosition', DWORD),
        ('anticlockwisePosition', DWORD),
        ('softLimitMode', WORD),
    ]


class MOT_PowerParameters(Structure):
    _fields_ = [
        ('restPercentage', WORD),
        ('movePercentage', WORD),
    ]


class MOT_DC_PIDParameters(Structure):
    _fields_ = [
        ('proportionalGain', c_int),
        ('integralGain', c_int),
        ('differentialGain', c_int),
        ('integralLimit', c_int),
        ('parameterFilter', WORD),
    ]


class BNT_IO_Settings(Structure):
    _fields_ = [
        ('channel', WORD),
        ('amplifierCurrentLimit', WORD),
        ('amplifierLowPassFilter', WORD),
        ('feedbackSignal', WORD),
        ('BNCtriggerOrLowVoltageOut', WORD),
    ]


class NT_HVComponent(Structure):
    _fields_ = [
        ('horizontalComponent', WORD),
        ('verticalComponent', WORD),
    ]


class NT_CircleParameters(Structure):
    _fields_ = [
        ('mode', WORD),
        ('diameter', WORD),
        ('samplesPerRevolution', WORD),
        ('minDiameter', WORD),
        ('maxDiameter', WORD),
        ('algorithmAdjustment', WORD),
    ]


class NT_CircleDiameterLUT(Structure):
    _fields_ = [
        ('LUTdiameter', WORD * NUM_TIA_RANGES),
    ]


class NT_TIARangeParameters(Structure):
    _fields_ = [
        ('mode', WORD),
        ('upLimit', WORD),
        ('downLimit', WORD),
        ('settleSamples', c_short),
        ('changeToOddOrEven', WORD),
        ('newRange', WORD),
    ]


class NT_LowPassFilterParameters(Structure):
    _fields_ = [
        ('param1', WORD),
        ('param2', WORD),
        ('param3', WORD),
        ('param4', WORD),
        ('param5', WORD),
    ]


class NT_TIAReading(Structure):
    _fields_ = [
        ('absoluteReading', c_float),
        ('relativeReading', WORD),
        ('selectedRange', WORD),
        ('underOrOverRead', WORD),
    ]


class NT_IOSettings(Structure):
    _fields_ = [
        ('lowVoltageOutRange', WORD),
        ('lowVoltageOutputRoute', WORD),
        ('notYetInUse', WORD),
        ('unused', WORD),
    ]


class NT_GainParameters(Structure):
    _fields_ = [
        ('controlMode', WORD),
        ('gain', c_short),
    ]


class PZ_FeedbackLoopConstants(Structure):
    _fields_ = [
        ('proportionalTerm', c_short),
        ('integralTerm', c_short),
    ]


class PZ_LUTWaveParameters(Structure):
    _fields_ = [
        ('mode', c_short),
        ('cycleLength', c_short),
        ('numCycles', c_uint),
        ('LUTValueDelay', c_uint),
        ('preCycleDelay', c_uint),
        ('postCycleDelay', c_uint),
        ('outTriggerStart', c_short),
        ('outTriggerDuration', c_uint),
        ('numOutTriggerRepeat', c_short),
    ]


class PPC_PIDConsts(Structure):
    _fields_ = [
        ('PIDConstsP', c_float),
        ('PIDConstsI', c_float),
        ('PIDConstsD', c_float),
        ('PIDConstsDFc', c_float),
        ('PIDDerivFilterOn', c_short),
    ]


class PPC_NotchParams(Structure):
    _fields_ = [
        ('filterNo', c_short),
        ('filter1Fc', c_float),
        ('filter1Q', c_float),
        ('notchFilter1On', c_short),
        ('filter2Fc', c_float),
        ('filter2Q', c_float),
        ('notchFilter2On', c_short),
    ]


class PPC_IOSettings(Structure):
    _fields_ = [
        ('controlSrc', c_short),
        ('monitorOPSig', c_short),
        ('monitorOPBandwidth', c_short),
        ('feedbackSrc', c_short),
        ('FPBrightness', c_short),
        ('reserved1', WORD),
    ]


class MOT_PIDLoopEncoderParams(Structure):
    _fields_ = [
        ('loopMode', WORD),
        ('proportionalGain', c_int),
        ('integralGain', c_int),
        ('differentialGain', c_int),
        ('PIDOutputLimit', c_int),
        ('PIDTolerance', c_int),
    ]


class FF_IOSettings(Structure):
    _fields_ = [
        ('transitTime', c_uint),
        ('ADCspeedValue', c_uint),
        ('digIO1OperMode', WORD),
        ('digIO1SignalMode', WORD),
        ('digIO1PulseWidth', c_uint),
        ('digIO2OperMode', WORD),
        ('digIO2SignalMode', WORD),
        ('digIO2PulseWidth', c_uint),
        ('reserved1', c_int),
        ('reserved2', c_uint),
    ]


class MOT_ButtonParameters(Structure):
    _fields_ = [
        ('buttonMode', WORD),
        ('leftButtonPosition', c_int),
        ('rightButtonPosition', c_int),
        ('timeout', WORD),
        ('unused', WORD),
    ]


class MOT_PotentiometerStep(Structure):
    _fields_ = [
        ('thresholdDeflection', WORD),
        ('velocity', DWORD),
    ]


class MOT_PotentiometerSteps(Structure):
    _fields_ = [
        ('potentiometerStepParameters', MOT_PotentiometerStep * 4),
    ]


class KMOT_MMIParams(Structure):
    _fields_ = [
        ('WheelMode', c_int16),
        ('WheelMaxVelocity', c_int32),
        ('WheelAcceleration', c_int32),
        ('WheelDirectionSense', c_short),
        ('PresetPos1', c_int32),
        ('PresetPos2', c_int32),
        ('DisplayIntensity', c_int16),
        ('DisplayTimeout', c_int16),
        ('DisplayDimIntensity', c_int16),
        ('reserved', c_int16 * 4),
    ]


class KMOT_TriggerConfig(Structure):
    _fields_ = [
        ('Trigger1Mode', c_int16),
        ('Trigger1Polarity', c_int16),
        ('Trigger2Mode', c_int16),
        ('Trigger2Polarity', c_int16),
    ]


class KMOT_TriggerParams(Structure):
    _fields_ = [
        ('TriggerStartPositionFwd', c_int32),
        ('TriggerIntervalFwd', c_int32),
        ('TriggerPulseCountFwd', c_int32),
        ('TriggerStartPositionRev', c_int32),
        ('TriggerIntervalRev', c_int32),
        ('TriggerPulseCountRev', c_int32),
        ('TriggerPulseWidth', c_int32),
        ('CycleCount', c_int32),
        ('reserved', c_int32 * 6),
    ]


class KIM_DriveOPParameters(Structure):
    _fields_ = [
        ('_maxVoltage', c_int16),
        ('_stepRate', c_int32),
        ('_stepAcceleration', c_int32),
    ]


class KIM_JogParameters(Structure):
    _fields_ = [
        ('_jogMode', c_uint16),
        ('_jogStepSizeFwd', c_int32),
        ('_jogStepSizeRev', c_int32),
        ('_jogStepRate', c_int32),
        ('_jogStepAcceleration', c_int32),
    ]


class KIM_LimitSwitchParameters(Structure):
    _fields_ = [
        ('_forwardLimit', c_int16),
        ('_reverseLimit', c_int16),
        ('_stageID', c_int16),
    ]


class KIM_HomeParameters(Structure):
    _fields_ = [
        ('_homeDirection', c_byte),
        ('_homeLimitSwitch', c_byte),
        ('_homeStepRate', c_int32),
        ('_homeOffset', c_int32),
    ]


class KIM_MMIParameters(Structure):
    _fields_ = [
        ('_joystickMode', c_int16),
        ('_maxStepRate', c_int32),
        ('_directionSense', c_int16),
        ('_displayIntensity', c_int16),
    ]


class KIM_MMIChannelParameters(Structure):
    _fields_ = [
        ('_presetPos1', c_int32),
        ('_presetPos2', c_int32),
    ]


class KIM_TrigIOConfig(Structure):
    _fields_ = [
        ('_trigChannel1', c_uint16),
        ('_trigChannel2', c_uint16),
        ('_trig1Mode', c_int16),
        ('_trig1Polarity', c_int16),
        ('_trig2Mode', c_int16),
        ('_trig2Polarity', c_int16),
    ]


class KIM_TrigParamsParameters(Structure):
    _fields_ = [
        ('_startPosFwd', c_int32),
        ('_intervalFwd', c_int32),
        ('_numberOfPulsesFwd', c_int32),
        ('_startPosRev', c_int32),
        ('_intervalRev', c_int32),
        ('_numberOfPulsesRev', c_int32),
        ('_pulseWidth', c_int32),
        ('_numberOfCycles', c_int32),
        ('_reserved', c_int16 * 6),
    ]


class KIM_FeedbackSigParams(Structure):
    _fields_ = [
        ('_feedbackSignalMode', c_int16),
        ('_encoderConst', c_int32),
        ('_reserved', c_int16 * 4),
    ]


class KIM_Status(Structure):
    _fields_ = [
        ('_position', c_int32),
        ('_encoderCount', c_int32),
        ('_statusBits', c_uint32),
    ]


class KLD_MMIParams(Structure):
    _fields_ = [
        ('displayIntensity', c_int16),
        ('reserved', c_int16 * 3),
    ]


class KLD_TrigIOParams(Structure):
    _fields_ = [
        ('mode1', c_ushort),
        ('polarity1', c_ushort),
        ('reserved1', c_int16),
        ('mode2', c_ushort),
        ('polarity2', c_ushort),
        ('reserved2', c_int16),
    ]


class KLS_MMIParams(Structure):
    _fields_ = [
        ('displayIntensity', c_int16),
        ('reserved', c_int16 * 3),
    ]


class KLS_TrigIOParams(Structure):
    _fields_ = [
        ('mode1', c_ushort),
        ('polarity1', c_ushort),
        ('reserved1', c_int16),
        ('mode2', c_ushort),
        ('polarity2', c_ushort),
        ('reserved2', c_int16),
    ]


class KNA_TIARangeParameters(Structure):
    _fields_ = [
        ('mode', WORD),
        ('upLimit', WORD),
        ('downLimit', WORD),
        ('settleSamples', c_short),
        ('changeToOddOrEven', WORD),
        ('newRange', WORD),
    ]


class KNA_TIAReading(Structure):
    _fields_ = [
        ('absoluteReading', c_float),
        ('relativeReading', WORD),
        ('selectedRange', WORD),
        ('underOrOverRead', WORD),
    ]


class KNA_IOSettings(Structure):
    _fields_ = [
        ('lowVoltageOutRange', WORD),
        ('lowVoltageOutputRoute', WORD),
        ('highVoltageOutRange', WORD),
        ('highVoltageOutputRoute', WORD),
    ]


class KNA_MMIParams(Structure):
    _fields_ = [
        ('WheelAdjustRate', c_int16),
        ('DisplayIntensity', c_int16),
        ('reserved', c_int16 * 6),
    ]


class KNA_TriggerConfig(Structure):
    _fields_ = [
        ('Trigger1Mode', c_int16),
        ('Trigger1Polarity', c_int16),
        ('unused1', c_int16),
        ('Trigger2Mode', c_int16),
        ('Trigger2Polarity', c_int16),
        ('unused2', c_int16),
        ('reserved', c_int16 * 4),
    ]


class KNA_FeedbackLoopConstants(Structure):
    _fields_ = [
        ('proportionalTerm', c_short),
        ('integralTerm', c_short),
    ]


class TPZ_IOSettings(Structure):
    _fields_ = [
        ('_hubAnalogueInput', c_short),
        ('_maximumOutputVoltage', c_short),
    ]


class KPZ_MMIParams(Structure):
    _fields_ = [
        ('JoystickMode', c_int16),
        ('VoltageAdjustRate', c_int16),
        ('VoltageStep', c_int32),
        ('JoystickDirectionSense', c_int16),
        ('PresetPos1', c_int32),
        ('PresetPos2', c_int32),
        ('DisplayIntensity', c_int16),
        ('DisplayTimeout', c_int16),
        ('DisplayDimIntensity', c_int16),
        ('reserved', c_int16 * 4),
    ]


class KPZ_TriggerConfig(Structure):
    _fields_ = [
        ('Trigger1Mode', c_int16),
        ('Trigger1Polarity', c_int16),
        ('Trigger2Mode', c_int16),
        ('Trigger2Polarity', c_int16),
        ('reserved', c_int16 * 6),
    ]


class QD_LoopParameters(Structure):
    _fields_ = [
        ('proportionalGain', c_float),
        ('integralGain', c_float),
        ('differentialGain', c_float),
        ('lowPassFilterCutOffFreq', c_float),
        ('notchFilterCenterFrequency', c_float),
        ('notchFilterQ', c_float),
        ('notchFilterEnabled', WORD),
        ('lowPassFilterEnabled', WORD),
    ]


class QD_PIDParameters(Structure):
    _fields_ = [
        ('proportionalGain', c_float),
        ('integralGain', c_float),
        ('differentialGain', c_float),
    ]


class QD_LowPassFilterParameters(Structure):
    _fields_ = [
        ('lowPassFilterCutOffFreq', c_float),
        ('lowPassFilterEnabled', WORD),
    ]


class QD_NotchFilterParameters(Structure):
    _fields_ = [
        ('notchFilterCenterFrequency', c_float),
        ('notchFilterQ', c_float),
        ('notchFilterEnabled', WORD),
    ]


class QD_PositionDemandParameters(Structure):
    _fields_ = [
        ('minXdemand', c_uint16),
        ('minYdemand', c_uint16),
        ('maxXdemand', c_uint16),
        ('maxYdemand', c_uint16),
        ('lowVoltageOutputRoute', c_short),
        ('openLoopOption', c_short),
        ('xFeedbackSignedGain', c_uint16),
        ('yFeedbackSignedGain', c_uint16),
    ]


class QD_Position(Structure):
    _fields_ = [
        ('x', c_uint16),
        ('y', c_uint16),
    ]


class QD_Readings(Structure):
    _fields_ = [
        ('posDifference', QD_Position),
        ('sum', WORD),
        ('demandedPos', QD_Position),
    ]


class QD_KPA_TrigIOConfig(Structure):
    _fields_ = [
        ('trig1Mode', WORD),
        ('trig1Polarity', WORD),
        ('trig1SumMin', WORD),
        ('trig1SumMax', WORD),
        ('trig1DiffThreshold', WORD),
        ('trig2Mode', WORD),
        ('trig2Polarity', WORD),
        ('trig2SumMin', WORD),
        ('trig2SumMax', WORD),
        ('trig2DiffThreshold', WORD),
        ('wReserved', WORD * 6),
    ]


class QD_KPA_DigitalIO(Structure):
    _fields_ = [
        ('wDigOPs', WORD),
        ('wReserved', WORD * 6),
    ]


class SC_CycleParameters(Structure):
    _fields_ = [
        ('openTime', c_uint),
        ('closedTime', c_uint),
        ('numCycles', c_uint),
    ]


class KSC_MMIParams(Structure):
    _fields_ = [
        ('unused', c_int16 * 10),
        ('DisplayIntensity', c_int16),
        ('DisplayTimeout', c_int16),
        ('DisplayDimIntensity', c_int16),
        ('reserved', c_int16 * 4),
    ]


class KSC_TriggerConfig(Structure):
    _fields_ = [
        ('Trigger1Mode', c_int16),
        ('Trigger1Polarity', c_int16),
        ('Trigger2Mode', c_int16),
        ('Trigger2Polarity', c_int16),
        ('reserved', c_int16 * 6),
    ]


class TSG_IOSettings(Structure):
    _fields_ = [
        ('hubAnalogOutput', c_short),
        ('displayMode', c_short),
        ('forceCalibration', c_uint),
        ('notYetInUse', WORD),
        ('futureUse', WORD),
    ]


class KSG_MMIParams(Structure):
    _fields_ = [
        ('DisplayIntensity', c_int16),
        ('DisplayTimeout', c_int16),
        ('DisplayDimIntensity', c_int16),
        ('reserved', c_int16 * 4),
    ]


class KSG_TriggerConfig(Structure):
    _fields_ = [
        ('Trigger1Mode', c_int16),
        ('Trigger1Polarity', c_int16),
        ('Trigger2Mode', c_int16),
        ('Trigger2Polarity', c_int16),
        ('LowerLimit', c_int32),
        ('UpperLimit', c_int32),
        ('SmoothingSamples', c_int16),
        ('reserved', c_int16 * 6),
    ]


class TIM_DriveOPParameters(Structure):
    _fields_ = [
        ('_maxVoltage', c_int16),
        ('_stepRate', c_int32),
        ('_stepAcceleration', c_int32),
    ]


class TIM_JogParameters(Structure):
    _fields_ = [
        ('_jogMode', c_uint16),
        ('_jogStepSize', c_int32),
        ('_jogStepRate', c_int32),
        ('_jogStepAcceleration', c_int32),
    ]


class TIM_ButtonParameters(Structure):
    _fields_ = [
        ('_buttonMode', c_uint16),
        ('_position1', c_int32),
        ('_position2', c_int32),
        ('_reserved', c_int16 * 2),
    ]


class TIM_Status(Structure):
    _fields_ = [
        ('_position', c_int32),
        ('_encoderCount', c_int32),
        ('_statusBits', c_uint32),
    ]


class TC_LoopParameters(Structure):
    _fields_ = [
        ('proportionalGain', c_ushort),
        ('integralGain', c_ushort),
        ('differentialGain', c_ushort),
    ]


STRUCT_LIST = [
    'BNT_IO_Settings',
    'FF_IOSettings',
    'KIM_DriveOPParameters',
    'KIM_FeedbackSigParams',
    'KIM_HomeParameters',
    'KIM_JogParameters',
    'KIM_LimitSwitchParameters',
    'KIM_MMIChannelParameters',
    'KIM_MMIParameters',
    'KIM_Status',
    'KIM_TrigIOConfig',
    'KIM_TrigParamsParameters',
    'KLD_MMIParams',
    'KLD_TrigIOParams',
    'KLS_MMIParams',
    'KLS_TrigIOParams',
    'KMOT_MMIParams',
    'KMOT_TriggerConfig',
    'KMOT_TriggerParams',
    'KNA_FeedbackLoopConstants',
    'KNA_IOSettings',
    'KNA_MMIParams',
    'KNA_TIARangeParameters',
    'KNA_TIAReading',
    'KNA_TriggerConfig',
    'KPZ_MMIParams',
    'KPZ_TriggerConfig',
    'KSC_MMIParams',
    'KSC_TriggerConfig',
    'KSG_MMIParams',
    'KSG_TriggerConfig',
    'MOT_BrushlessCurrentLoopParameters',
    'MOT_BrushlessElectricOutputParameters',
    'MOT_BrushlessPositionLoopParameters',
    'MOT_BrushlessTrackSettleParameters',
    'MOT_ButtonParameters',
    'MOT_DC_PIDParameters',
    'MOT_HomingParameters',
    'MOT_JogParameters',
    'MOT_JoystickParameters',
    'MOT_LimitSwitchParameters',
    'MOT_PIDLoopEncoderParams',
    'MOT_PotentiometerStep',
    'MOT_PotentiometerSteps',
    'MOT_PowerParameters',
    'MOT_StageAxisParameters',
    'MOT_VelocityParameters',
    'MOT_VelocityProfileParameters',
    'NT_CircleDiameterLUT',
    'NT_CircleParameters',
    'NT_GainParameters',
    'NT_HVComponent',
    'NT_IOSettings',
    'NT_LowPassFilterParameters',
    'NT_TIARangeParameters',
    'NT_TIAReading',
    'PPC_IOSettings',
    'PPC_NotchParams',
    'PPC_PIDConsts',
    'PZ_FeedbackLoopConstants',
    'PZ_LUTWaveParameters',
    'QD_KPA_DigitalIO',
    'QD_KPA_TrigIOConfig',
    'QD_LoopParameters',
    'QD_LowPassFilterParameters',
    'QD_NotchFilterParameters',
    'QD_PIDParameters',
    'QD_Position',
    'QD_PositionDemandParameters',
    'QD_Readings',
    'SC_CycleParameters',
    'TC_LoopParameters',
    'TIM_ButtonParameters',
    'TIM_DriveOPParameters',
    'TIM_JogParameters',
    'TIM_Status',
    'TLI_DeviceInfo',
    'TLI_HardwareInformation',
    'TPZ_IOSettings',
    'TSG_IOSettings',
]


if __name__ == '__main__':
    # The following was used to automatically generate the above...
    import os
    from msl.equipment.resources.utils import CHeader

    structs = {}
    root = r'C:\Program Files\Thorlabs\Kinesis'
    for f in os.listdir(root):
        if f.endswith('.h'):
            header = CHeader(os.path.join(root, f))
            for key, value in header.structs().items():
                if key not in structs:
                    structs[key] = value

    for key, value in structs.items():
        print('class {}(Structure):'.format(key))
        print('    _fields_ = [')
        for field in value:
            print("        ('{}', {}),".format(field[1], field[0]))
        print('    ]\n\n')

    print('STRUCT_LIST = [')
    for item in sorted(structs):
        print("    '{}',".format(item))
    print(']')
