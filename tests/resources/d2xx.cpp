// d2xx.cpp
// Mocks a D2xx library for testing purposes.
//
// Compiled using:
//   cl /LD d2xx.cpp /link /OUT:d2xx.dll
//   g++ d2xx.cpp -fPIC -shared -Bstatic -Wall -o d2xx.so
//   g++ d2xx.cpp -fPIC -shared -Bstatic -Wall -o d2xx.dylib
//
#include "d2xx.h"
#include <cstring>

#if defined(_MSC_VER)
#else
    int FT_SetVIDPID(long vid, long pid) { return 0; }
#endif

int FT_Open(long deviceNumber, int *handle) { *handle=1; return 0; }
int FT_OpenEx(int arg1, long flags, int *handle) { *handle=2; return 0; }
int FT_Close(int handle) { return 0; }
int FT_Read(int handle, void *buffer, long bytesToRead, long *bytesReturned) {
    memset(buffer, 'A', 92);
    return 0;
}
int FT_Write(int handle, void *buffer, long bytesToWrite, long *bytesWritten) {
    *bytesWritten = 10;
    return 0;
}
int FT_SetBaudRate(int handle, long baudRate) { return 0; }
int FT_SetDivisor(int handle, short divisor) { return 17; } // FT_NOT_SUPPORTED
int FT_SetDataCharacteristics(int handle, char wordLength, char stopBits, char parity) { return 0; }
int FT_SetTimeouts(int handle, long read, long write) { return 0; }
int FT_SetFlowControl(int handle, short flow, char xonChar, char xoffChar) { return 0; }
int FT_SetDtr(int handle) { return 0; }
int FT_ClrDtr(int handle) { return 0; }
int FT_SetRts(int handle) { return 0; }
int FT_ClrRts(int handle) { return 0; }
int FT_GetModemStatus(int handle, long *status) {
    *status = 24593;  // modem=17, line=96
    return 0;
}
int FT_GetQueueStatus(int handle, long *inRxQueue) {
    if ( handle == 1 ) {
        *inRxQueue = 0;
    } else {
        *inRxQueue = 90;
    }
    return 0; }
int FT_GetStatus(int handle, long *inRxQueue, long *inTxQueue, long *eventStatus) {
    *inRxQueue = 1;
    *inTxQueue = 2;
    *eventStatus = 3;
    return 0;
}
int FT_SetEventNotification(int handle, long mask, void *eventHandle) { return 0; }
int FT_SetChars(int handle, char eventChar, char eventCharEnabled, char errorChar, char errorCharEnabled) { return 0; }
int FT_SetBreakOn(int handle) { return 0; }
int FT_SetBreakOff(int handle) { return 0; }
int FT_Purge(int handle, long mask) { return 0; }
int FT_ResetDevice(int handle) { return 0; }
int FT_ResetPort(int handle) { return 0; }
int FT_CyclePort(int handle) { return 0; }
int FT_StopInTask(int handle) { return 0; }
int FT_RestartInTask(int handle) { return 0; }
int FT_SetWaitMask(int handle, long mask) { return 0; }
int FT_WaitOnMask(int handle, long *mask) { *mask=4; return 0; }
int FT_SetLatencyTimer(int handle, char latency) { return 0; }
int FT_GetLatencyTimer(int handle, char *latency) { *latency=7; return 0; }
int FT_SetBitMode(int handle, char mask, char enable) { return 0; }
int FT_GetBitMode(int handle, char *mode) { *mode=20; return 0; }
int FT_SetUSBParameters(int handle, long inSize, long outSize) { return 0; }

int FT_CreateDeviceInfoList(long *numDevs) {
    *numDevs = 4;
    return 0;
}

int FT_GetDeviceInfoDetail(long index, long *flags, long *type, long *id, long *locId, void *serialNumber, void *description, int *handle) {
    *id = 67330049; // vid=0x0403, pid=0x6001
    if ( index == 1 ) {
        memset(serialNumber, 'A', 6);
        memset(description, 'B', 10);
    } else if ( index == 2 ) {
        memset(serialNumber, 'C', 6);
        memset(description, 'D', 10);
    } else {
        memset(serialNumber, 'E', 6);
        memset(description, 'F', 10);
    }
    return 0;
}
