"""
Enums defined in Thorlabs Kinesis v1.14.9
"""
from enum import IntEnum
from ctypes import c_byte, c_ushort, c_short, c_int16, c_uint16, c_int

from msl.equipment.resources.utils import WORD


class FT_Status(IntEnum):
    FT_OK = 0x00
    FT_InvalidHandle = 0x01
    FT_DeviceNotFound = 0x02
    FT_DeviceNotOpened = 0x03
    FT_IOError = 0x04
    FT_InsufficientResources = 0x05
    FT_InvalidParameter = 0x06
    FT_DeviceNotPresent = 0x07
    FT_IncorrectDevice = 0x08


class MOT_MotorTypes(IntEnum):
    MOT_NotMotor = 0
    MOT_DCMotor = 1
    MOT_StepperMotor = 2
    MOT_BrushlessMotor = 3
    MOT_CustomMotor = 100


class MOT_TravelModes(IntEnum):
    MOT_TravelModeUndefined = 0
    MOT_Linear = 0x01
    MOT_Rotational = 0x02


class MOT_TravelDirection(IntEnum):
    MOT_TravelDirectionDisabled = 0x00
    MOT_Forwards = 0x01
    MOT_Reverse = 0x02


class MOT_DirectionSense(IntEnum):
    MOT_Normal = 0x00
    MOT_Backwards = 0x01


class MOT_HomeLimitSwitchDirection(IntEnum):
    MOT_LimitSwitchDirectionUndefined = 0
    MOT_ReverseLimitSwitch = 0x01
    MOT_ForwardLimitSwitch = 0x04


class MOT_JogModes(IntEnum):
    MOT_JogModeUndefined = 0x00
    MOT_Continuous = 0x01
    MOT_SingleStep = 0x02


class MOT_StopModes(IntEnum):
    MOT_StopModeUndefined = 0x00
    MOT_Immediate = 0x01
    MOT_Profiled = 0x02


class MOT_ButtonModes(IntEnum):
    MOT_ButtonModeUndefined = 0x00
    MOT_JogMode = 0x01
    MOT_Preset = 0x02


class MOT_VelocityProfileModes(IntEnum):
    MOT_Trapezoidal = 0x00
    MOT_SCurve = 0x02


class MOT_LimitSwitchModes(IntEnum):
    MOT_LimitSwitchModeUndefined = 0x00
    MOT_LimitSwitchIgnoreSwitch = 0x01
    MOT_LimitSwitchMakeOnContact = 0x02
    MOT_LimitSwitchBreakOnContact = 0x03
    MOT_LimitSwitchMakeOnHome = 0x04
    MOT_LimitSwitchBreakOnHome = 0x05
    MOT_PMD_Reserved = 0x06
    MOT_LimitSwitchIgnoreSwitchSwapped = 0x81
    MOT_LimitSwitchMakeOnContactSwapped = 0x82
    MOT_LimitSwitchBreakOnContactSwapped = 0x83
    MOT_LimitSwitchMakeOnHomeSwapped = 0x84
    MOT_LimitSwitchBreakOnHomeSwapped = 0x85


class MOT_LimitSwitchSWModes(IntEnum):
    MOT_LimitSwitchSWModeUndefined = 0x00
    MOT_LimitSwitchIgnored = 0x01
    MOT_LimitSwitchStopImmediate = 0x02
    MOT_LimitSwitchStopProfiled = 0x03
    MOT_LimitSwitchIgnored_Rotational = 0x81
    MOT_LimitSwitchStopImmediate_Rotational = 0x82
    MOT_LimitSwitchStopProfiled_Rotational = 0x83


class MOT_LimitsSoftwareApproachPolicy(IntEnum):
    DisallowIllegalMoves = 0
    AllowPartialMoves = 1
    AllowAllMoves = 2


class MOT_CurrentLoopPhases(IntEnum):
    MOT_PhaseA = 0x0
    MOT_PhaseB = 0x1
    MOT_PhaseAB = 0x2


