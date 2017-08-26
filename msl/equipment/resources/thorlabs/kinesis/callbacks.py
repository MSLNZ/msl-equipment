"""
Callbacks defined in the Thorlabs Kinesis software v1.11.0
"""
from msl.loadlib import IS_WINDOWS

if IS_WINDOWS:
    from ctypes import WINFUNCTYPE
    FUNCTYPE = WINFUNCTYPE
else:
    from ctypes import CFUNCTYPE
    FUNCTYPE = CFUNCTYPE

MotionControlCallback = FUNCTYPE(None)
"""A callback to register for a MotionControl message queue.

Example usage::

    from msl.equipment import Config
    from msl.equipment.resources.thorlabs import MotionControlCallback
    from msl.examples.equipment import EXAMPLES_DIR
    
    @MotionControlCallback
    def msg_callback():
        print('MotionControlCallback: ', flipper.convert_message(*flipper.get_next_message()))        

    # The "equipment-configuration.xml" configuration file contains the following element:
    # <equipment alias="filter_flipper" manufacturer="Thorlabs" model="MFF101/M" serial="37871232"/>

    db = Config(os.path.join(EXAMPLES_DIR, 'equipment-configuration.xml')).database()
    flipper = db.equipment['filter_flipper'].connect()
    flipper.register_message_callback(msg_callback)
    
    ... do stuff with the `flipper` ...
"""
