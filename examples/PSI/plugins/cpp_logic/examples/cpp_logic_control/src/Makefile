include /ioc/tools/driver.makefile
BUILDCLASSES = Linux
ARCH_FILTER = deb10% deb12%
EXCLUDE_VERSIONS+=3 7.0.5 7.0.6 7.0.7
USR_CXXFLAGS += -std=c++17
ecmc_VERSION = strucpp
DIRS+=.
SOURCES += $(foreach d,${DIRS}, $(wildcard $d/*.c) $(wildcard $d/*.cpp))
HEADERS += $(foreach d,${DIRS}, $(wildcard $d/*.h))
HEADERS += $(foreach d,${DIRS}, $(wildcard $d/*.hpp))

CPP_LOGIC_ROOT ?= $(abspath ../../..)
PYTHON ?= python3
SUBSGEN := $(CPP_LOGIC_ROOT)/utils/ecmcCppLogicSourceSubstGen.py
STAGE_DIR := ../bin
STAGE_LIB := $(STAGE_DIR)/main.so
STAGE_SUBS := $(STAGE_DIR)/main.so.substitutions
LOCAL_MODULE := $(notdir $(abspath ..))

.PHONY: stage

stage:
	@lib_path="$$(find . -maxdepth 2 -path './O.*/lib$(LOCAL_MODULE).so' -printf '%T@ %p\n' | sort -nr | awk 'NR==1 {print $$2}')"; \
	if [ -z "$$lib_path" ]; then \
		echo "No built library found for $(LOCAL_MODULE). Run make build first." >&2; \
		exit 1; \
	fi; \
	mkdir -p $(STAGE_DIR); \
	cp "$$lib_path" $(STAGE_LIB); \
	$(PYTHON) $(SUBSGEN) --source main.cpp --logic-name "$(LOCAL_MODULE)" --output $(STAGE_SUBS)
