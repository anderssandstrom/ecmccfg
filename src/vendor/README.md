# Header-only dependencies for native hardware profiles

These unmodified single headers were copied from the local ECB vendor tree
(commit `79a9ef6`) so building ecmccfg does not require an ECB checkout.

- `nlohmann/json.hpp`: JSON for Modern C++, version recorded in the header.
- `rapidyaml/rapidyaml.hpp`: rapidyaml amalgamation, including c4core; version
  information and upstream copyright notices are included in the header.

Both are MIT licensed; each directory includes its upstream LICENSE.
Keep these notices with any redistributed headers. Only
`ecmcHardwareProfiles.cpp` defines `RYML_SINGLE_HDR_DEFINE_NOW`.
