// gpib.cpp
// Mocks a GPIB library for testing purposes.
//
// Compiled using:
//   cl /LD gpib.cpp /link /OUT:gpib.dll
//   g++ gpib.cpp -fPIC -shared -Bstatic -Wall -o gpib.so
//   g++ gpib.cpp -fPIC -shared -Bstatic -Wall -o gpib.dylib
//
#include "gpib.h"
#include <cstring>

int ThreadIbsta( void ) { return 0; }
int ThreadIberr( void ) { return EARG; }
int ThreadIbcnt( void ) {
    return 10;  // pretend 10 bytes are sent or received.
}
int ibask( int ud, int option, int *value ) {
    if (option == 0x03) {
        *value = 11;  // timeout of 1 second
    }
    return 0;
}
int ibcac( int ud, int synchronous ) { return synchronous + 10; }
int ibclr( int ud ) { return TIMO; }
int ibcmd( int ud, const void *cmd, long cnt ) { return ERR; }
int ibconfig( int ud, int option, int value ) { return 22; }
int ibdev( int board_index, int pad, int sad, int timo, int send_eoi, int eosmode ) {
    if (board_index == 3) {
        return -1;
    }
    return 3;
}
int ibgts(int ud, int shadow_handshake) { return shadow_handshake + 1; }
int iblines( int ud, short *line_status ) { *line_status=24; return 0; }
int ibln( int ud, int pad, int sad, short *found_listener ) {
    if ((ud == 0 && pad == 5 && sad ==0 ) || (ud == 15 && pad == 11 && sad == 0) || (ud == 15 && pad == 11 && sad == 123)) {
        *found_listener = 1;
        return 0;
    };
    return ERR;
}
int ibloc( int ud ) { return 25; }
int ibonl( int ud, int onl ) { return 26; }
int ibpct( int ud ) { return 27; }
int ibrd( int ud, void *buf, long count ) {
    memset(buf, 'A', 10);
    return END;
}
int ibrsp( int ud, char *spr ) { memset(spr, 'p', 1); return 0; }
int ibsic( int ud ) { return 29; }
int ibspb( int ud, short *sp_bytes ) { *sp_bytes=30; return 0; }
int ibtrg( int ud ) { return 31; }
int ibwait( int ud, int mask ) { return 32; }
int ibwrt( int ud, const void *buf, long count ) { return 33; }
int ibwrta( int ud, const void *buf, long count ) { return 34; }

#if defined(_MSC_VER)
    int ibfindW(const wchar_t *dev) {
        if (wcscmp(dev, L"bad") == 0) return -1;
        return 2;
    }
#else
    int ibfind( const char *dev ) {
        if (strcmp(dev, "bad") == 0) return -1;
        return 2;
    }
    void ibvers( char **version) { *version = (char*)"1.2"; }
#endif