class MOT_MovementModes(IntEnum):
    LinearRange = 0x00
    RotationalUnlimited = 0x01
    RotationalWrapping = 0x02


class MOT_MovementDirections(IntEnum):
    Quickest = 0x00
    Forwards = 0x01
    Reverse = 0x02


class MOT_PID_LoopMode(IntEnum):
    MOT_PIDLoopModeDisabled = 0x00
    MOT_PIDOpenLoopMode = 0x01
    MOT_PIDClosedLoopMode = 0x02


class NT_SignalState(IntEnum):
    NT_BadSignal = 0x00
    NT_GoodSignal = 0x01


class NT_Mode(IntEnum):
    NT_ModeUndefined = 0x00
    NT_Piezo = 0x01
    NT_Latch = 0x02
    NT_Tracking = 0x03
    NT_HorizontalTracking = 0x04
    NT_VerticalTracking = 0x05


class NT_ControlMode(IntEnum):
    NT_ControlModeUndefined = 0x00
    NT_OpenLoop = 0x01
    NT_ClosedLoop = 0x02
    NT_OpenLoopSmoothed = 0x03
    NT_ClosedLoopSmoothed = 0x04


class NT_FeedbackSource(IntEnum):
    NT_FeedbackSourceUndefined = 0x00
    NT_TIA = 0x01
    NT_BNC_1v = 0x02
    NT_BNC_2v = 0x03
    NT_BNC_5v = 0x04
    NT_BNC_10v = 0x05


class NT_TIARange(IntEnum):
    NT_TIARange1_3nA = 0x0003
    NT_TIARange2_10nA = 0x0004
    NT_TIARange3_30nA = 0x0005
    NT_TIARange4_100nA = 0x0006
    NT_TIARange5_300nA = 0x0007
    NT_TIARange6_1uA = 0x0008
    NT_TIARange7_3uA = 0x0009
    NT_TIARange8_10uA = 0x000A
    NT_TIARange9_30uA = 0x000B
    NT_TIARange10_100uA = 0x000C
    NT_TIARange11_300uA = 0x000D
    NT_TIARange12_1mA = 0x000E
    NT_TIARange13_3mA = 0x000F
    NT_TIARange14_10mA = 0x0010


class NT_OddOrEven(IntEnum):
    NT_OddAndEven = 0x0001
    NT_Odd = 0x0002
    NT_Even = 0x0003


class NT_UnderOrOver(IntEnum):
    NT_InRange = 0x0001
    NT_UnderRange = 0x0002
    NT_OverRange = 0x0003


class NT_CircleDiameterMode(IntEnum):
    NT_ParameterCircleMode = 0x0001
    NT_AbsPowerCircleMode = 0x0002
    NT_LUTCircleMode = 0x0003


class NT_CircleAdjustment(IntEnum):
    NT_LinearCircleAdjustment = 0x0001
    NT_LogCircleAdjustment = 0x0002
    NT_SquareCircleAdjustment = 0x0003
    NT_CubeCircleAdjustment = 0x0004


class NT_TIARangeMode(IntEnum):
    NT_TIARangeModeUndefined = 0x0000
    NT_AutoRangeAtSelected = 0x0001
    NT_ManualRangeAtSelected = 0x0002
    NT_ManualRangeAtParameter = 0x0003
    NT_AutoRangeAtParameter = 0x0004


class NT_LowPassFrequency(IntEnum):
    NT_LowPassNone = 0
    NT_LowPass_1Hz = 1
    NT_LowPass_3Hz = 2
    NT_LowPass_10Hz = 3
    NT_LowPass_30Hz = 4
    NT_LowPass_100Hz = 5


class NT_VoltageRange(IntEnum):
    NT_VoltageRangeUndefined = 0x0000
    NT_VoltageRange_5v = 0x0001
    NT_VoltageRange_10v = 0x0002


class NT_OutputVoltageRoute(IntEnum):
    NT_SMAOnly = 0x0001
    NT_HubOrSMA = 0x0002


class NT_PowerInputUnits(IntEnum):
    NT_Amps = 0
    NT_Watts = 1
    NT_Db = 2


