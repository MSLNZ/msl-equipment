from ctypes import Structure, c_int16, c_uint16, c_uint32, c_int64, c_uint64

from .picoscope import c_enum
from .errors import PICO_STATUS


# ************************ typedef struct for ps2000 ************************


class PS2000TriggerChannelProperties(Structure):
    _fields_ = [
        ('thresholdMajor', c_int16),
        ('thresholdMinor', c_int16),
        ('hysteresis'    , c_uint16),
        ('channel'       , c_int16),
        ('thresholdMode' , c_enum),
    ]


class PS2000TriggerConditions(Structure):
    _fields_ = [
        ('channelA'           , c_enum),
        ('channelB'           , c_enum),
        ('channelC'           , c_enum),
        ('channelD'           , c_enum),
        ('external'           , c_enum),
        ('pulseWidthQualifier', c_enum),
    ]


class PS2000PwqConditions(Structure):
    _fields_ = [
        ('channelA', c_enum),
        ('channelB', c_enum),
        ('channelC', c_enum),
        ('channelD', c_enum),
        ('external', c_enum),
    ]


# ************************ typedef struct for ps2000aApi ************************


class PS2000ATriggerConditions(Structure):
    _fields_ = [
        ('channelA'           , c_enum),
        ('channelB'           , c_enum),
        ('channelC'           , c_enum),
        ('channelD'           , c_enum),
        ('external'           , c_enum),
        ('aux'                , c_enum),
        ('pulseWidthQualifier', c_enum),
        ('digital'            , c_enum),
    ]


class PS2000APwqConditions(Structure):
    _fields_ = [
        ('channelA', c_enum),
        ('channelB', c_enum),
        ('channelC', c_enum),
        ('channelD', c_enum),
        ('external', c_enum),
        ('aux'     , c_enum),
        ('digital' , c_enum),
    ]


class PS2000ADigitalChannelDirections(Structure):
    _fields_ = [
        ('channel'  , c_enum),
        ('direction', c_enum),
    ]


class PS2000ATriggerChannelProperties(Structure):
    _fields_ = [
        ('thresholdUpper'          , c_int16),
        ('thresholdUpperHysteresis', c_uint16),
        ('thresholdLower'          , c_int16),
        ('thresholdLowerHysteresis', c_uint16),
        ('channel'                 , c_enum),
        ('thresholdMode'           , c_enum),
    ]


# ************************ typedef struct for ps3000 ************************


class PS3000TriggerChannelProperties(Structure):
    _fields_ = [
        ('thresholdMajor', c_int16),
        ('thresholdMinor', c_int16),
        ('hysteresis'    , c_uint16),
        ('channel'       , c_int16),
        ('thresholdMode' , c_enum),
    ]


class PS3000TriggerConditions(Structure):
    _fields_ = [
        ('channelA'           , c_enum),
        ('channelB'           , c_enum),
        ('channelC'           , c_enum),
        ('channelD'           , c_enum),
        ('external'           , c_enum),
        ('pulseWidthQualifier', c_enum),
    ]


class PS3000PwqConditions(Structure):
    _fields_ = [
        ('channelA', c_enum),
        ('channelB', c_enum),
        ('channelC', c_enum),
        ('channelD', c_enum),
        ('external', c_enum),
    ]


# ************************ typedef struct for ps3000aApi ************************


class PS3000ATriggerConditions(Structure):
    _fields_ = [
        ('channelA'           , c_enum),
        ('channelB'           , c_enum),
        ('channelC'           , c_enum),
        ('channelD'           , c_enum),
        ('external'           , c_enum),
        ('aux'                , c_enum),
        ('pulseWidthQualifier', c_enum),
    ]


class PS3000ATriggerConditionsV2(Structure):
    _fields_ = [
        ('channelA'           , c_enum),
        ('channelB'           , c_enum),
        ('channelC'           , c_enum),
        ('channelD'           , c_enum),
        ('external'           , c_enum),
        ('aux'                , c_enum),
        ('pulseWidthQualifier', c_enum),
        ('digital'            , c_enum),
    ]


class PS3000APwqConditions(Structure):
    _fields_ = [
        ('channelA', c_enum),
        ('channelB', c_enum),
        ('channelC', c_enum),
        ('channelD', c_enum),
        ('external', c_enum),
        ('aux'     , c_enum),
    ]


class PS3000APwqConditionsV2(Structure):
    _fields_ = [
        ('channelA', c_enum),
        ('channelB', c_enum),
        ('channelC', c_enum),
        ('channelD', c_enum),
        ('external', c_enum),
        ('aux'     , c_enum),
        ('digital' , c_enum),
    ]


class PS3000ADigitalChannelDirections(Structure):
    _fields_ = [
        ('channel'  , c_enum),
        ('direction', c_enum),
    ]


