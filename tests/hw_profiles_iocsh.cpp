// Integration test against real EPICS libCom/iocsh, without an EtherCAT IOC.
#include "vendor/nlohmann/json.hpp"
#include "ecmcHardwareProfiles.h"
#include <iocsh.h>
#include <cassert>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>

extern "C" void (*pvar_func_ecmcHardwareProfilesRegister)();

namespace {
std::string quote(const std::string& value) {
    std::string result = "\"";
    for (char c : value) {
        if (c == '\\' || c == '"') result += '\\';
        result += c;
    }
    return result + '"';
}
std::string command(const std::filesystem::path& input, const std::filesystem::path& output,
                    const std::string& catalogue = "") {
    return "ecmcExpandHwProfiles(" + quote(input.string()) + "," + quote(output.string()) +
           (catalogue.empty() ? "" : "," + quote(catalogue)) + ")";
}
void write(const std::filesystem::path& path, const std::string& text) {
    std::ofstream output(path);
    output << text;
    output.close();
    assert(output);
}
void mark_call(const iocshArgBuf* args) {
    write(args[0].sval, "reached");
    iocshSetError(0);
}
void register_marker() {
    static const iocshArg argument = {"Marker file", iocshArgString};
    static const iocshArg* const arguments[] = {&argument};
    static const iocshFuncDef marker = {"testMarkFile", 1, arguments
#ifdef IOCSHFUNCDEF_HAS_USAGE
        , "Test marker"
#endif
    };
    iocshRegister(&marker, mark_call);
}

nlohmann::json read(const std::filesystem::path& path) {
    std::ifstream input(path);
    return nlohmann::json::parse(input);
}
}

