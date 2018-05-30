"""
Device Message Queue defined in Thorlabs.MotionControl.C_API.

The device message queue allows the internal events raised by the device to be 
monitored by the DLLs owner. 

The device raises many different events, usually associated with a change of state.

These messages are temporarily stored in the DLL and can be accessed using the 
appropriate message functions.
"""

#: MessageTypes
MessageTypes = {
    0: 'GenericDevice',
    1: 'GenericPiezo',
    2: 'GenericMotor',
    3: 'GenericDCMotor',
    4: 'GenericSimpleMotor',
    5: 'RackDevice',
    6: 'Laser',
    7: 'TECCtlr',
    8: 'Quad',
    9: 'NanoTrak',
    10: 'Specialized',
    11: 'Solenoid',
}

#: GenericDevice
GenericDevice = {
    0: 'settingsInitialized',
    1: 'settingsUpdated',
    2: 'error',
    3: 'close',
}

#: GenericPiezo
GenericPiezo = {
    0: 'maxVoltageChanged',
    1: 'controlModeChanged',
    2: 'statusChanged',
    3: 'maxTravelChanged',
    4: 'TSG_Status',
    5: 'TSG_DisplayModeChanged',
}

#: GenericMotor
GenericMotor = {
    0: 'Homed',
    1: 'Moved',
    2: 'Stopped',
    3: 'LimitUpdated',
}

#: GenericDCMotor
GenericDCMotor = {
    0: 'error',
    1: 'status',
}

#: GenericSimpleMotor
GenericSimpleMotor = {}

#: RackDevice
RackDevice = {
    0: 'RackCountEstablished',
    1: 'RackBayState',
}

#: Laser
Laser = {
    0: 'statusChanged',
    1: 'controlSourceChanged',
    2: 'displayModeChanged',
}

#: TECCtlr
TECCtlr = {
    0: 'statusChanged',
    2: 'displaySettingsChanged',
    3: 'feedbackParamsChanged',
}

#: Quad
Quad = {
    0: 'statusChanged',
}

#: NanoTrak
NanoTrak = {
    0: 'statusChanged',
}

#: Specialized
Specialized = {}

#: Solenoid
Solenoid = {
    0: 'statusChanged',
}

#: MessageID
MessageID = {
    'GenericDevice': GenericDevice,
    'GenericPiezo': GenericPiezo,
    'GenericMotor': GenericMotor,
    'GenericDCMotor': GenericDCMotor,
    'GenericSimpleMotor': GenericSimpleMotor,
    'RackDevice': RackDevice,
    'Laser': Laser,
    'TECCtlr': TECCtlr,
    'Quad': Quad,
    'NanoTrak': NanoTrak,
    'Specialized': Specialized,
    'Solenoid': Solenoid,
}
