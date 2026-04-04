.PHONY: all install clean

IOC_STARTUP_FILE := $(notdir $(firstword $(wildcard *_startup.script)))
IOC_PARAMS_FILE := $(notdir $(firstword $(wildcard *_parameters.yaml)))
IOC_NAME ?= $(patsubst %_startup.script,%,$(IOC_STARTUP_FILE))
ifeq ($(IOC_NAME),)
IOC_NAME := $(patsubst %_parameters.yaml,%,$(IOC_PARAMS_FILE))
endif
CPP_LOGIC_ROOT ?= $(abspath ../..)
PYTHON ?= python3
GENERATE_QT ?= 1
IOC_QT_PANEL := qt/$(IOC_NAME)_cpp_logic.ui
IOC_QTGEN := $(CPP_LOGIC_ROOT)/utils/cpp_logic_ioc_qtgen.py

all:
	$(MAKE) -C src stage
	if [ "$(GENERATE_QT)" = "1" ]; then $(PYTHON) $(IOC_QTGEN) --input bin/main.so.substitutions --output $(IOC_QT_PANEL) --pv-prefix "$(IOC_NAME):" --title "$(IOC_NAME) cpp_logic PVs"; fi

install: all
	ioc install --clean -V --ioc $(IOC_NAME)

clean:
	$(MAKE) -C src clean
	$(RM) $(IOC_QT_PANEL)
