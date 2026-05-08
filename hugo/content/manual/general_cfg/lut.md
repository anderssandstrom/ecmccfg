+++
title = "Lookup Tables"
weight = 20
chapter = false
+++

## Scope
Lookup tables, or LUTs, are numeric tables loaded into ecmc and then accessed at runtime.

Use them when:

- an axis or encoder needs correction data
- PLC logic needs a fixed indexed value table
- a calibration curve should be kept outside the PLC source code

## Startup Interface

Load a LUT from file with:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}loadLUTFile.cmd "FILE=./cfg/example.lut"
```

Optional:

- `LUT_ID`: explicit LUT id

After load, the actual id is also available in `ECMC_LUT_ID`.

## File Format

The LUT file is a plain text file with two numeric columns.

Example:

```text
# Encoder correction example
PREC=5
-10 -10.12345
0 0.12345
10 10.12345
PREC=6
12.67898 12.345679
```

Notes:

- numbers can be comma- or space-separated
- `PREC=<n>` changes the read precision for the following rows
- comments are allowed

The exact interpretation of the two columns depends on how the LUT is used. A common pattern is:

- column 1: input/index/position
- column 2: output/correction/value

## Typical Use Cases

### Encoder correction

One common use is encoder correction data, where:

- column 1 is the measured encoder position
- column 2 is the correction value

### PLC lookup logic

LUTs can also be used directly from PLC logic through the `lut_...` helper functions.

That is useful when:

- a small calibration or recipe table should be editable as data instead of PLC code
- the same numeric table should be shared across several PLC functions

### C++ logic lookup

`cpp_logic` modules can read the same loaded LUT objects through
`ecmcCpp::lutGetValue(...)` from `ecmcCppLogic.hpp`.

Example:

```cpp
double value = 0.0;
if (ecmcCpp::lutExists(0)) {
  value = ecmcCpp::lutGetValue(0, index);
}
```

The first argument is the LUT id. The second argument is the input/index value.
The helper returns `0.0` if the LUT id is out of range or if the LUT object has
not been loaded. Use `ecmcCpp::lutExists(...)` to test whether an optional LUT
has been loaded without logging an error. See [C++ Logic Helpers]({{< relref "/manual/plugins/cpp_logic_helpers.md" >}})
for the cpp-logic helper reference.

## Runtime Interfaces

### PLC Interface

The PLC function library provides `lut_...` helper functions.

A typical pattern is:

```text
value = lut_get_value(0,index);
```

Use [PLC functions]({{< relref "/manual/PLC_cfg/functions.md" >}}) for the full `lut_...` reference.

### C++ Logic Interface

Use `ecmcCpp::lutExists(lutId)` and `ecmcCpp::lutGetValue(lutId, index)` from
`ecmcCppLogic.hpp`.

## Recommended Usage

Use LUTs when the data is:

- numeric
- relatively static
- better maintained as a file than hard-coded in PLC expressions

Do not use LUTs as a replacement for:

- high-rate streaming data
- arbitrary operator-editable runtime state
- large buffered acquisitions

For those cases, use data storage, plugins, or normal EPICS/PLC state instead.

## Related Pages

- [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
- [PLC functions]({{< relref "/manual/PLC_cfg/functions.md" >}})
- [yaml configuration]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
- [Examples]({{< relref "/manual/examples.md" >}})
