.PHONY: all install clean

IOC_STARTUP_FILE := $(notdir $(firstword $(wildcard *_startup.script)))
IOC_PARAMS_FILE := $(notdir $(firstword $(wildcard *_parameters.yaml)))
IOC_NAME ?= $(patsubst %_startup.script,%,$(IOC_STARTUP_FILE))
ifeq ($(IOC_NAME),)
IOC_NAME := $(patsubst %_parameters.yaml,%,$(IOC_PARAMS_FILE))
endif

all:
	$(MAKE) -C src stage

install: all
	ioc install --clean -V --ioc $(IOC_NAME)

clean:
	$(MAKE) -C src clean
