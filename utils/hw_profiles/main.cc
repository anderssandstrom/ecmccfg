#include "ecmcHardwareProfiles.h"
#include <exception>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        std::cout << "Usage: ecmc-hw-profiles --profiles CATALOGUE.json INPUT.yaml OUTPUT.yaml\n";
        return 0;
    }
    if (argc != 5 || std::string(argv[1]) != "--profiles") {
        std::cerr << "Usage: ecmc-hw-profiles --profiles CATALOGUE.json INPUT.yaml OUTPUT.yaml\n";
        return 2;
    }
    try {
        ecmccfg::expandHardwareProfiles(argv[3], argv[4], argv[2]);
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ecmc-hw-profiles: " << error.what() << '\n';
        return 1;
    }
}