class NT_SMA_Units(IntEnum):
    NT_Voltage = 0
    NT_FullRange = 1
    NT_UserDefined = 2


class BNT_CurrentLimit(IntEnum):
    NT_CurrentLimit_100mA = 0x00
    NT_CurrentLimit_250mA = 0x01
    NT_CurrentLimit_500mA = 0x02


class BNT_OutputLowPassFilter(IntEnum):
    NT_OutputFilter_10Hz = 0x0
    NT_OutputFilter_100Hz = 0x1
    NT_OutputFilter_5kHz = 0x2
    NT_OutputFilter_None = 0x3


class BNT_FeedbackSignalSelection(IntEnum):
    NT_FeedbackSignalDC = 0x0000
    NT_FeedbackSignalAC = 0xFFFF


class BNT_BNCTriggerModes(IntEnum):
    NT_BNCModeTrigger = 0x0000
    NT_BNCModeLVOut = 0xFFFF


class PZ_ControlModeTypes(IntEnum):
    PZ_Undefined = 0
    PZ_OpenLoop = 1
    PZ_CloseLoop = 2
    PZ_OpenLoopSmooth = 3
    PZ_CloseLoopSmooth = 4


class PZ_InputSourceFlags(IntEnum):
    PZ_SoftwareOnly = 0
    PZ_ExternalSignal = 0x01
    PZ_Potentiometer = 0x02
    PZ_All = PZ_ExternalSignal | PZ_Potentiometer


class PZ_OutputLUTModes(IntEnum):
    PZ_Continuous = 0x01
    PZ_Fixed = 0x02
    PZ_OutputTrigEnable = 0x04
    PZ_InputTrigEnable = 0x08
    PZ_OutputTrigSenseHigh = 0x10
    PZ_InputTrigSenseHigh = 0x20
    PZ_OutputGated = 0x40
    PZ_OutputTrigRepeat = 0x80


class PPC_DerivFilterState(IntEnum):
    DerivFilterOn = 0x01
    DerivFilterOff = 0x02


class PPC_NotchFilterState(IntEnum):
    NotchFilterOn = 0x01
    NotchFilterOff = 0x02


class PPC_NotchFilterChannel(IntEnum):
    NotchFilter1 = 0x01
    NotchFilter2 = 0x02
    NotchFilterBoth = 0x03


class PPC_IOControlMode(IntEnum):
    SWOnly = 0x00
    ExtBNC = 0x01
    Joystick = 0x02
    JoystickBnc = 0x03


class PPC_IOOutputMode(IntEnum):
    HV = 0x01
    PosRaw = 0x02
    PosCorrected = 0x03


class PPC_IOOutputBandwidth(IntEnum):
    OP_Unfiltered = 0x01
    OP_200Hz = 0x02


class PPC_IOFeedbackSourceDefinition(IntEnum):
    StrainGauge = 0x01
    Capacitive = 0x02
    Optical = 0x03


class PPC_DisplayIntensity(IntEnum):
    Bright = 0x01
    Dim = 0x02
    Off = 0x03


class FF_Positions(IntEnum):
    FF_PositionError = 0
    Position1 = 0x01
    Position2 = 0x02


class FF_IOModes(IntEnum):
    FF_ToggleOnPositiveEdge = 0x01
    FF_SetPositionOnPositiveEdge = 0x02
    FF_OutputHighAtSetPosition = 0x04
    FF_OutputHighWhemMoving = 0x08


class FF_SignalModes(IntEnum):
    FF_InputButton = 0x01
    FF_InputLogic = 0x02
    FF_InputSwap = 0x04
    FF_OutputLevel = 0x10
    FF_OutputPulse = 0x20
    FF_OutputSwap = 0x40


class KMOT_WheelDirectionSense(IntEnum):
    KMOT_WM_Positive = 0x01
    KMOT_WM_Negative = 0x02


class KMOT_WheelMode(IntEnum):
    KMOT_WM_Velocity = 0x01
    KMOT_WM_Jog = 0x02
    KMOT_WM_MoveAbsolute = 0x03


