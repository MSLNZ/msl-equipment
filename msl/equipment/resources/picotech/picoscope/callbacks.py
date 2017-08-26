"""
Callback functions in the Pico Technology SDK v10.6.10.24
"""
from ctypes import POINTER, c_int16, c_uint32, c_void_p, c_int32

from msl.loadlib import IS_WINDOWS

from .errors import PICO_STATUS

if IS_WINDOWS:
    from ctypes import WINFUNCTYPE
    FUNCTYPE = WINFUNCTYPE
else:
    from ctypes import CFUNCTYPE
    FUNCTYPE = CFUNCTYPE

BlockReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
"""All BlockReady callbacks have the same function signature, so create a generic BlockReady callback."""

ps2000aBlockReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
"""ps2000aBlockReady callback"""
ps3000aBlockReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
"""ps3000aBlockReady callback"""
ps4000BlockReady  = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
"""ps4000BlockReady callback"""
ps4000aBlockReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
"""ps4000aBlockReady callback"""
ps5000BlockReady  = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
"""ps5000BlockReady callback"""
ps5000aBlockReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
"""ps5000aBlockReady callback"""
ps6000BlockReady  = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
"""ps6000BlockReady callback"""

ps2000aStreamingReady = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
"""ps2000aStreamingReady callback"""
ps3000aStreamingReady = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
"""ps3000aStreamingReady callback"""
ps4000StreamingReady  = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
"""ps4000StreamingReady callback"""
ps4000aStreamingReady = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
"""ps4000aStreamingReady callback"""
ps5000StreamingReady  = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
"""ps5000StreamingReady callback"""
ps5000aStreamingReady = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
"""ps5000aStreamingReady callback"""
ps6000StreamingReady  = FUNCTYPE(None, c_int16, c_uint32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
"""ps6000StreamingReady callback"""

ps2000aDataReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_uint32, c_int16, c_void_p)
"""ps2000aDataReady callback"""
ps3000aDataReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_uint32, c_int16, c_void_p)
"""ps3000aDataReady callback"""
ps4000DataReady  = FUNCTYPE(None, c_int16, c_int32, c_int16, c_uint32, c_int16, c_void_p)
"""ps4000DataReady callback"""
ps4000aDataReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_uint32, c_int16, c_void_p)
"""ps4000aDataReady callback"""
ps5000DataReady  = FUNCTYPE(None, c_int16, c_int32, c_int16, c_uint32, c_int16, c_void_p)
"""ps5000DataReady callback"""
ps5000aDataReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_uint32, c_int16, c_void_p)
"""ps5000aDataReady callback"""
ps6000DataReady  = FUNCTYPE(None, c_int16, PICO_STATUS, c_uint32, c_int16, c_void_p)
"""ps6000DataReady callback"""

PS3000_CALLBACK_FUNC = FUNCTYPE(None, POINTER(c_int16), c_int16)
"""PS3000_CALLBACK_FUNC callback"""

GetOverviewBuffersMaxMin = FUNCTYPE(None, POINTER(POINTER(c_int16)), c_int16, c_uint32, c_int16, c_int16, c_uint32)
"""GetOverviewBuffersMaxMin callback"""

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
