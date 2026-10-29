// Minimal EPICS boundary for exercising the production aSub callbacks without
// starting an IOC. This is not a replacement for a target EPICS module build.
#ifndef EC_TOOL_TEST_EPICS_STUBS_H
#define EC_TOOL_TEST_EPICS_STUBS_H
#include <map>
#include <string>
#include <cstring>
#define MAX_STRING_SIZE 40
#define DBF_STRING 0
#define DBF_DOUBLE 9
#define DBR_STRING 0
#define CONSTANT 0
#define PV_LINK 1
#define DB_LINK 2
#define CA_LINK 3
struct DBLINK {
    int type;
    struct { struct { const char *pvname; } pv_link; } value;
};
struct DBADDR { const char *name; };
struct aSubRecord {
    char name[64];
    void *dpvt, *a, *b, *d, *e, *i, *r, *s, *t, *u;
    int fta, ftb, ftd, fte, fti, ftr, fts, ftt, ftu;
    DBLINK inpr, inps, inpt;
};
static std::map<std::string, std::string> testDatabase;
static int testSignals;
inline long dbNameToAddr(const char *name, DBADDR *address) {
    address->name = name;
    return testDatabase.count(name) ? 0 : -1;
}
inline long dbGetField(DBADDR *address, short, void *out, long *, long *, void *) {
    std::strncpy(static_cast<char *>(out), testDatabase[address->name].c_str(), MAX_STRING_SIZE);
    return 0;
}
typedef int *epicsEventId;
typedef int *epicsMutexId;
enum { epicsEventEmpty, epicsThreadPriorityLow, epicsThreadStackMedium };
inline epicsEventId epicsEventCreate(int) { return new int(0); }
inline void epicsEventDestroy(epicsEventId p) { delete p; }
inline void epicsEventWait(epicsEventId) {}
inline void epicsEventSignal(epicsEventId) { ++testSignals; }
inline epicsMutexId epicsMutexCreate() { return new int(0); }
inline void epicsMutexDestroy(epicsMutexId p) { delete p; }
inline void epicsMutexLock(epicsMutexId) {}
inline void epicsMutexUnlock(epicsMutexId) {}
inline int epicsThreadGetStackSize(int) { return 0; }
inline void *epicsThreadCreate(const char *, int, int, void (*)(void *), void *) {
    return reinterpret_cast<void *>(1);
}
#define epicsRegisterFunction(name)
#endif