class KMOT_TriggerPortMode(IntEnum):
    KMOT_TrigDisabled = 0x00
    KMOT_TrigIn_GPI = 0x01
    KMOT_TrigIn_RelativeMove = 0x02
    KMOT_TrigIn_AbsoluteMove = 0x03
    KMOT_TrigIn_Home = 0x04
    KMOT_TrigOut_GPO = 0x0A
    KMOT_TrigOut_InMotion = 0x0B
    KMOT_TrigOut_AtMaxVelocity = 0x0C
    KMOT_TrigOut_AtPositionSteps = 0x0D
    KMOT_TrigOut_Synch = 0x0E


class KMOT_TriggerPortPolarity(IntEnum):
    KMOT_TrigPolarityHigh = 0x01
    KMOT_TrigPolarityLow = 0x02


class KIM_Channels(IntEnum):
    Channel1 = 1
    Channel2 = 2
    Channel3 = 3
    Channel4 = 4


class KIM_JogMode(IntEnum):
    JogContinuous = 0x01
    JogStep = 0x02


class KIM_TravelDirection(IntEnum):
    Forward = 0x01
    Reverse = 0x02


class KIM_FBSignalMode(IntEnum):
    FB_LimitSwitch = 0x01
    FB_Encoder = 0x02


class KIM_LimitSwitchModes(IntEnum):
    Ignore = 0x01
    SwitchMakes = 0x02
    SwitchBreaks = 0x03
    SwitchMakes_HomeOnly = 0x04
    SwitchBreaks_HomeOnly = 0x05


class KIM_DirectionSense(IntEnum):
    Dir_Disabled = 0x0
    Dir_Forward = 0x01
    Dir_Reverse = 0x02


class KIM_TrigModes(IntEnum):
    Trig_Disabled = 0x00
    Trig_In_GPI = 0x01
    Trig_InRelativeMove = 0x02
    Trig_InAbsoluteMove = 0x03
    Trig_InResetCount = 0x04
    Trig_Out_GP0 = 0x0A
    Trig_Out_InMotion = 0x0B
    Trig_Out_AtMaxVelocity = 0x0C
    Trig_Out_PosStepFwd = 0x0D
    Trig_Out_PosStepRev = 0x0E
    Trig_Out_PosStepBoth = 0x0F
    Trig_Out_AtFwdLimit = 0x10
    Trig_Out_AtRevLimit = 0x11
    Trig_Out_AtEitherLimit = 0x12


class KIM_TrigPolarities(IntEnum):
    Trig_High = 0x01
    Trig_Low = 0x02


class KIM_JoysticModes(IntEnum):
    JS_Velocity = 0x01
    JS_Jog = 0x02
    JS_GotoPosition = 0x03


class ChannelEnableModes(IntEnum):
    NONE = 0x00
    Channel1Only = 0x01
    Channel2Only = 0x02
    Channel3Only = 0x03
    Channel4Only = 0x04
    Channels1and2 = 0x05
    Channels3and4 = 0x06


class LD_InputSourceFlags(IntEnum):
    LD_SoftwareOnly = 0x01
    LD_ExternalSignal = 0x02
    LD_Potentiometer = 0x04


class LD_DisplayUnits(IntEnum):
    LD_ILim = 0x01
    LD_ILD = 0x02
    LD_IPD = 0x03
    LD_PLD = 0x04


class LD_TIA_RANGES(IntEnum):
    LD_TIA_10uA = 1
    LD_TIA_100uA = 2
    LD_TIA_1mA = 4
    LD_TIA_10mA = 8


class LD_POLARITY(IntEnum):
    LD_CathodeGrounded = 1
    LD_AnodeGrounded = 2


class KLD_TriggerMode(IntEnum):
    KLD_Disabled = 0
    KLD_Input = 1
    KLD_Output = 0x0a
    KLD_LaserOn = 0x0b
    KLD_InterlockEnabled = 0x0c
    KLD_SetPointChange = 0x0d
    KLD_HighStability = 0x0e
    KLD_LowStability = 0x0f


