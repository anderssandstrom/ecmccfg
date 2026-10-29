#ifndef ECMCCFG_EC_TOOL_COMMAND_H
#define ECMCCFG_EC_TOOL_COMMAND_H

#include <cmath>
#include <climits>
#include <cstdio>
#include <string>
#include <vector>
#include <cerrno>
#include <spawn.h>
#include <sys/wait.h>

namespace ecTool {
typedef std::vector<std::string> Arguments;

inline bool integer(double value, int minimum, int maximum, int &result) {
    // Range comparisons also reject NaN and infinity before the integer cast.
    if (!(value >= minimum && value <= maximum) || std::floor(value) != value)
        return false;
    result = static_cast<int>(value);
    return true;
}

inline std::string decimal(int value) {
    char text[32];
    std::snprintf(text, sizeof(text), "%d", value);
    return text;
}

inline bool versionComponent(const std::string &value) {
    if (value.empty() || value == "." || value == "..") return false;
    return value.find_first_not_of(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._+-") ==
        std::string::npos;
}

inline bool build(const std::string &directory, const std::string &prefix,
                  double masterValue, double commandValue, double slaveValue,
                  double channelValue, double argumentValue, Arguments &args) {
    args.clear();
    int master, command, slave, channel, argument;
    if (!integer(masterValue, 0, INT_MAX, master) ||
        !integer(commandValue, 0, INT_MAX, command)) return false;
    // caput interprets a leading '-' as an option, even in a separate argv item.
    if (!prefix.empty() && prefix[0] == '-') return false;
    const char *script = NULL;
    switch (command) {
    case 5: script = "ecToolEthercatMaster.sh"; break;
    case 11: script = "ecToolEthercatSlaves.sh"; break;
    case 20: script = "ecToolReadHwDiag.sh"; break;
    case 70621: script = "ecToolEL7062_triggTune.sh"; break;
    case 70622: script = "ecToolEL7062_readBackParams.sh"; break;
    case 10: break;
    default: return false;
    }
    if (command != 5 && command != 11 &&
        !integer(slaveValue, 0, 65535, slave)) return false;
    if ((command == 70621 || command == 70622) &&
        !integer(channelValue, 1, 2, channel)) return false;
    if (command == 10) {
        if (!integer(argumentValue, 0, 8, argument)) return false;
        const char *state = NULL;
        switch (argument) {
        case 1: state = "INIT"; break;
        case 2: state = "PREOP"; break;
        case 3: state = "BOOT"; break;
        case 4: state = "SAFEOP"; break;
        case 8: state = "OP"; break;
        default: return false;
        }
        args.push_back("/opt/etherlab/bin/ethercat");
        args.push_back("states");
        args.push_back("-m" + decimal(master));
        args.push_back("-p" + decimal(slave));
        args.push_back(state);
    } else {
        args.push_back("/bin/bash");
        args.push_back("--noprofile");
        args.push_back("--norc");
        args.push_back("--");
        args.push_back(directory + "/" + script);
        args.push_back(decimal(master));
        if (command != 5 && command != 11) args.push_back(decimal(slave));
        if (command == 70621 || command == 70622) args.push_back(decimal(channel));
        args.push_back(prefix);
    }
    return true;
}

inline bool safeEnvironmentEntry(const std::string &entry) {
    // Bash startup hooks and exported functions must not run before the helper.
    return entry.compare(0, 9, "BASH_ENV=") != 0 &&
           entry.compare(0, 4, "ENV=") != 0 &&
           entry.compare(0, 10, "SHELLOPTS=") != 0 &&
           entry.compare(0, 9, "BASHOPTS=") != 0 &&
           entry.compare(0, 10, "BASH_FUNC_") != 0;
}

inline int execute(const Arguments &args, const Arguments &environment) {
    if (args.empty()) return EINVAL;
    std::vector<char *> argv, envp;
    for (size_t i = 0; i < args.size(); ++i)
        argv.push_back(const_cast<char *>(args[i].c_str()));
    for (size_t i = 0; i < environment.size(); ++i)
        envp.push_back(const_cast<char *>(environment[i].c_str()));
    argv.push_back(NULL);
    envp.push_back(NULL);
    pid_t child;
    int error = posix_spawn(&child, argv[0], NULL, NULL, &argv[0], &envp[0]);
    if (error) return error;
    int status;
    while (waitpid(child, &status, 0) < 0) {
        if (errno != EINTR) return errno;
    }
    return WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status);
}
}
#endif
