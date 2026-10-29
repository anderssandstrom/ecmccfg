//
// ECMCCFG ethercatTool
//
// provides host-related commands that can be configured and executed via a
// EPICS record:
//
// ${P}${ECMC_EC_MP}${MASTER_ID}-EcTool
//
// | field | description      | datatype |
// |-------|------------------|----------|
// | A     | master id        | double   |
// | B     | command          | double   |
// | C     | reserved         |          |
// | D     | slave id         | double   |
// | E     | channel id       | double   |
// | F     | sdo index        | double   |
// | G     | sdo subindex     | double   |
// | H     | data type        | string   |
// | I     | command argument | double   |
// | R     | prefix           | string   |
// | S     | epics version    | string   |
// | T     | ecmccfg version  | string   |
// | U     | trigger          | double   |
// | VALA  | return status    | double   |
//

#include "ecToolCommand.h"
#include <cstring>
#include <cfloat>
#include <new>
#include <aSubRecord.h>
#include <dbAccess.h>
#include <dbAddr.h>
#include <dbDefs.h>
#include <epicsEvent.h>
#include <epicsExport.h>
#include <epicsMutex.h>
#include <epicsThread.h>
#include <registryFunction.h>

extern char **environ;

namespace {
struct EcToolContext {
    epicsEventId event;
    epicsMutexId lock;
    std::string directory, prefix, name;
    ecTool::Arguments environment, job;
    bool busy;
    EcToolContext() : event(NULL), lock(NULL), busy(false) {}
};

// Read only local startup configuration, before the IOC starts serving CA.
// dbGetField avoids depending on the initialization order of DB links.
bool startupString(DBLINK &link, const void *constant, std::string &value) {
    char text[MAX_STRING_SIZE] = {0};
    if (link.type == CONSTANT) {
        if (!constant) return false;
        std::memcpy(text, constant, sizeof(text));
    } else if (link.type == PV_LINK || link.type == DB_LINK || link.type == CA_LINK) {
        DBADDR address;
        long count = 1;
        if (!link.value.pv_link.pvname ||
            dbNameToAddr(link.value.pv_link.pvname, &address) ||
            dbGetField(&address, DBR_STRING, text, NULL, &count, NULL) || count != 1)
            return false;
    } else return false;
    text[sizeof(text) - 1] = '\0';
    value = text;
    return true;
}

void workerEtherCATTool(void *arg) {
    EcToolContext *context = static_cast<EcToolContext *>(arg);
    while (true) {
        epicsEventWait(context->event);
        epicsMutexLock(context->lock);
        ecTool::Arguments job = context->job;
        epicsMutexUnlock(context->lock);
        // Do not hold the lock while waiting: processing a busy record must
        // return promptly, not block the IOC database lock behind a subprocess.
        int result = ecTool::execute(job, context->environment);
        if (result)
            std::fprintf(stderr, "%s: EcTool helper failed (%d)\n",
                         context->name.c_str(), result);
        epicsMutexLock(context->lock);
        context->job.clear();
        context->busy = false;
        epicsMutexUnlock(context->lock);
    }
}
}

static void initEtherCATTool(struct aSubRecord *rec) {
    rec->dpvt = NULL;
    EcToolContext *context = new (std::nothrow) EcToolContext;
    if (!context) return;
    std::string epics, version;
    if (rec->ftr != DBF_STRING || rec->fts != DBF_STRING || rec->ftt != DBF_STRING ||
        !startupString(rec->inpr, rec->r, context->prefix) ||
        !startupString(rec->inps, rec->s, epics) ||
        !startupString(rec->inpt, rec->t, version) ||
        !ecTool::versionComponent(epics) || !ecTool::versionComponent(version) ||
        (!context->prefix.empty() && context->prefix[0] == '-')) {
        std::fprintf(stderr, "%s: EcTool requires valid local startup prefix/version records\n", rec->name);
        delete context;
        return;
    }
    // Preserve the deployed helper layout. Later metadata/link writes cannot
    // change either the directory or the publication prefix.
    context->directory = "/ioc/modules/ecmccfg/" + version + "/R" + epics;
    context->name = rec->name;
    for (char **entry = environ; entry && *entry; ++entry)
        if (ecTool::safeEnvironmentEntry(*entry)) context->environment.push_back(*entry);
    context->lock = epicsMutexCreate();
    context->event = epicsEventCreate(epicsEventEmpty);
    if (!context->lock || !context->event ||
        !epicsThreadCreate("EtherCAT worker", epicsThreadPriorityLow,
                           epicsThreadGetStackSize(epicsThreadStackMedium),
                           workerEtherCATTool, context)) {
        if (context->event) epicsEventDestroy(context->event);
        if (context->lock) epicsMutexDestroy(context->lock);
        delete context;
        std::fprintf(stderr, "%s: EcTool worker initialization failed\n", rec->name);
        return;
    }
    rec->dpvt = context;
}
epicsRegisterFunction(initEtherCATTool);

static long runEtherCATTool(struct aSubRecord *rec) {
    EcToolContext *context = static_cast<EcToolContext *>(rec->dpvt);
    if (!context || rec->ftu != DBF_DOUBLE || !rec->u) return -1;
    const double trigger = *static_cast<double *>(rec->u);
    if (trigger == 0) return 0;
    if (!(trigger >= -DBL_MAX && trigger <= DBL_MAX)) return -1;
    if (rec->fta != DBF_DOUBLE || rec->ftb != DBF_DOUBLE ||
        rec->ftd != DBF_DOUBLE || rec->fte != DBF_DOUBLE || rec->fti != DBF_DOUBLE ||
        !rec->a || !rec->b || !rec->d || !rec->e || !rec->i) return -1;
    ecTool::Arguments job;
    if (!ecTool::build(context->directory, context->prefix,
                       *static_cast<double *>(rec->a), *static_cast<double *>(rec->b),
                       *static_cast<double *>(rec->d), *static_cast<double *>(rec->e),
                       *static_cast<double *>(rec->i), job)) {
        std::fprintf(stderr, "%s: invalid EcTool command or argument\n", rec->name);
        return -1;
    }
    epicsMutexLock(context->lock);
    if (context->busy) {
        epicsMutexUnlock(context->lock);
        return -1;
    }
    context->job.swap(job);
    context->busy = true;
    epicsEventSignal(context->event);
    epicsMutexUnlock(context->lock);
    return 0;
}
epicsRegisterFunction(runEtherCATTool);