class KLD_TrigPolarity(IntEnum):
    KLD_TrigPol_High = 0x01
    KLD_TrigPol_Low = 0x02


class LS_InputSourceFlags(IntEnum):
    LS_SoftwareOnly = 0
    LS_ExternalSignal = 0x01
    LS_Potentiometer = 0x04


class KLS_OpMode(IntEnum):
    KLS_ConstantPower = 0
    KLS_ConstantCurrent = 1


class KLS_TriggerMode(IntEnum):
    KLS_Disabled = 0
    KLS_Input = 1
    KLS_Output = 0x0a
    KLS_LaserOn = 0x0b
    KLS_InterlockEnabled = 0x0c
    KLS_SetPointChange = 0x0d
    KLS_HighStability = 0x0e
    KLS_LowStability = 0x0f


class KLS_TrigPolarity(IntEnum):
    KLS_TrigPol_High = 0x01
    KLS_TrigPol_Low = 0x02


class KNA_FeedbackSource(IntEnum):
    NT_FeedbackSourceUndefined = 0x00
    NT_TIA = 0x01
    NT_IO1_5v = 0x04


class KNA_TIARange(IntEnum):
    KNA_TIARange1_5nA = 0x0003
    KNA_TIARange2_16_6nA = 0x0004
    KNA_TIARange3_50nA = 0x0005
    KNA_TIARange4_166nA = 0x0006
    KNA_TIARange5_500nA = 0x0007
    KNA_TIARange6_1_66uA = 0x0008
    KNA_TIARange7_5uA = 0x0009
    KNA_TIARange8_16_6uA = 0x000A
    KNA_TIARange9_50uA = 0x000B
    KNA_TIARange10_166uA = 0x000C
    KNA_TIARange11_500uA = 0x000D
    KNA_TIARange12_1_66mA = 0x000E
    KNA_TIARange13_5mA = 0x000F


class KNA_LowVoltageRange(IntEnum):
    KNA_VoltageRange_10v = 0x0002


class KNA_LowOutputVoltageRoute(IntEnum):
    KNA_IO1Only = 0x0001


class KNA_HighVoltageRange(IntEnum):
    KNA_Default_Range = 0x00
    KNA_VoltageRange_CH1_75v = 0x00
    KNA_VoltageRange_CH1_150v = 0x01
    KNA_VoltageRange_CH2_75v = 0x00
    KNA_VoltageRange_CH2_150v = 0x10


class KNA_HighOutputVoltageRoute(IntEnum):
    KNA_Default_Route = 0x0000
    KNA_ExtIn_PIN = 0x0000
    KNA_ExtIn_IO1 = 0x0001
    KNA_ExtOut_Dis = 0x0000
    KNA_ExtOut_IO2 = 0x0010
    KNA_EnableInputBoost = 0x0100


class NT_IO1_Units(IntEnum):
    NT_Voltage = 0
    NT_FullRange = 1
    NT_UserDefined = 2


class KNA_WheelAdjustRate(IntEnum):
    KNA_WM_Low = 0x00
    KNA_WM_Medium = 0x01
    KNA_WM_High = 0x02


class KNA_TriggerPortMode(IntEnum):
    KNA_TrigDisabled = 0x00
    KNA_TrigIn_GPI = 0x01
    KNA_TrigIn_VoltageStepUp = 0x02
    KNA_TrigIn_VoltageStepDown = 0x03
    KNA_TrigOut_GPO = 0x0A


class KNA_TriggerPortPolarity(IntEnum):
    KNA_TrigPolarityHigh = 0x01
    KNA_TrigPolarityLow = 0x02


class KNA_Channels(IntEnum):
    KNA_ChannelUndefined = 0x00
    KNA_Channel1 = 0x01
    KNA_Channel2 = 0x02


class KNA_FeedbackModeTypes(IntEnum):
    PZ_ControlModeUndefined = 0
    PZ_OpenLoop = 1
    PZ_CloseLoop = 2
    PZ_OpenLoopSmooth = 3
    PZ_CloseLoopSmooth = 4


