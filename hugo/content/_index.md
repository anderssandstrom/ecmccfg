+++  
title = "ecmccfg"   
weight = 5  
chapter = true  
+++  

# ecmccfg

A configuration framework for ECMC Motion Control Module for EPICS.

## License <a href="https://github.com/paulscherrerinstitute/ecmccfg/blob/master/LICENSE" target="_blank" rel="license">![GitHub](https://img.shields.io/github/license/paulscherrerinstitute/ecmccfg?style=for-the-badge)</a>

This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3 of the License, or
   (at your option) any later version.

This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software Foundation,
   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

## Latest release

<a href="https://github.com/paulscherrerinstitute/ecmccfg/releases/latest" target="_blank" rel="latest release">![GitHub release (latest by date)](https://img.shields.io/github/v/release/paulscherrerinstitute/ecmccfg?style=for-the-badge)</a>

## Download

<a href="https://github.com/paulscherrerinstitute/ecmccfg" target="_blank" rel="top language">![GitHub top language](https://img.shields.io/github/languages/top/paulscherrerinstitute/ecmccfg?style=for-the-badge)</a>

## Start here

- [Quickstart]({{< relref "/manual/quickstart.md" >}}): prepare an IOC and bring up an axis using YAML.
- [Manual]({{< relref "/manual/_index.md" >}}): choose a commissioning or reference topic.
- [Simulation (SIM=1)]({{< relref "/manual/general_cfg/ethercat/simulation.md" >}}): run the realtime engine with memory-backed I/O and external device models.
- [Examples]({{< relref "/manual/examples.md" >}}): adapt complete configurations and test fixtures.
- [Troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting.md" >}}): diagnose startup and runtime problems.

`ecmccfg` supplies IOC scripts, YAML loaders, EPICS records and operator panels.
The ECMC module supplies the realtime motion and PLC engine. Hardware operation,
simulation (`SIM=1`) and masterless logic (`MASTER_ID=-1`) share the same engine;
see [the layer overview]({{< relref "/manual/general_cfg/startup/_index.md#how-the-layers-fit-together" >}})
for how they differ.
