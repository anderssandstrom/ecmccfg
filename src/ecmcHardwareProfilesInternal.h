// ECMC hardware profile expansion. Keep semantics in sync with
// scripts/jinja2/ecmcHardwareProfiles.py. No dependency on ECB implementation.
#ifndef ECMCCFG_HW_PROFILES_H
#define ECMCCFG_HW_PROFILES_H
#include "vendor/nlohmann/json.hpp"
#include <algorithm>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace ecmccfg {
namespace profiles {
using json = nlohmann::json;
inline json merge(json defaults, const json& explicit_values) {
    for (const auto& item : explicit_values.items()) {
        if (item.value().is_object() && defaults.contains(item.key()) && defaults[item.key()].is_object())
            defaults[item.key()] = merge(defaults[item.key()], item.value());
        else
            defaults[item.key()] = item.value();
    }
    return defaults;
}
inline json expand(json value, const std::string& prefix, const std::string& channel) {
    if (value.is_structured()) {
        for (auto& item : value) item = expand(item, prefix, channel);
    } else if (value.is_string()) {
        std::string s = value;
        for (const auto& pair : {std::make_pair(std::string("{channel}"), channel),
                                 std::make_pair(std::string("{prefix}"), prefix)}) {
            size_t pos = 0;
            while ((pos = s.find(pair.first, pos)) != std::string::npos) {
                s.replace(pos, pair.first.size(), pair.second);
                pos += pair.second.size();
            }
        }
        value = s;
    }
    return value;
}
inline json take(json& object, const std::string& key, const json& fallback) {
    json value = object.value(key, fallback);
    object.erase(key);
    return value;
}
inline json positive(const json& value, const std::string& name) {
    if (!value.is_number() || !std::isfinite(value.get<double>()) || value.get<double>() <= 0)
        throw std::runtime_error(name + " must be a finite positive number (expand macros first)");
    return value;
}
inline std::string address(const json& value, const std::string& name) {
    if (value.is_string() && !value.get<std::string>().empty()) return value;
    if (value.is_number_integer() && value.get<long long>() >= 0) return value.dump();
    throw std::runtime_error(name + " must be a non-negative integer or macro string");
}
inline bool selected(const json& data, const std::string& role) {
    return data.contains(role) && data[role].is_object() && data[role].contains("profile");
}
inline json resolve_inputs(json inputs, const json& digital_inputs) {
    if (!inputs.is_object()) throw std::runtime_error("input must be a mapping");
    if (inputs.contains("limit") && !inputs["limit"].is_object())
        throw std::runtime_error("input.limit must be a mapping");
    for (const std::string path : {"/home", "/interlock", "/limit/forward", "/limit/backward"}) {
        const json::json_pointer ptr(path);
        if (!inputs.contains(ptr) || !inputs[ptr].is_object()) continue;
        auto& value = inputs[ptr];
        if (value.size() != 1 || !value.contains("driveInput") || !value["driveInput"].is_number_integer())
            throw std::runtime_error("Unsupported driveInput selector: " + value.dump());
        auto key = value["driveInput"].dump();
        if (!digital_inputs.contains(key))
            throw std::runtime_error("Unsupported driveInput selector: " + value.dump());
        value = digital_inputs[key];
    }
    return inputs;
}
inline json resolve(json data, const json& catalogue) {
    if (!selected(data, "drive") && !selected(data, "encoder")) return data;
    if (catalogue.value("version", 0) != 1)
        throw std::runtime_error("Unsupported hardware profile catalogue version");
    for (const std::string role : {"drive", "encoder"}) {
        if (!selected(data, role)) continue;
        json explicit_values = data[role];
        json name = take(explicit_values, "profile", nullptr);
        if (!name.is_string() || !catalogue.at(role).contains(name.get<std::string>()))
            throw std::runtime_error("Unknown " + role + " profile: " + name.dump());
        const auto& profile = catalogue.at(role).at(name.get<std::string>());
        auto slave = address(take(explicit_values, "slave", nullptr), role + ".slave");
        auto master = address(take(explicit_values, "master", 0), role + ".master");
        auto channel = take(explicit_values, "channel", 1);
        if (!channel.is_number_integer() ||
            std::find(profile["channels"].begin(), profile["channels"].end(), channel) == profile["channels"].end())
            throw std::runtime_error("Unsupported channel for " + name.get<std::string>());
        std::ostringstream ch;
        ch << std::setfill('0') << std::setw(2) << channel.get<int>();
        const auto prefix = "ec" + master + ".s" + slave;
        auto defaults = expand(profile["defaults"], prefix, ch.str());
        if (role == "drive") {
            if (!data.contains("axis")) data["axis"] = json::object();
            auto& axis = data["axis"];
            std::string mode = axis.value("mode", profile["mode"]).get<std::string>();
            std::transform(mode.begin(), mode.end(), mode.begin(), [](unsigned char c) {return std::toupper(c);});
            if (mode != profile["mode"])
                throw std::runtime_error(name.get<std::string>() + " requires axis.mode=" + profile["mode"].get<std::string>());
            if (!axis.contains("mode")) axis["mode"] = profile["mode"];
            auto input_defaults = profile.value("inputDefaults", json::object());
            auto digital_inputs = expand(profile.value("digitalInputs", json::object()), prefix, ch.str());
            if (!input_defaults.empty() || data.contains("input")) {
                if (data.contains("input") && !data["input"].is_object())
                    throw std::runtime_error("input must be a mapping");
                data["input"] = resolve_inputs(merge(input_defaults, data.value("input", json::object())), digital_inputs);
            }
            if (explicit_values.contains("maxVelocity"))
                defaults["numerator"] = positive(take(explicit_values, "maxVelocity", nullptr), "drive.maxVelocity");
        } else {
            if (explicit_values.contains("countsPerMotorRev")) {
                defaults["denominator"] = positive(take(explicit_values, "countsPerMotorRev", nullptr), "encoder.countsPerMotorRev");
                defaults["numerator"] = positive(take(explicit_values, "unitsPerMotorRev", 1), "encoder.unitsPerMotorRev");
            } else if (explicit_values.contains("unitsPerMotorRev"))
                throw std::runtime_error("encoder.unitsPerMotorRev requires countsPerMotorRev");
            if (explicit_values.contains("homing") && explicit_values["homing"].is_object() && explicit_values["homing"].contains("method")) {
                auto& homing = explicit_values["homing"];
                auto method = take(homing, "method", nullptr);
                if (!method.is_string() || !profile.contains("homing") || !profile["homing"].contains(method.get<std::string>()))
                    throw std::runtime_error("Unsupported homing method for " + name.get<std::string>());
                auto seq = profile["homing"][method.get<std::string>()];
                if (homing.contains("type") && homing["type"] != seq)
                    throw std::runtime_error("encoder.homing.type conflicts with method");
                defaults = merge(defaults, expand(profile["index"], prefix, ch.str()));
                defaults["homing"] = {{"type", seq}, {"latchCount", 1}};
            }
        }
        data[role] = merge(defaults, explicit_values);
        for (const std::string key : {"numerator", "denominator"})
            if (!data[role].contains(key))
                throw std::runtime_error(role + "." + key + " is required: provide explicit scaling or profile scaling inputs");
    }
    return data;
}
} // namespace profiles
} // namespace ecmccfg
#endif