class KPZ_WheelDirectionSense(IntEnum):
    KPZ_WM_Positive = 0x01
    KPZ_WM_Negative = 0x02


class KPZ_WheelMode(IntEnum):
    KPZ_WM_MoveAtVoltage = 0x01
    KPZ_WM_JogVoltage = 0x02
    KPZ_WM_SetVoltage = 0x03


class KPZ_WheelChangeRate(IntEnum):
    KPZ_WM_High = 0x01
    KPZ_WM_Medium = 0x02
    KPZ_WM_Low = 0x03


class KPZ_TriggerPortMode(IntEnum):
    KPZ_TrigDisabled = 0x00
    KPZ_TrigIn_GPI = 0x01
    KPZ_TrigIn_VoltageStepUp = 0x02
    KPZ_TrigIn_VoltageStepDown = 0x03
    KPZ_TrigOut_GPO = 0x0A


class KPZ_TriggerPortPolarity(IntEnum):
    KPZ_TrigPolarityHigh = 0x01
    KPZ_TrigPolarityLow = 0x02


class HubAnalogueModes(IntEnum):
    AnalogueCh1 = 1
    AnalogueCh2 = 2
    ExtSignalSMA = 3


class QD_OperatingMode(IntEnum):
    QD_ModeUndefined = 0
    QD_Monitor = 1
    QD_OpenLoop = 2
    QD_ClosedLoop = 3
    QD_AutoOpenClosedLoop = 4


class QD_LowVoltageRoute(IntEnum):
    QD_RouteUndefined = 0
    QD_SMAOnly = 1
    QD_HubAndSMA = 2


class QD_OpenLoopHoldValues(IntEnum):
    QD_HoldOnZero = 1
    QD_HoldOnLastValue = 2


class QD_FilterEnable(IntEnum):
    QD_Undefined = 0
    QD_Enabled = 1
    QD_Disabled = 2


class QD_KPA_TrigModes(IntEnum):
    QD_Trig_Disabled = 0x00
    QD_TrigIn_GPI = 0x01
    QD_TrigIn_LoopOpenClose = 0x02
    KD_TrigOut_GPO = 0x0A
    KD_TrigOut_Sum = 0x0B
    KD_TrigOut_Diff = 0x0C
    KD_TrigOut_SumDiff = 0x0D


class QD_KPA_TrigPolarities(IntEnum):
    GD_Trig_High = 0x01
    GD_Trig_Low = 0x02


class SC_OperatingModes(IntEnum):
    SC_Manual = 0x01
    SC_Single = 0x02
    SC_Auto = 0x03
    SC_Triggered = 0x04


class SC_OperatingStates(IntEnum):
    SC_Active = 0x01
    SC_Inactive = 0x02


class SC_SolenoidStates(IntEnum):
    SC_SolenoidOpen = 0x01
    SC_SolenoidClosed = 0x02


class KSC_TriggerPortMode(IntEnum):
    KSC_TrigDisabled = 0x00
    KSC_TrigIn_GPI = 0x01
    KSC_TrigOut_GPO = 0x0A


class KSC_TriggerPortPolarity(IntEnum):
    KSC_TrigPolarityHigh = 0x01
    KSC_TrigPolarityLow = 0x02


class TIM_Channels(IntEnum):
    Channel1 = 1
    Channel2 = 2
    Channel3 = 3
    Channel4 = 4


class TIM_JogMode(IntEnum):
    JogContinuous = 0x01
    JogStep = 0x02


class TIM_ButtonsMode(IntEnum):
    Jog = 0x01
    Position = 0x02


class TIM_Direction(IntEnum):
    Forward = 0x01
    Reverse = 0x02


class LS_DisplayUnits(IntEnum):
    LS_mAmps = 0x01
    LS_mWatts = 0x02
    LS_mDb = 0x03


