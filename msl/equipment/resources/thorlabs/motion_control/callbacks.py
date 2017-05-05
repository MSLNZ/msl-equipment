from ctypes import WINFUNCTYPE

MotionControlCallback = WINFUNCTYPE(None)
"""A callback to register for a MotionControl message queue.

Example usage::

    from msl.examples.equipment import EXAMPLES_DIR
    from msl.equipment.database import load
    from msl.equipment.resources.thorlabs import MotionControlCallback
    
    @MotionControlCallback
    def msg_callback():
        print('MotionControlCallback: ', flipper.convert_message(*flipper.get_next_message()))        

    # The "equipment-configuration.xml" configuration file contains the following element:
    # <equipment alias="filter_flipper" manufacturer="Thorlabs" model="MFF101/M" serial="37871232"/>

    db = load(os.path.join(EXAMPLES_DIR, 'equipment-configuration.xml'))
    flipper = db.equipment['filter_flipper'].connect()
    flipper.register_message_callback(msg_callback)
    
    ... do stuff with the `flipper` ...
"""
