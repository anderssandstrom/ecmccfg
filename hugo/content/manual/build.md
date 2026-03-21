+++
title = "build at PSI"
weight = 1
chapter = false
+++

{{% notice warning %}}
These instructions are PSI-specific.
{{% /notice %}}

## Scope

This page describes the local PSI build and test workflow for `ecmccfg`.

## Build

The normal build path uses `driver.makefile`.

Current assumptions:

- Debian 10 or Debian 12
- EPICS `>= R7.0.7`

Build on the login cluster with:

```bash
make [LIBVERSION] [clean] [uninstall] install
```

## Check a particular version

To check that a specific module version loads, you can start an IOC shell with
explicit versions.

Example:

```bash
iocsh -7 -r "ecmccfg,dev 'ECMC_VER=dev,MASTER_ID=-1'"
```

This example checks:

- `ecmccfg` version `dev`
- `ECMC_VER=dev`
- `MASTER_ID=-1`, which runs ecmc in master-less mode

Adjust the versions and startup arguments to match the environment you want to
test.
