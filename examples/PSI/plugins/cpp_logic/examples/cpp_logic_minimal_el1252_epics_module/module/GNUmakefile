include /ioc/tools/driver.makefile

MODULE=ecmc_cpp_logic_as_module

BUILDCLASSES = Linux
EXCLUDE_VERSIONS = 3 7.0.5 7.0.6 7.0.7

ARCH_FILTER=deb10% deb12% deb13%

SCRIPTS+=startup.cmd


TEMPLATES+=$(wildcard ./db/*.db)
TEMPLATES+=$(wildcard ./db/*.template)
TEMPLATES+=$(wildcard ./db/*.substitutions)
TEMPLATES+=$(wildcard ./db/*.subs)
TEMPLATES+=$(wildcard ./db/*/*.db)
TEMPLATES+=$(wildcard ./db/*/*.template)
TEMPLATES+=$(wildcard ./db/*/*.substitutions)
TEMPLATES+=$(wildcard ./db/*/*.subs)

SOURCES += $(wildcard ./src/*.cpp)
DBDS    += $(wildcard ./dbd/*.dbd)

