# Generate configurations for an unchanged ECB; no Python is used.
REPO_ROOT := $(abspath ../../..)
TOOL_DIR := $(REPO_ROOT)/utils/hw_profiles
PROFILE_TOOL ?= $(TOOL_DIR)/ecmc-hw-profiles
CATALOGUE := $(REPO_ROOT)/scripts/jinja2/hardwareProfiles.json
SOURCES := $(wildcard */cfg/*.yaml)
OUTPUTS := $(subst /cfg/,/generated/,$(SOURCES))

.PHONY: all
all: $(OUTPUTS)

$(PROFILE_TOOL): $(TOOL_DIR)/main.cc $(REPO_ROOT)/src/ecmcHardwareProfiles.cpp $(REPO_ROOT)/src/ecmcHardwareProfiles.h $(REPO_ROOT)/src/ecmcHardwareProfilesInternal.h $(REPO_ROOT)/src/vendor/nlohmann/json.hpp $(REPO_ROOT)/src/vendor/rapidyaml/rapidyaml.hpp $(TOOL_DIR)/Makefile
	$(MAKE) -C $(TOOL_DIR) TARGET=$(PROFILE_TOOL)

define generate
$(subst /cfg/,/generated/,$(1)): $(1) $(CATALOGUE) $(PROFILE_TOOL)
	mkdir -p $$(dir $$@)
	$(PROFILE_TOOL) --profiles $(CATALOGUE) $$< $$@
endef
$(foreach source,$(SOURCES),$(eval $(call generate,$(source))))
