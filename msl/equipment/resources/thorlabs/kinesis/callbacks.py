"""
A callback to register for a :class:`~msl.equipment.resources.thorlabs.kinesis.motion_control.MotionControl`
message queue.

.. code-block:: python

   from msl.equipment import Config
   from msl.equipment.resources.thorlabs import MotionControlCallback
   from msl.examples.equipment import EXAMPLES_DIR

   @MotionControlCallback
   def msg_callback():
       print('MotionControlCallback: ', flipper.convert_message(*flipper.get_next_message()))

   # The "example2.xml" configuration file contains the following element:
   # <equipment alias="filter_flipper" manufacturer="Thorlabs" model="MFF101/M"/>

   db = Config(os.path.join(EXAMPLES_DIR, 'example2.xml')).database()

   flipper = db.equipment['filter_flipper'].connect()
   flipper.register_message_callback(msg_callback)

   ... do stuff with the `flipper` ...

"""
from msl.loadlib import IS_WINDOWS

if IS_WINDOWS:
    from ctypes import WINFUNCTYPE
    FUNCTYPE = WINFUNCTYPE
else:
    from ctypes import CFUNCTYPE
    FUNCTYPE = CFUNCTYPE

MotionControlCallback = FUNCTYPE(None)
"""
A callback to register for a :class:`~msl.equipment.resources.thorlabs.kinesis.motion_control.MotionControl`
message queue.
"""
