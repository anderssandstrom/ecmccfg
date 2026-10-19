// Shared native profile compiler for IOC shell and standalone use.
#define RYML_SINGLE_HDR_DEFINE_NOW
#include "vendor/rapidyaml/rapidyaml.hpp"
#include "ecmcHardwareProfilesInternal.h"
#include "ecmcHardwareProfiles.h"

namespace {
[[noreturn]] void yaml_error(const char* msg, size_t length, ryml::Location location, void*) {
    throw std::runtime_error("YAML error at line " + std::to_string(location.line + 1) +
                             ": " + std::string(msg, length));
}

// rapidyaml's JSON emitter recognizes lowercase JSON literals. Canonicalize
// YAML 1.2 case variants without changing explicitly quoted string values.
void normalize_literals(ryml::NodeRef node) {
    if (node.has_val() && !node.is_val_quoted()) {
        const auto scalar = node.val();
        std::string value(scalar.str, scalar.len);
        std::transform(value.begin(), value.end(), value.begin(),
                       [](unsigned char c) { return std::tolower(c); });
        if (value == "true") node.set_val(ryml::to_csubstr("true"));
        else if (value == "false") node.set_val(ryml::to_csubstr("false"));
        else if (value == "null") node.set_val(ryml::to_csubstr("null"));
    }
    for (auto child : node.children()) normalize_literals(child);
}

} // namespace

void ecmccfg::expandHardwareProfiles(const std::string& input_file,
                                    const std::string& output_file,
                                    const std::string& catalogue_file) {
    if (input_file.empty() || output_file.empty())
        throw std::runtime_error("Input and output filenames are required");
    const auto input_path = std::filesystem::absolute(input_file).lexically_normal();
    const auto output_path = std::filesystem::absolute(output_file).lexically_normal();
    if (input_path == output_path || (std::filesystem::exists(output_path) &&
            std::filesystem::equivalent(input_path, output_path)))
        throw std::runtime_error("Input and output must be different files");
    std::ifstream input(input_path);
    if (!input) throw std::runtime_error("Cannot read input: " + input_path.string());
    std::string yaml((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    const std::string original_yaml = yaml;
    ryml::Tree tree(ryml::Callbacks(nullptr, nullptr, nullptr, yaml_error));
    ryml::parse_in_place(ryml::to_substr(yaml), &tree);
    // Resolve YAML anchors before conversion; no template/macro evaluation.
    tree.resolve();
    normalize_literals(tree.rootref());
    std::ostringstream serialized;
    serialized << ryml::as_json(tree);
    auto data = nlohmann::json::parse(serialized.str());
    if (!data.is_object()) throw std::runtime_error("Configuration must be a mapping");
    std::string output = original_yaml;
    if (ecmccfg::profiles::selected(data, "drive") || ecmccfg::profiles::selected(data, "encoder")) {
        std::ifstream catalogue(catalogue_file);
        if (!catalogue) throw std::runtime_error("Cannot read profile catalogue: " + std::string(catalogue_file));
        const auto definitions = nlohmann::json::parse(catalogue);
        data = ecmccfg::profiles::resolve(data, definitions);
        output = data.dump(2) + "\n";
    }
    // Finish parsing/resolution before opening output, so validation errors
    // cannot truncate an existing generated configuration.
    std::filesystem::create_directories(output_path.parent_path());
    std::ofstream file(output_path);
    if (!file) throw std::runtime_error("Cannot write output: " + output_path.string());
    file << output;
    file.close();
    if (!file) throw std::runtime_error("Failed to write output: " + output_path.string());
}
