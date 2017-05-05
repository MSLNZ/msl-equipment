"""
Attribute token definition file for Bentham Instruments Spectroradiometer 
Control DLL.
"""

# -----------------------------------------------------------------------------
# Monochromator attributes
# -----------------------------------------------------------------------------
MonochromatorScanDirection = 10
MonochromatorCurrentWL = 11
MonochromatorCurrentDialReading = 12
MonochromatorParkDialReading = 13
MonochromatorCurrentGrating = 14
MonochromatorPark = 15
MonochromatorSelfPark = 16
MonochromatorModeSwitchNum = 17
MonochromatorModeSwitchState = 18
MonochromatorCanModeSwitch = 19

Gratingd = 20
GratingZ = 21
GratingA = 22
GratingWLMin = 23
GratingWLMax = 24
GratingX2 = 25
GratingX1 = 26
GratingX = 27

ChangerZ = 50

# -----------------------------------------------------------------------------
# Filter wheel attributes
# -----------------------------------------------------------------------------
FWheelFilter = 100
FWheelPositions = 101
FWheelCurrentPosition = 102

# -----------------------------------------------------------------------------
#  TLS attributes
# -----------------------------------------------------------------------------
TLSCurrentPosition = 150
TLSWL = 151
TLSPOS = 152
TLSSelectWavelength = 153
TLSPositionsCommand = 154

# -----------------------------------------------------------------------------
# Switch-over box attributes
# -----------------------------------------------------------------------------
SOBInitialState = 200
SOBState = 202

# -----------------------------------------------------------------------------
# SAM attributes
# -----------------------------------------------------------------------------
SAMInitialState = 300
SAMSwitchWL = 301
SAMState = 302
SAMCurrentState = 303

# -----------------------------------------------------------------------------
# Stepper SAM attributes
# -----------------------------------------------------------------------------
SSEnergisedSteps = 320
SSRelaxedSteps = 321
SSMaxSteps = 322
SSSpeed = 323
SSMoveCurrent = 324
SSIdleCurrent = 325

# -----------------------------------------------------------------------------
# 262 attributes
# -----------------------------------------------------------------------------
biRelay = 350
biCurrentRelay = 351

# -----------------------------------------------------------------------------
# MVSS attributes
# -----------------------------------------------------------------------------
MVSSSwitchWL = 401
MVSSWidth = 402
MVSSCurrentWidth = 403
MVSSSetWidth = 404
MVSSConstantBandwidth = 405
MVSSConstantwidth = 406
MVSSSlitMode = 407
MVSSPosition = 408

# -----------------------------------------------------------------------------
# ADC attributes
# -----------------------------------------------------------------------------
ADCSamplesPerReading = 500
ADCAdaptiveIntegration = 501
ADCSamplePeriod = 502
ADCVolts = 504

# -----------------------------------------------------------------------------
# ADC CHOPPER attributes
# -----------------------------------------------------------------------------
ADCChoppedAverages = 503

# -----------------------------------------------------------------------------
# General amplifier attributes
# -----------------------------------------------------------------------------
AmpGain = 600
AmpChannel = 601
AmpMinRange = 602
AmpMaxRange = 603
AmpStartRange = 604
AmpUseSetup = 605
AmpCurrentRange = 606
AmpCurrentChannel = 607
AmpOverload = 608
AmpOverrideWl = 609

# -----------------------------------------------------------------------------
# 225 attributes
# -----------------------------------------------------------------------------
A225TargetRange = 700
A225PhaseVariable = 701
A225PhaseQuadrant = 702
A225TimeConstant = 703
A225fMode = 704

# -----------------------------------------------------------------------------
# Camera attributes
# -----------------------------------------------------------------------------
CameraIntegrationTime = 800
CameraMinWl = 801
CameraMaxWl = 802
CameraNumPixelsW = 803
CameraWidth = 804
CameraDataSize_nm = 805
CameraSAMState = 806
CameraAutoRange = 807
CameraMVSSWidth = 808
CameraAverages = 809
CameraMinITime = 810
CameraMaxITime = 811
CameraUnitMaxITime = 812
CameraZCITime = 813
CameraZCAverages = 814
CameraDataLToR = 815

# -----------------------------------------------------------------------------
# Motorised Stage attributes
# -----------------------------------------------------------------------------
MotorPosition = 900

# -----------------------------------------------------------------------------
# Miscellaneous attributes
# -----------------------------------------------------------------------------
biSettleDelay = 1000
biMin = 1001
biMax = 1002
biParkPos = 1003
biInput = 1004
biCurrentInput = 1005
biMoveWithWavelength = 1006
biHasSetupWindow = 1007
biHasAdvancedWindow = 1008
biDescriptor = 1009
biParkOffset = 1010
biProductName = 1011

# -----------------------------------------------------------------------------
# System attributes
# -----------------------------------------------------------------------------
SysStopCount = 9000
SysDarkIIntegrationTime = 9001
Sys225_277Input = 9002

# -----------------------------------------------------------------------------
# Bentham Hardware Types
# -----------------------------------------------------------------------------
BenInterface = 10000
BenSAM = 10001
BenSlit = 10002
BenFilterWheel = 10003
BenADC = 10004
BenPREAMP = 10005
BenACAMP = 10006
BenDCAMP = 10007
BenPOSTAMP = 10012
BenRelayUnit = 10008
BenMono = 10009
BenAnonDevice = 10010
BenCamera = 10020
BenDiodeArray = 10021
BenORM = 10022

BenUnknown = 10011
