+++
title = "syntax"
weight = 13
chapter = false
+++

In `ecmc`, PLCs are based on the `exprtk` expression evaluation library.
For detailed syntax help, see the [exprtk website](https://github.com/ArashPartow/exprtk).

Companion pages:
- [variables]({{< relref "/manual/PLC_cfg/variables.md" >}})
- [patterns]({{< relref "/manual/PLC_cfg/patterns.md" >}})
- [functions]({{< relref "/manual/PLC_cfg/functions.md" >}})
- [best practice]({{< relref "/manual/PLC_cfg/best_practice.md" >}})
- [function libs]({{< relref "/manual/PLC_cfg/function_libs.md" >}})

As a general rule, prefer PLC helper functions over direct raw variable access
when both are available. The function calls are usually clearer, more stable as
an interface, and easier to search for in examples and documentation. This is
also the better runtime choice: PLC variables are refreshed around each PLC
scan, while function calls read the current value directly. This is similar to
other PLC systems where the normal variable view is scan-based.

## common errors, misconceptions and info
### operators
- `:=`: assignment
- `=` or `==`: equal comparison

### functions
PLCs do _not_ immediately write to the bus.
The PLC will execute synchronously with the cycle, or at an integer fraction of it.
The processed data will be sent to the bus with the next cycle.
PLCs do _not_ delay the bus!

### statement terminator
Statements are terminated by a semicolon `;`

### variables
All variables are initialized to `0`.

#### declaration
Variables can be declared in the beginning of the PLC code by defining a `VAR..END_VAR` block:
```
VAR
  <var_name> : <address>;
END_VAR
```

`<var_name>` in the PLC code will then be substituted by `<address>` before compilation.

The following "addresses" are supported:
* global:
  - `global.<name>`
* static:
  - `static.<name>`
* EtherCAT
  - `ec<mid>`
  - `ec<mid>.s<sid>`
  - `ec<mid>.s<sid>.<name>`
* motion:
  - `ax<id>`
  - `ax<id>.traj`
  - `ax<id>.enc`
  - `ax<id>.drv`
  - `ax<id>.mon`
  - `ax<id>.traj.<name>`
  - `ax<id>.enc.<name>`
  - `ax<id>.drv.<name>`
  - `ax<id>.mon.<name>`
* data storage:
  - `ds<id>`
  - `ds<id>.<name>`
* plc:
  - `plc<id>`
* constants
  - `<name>`

`static.<name>` variables are private to one PLC, while `global.<name>` variables are shared between PLCs.
Both can also be exposed as EPICS PVs; see [best practice]({{< relref "/manual/PLC_cfg/best_practice.md" >}}).

### comments
The hash character `#` is reserved for comments.
Everything after this character will be removed before compilation.
{{% notice warning %}}
`println('########');` will be seen by the compiler as `println('` !
{{% /notice %}}

### macros
{{% notice warning %}}
So far macro substitution is **not** implemented for `yaml`!
{{% /notice %}}

{{% notice tip %}}
If macro substitution is needed, please use the traditional approach using `loadPLCFile.cmd`, with the `PLC_MACROS` variable.
{{% /notice %}}

## Reference pages

- [variables]({{< relref "/manual/PLC_cfg/variables.md" >}}) for `static`, `global`, EtherCAT, motion, PLC, and data-storage namespaces.
- [patterns]({{< relref "/manual/PLC_cfg/patterns.md" >}}) for short practical PLC snippets.
- [functions]({{< relref "/manual/PLC_cfg/functions.md" >}}) for the full `ec_`, `mc_`, `mc_grp_`, `ds_`, `lut_`, `m2m_`, and `epics_` reference.

{{% notice tip %}}
Custom function libs in exprtk syntax can be added and loaded to the PLC objects.
{{% /notice %}}

{{% notice tip %}}
Custom PLC functions can be written in C in plugins.
{{% /notice %}}

### general

```text
  1. Assignment:
     ec0.s1.VALUE:=100;

  2. if-else (note the equal sign):
     if(ec0.s1.VALUE=100) {
       # code
     }
     else {
       # code
     };

   3. for loop:
     for (static.i := 0; static.i < static.elements; static.i += 1) {
       # code
     };

   4. printouts (minimize printouts or use only for debug):
      print("The value of ec0.s1.VALUE is: ",ec0.s1.VALUE);  # Without line feed
      println("The value of ec0.s1.VALUE is: ",ec0.s1.VALUE);  # With line feed

      Also see the "ec_print_bin()" and "ec_print_hex()" below.
```