int main(int argc, char** argv) {
    if (argc == 3 && std::string(argv[1]) == "--halt") {
        pvar_func_ecmcHardwareProfilesRegister();
        register_marker();
        return iocshLoad(argv[2], nullptr);
    }
    assert(argc == 2);
    const std::string catalogue = std::filesystem::absolute(argv[1]).string();
    char dir[] = "/tmp/ecmccfg-iocsh-XXXXXX";
    assert(mkdtemp(dir));
    const std::filesystem::path work(dir);
    const auto input = work / "source.yaml";
    const auto output = work / "generated/axis.yaml";
    write(input,
          "drive: {profile: beckhoff/EL7041/CSV, slave: '${DRV_SID}', maxVelocity: 10}\n"
          "input: {home: {driveInput: 1}}\n"
          "encoder: {profile: beckhoff/EL7062/incremental, slave: 3, countsPerMotorRev: 4000, homing: {type: 1}}\n");
    pvar_func_ecmcHardwareProfilesRegister();
    assert(iocshCmd(command(input, output, catalogue).c_str()) == 0);
    const auto expected = read(output);
    assert(expected["drive"]["reduceTorqueEnable"] == true);
    assert(expected["input"]["home"] == "ec0.s${DRV_SID}.driveStatus01.11");
    assert(expected["encoder"]["homing"]["type"] == 1);
    assert(!expected["encoder"].contains("latch"));

    // Discovery uses actual IOC commands and per-master/slave/channel metadata.
    assert(iocshCmd(("ecmcListHwProfiles(" + quote(catalogue) + ")").c_str()) == 0);
    assert(ecmccfg::listHardwareProfiles(catalogue).find("beckhoff/EL7041/CSV") != std::string::npos);
    auto report = [&] (int master, int slave, int channel) {
        return ecmccfg::listCompatibleHardwareProfiles(master, slave, channel, catalogue);
    };
    assert(report(0, 3, 1).find("UNVERIFIED") != std::string::npos);
    const auto reg = "ecmcRegisterHwProfileChannel(0,3,1,EL7062_OPT," +
        quote("MODE=CSV,TP=0,INPUTS=1,ENC2=1") + ")";
    assert(iocshCmd(reg.c_str()) == 0);
    assert(report(0, 3, 1).find("COMPATIBLE drive beckhoff/EL7062/CSV") != std::string::npos);
    assert(report(0, 3, 1).find("COMPATIBLE encoder") != std::string::npos);
    assert(report(0, 3, 1).find("unavailable: requires TP=1") != std::string::npos);
    assert(report(1, 3, 1).find("UNVERIFIED") != std::string::npos);
    assert(report(0, 3, 2).find("UNVERIFIED") != std::string::npos);
    ecmccfg::registerHardwareProfileChannel(0, 3, 2, "EL7062_OPT", "MODE=CSP,TP=1,INPUTS=0,ENC2=0");
    assert(report(0, 3, 2).find("requires MODE=\"CSV\"") != std::string::npos);
    assert(report(0, 3, 2).find("requires INPUTS=1") != std::string::npos);
    assert(report(0, 3, 2).find("requires ENC2=1") != std::string::npos);
    assert(iocshCmd(("ecmcListCompatibleProfiles(0,3,2," + quote(catalogue) + ")").c_str()) == 0);
    assert(iocshCmd("ecmcRegisterHwProfileChannel(0,3,1,EL7062_OPT,invalid)") != 0);
    assert(report(0, 3, 1).find("COMPATIBLE drive") != std::string::npos);
    // Registry state must never implicitly select a profile or change legacy YAML.
    const auto manual_input = work / "manual.yaml";
    const auto manual_output = work / "manual-expanded.yaml";
    const std::string manual = "drive: {slave: 3, maxVelocity: 100}\n";
    write(manual_input, manual);
    assert(iocshCmd(command(manual_input, manual_output, catalogue).c_str()) == 0);
    std::ifstream manual_file(manual_output);
    assert(std::string((std::istreambuf_iterator<char>(manual_file)), {}) == manual);
    write(manual_input, "drive: {profile: auto, slave: 3, maxVelocity: 100}\n");
    assert(iocshCmd(command(manual_input, manual_output, catalogue).c_str()) != 0);
    assert(iocshCmd("ecmcClearHwProfileSlave(0,3)") == 0);
    assert(report(0, 3, 1).find("UNVERIFIED") != std::string::npos);
    assert(report(0, 3, 2).find("UNVERIFIED") != std::string::npos);

    // Omitted catalogue resolves against ECMC_CONFIG_ROOT (with/without slash).
    const auto root = std::filesystem::path(catalogue).parent_path().string();
    assert(setenv("ECMC_CONFIG_ROOT", root.c_str(), 1) == 0);
    assert(iocshCmd(command(input, output).c_str()) == 0);
    assert(read(output) == expected);
    assert(setenv("ECMC_CONFIG_ROOT", (root + "/").c_str(), 1) == 0);
    assert(iocshCmd(command(input, output).c_str()) == 0);
    unsetenv("ECMC_CONFIG_ROOT");
    assert(iocshCmd(command(input, output).c_str()) != 0);
    assert(iocshCmd("ecmcExpandHwProfiles()") != 0);

    // Bad YAML must report an error, not abort the process or truncate output.
    write(input, "encoder: [unterminated\n");
    assert(iocshCmd(command(input, output, catalogue).c_str()) != 0);
    assert(read(output) == expected);

    // Verify the real shell stops on failure, so a stale generated file is not loaded.
    const auto script = work / "halt.cmd";
    const auto ready = work / "ready";
    const auto should_not_run = work / "should-not-run";
    write(script, "on error halt\ntestMarkFile " + quote(ready.string()) + "\n" +
                 command(input, output, catalogue) + "\ntestMarkFile " +
                 quote(should_not_run.string()) + "\n");
    // EPICS 'halt' suspends the shell thread, so isolate it in a child process.
    const auto child = fork();
    assert(child >= 0);
    if (child == 0) {
        execl(argv[0], argv[0], "--halt", script.c_str(), nullptr);
        _exit(127);
    }
    for (unsigned i = 0; i < 100 && !std::filesystem::exists(ready); ++i) usleep(10000);
    usleep(100000);
    const bool reached = std::filesystem::exists(ready);
    const bool continued = std::filesystem::exists(should_not_run);
    int status;
    if (waitpid(child, &status, WNOHANG) == 0) {
        kill(child, SIGTERM);
        assert(waitpid(child, &status, 0) == child);
    }
    assert(reached);
    assert(!continued);

    write(input, "drive: {profile: unknown, slave: 1}\n");
    assert(iocshCmd(command(input, output, catalogue).c_str()) != 0);
    assert(read(output) == expected);
    assert(iocshCmd(command(input, input, catalogue).c_str()) != 0);
    std::filesystem::remove_all(work);
    std::cout << "IOC-shell profile integration passed\n";
}
