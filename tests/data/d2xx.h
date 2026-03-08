// d2xx.h
// Mocks a D2xx library for testing purposes.
//

#if defined(_MSC_VER)
    // Microsoft
    #define EXPORT __declspec(dllexport)
#elif defined(__GNUC__)
    // G++
    #define EXPORT __attribute__((visibility("default")))
#else
#   error "Unknown EXPORT semantics"
#endif

extern "C" {
    #if defined(_MSC_VER)
    #else
        EXPORT int FT_SetVIDPID(long vid, long pid);
    #endif

    EXPORT int FT_Open(long deviceNumber, int *handle);
    EXPORT int FT_OpenEx(int arg1, long flags, int *handle);
    EXPORT int FT_Close(int handle);
    EXPORT int FT_Read(int handle, void *buffer, long bytesToRead, long *bytesReturned);
    EXPORT int FT_Write(int handle, void *buffer, long bytesToWrite, long *bytesWritten);
    EXPORT int FT_SetBaudRate(int handle, long baudRate);
    EXPORT int FT_SetDivisor(int handle, short divisor);
    EXPORT int FT_SetDataCharacteristics(int handle, char wordLength, char stopBits, char parity);
    EXPORT int FT_SetTimeouts(int handle, long read, long write);
    EXPORT int FT_SetFlowControl(int handle, short flow, char xonChar, char xoffChar);
    EXPORT int FT_SetDtr(int handle);
    EXPORT int FT_ClrDtr(int handle);
    EXPORT int FT_SetRts(int handle);
    EXPORT int FT_ClrRts(int handle);
    EXPORT int FT_GetModemStatus(int handle, long *status);
    EXPORT int FT_GetQueueStatus(int handle, long *inRxQueue);
    EXPORT int FT_GetStatus(int handle, long *inRxQueue, long *inTxQueue, long *eventStatus);
    EXPORT int FT_SetEventNotification(int handle, long mask, void *eventHandle);
    EXPORT int FT_SetChars(int handle, char eventChar, char eventCharEnabled, char errorChar, char errorCharEnabled);
    EXPORT int FT_SetBreakOn(int handle);
    EXPORT int FT_SetBreakOff(int handle);
    EXPORT int FT_Purge(int handle, long mask);
    EXPORT int FT_ResetDevice(int handle);
    EXPORT int FT_ResetPort(int handle);
    EXPORT int FT_CyclePort(int handle);
    EXPORT int FT_StopInTask(int handle);
    EXPORT int FT_RestartInTask(int handle);
    EXPORT int FT_SetWaitMask(int handle, long mask);
    EXPORT int FT_WaitOnMask(int handle, long *mask);
    EXPORT int FT_SetLatencyTimer(int handle, char latency);
    EXPORT int FT_GetLatencyTimer(int handle, char *latency);
    EXPORT int FT_SetBitMode(int handle, char mask, char enable);
    EXPORT int FT_GetBitMode(int handle, char *mode);
    EXPORT int FT_SetUSBParameters(int handle, long inSize, long outSize);

    EXPORT int FT_CreateDeviceInfoList(long *numDevs);
    EXPORT int FT_GetDeviceInfoDetail(long index, long *flags, long *type, long *id, long *locId, void *serialNumber, void *description, int *handle);
}