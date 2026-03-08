// gpib.h
// Mocks a GPIB library for testing purposes.
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

int EARG = 4;
int END = 0x2000;
int TIMO = 0x4000;
int ERR = 0x8000;

extern "C" {
    EXPORT volatile long ibcntl;

    EXPORT int ThreadIbsta( void );
    EXPORT int ThreadIberr( void );
    EXPORT int ThreadIbcnt( void );
    EXPORT int ibask( int ud, int option, int *value );
    EXPORT int ibcac( int ud, int synchronous );
    EXPORT int ibclr( int ud );
    EXPORT int ibcmd( int ud, const void *cmd, long cnt );
    EXPORT int ibconfig( int ud, int option, int value );
    EXPORT int ibdev( int board_index, int pad, int sad, int timo, int send_eoi, int eosmode );
    EXPORT int ibgts(int ud, int shadow_handshake);
    EXPORT int iblines( int ud, short *line_status );
    EXPORT int ibln( int ud, int pad, int sad, short *found_listener );
    EXPORT int ibloc( int ud );
    EXPORT int ibonl( int ud, int onl );
    EXPORT int ibpct( int ud );
    EXPORT int ibrd( int ud, void *buf, long count );
    EXPORT int ibrsp( int ud, char *spr );
    EXPORT int ibsic( int ud );
    EXPORT int ibspb( int ud, short *sp_bytes );
    EXPORT int ibtrg( int ud );
    EXPORT int ibwait( int ud, int mask );
    EXPORT int ibwrt( int ud, const void *buf, long count );
    EXPORT int ibwrta( int ud, const void *buf, long count );

    #if defined(_MSC_VER)
      EXPORT int ibfindW(const wchar_t *dev);
    #else
      EXPORT int ibfind( const char *dev );
      EXPORT void ibvers( char **version);
    #endif
}