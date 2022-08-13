"""
Resources for equipment from `Pico Technology <https://www.picotech.com/>`_.
"""
from ctypes import c_uint32 as c_enum

from .picoscope import enums
from .picoscope import structs
from .picoscope.callbacks import BlockReady
from .picoscope.callbacks import GetOverviewBuffersMaxMin
from .picoscope.callbacks import ps2000aBlockReady
from .picoscope.callbacks import ps2000aDataReady
from .picoscope.callbacks import ps2000aStreamingReady
from .picoscope.callbacks import ps3000aBlockReady
from .picoscope.callbacks import ps3000aDataReady
from .picoscope.callbacks import ps3000aStreamingReady
from .picoscope.callbacks import ps4000BlockReady
from .picoscope.callbacks import ps4000DataReady
from .picoscope.callbacks import ps4000StreamingReady
from .picoscope.callbacks import ps4000aBlockReady
from .picoscope.callbacks import ps4000aDataReady
from .picoscope.callbacks import ps4000aStreamingReady
from .picoscope.callbacks import ps5000BlockReady
from .picoscope.callbacks import ps5000DataReady
from .picoscope.callbacks import ps5000StreamingReady
from .picoscope.callbacks import ps5000aBlockReady
from .picoscope.callbacks import ps5000aDataReady
from .picoscope.callbacks import ps5000aStreamingReady
from .picoscope.callbacks import ps6000BlockReady
from .picoscope.callbacks import ps6000DataReady
from .picoscope.callbacks import ps6000StreamingReady
from .picoscope.callbacks import PS3000_CALLBACK_FUNC
from .picoscope.ps2000 import PicoScope2000
from .picoscope.ps2000a import PicoScope2000A
from .picoscope.ps3000 import PicoScope3000
from .picoscope.ps3000a import PicoScope3000A
from .picoscope.ps4000 import PicoScope4000
from .picoscope.ps4000a import PicoScope4000A
from .picoscope.ps5000 import PicoScope5000
from .picoscope.ps5000a import PicoScope5000A
from .picoscope.ps6000 import PicoScope6000
from .pt104 import Pt104DataType
from .pt104 import PT104
