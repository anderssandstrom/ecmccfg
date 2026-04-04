.PHONY: all install clean

IOC_STARTUP_FILE := $(notdir $(firstword $(wildcard *_startup.script)))
IOC_PARAMS_FILE := $(notdir $(firstword $(wildcard *_parameters.yaml)))
IOC_NAME ?= $(patsubst %_startup.script,%,$(IOC_STARTUP_FILE))
ifeq ($(IOC_NAME),)
IOC_NAME := $(patsubst %_parameters.yaml,%,$(IOC_PARAMS_FILE))
endif
IOC_NATIVE_SUBS := $(IOC_NAME)_native_logic.subs

all:
	$(MAKE) -C src stage
	cp bin/main.so.substitutions $(IOC_NATIVE_SUBS)

install: all
	ioc install --clean -V --ioc $(IOC_NAME)

clean:
	$(MAKE) -C src clean
	$(RM) $(IOC_NATIVE_SUBS)
