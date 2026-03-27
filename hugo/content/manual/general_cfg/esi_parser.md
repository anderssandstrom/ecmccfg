+++
title = "ESI Parser"
weight = 17
chapter = false
+++

## Scope
This page documents the legacy EtherCAT ESI parser utility.

The tool parses an EtherCAT ESI XML file, filters slaves by name and revision,
optionally filters alternative PDO mappings, and can export:

- a JSON summary of the parsed device data
- generated ecmc hardware support snippets

This is a utility/developer workflow, not a normal IOC startup script.

## Current Status

- The parser is currently described in [utils/readme.md](/Users/sandst_a/sources/ecmccfg/utils/readme.md).
- The note in that file still applies: support is limited and mainly intended
  for slaves with several alternative PDO mappings.
- For interactive inspection and snippet generation, the newer
  `utils/esi_mapping_browser.py` tool is generally the better starting point.
- If hardware support does not exist yet, this tool can help generate base
  configuration files from an ESI XML.
- The generated files are only a starting point. More advanced slaves can still
  require manual editing before the result is ready to use.
- Distributed-clock configuration is not handled by this parser.

## Input And Output

Input:

- an EtherCAT ESI XML file
- a slave name wildcard
- a revision wildcard

Optional filtering:

- selected slave indices
- selected PDO mapping indices
- merge entries smaller than 8 bits

Output:

- console printout of the matching PDO mappings
- optional JSON file with parsed device information
- optional generated ecmc hardware snippet files

## Command Line Parameters

The parser currently supports these arguments:

| Argument | Meaning |
| --- | --- |
| `--file` | Path to the ESI XML file. |
| `--name` | Slave name wildcard, for example `EL7211*`. |
| `--rev` | Revision wildcard, for example `0x1000*` or `*`. |
| `--filtSlaves` | Optional slave-index filter, for example `1,2,5` or `all`. |
| `--filtPdoMaps` | Optional PDO-map filter, for example `1,2,5` or `all`. |
| `--mergeEntries` | Optional merge of entries smaller than 8 bits. |
| `--outputJSON` | Optional output filename for parsed JSON. |
| `--outputECMC` | Optional filename base for generated ecmc hardware support files. |

## Example

```bash
cd utils/back
python3 esi_parser.py \
  --file ../../../beckhoff_xml/Beckhoff\ EL72xx.xml \
  --name "EL7211*" \
  --rev "*" \
  --filtSlaves "1" \
  --outputJSON parsed_devices.json \
  --outputECMC "" \
  --mergeEntries 1
```

## Typical Use

Use this utility when you need to inspect one slave family in an ESI XML and
generate a first draft of ecmc hardware support from a selected PDO mapping.

This is especially useful when a slave is not supported yet and you need a base
configuration file to start from. For more advanced slaves, expect to review
and extend the generated result manually. DC clock configuration must also be
added separately.

Typical flow:

1. Choose the ESI XML file and a slave name/revision filter.
2. Restrict to one slave instance with `--filtSlaves` if needed.
3. Restrict to one or more PDO maps with `--filtPdoMaps`.
4. Generate JSON and/or ecmc output.
5. Review the generated hardware snippet before using it in `hardware/`.

## Related Pages

- [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
- [Supported Slaves]({{< relref "/manual/general_cfg/supported_slaves.md" >}})
