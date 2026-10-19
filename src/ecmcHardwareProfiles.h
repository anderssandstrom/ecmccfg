#ifndef ECMCCFG_HARDWARE_PROFILES_H
#define ECMCCFG_HARDWARE_PROFILES_H
#include <string>

namespace ecmccfg {
// Expand to explicit YAML-compatible JSON; preserve macros and unrelated data.
// Creates output parent directories. Throws on failure before output is opened
// for parse/profile errors. Does not perform schema validation or hardware I/O.
void expandHardwareProfiles(const std::string& input_file,
                            const std::string& output_file,
                            const std::string& catalogue_file);
// Startup metadata only; no live EtherCAT probing. Options are comma-separated KEY=VALUE pairs.
void registerHardwareProfileChannel(int master, int slave, int channel,
                                    const std::string& hardware, const std::string& options);
void clearHardwareProfileSlave(int master, int slave);
std::string listHardwareProfiles(const std::string& catalogue_file);
std::string listCompatibleHardwareProfiles(int master, int slave, int channel,
                                           const std::string& catalogue_file);
}
#endif