class TST_Stages(IntEnum):
    ZST6 = 0x20
    ZST13 = 0x21
    ZST25 = 0x22
    ZST206 = 0x30
    ZST213 = 0x31
    ZST225 = 0x32
    ZFS206 = 0x40
    ZFS213 = 0x41
    ZFS225 = 0x42
    TBD1 = 0x60
    TBD2 = 0x61
    TBD3 = 0x62
    TBD4 = 0x63
    NR360 = 0x70
    MVS025 = 0x71
    PLS_X25MM = 0x72
    PLS_X25MM_HiRes = 0x73
    FW103 = 0x75
    NEWZFS06 = 10006
    NEWZFS13 = 10013
    NEWZFS25 = 10025
    NEWZST06 = 11006
    NEWZST13 = 11013
    NEWZST25 = 12025


class TSG_Hub_Analogue_Modes(IntEnum):
    TSG_HubChannel1 = 1
    TSG_HubChannel2 = 2


class TSG_Display_Modes(IntEnum):
    TSG_Undefined = 0
    TSG_Position = 1
    TSG_Voltage = 2
    TSG_Force = 3


class TC_SensorTypes(IntEnum):
    TC_Transducer = 0x00
    TC_TH20kOhm = 0x01
    TC_TH200kOhm = 0x02


class TC_DisplayModes(IntEnum):
    TC_ActualTemperature = 0x00
    TC_TargetTemperature = 0x01
    TC_TempDifference = 0x02
    TC_Current = 0x03


class UnitType(IntEnum):
    DISTANCE = 0
    VELOCITY = 1
    ACCELERATION = 2


