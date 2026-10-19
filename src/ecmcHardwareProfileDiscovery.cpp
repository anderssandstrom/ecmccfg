#include "ecmcHardwareProfiles.h"
#include "vendor/nlohmann/json.hpp"
#include <algorithm>
#include <fstream>
#include <map>
#include <mutex>
#include <sstream>
#include <stdexcept>
#include <tuple>

namespace ecmccfg {
namespace {
using Json = nlohmann::json;
using Key = std::tuple<int, int, int>;
struct Channel { std::string hardware; Json options; };
std::map<Key, Channel> channels;
std::mutex channel_mutex;
void address(int master, int slave, int channel = 1) {
    if (master < 0 || slave < 0 || channel < 1)
        throw std::runtime_error("Master/slave must be nonnegative and channel must be positive");
}
Json catalogue(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("Cannot open profile catalogue: " + path);
    Json result = Json::parse(input);
    if (result.at("version") != 1) throw std::runtime_error("Unsupported profile catalogue version");
    return result;
}
std::string describe(const std::string& kind, const std::string& name, const Json& profile) {
    std::ostringstream out;
    out << kind << " " << name << " channels=" << profile.at("channels").dump();
    if (profile.contains("compatibility")) out << " requires=" << profile["compatibility"].dump();
    if (profile.contains("digitalInputs")) out << " digitalInputs=" << profile["digitalInputs"].dump();
    if (profile.contains("homing")) out << " indexHoming=" << profile["homing"].dump() << " (requires TP=1 and configured index trigger)";
    return out.str();
}
std::string incompatible(const Json& profile, const Channel& configured, int channel) {
    if (!profile.contains("compatibility")) return " no compatibility metadata;";
    std::string reason;
    const auto& compat = profile.at("compatibility");
    const auto& hardware = compat.at("hardware");
    if (std::find(hardware.begin(), hardware.end(), configured.hardware) == hardware.end())
        reason += " hardware descriptor not supported;";
    const auto& supported = profile.at("channels");
    if (std::find(supported.begin(), supported.end(), channel) == supported.end()) reason += " channel not supported;";
    for (auto req = compat.at("requires").begin(); req != compat.at("requires").end(); ++req)
        if (!configured.options.contains(req.key()) || configured.options[req.key()] != req.value())
            reason += " requires " + req.key() + "=" + req.value().dump() + ";";
    return reason;
}

}
void registerHardwareProfileChannel(int master, int slave, int channel,
                                    const std::string& hardware, const std::string& options) {
    address(master, slave, channel);
    if (hardware.empty()) throw std::runtime_error("Hardware descriptor is required");
    Json parsed = Json::object();
    std::istringstream stream(options);
    std::string option;
    if (options.empty()) throw std::runtime_error("Channel options are required");
    while (std::getline(stream, option, ',')) {
        const auto equals = option.find('=');
        if (equals == std::string::npos) throw std::runtime_error("Expected KEY=VALUE channel option");
        const auto key = option.substr(0, equals);
        const auto value = option.substr(equals + 1);
        if (parsed.contains(key)) throw std::runtime_error("Duplicate channel option: " + key);
        if (key == "MODE") parsed[key] = value;
        else {
            if (value != "0" && value != "1") throw std::runtime_error(key + " must be 0 or 1");
            parsed[key] = value == "1" ? 1 : 0;
        }
    }
    for (auto it = parsed.begin(); it != parsed.end(); ++it) {
        if (it.key() == "MODE") {
            if (it.value() != "CSV" && it.value() != "CSP" && it.value() != "CST")
                throw std::runtime_error("MODE must be CSV, CSP or CST");
        } else if (it.key() == "TP" || it.key() == "INPUTS" || it.key() == "ENC2") {
            if (!it.value().is_number_integer() || (it.value() != 0 && it.value() != 1))
                throw std::runtime_error(it.key() + " must be 0 or 1");
        } else throw std::runtime_error("Unknown channel option: " + it.key());
    }
    std::lock_guard<std::mutex> lock(channel_mutex);
    channels[{master, slave, channel}] = {hardware, parsed};
}
void clearHardwareProfileSlave(int master, int slave) {
    address(master, slave);
    std::lock_guard<std::mutex> lock(channel_mutex);
    for (auto it = channels.begin(); it != channels.end();) {
        if (std::get<0>(it->first) == master && std::get<1>(it->first) == slave) it = channels.erase(it);
        else ++it;
    }
}
std::string listHardwareProfiles(const std::string& path) {
    const Json data = catalogue(path);
    std::ostringstream out;
    for (const char* kind : {"drive", "encoder"})
        for (auto it = data.at(kind).begin(); it != data.at(kind).end(); ++it)
            out << describe(kind, it.key(), it.value()) << '\n';
    return out.str();
}
std::string listCompatibleHardwareProfiles(int master, int slave, int channel, const std::string& path) {
    address(master, slave, channel);
    const Json data = catalogue(path);
    std::lock_guard<std::mutex> lock(channel_mutex);
    const auto found = channels.find({master, slave, channel});
    if (found == channels.end())
        return "UNVERIFIED: no registered _OPT metadata for ec" + std::to_string(master) + ".s" + std::to_string(slave) + " channel " + std::to_string(channel) + "\n";
    const auto& configured = found->second;
    std::ostringstream out;
    out << configured.hardware << " " << configured.options.dump() << " (startup metadata; no live hardware verification)\n";
    for (const char* kind : {"drive", "encoder"}) {
        for (auto it = data.at(kind).begin(); it != data.at(kind).end(); ++it) {
            const auto& profile = it.value();
            std::string reason;
            if (!profile.contains("compatibility")) {
                out << "UNVERIFIED " << it.key() << ": no compatibility metadata\n";
                continue;
            }
            reason = incompatible(profile, configured, channel);
            out << (reason.empty() ? "COMPATIBLE " : "UNAVAILABLE ") << kind << " " << it.key() << reason << '\n';
            if (reason.empty() && profile.contains("index"))
                out << "  Index homing: " << (configured.options.value("TP", 0) == 1 ? "capture mapped; index trigger/source still needs configuration" : "unavailable: requires TP=1") << "; numeric homing IDs do not add capture\n";
        }
    }
    out << "Compatibility assumes profile defaults, including limit inputs. YAML overrides are not evaluated.\n";
    return out.str();
}
}
