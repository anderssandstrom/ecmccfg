# Build the CLI around the same native core used by the ecmccfg IOC command.
SOURCE_DIR := ../../src
CXX ?= c++
CXXFLAGS ?= -O2 -Wall -Wextra
TARGET ?= ecmc-hw-profiles

.PHONY: all clean
all: $(TARGET)

$(TARGET): main.cc $(SOURCE_DIR)/ecmcHardwareProfiles.cpp $(SOURCE_DIR)/ecmcHardwareProfiles.h $(SOURCE_DIR)/ecmcHardwareProfilesInternal.h $(SOURCE_DIR)/vendor/nlohmann/json.hpp $(SOURCE_DIR)/vendor/rapidyaml/rapidyaml.hpp
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -std=c++17 -I$(SOURCE_DIR) main.cc $(SOURCE_DIR)/ecmcHardwareProfiles.cpp $(LDFLAGS) $(LDLIBS) -o $@

clean:
	$(RM) $(TARGET)

# Optional integration test using a built EPICS Base. No Python required.
EPICS_OS_CLASS ?= $(shell uname -s)
EPICS_HOST_ARCH ?= $(shell $(EPICS_BASE)/startup/EpicsHostArch)
IOC_TEST ?= hw-profiles-iocsh-test
.PHONY: test-iocsh
test-iocsh:
	@test -n "$(EPICS_BASE)" || { echo "Set EPICS_BASE to a built EPICS Base"; exit 1; }
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -std=c++17 -I$(SOURCE_DIR) -I$(EPICS_BASE)/include -I$(EPICS_BASE)/include/os/$(EPICS_OS_CLASS) -I$(EPICS_BASE)/include/compiler/clang -I$(EPICS_BASE)/include/compiler/gcc ../../tests/hw_profiles_iocsh.cpp $(SOURCE_DIR)/ecmcHardwareProfileDiscovery.cpp $(SOURCE_DIR)/ecmcHardwareProfiles.cpp $(SOURCE_DIR)/ecmcHardwareProfilesIocsh.cpp -L$(EPICS_BASE)/lib/$(EPICS_HOST_ARCH) -Wl,-rpath,$(EPICS_BASE)/lib/$(EPICS_HOST_ARCH) $(LDFLAGS) $(LDLIBS) -lCom -o $(IOC_TEST)
	$(abspath $(IOC_TEST)) ../../scripts/jinja2/hardwareProfiles.json
