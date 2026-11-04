#!/bin/bash
set -euo pipefail
source /opt/slit/runtime.env
unset LD_PRELOAD
export PYEPICS_LIBCA=/opt/epics/base/lib/${EPICS_HOST_ARCH}/libca.so
cd /opt/slit/sources/ecmccfg
exec /opt/slit/venv/bin/python tests/integration/slit/run.py \
  --config /opt/slit/sources/ecmccfg/tests/integration/slit/ioc \
  --prefix SIMSLIT: "$@"
