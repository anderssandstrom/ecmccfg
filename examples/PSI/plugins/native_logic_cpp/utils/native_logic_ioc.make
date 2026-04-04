PROGRAM ?= main
CXX ?= c++
PYTHON ?= python3
NATIVE_LOGIC_CPP_ROOT ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
ECMC ?= $(abspath $(NATIVE_LOGIC_CPP_ROOT)/../../../../../ecmc)
SUBSGEN ?= $(NATIVE_LOGIC_CPP_ROOT)/utils/ecmcNativeLogicSubstGen.py
EPICS_VERSION ?= 7.0.10
OS_CLASS ?= deb12
CPU_ARCH ?= x86_64
BUILD_DIR ?= O.$(EPICS_VERSION)_$(OS_CLASS)-$(CPU_ARCH)
PROGRAM_SO := $(BUILD_DIR)/$(PROGRAM).so
PROGRAM_SUBS := $(BUILD_DIR)/$(PROGRAM).so.substitutions
STAGE_DIR := ../bin

CPPFLAGS += -I$(ECMC)/devEcmcSup/logic
CXXFLAGS ?= -O2 -g -Wall -Wextra -std=c++17 -fPIC
LDFLAGS += -shared

.PHONY: all stage clean

all: $(PROGRAM_SO) $(PROGRAM_SUBS)

$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/$(PROGRAM).o: $(PROGRAM).cpp | $(BUILD_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c $< -o $@

$(PROGRAM_SO): $(BUILD_DIR)/$(PROGRAM).o
	$(CXX) $(LDFLAGS) -o $@ $^

$(PROGRAM_SUBS): $(PROGRAM_SO)
	$(PYTHON) $(SUBSGEN) --logic-lib $(PROGRAM_SO) --output $@

stage: all
	mkdir -p $(STAGE_DIR)
	cp $(PROGRAM_SO) $(STAGE_DIR)/main.so
	cp $(PROGRAM_SUBS) $(STAGE_DIR)/main.so.substitutions

clean:
	$(RM) -r $(BUILD_DIR)
	$(RM) -r $(STAGE_DIR)
