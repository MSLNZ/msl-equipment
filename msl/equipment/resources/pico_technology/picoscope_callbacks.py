import sys
from ctypes import WINFUNCTYPE, CFUNCTYPE, POINTER, c_int16, c_uint32, c_void_p, c_int32

from msl.equipment.resources.pico_technology.pico_status import PICO_STATUS

if sys.platform in ('win32', 'cygwin'):
    FUNCTYPE = WINFUNCTYPE
else:
    FUNCTYPE = CFUNCTYPE

ps2000aBlockReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
ps3000aBlockReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
ps4000BlockReady  = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
ps4000aBlockReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
ps5000BlockReady  = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
ps5000aBlockReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
ps6000BlockReady  = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)

ps2000aStreamingReady = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
ps3000aStreamingReady = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
ps4000StreamingReady  = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
ps4000aStreamingReady = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
ps5000StreamingReady  = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
ps5000aStreamingReady = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
ps6000StreamingReady  = FUNCTYPE(None, c_int16, c_uint32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)

ps2000aDataReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_uint32, c_int16, c_void_p)
ps3000aDataReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_uint32, c_int16, c_void_p)
ps4000DataReady  = FUNCTYPE(None, c_int16, c_int32, c_int16, c_uint32, c_int16, c_void_p)
ps4000aDataReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_uint32, c_int16, c_void_p)
ps5000DataReady  = FUNCTYPE(None, c_int16, c_int32, c_int16, c_uint32, c_int16, c_void_p)
ps5000aDataReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_uint32, c_int16, c_void_p)
ps6000DataReady  = FUNCTYPE(None, c_int16, PICO_STATUS, c_uint32, c_int16, c_void_p)

PS3000_CALLBACK_FUNC = FUNCTYPE(None, POINTER(c_int16), c_int16)

GetOverviewBuffersMaxMin = FUNCTYPE(None, POINTER(POINTER(c_int16)), c_int16, c_uint32, c_int16, c_int16, c_uint32)

CALLBACK_NAMES = [
    'GetOverviewBuffersMaxMin',
    'ps2000aBlockReady',
    'ps2000aStreamingReady',
    'ps2000aDataReady',
    'PS3000_CALLBACK_FUNC',
    'ps3000aBlockReady',
    'ps3000aStreamingReady',
    'ps3000aDataReady',
    'ps4000BlockReady',
    'ps4000StreamingReady',
    'ps4000DataReady',
    'ps4000aBlockReady',
    'ps4000aStreamingReady',
    'ps4000aDataReady',
    'ps5000BlockReady',
    'ps5000StreamingReady',
    'ps5000DataReady',
    'ps5000aBlockReady',
    'ps5000aStreamingReady',
    'ps5000aDataReady',
    'ps6000BlockReady',
    'ps6000StreamingReady',
    'ps6000DataReady',
]