class PS3000ATriggerChannelProperties(Structure):
    _fields_ = [
        ('thresholdUpper'          , c_int16),
        ('thresholdUpperHysteresis', c_uint16),
        ('thresholdLower'          , c_int16),
        ('thresholdLowerHysteresis', c_uint16),
        ('channel'                 , c_enum),
        ('thresholdMode'           , c_enum),
    ]


class PS3000ATriggerInfo(Structure):
    _fields_ = [
        ('status'          , PICO_STATUS),
        ('segmentIndex'    , c_uint32),
        ('reserved0'       , c_uint32),
        ('triggerTime'     , c_int64),
        ('timeUnits'       , c_int16),
        ('reserved1'       , c_int16),
        ('timeStampCounter', c_uint64),
    ]


# ************************ typedef struct for ps4000Api ************************


class PS4000TriggerConditions(Structure):
    _fields_ = [
        ('channelA'           , c_enum),
        ('channelB'           , c_enum),
        ('channelC'           , c_enum),
        ('channelD'           , c_enum),
        ('external'           , c_enum),
        ('aux'                , c_enum),
        ('pulseWidthQualifier', c_enum),
    ]


class PS4000PwqConditions(Structure):
    _fields_ = [
        ('channelA', c_enum),
        ('channelB', c_enum),
        ('channelC', c_enum),
        ('channelD', c_enum),
        ('external', c_enum),
        ('aux'     , c_enum),
    ]


class PS4000TriggerChannelProperties(Structure):
    _fields_ = [
        ('thresholdUpper'          , c_int16),
        ('thresholdUpperHysteresis', c_uint16),
        ('thresholdLower'          , c_int16),
        ('thresholdLowerHysteresis', c_uint16),
        ('channel'                 , c_enum),
        ('thresholdMode'           , c_enum),
    ]


# ************************ typedef struct for ps4000aApi ************************


class PS4000AChannelLedSetting(Structure):
    _fields_ = [
        ('channel', c_enum),
        ('state'  , c_enum),
    ]


class PS4000ADirection(Structure):
    _fields_ = [
        ('channel'  , c_enum),
        ('direction', c_enum),
    ]


class PS4000ACondition(Structure):
    _fields_ = [
        ('source'   , c_enum),
        ('condition', c_enum),
    ]


class PS4000ATriggerChannelProperties(Structure):
    _fields_ = [
        ('thresholdUpper'          , c_int16),
        ('thresholdUpperHysteresis', c_uint16),
        ('thresholdLower'          , c_int16),
        ('thresholdLowerHysteresis', c_uint16),
        ('channel'                 , c_enum),
        ('thresholdMode'           , c_enum),
    ]


class PS4000AConnectDetect(Structure):
    _fields_ = [
        ('channel', c_enum),
        ('state'  , c_enum),
    ]


# ************************ typedef struct for ps5000Api ************************


class PS5000TriggerConditions(Structure):
    _fields_ = [
        ('channelA'           , c_enum),
        ('channelB'           , c_enum),
        ('channelC'           , c_enum),
        ('channelD'           , c_enum),
        ('external'           , c_enum),
        ('aux'                , c_enum),
        ('pulseWidthQualifier', c_enum),
    ]


class PS5000PwqConditions(Structure):
    _fields_ = [
        ('channelA', c_enum),
        ('channelB', c_enum),
        ('channelC', c_enum),
        ('channelD', c_enum),
        ('external', c_enum),
        ('aux'     , c_enum),
    ]


class PS5000TriggerChannelProperties(Structure):
    _fields_ = [
        ('thresholdMajor', c_int16),
        ('thresholdMinor', c_int16),
        ('hysteresis'    , c_uint16),
        ('channel'       , c_enum),
        ('thresholdMode' , c_enum),
    ]


# ************************ typedef struct for ps5000aApi ************************


class PS5000ATriggerInfo(Structure):
    _fields_ = [
        ('status'      , PICO_STATUS),
        ('segmentIndex', c_uint32),
        ('triggerIndex', c_uint32),
        ('triggerTime' , c_int64),
        ('timeUnits'   , c_int16),
        ('reserved0'   , c_int16),
        ('reserved1'   , c_uint64),
    ]


class PS5000ATriggerConditions(Structure):
    _fields_ = [
        ('channelA'           , c_enum),
        ('channelB'           , c_enum),
        ('channelC'           , c_enum),
        ('channelD'           , c_enum),
        ('external'           , c_enum),
        ('aux'                , c_enum),
        ('pulseWidthQualifier', c_enum),
    ]


class PS5000APwqConditions(Structure):
    _fields_ = [
        ('channelA', c_enum),
        ('channelB', c_enum),
        ('channelC', c_enum),
        ('channelD', c_enum),
        ('external', c_enum),
        ('aux'     , c_enum),
    ]


