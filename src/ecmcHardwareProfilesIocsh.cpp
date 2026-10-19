#include "ecmcHardwareProfiles.h"
#include <cstdio>
#include <cstdlib>
#include <exception>
#include <string>
#include <stdexcept>
#include <iocsh.h>
#include <epicsExport.h>

namespace {
const iocshArg input_arg = {"Input YAML file", iocshArgString};
const iocshArg output_arg = {"Output YAML file", iocshArgString};
const iocshArg catalogue_arg = {"Profile catalogue (default: ECMC_CONFIG_ROOT/hardwareProfiles.json)", iocshArgString};
const iocshArg* const arguments[] = {&input_arg, &output_arg, &catalogue_arg};
const iocshFuncDef command = {"ecmcExpandHwProfiles", 3, arguments
#ifdef IOCSHFUNCDEF_HAS_USAGE
    , "Expand hardware profiles into explicit YAML; default catalogue comes from ECMC_CONFIG_ROOT."
#endif
};

std::string catalogue_path(const char* explicit_path) {
    if (explicit_path && *explicit_path) return explicit_path;
    const char* root = std::getenv("ECMC_CONFIG_ROOT");
    if (!root || !*root) throw std::runtime_error("Pass a catalogue filename or set ECMC_CONFIG_ROOT");
    return std::string(root) + (std::string(root).back() == '/' ? "" : "/") + "hardwareProfiles.json";
}
template<typename F> void invoke(const char* name, F action) {
    try { action(); iocshSetError(0); }
    catch (const std::exception& error) {
        std::fprintf(stderr, "%s: %s\n", name, error.what()); iocshSetError(1);
    }
    catch (...) { std::fprintf(stderr, "%s: unknown error\n", name); iocshSetError(1); }
}
const iocshArg master_arg = {"Master", iocshArgInt};
const iocshArg slave_arg = {"Slave", iocshArgInt};
const iocshArg channel_arg = {"Channel (1-based)", iocshArgInt};
const iocshArg hardware_arg = {"Hardware descriptor", iocshArgString};
const iocshArg options_arg = {"Resolved options (MODE=CSV,TP=1,INPUTS=1,ENC2=1)", iocshArgString};
const iocshArg* const list_args[] = {&catalogue_arg};
const iocshArg* const compatible_args[] = {&master_arg, &slave_arg, &channel_arg, &catalogue_arg};
const iocshArg* const register_args[] = {&master_arg, &slave_arg, &channel_arg, &hardware_arg, &options_arg};
const iocshArg* const clear_args[] = {&master_arg, &slave_arg};
#ifdef IOCSHFUNCDEF_HAS_USAGE
#define PROFILE_USAGE(text) , text
#else
#define PROFILE_USAGE(text)
#endif
const iocshFuncDef list_command = {"ecmcListHwProfiles", 1, list_args PROFILE_USAGE("List installed hardware profiles and requirements.")};
const iocshFuncDef compatible_command = {"ecmcListCompatibleProfiles", 4, compatible_args PROFILE_USAGE("Compare profiles with registered _OPT startup metadata; not live hardware validation.")};
const iocshFuncDef register_command = {"ecmcRegisterHwProfileChannel", 5, register_args PROFILE_USAGE("Internal _OPT startup metadata registration.")};
const iocshFuncDef clear_command = {"ecmcClearHwProfileSlave", 2, clear_args PROFILE_USAGE("Discard startup metadata for a slave before reconfiguration.")};
#undef PROFILE_USAGE
void list_call(const iocshArgBuf* a) {
    invoke(list_command.name, [&] { std::printf("%s", ecmccfg::listHardwareProfiles(catalogue_path(a[0].sval)).c_str()); });
}
void compatible_call(const iocshArgBuf* a) {
    invoke(compatible_command.name, [&] { std::printf("%s", ecmccfg::listCompatibleHardwareProfiles(a[0].ival, a[1].ival, a[2].ival, catalogue_path(a[3].sval)).c_str()); });
}
void register_call(const iocshArgBuf* a) {
    invoke(register_command.name, [&] { ecmccfg::registerHardwareProfileChannel(a[0].ival, a[1].ival, a[2].ival, a[3].sval ? a[3].sval : "", a[4].sval ? a[4].sval : ""); });
}
void clear_call(const iocshArgBuf* a) {
    invoke(clear_command.name, [&] { ecmccfg::clearHardwareProfileSlave(a[0].ival, a[1].ival); });
}

void expand_call(const iocshArgBuf* args) {
    try {
        std::string catalogue = args[2].sval ? args[2].sval : "";
        if (catalogue.empty()) {
            const char* root = std::getenv("ECMC_CONFIG_ROOT");
            if (!root || !*root)
                throw std::runtime_error("Pass a catalogue filename or set ECMC_CONFIG_ROOT");
            catalogue = root;
            if (catalogue.back() != '/') catalogue += '/';
            catalogue += "hardwareProfiles.json";
        }
        ecmccfg::expandHardwareProfiles(args[0].sval ? args[0].sval : "",
                                       args[1].sval ? args[1].sval : "", catalogue);
        iocshSetError(0);
    } catch (const std::exception& error) {
        std::fprintf(stderr, "ecmcExpandHwProfiles: %s\n", error.what());
        iocshSetError(1);
    } catch (...) {
        std::fprintf(stderr, "ecmcExpandHwProfiles: unknown error\n");
        iocshSetError(1);
    }
}
} // namespace

static void ecmcHardwareProfilesRegister() {
    iocshRegister(&command, expand_call);
    iocshRegister(&list_command, list_call);
    iocshRegister(&compatible_command, compatible_call);
    iocshRegister(&register_command, register_call);
    iocshRegister(&clear_command, clear_call);
}
extern "C" {
epicsExportRegistrar(ecmcHardwareProfilesRegister);
}