ENUM_CTYPE = {
    'BNT_BNCTriggerModes': WORD,
    'BNT_CurrentLimit': WORD,
    'BNT_FeedbackSignalSelection': WORD,
    'BNT_OutputLowPassFilter': WORD,
    'ChannelEnableModes': c_int16,
    'FF_IOModes': WORD,
    'FF_Positions': c_int,
    'FF_SignalModes': WORD,
    'FT_Status': c_short,
    'HubAnalogueModes': c_short,
    'KIM_Channels': c_uint16,
    'KIM_DirectionSense': c_int16,
    'KIM_FBSignalMode': c_int16,
    'KIM_JogMode': c_uint16,
    'KIM_JoysticModes': c_int16,
    'KIM_LimitSwitchModes': c_int16,
    'KIM_TravelDirection': c_byte,
    'KIM_TrigModes': c_int16,
    'KIM_TrigPolarities': c_int16,
    'KLD_TrigPolarity': c_ushort,
    'KLD_TriggerMode': c_ushort,
    'KLS_OpMode': c_ushort,
    'KLS_TrigPolarity': c_ushort,
    'KLS_TriggerMode': c_ushort,
    'KMOT_TriggerPortMode': c_int16,
    'KMOT_TriggerPortPolarity': c_int16,
    'KMOT_WheelDirectionSense': c_int16,
    'KMOT_WheelMode': c_int16,
    'KNA_Channels': WORD,
    'KNA_FeedbackModeTypes': c_short,
    'KNA_FeedbackSource': WORD,
    'KNA_HighOutputVoltageRoute': WORD,
    'KNA_HighVoltageRange': WORD,
    'KNA_LowOutputVoltageRoute': WORD,
    'KNA_LowVoltageRange': WORD,
    'KNA_TIARange': WORD,
    'KNA_TriggerPortMode': c_int16,
    'KNA_TriggerPortPolarity': c_int16,
    'KNA_WheelAdjustRate': c_int16,
    'KPZ_TriggerPortMode': c_int16,
    'KPZ_TriggerPortPolarity': c_int16,
    'KPZ_WheelChangeRate': c_int16,
    'KPZ_WheelDirectionSense': c_int16,
    'KPZ_WheelMode': c_int16,
    'KSC_TriggerPortMode': c_int16,
    'KSC_TriggerPortPolarity': c_int16,
    'LD_DisplayUnits': c_ushort,
    'LD_InputSourceFlags': c_ushort,
    'LD_POLARITY': c_int,
    'LD_TIA_RANGES': c_int,
    'LS_DisplayUnits': c_ushort,
    'LS_InputSourceFlags': c_ushort,
    'MOT_ButtonModes': WORD,
    'MOT_CurrentLoopPhases': WORD,
    'MOT_DirectionSense': c_short,
    'MOT_HomeLimitSwitchDirection': c_short,
    'MOT_JogModes': c_short,
    'MOT_LimitSwitchModes': WORD,
    'MOT_LimitSwitchSWModes': WORD,
    'MOT_LimitsSoftwareApproachPolicy': c_short,
    'MOT_MotorTypes': c_int,
    'MOT_MovementDirections': c_int,
    'MOT_MovementModes': c_int,
    'MOT_PID_LoopMode': WORD,
    'MOT_StopModes': c_short,
    'MOT_TravelDirection': c_short,
    'MOT_TravelModes': c_int,
    'MOT_VelocityProfileModes': WORD,
    'NT_CircleAdjustment': WORD,
    'NT_CircleDiameterMode': WORD,
    'NT_ControlMode': WORD,
    'NT_FeedbackSource': WORD,
    'NT_IO1_Units': WORD,
    'NT_LowPassFrequency': WORD,
    'NT_Mode': WORD,
    'NT_OddOrEven': WORD,
    'NT_OutputVoltageRoute': WORD,
    'NT_PowerInputUnits': WORD,
    'NT_SMA_Units': WORD,
    'NT_SignalState': c_int,
    'NT_TIARange': WORD,
    'NT_TIARangeMode': WORD,
    'NT_UnderOrOver': WORD,
    'NT_VoltageRange': WORD,
    'PPC_DerivFilterState': c_short,
    'PPC_DisplayIntensity': c_short,
    'PPC_IOControlMode': c_short,
    'PPC_IOFeedbackSourceDefinition': c_short,
    'PPC_IOOutputBandwidth': c_short,
    'PPC_IOOutputMode': c_short,
    'PPC_NotchFilterChannel': c_short,
    'PPC_NotchFilterState': c_short,
    'PZ_ControlModeTypes': c_short,
    'PZ_InputSourceFlags': c_short,
    'PZ_OutputLUTModes': c_short,
    'QD_FilterEnable': WORD,
    'QD_KPA_TrigModes': WORD,
    'QD_KPA_TrigPolarities': WORD,
    'QD_LowVoltageRoute': c_short,
    'QD_OpenLoopHoldValues': c_short,
    'QD_OperatingMode': c_short,
    'SC_OperatingModes': c_byte,
    'SC_OperatingStates': c_byte,
    'SC_SolenoidStates': c_byte,
    'TC_DisplayModes': c_ushort,
    'TC_SensorTypes': c_ushort,
    'TIM_ButtonsMode': c_uint16,
    'TIM_Channels': c_ushort,
    'TIM_Direction': c_byte,
    'TIM_JogMode': c_uint16,
    'TSG_Display_Modes': c_short,
    'TSG_Hub_Analogue_Modes': c_short,
    'TST_Stages': c_short,
    'UnitType': c_short,
}


if __name__ == '__main__':
    # The following was used to automatically generate the above...
    import os
    from msl.equipment.resources.utils import CHeader

    enums = {}  # dict of all enums
    enum_ctypes = {'UnitType': 'c_short'}  # dict of enum data types

    root = r'C:\Program Files\Thorlabs\Kinesis'
    for f in os.listdir(root):
        if f.endswith('.h'):
            header = CHeader(os.path.join(root, f))
            for key, value in header.enums().items():
                if key in enums:
                    continue
                enum_ctypes[key] = value[1]
                enums[key] = value[2]

    for class_name in enums:
        print('class {}(IntEnum):'.format(class_name))
        for name, value in enums[class_name].items():
            print('    {} = {}'.format(name, value))
        print('\n')

    print('class UnitType(IntEnum):')
    print('    DISTANCE = 0')
    print('    VELOCITY = 1')
    print('    ACCELERATION = 2')

    print('\n')
    print('ENUM_CTYPE = {')
    for e in sorted(enum_ctypes):
        print("    '{}': {},".format(e, enum_ctypes[e]))
    print('}')