class PS5000ATriggerChannelProperties(Structure):
    _fields_ = [
        ('thresholdUpper'          , c_int16),
        ('thresholdUpperHysteresis', c_uint16),
        ('thresholdLower'          , c_int16),
        ('thresholdLowerHysteresis', c_uint16),
        ('channel'                 , c_enum),
        ('thresholdMode'           , c_enum),
    ]


# ************************ typedef struct for ps6000Api ************************


class PS6000TriggerConditions(Structure):
    _fields_ = [
        ('channelA'           , c_enum),
        ('channelB'           , c_enum),
        ('channelC'           , c_enum),
        ('channelD'           , c_enum),
        ('external'           , c_enum),
        ('aux'                , c_enum),
        ('pulseWidthQualifier', c_enum),
    ]


class PS6000PwqConditions(Structure):
    _fields_ = [
        ('channelA', c_enum),
        ('channelB', c_enum),
        ('channelC', c_enum),
        ('channelD', c_enum),
        ('external', c_enum),
        ('aux'     , c_enum),
    ]


class PS6000TriggerChannelProperties(Structure):
    _fields_ = [
        ('thresholdUpper' , c_int16),
        ('hysteresisUpper', c_uint16),
        ('thresholdLower' , c_int16),
        ('hysteresisLower', c_uint16),
        ('channel'        , c_enum),
        ('thresholdMode'  , c_enum),
    ]


STRUCT_DATA_TYPE_ALIASES = {
    'PS2000A_DIGITAL_CHANNEL_DIRECTIONS': PS2000ADigitalChannelDirections,
    'PS2000A_PWQ_CONDITIONS': PS2000APwqConditions,
    'PS2000A_TRIGGER_CHANNEL_PROPERTIES': PS2000ATriggerChannelProperties,
    'PS2000A_TRIGGER_CONDITIONS': PS2000ATriggerConditions,
    'PS2000_PWQ_CONDITIONS': PS2000PwqConditions,
    'PS2000_TRIGGER_CHANNEL_PROPERTIES': PS2000TriggerChannelProperties,
    'PS2000_TRIGGER_CONDITIONS': PS2000TriggerConditions,
    'PS3000A_DIGITAL_CHANNEL_DIRECTIONS': PS3000ADigitalChannelDirections,
    'PS3000A_PWQ_CONDITIONS': PS3000APwqConditions,
    'PS3000A_PWQ_CONDITIONS_V2': PS3000APwqConditionsV2,
    'PS3000A_TRIGGER_CHANNEL_PROPERTIES': PS3000ATriggerChannelProperties,
    'PS3000A_TRIGGER_CONDITIONS': PS3000ATriggerConditions,
    'PS3000A_TRIGGER_CONDITIONS_V2': PS3000ATriggerConditionsV2,
    'PS3000A_TRIGGER_INFO': PS3000ATriggerInfo,
    'PS3000_PWQ_CONDITIONS': PS3000PwqConditions,
    'PS3000_TRIGGER_CHANNEL_PROPERTIES': PS3000TriggerChannelProperties,
    'PS3000_TRIGGER_CONDITIONS': PS3000TriggerConditions,
    'PS4000A_CHANNEL_LED_SETTING': PS4000AChannelLedSetting,
    'PS4000A_CONDITION': PS4000ACondition,
    'PS4000A_CONNECT_DETECT': PS4000AConnectDetect,
    'PS4000A_DIRECTION': PS4000ADirection,
    'PS4000A_TRIGGER_CHANNEL_PROPERTIES': PS4000ATriggerChannelProperties,
    'PS4000_PWQ_CONDITIONS': PS4000PwqConditions,
    'PS4000_TRIGGER_CHANNEL_PROPERTIES': PS4000TriggerChannelProperties,
    'PS4000_TRIGGER_CONDITIONS': PS4000TriggerConditions,
    'PS5000A_PWQ_CONDITIONS': PS5000APwqConditions,
    'PS5000A_TRIGGER_CHANNEL_PROPERTIES': PS5000ATriggerChannelProperties,
    'PS5000A_TRIGGER_CONDITIONS': PS5000ATriggerConditions,
    'PS5000A_TRIGGER_INFO': PS5000ATriggerInfo,
    'PS5000_PWQ_CONDITIONS': PS5000PwqConditions,
    'PS5000_TRIGGER_CHANNEL_PROPERTIES': PS5000TriggerChannelProperties,
    'PS5000_TRIGGER_CONDITIONS': PS5000TriggerConditions,
    'PS6000_PWQ_CONDITIONS': PS6000PwqConditions,
    'PS6000_TRIGGER_CHANNEL_PROPERTIES': PS6000TriggerChannelProperties,
    'PS6000_TRIGGER_CONDITIONS': PS6000TriggerConditions,
}
