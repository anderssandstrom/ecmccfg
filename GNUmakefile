include /ioc/tools/driver.makefile
include $(EPICS_MODULES)/makeUtils/latest/utils.mk

MODULE=ecmccfg

LIBVERSION = dev

BUILDCLASSES = Linux
EXCLUDE_VERSIONS=3 7.0.3
ARCH_FILTER=RHEL%

SCRIPTS+=startup.cmd

SCRIPTS+=$(wildcard ./scripts/*)
SCRIPTS+=$(wildcard ./general/*)
SCRIPTS+=$(wildcard ./hardware/*/*.cmd)
SCRIPTS+=$(wildcard ./motion/*)
SCRIPTS+=$(wildcard ./protocol/*)

TEMPLATES+=$(wildcard ./db/*.db)
TEMPLATES+=$(wildcard ./db/*.template)
TEMPLATES+=$(wildcard ./db/*.substitutions)
TEMPLATES+=$(wildcard ./db/*.subs)
TEMPLATES+=$(wildcard ./db/*/*.db)
TEMPLATES+=$(wildcard ./db/*/*.template)
TEMPLATES+=$(wildcard ./db/*/*.substitutions)
TEMPLATES+=$(wildcard ./db/*/*.subs)

