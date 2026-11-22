#!/usr/bin/env python3
"""Resolve opt-in section defaults before the existing Jinja/ECB axis pipeline.

Example: python resolveAxisHardwareProfiles.py axis.yaml resolved.yaml --profiles hardwareProfiles
The output contains only keys understood by the existing axis schema.
"""
import argparse
import copy
import pathlib
import re
import shutil

import yaml

_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_SECTIONS = {
    "drive": ("drive",),
    "encoder": ("encoder",),
    "encoder.homing": ("encoder", "homing"),
    "input": ("input",),
}


def deep_merge(defaults, overrides):
    """Recursively merge mappings; application settings win, including false/0/null."""
    if not isinstance(defaults, dict) or not isinstance(overrides, dict):
        return copy.deepcopy(overrides)
    out = copy.deepcopy(defaults)
    for key, value in overrides.items():
        if key in out:
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def resolve(document, profiles_dir):
    if not isinstance(document, dict):
        raise ValueError("Axis YAML root must be a mapping")
    selectors = document.get("hardwareProfiles")
    if selectors is None:
        return copy.deepcopy(document)
    if not isinstance(selectors, dict):
        raise ValueError("hardwareProfiles must be a section-to-hardware mapping")
    result = {}
    for section, hw in selectors.items():
        if section not in _SECTIONS:
            raise ValueError("Unsupported hardware profile section: %s" % section)
        if not isinstance(hw, str) or not _SAFE_NAME.fullmatch(hw) or hw in (".", ".."):
            raise ValueError("Invalid hardware profile name for %s: %r" % (section, hw))
        target = _SECTIONS[section]
        profile = pathlib.Path(profiles_dir) / hw / (section + ".yaml")
        if not profile.is_file():
            raise FileNotFoundError("No hardware profile for %s: %s" % (section, profile))
        with profile.open(encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
        if not isinstance(data, dict):
            raise ValueError("Hardware profile must contain a mapping: %s" % profile)
        if any(key != section.split(".")[-1] for key in data):
            # Section documents use the exact section key and can be merged safely.
            raise ValueError("Unexpected keys in hardware profile: %s" % profile)
        # Wrap nested selectors (encoder.homing) inside their parent section.
        for key in reversed(target[:-1]):
            data = {key: data}
        result = deep_merge(result, data)
    axis = {k: v for k, v in document.items() if k != "hardwareProfiles"}
    return deep_merge(result, axis)


def preprocess(src, dst, profiles_dir):
    src = pathlib.Path(src)
    dst = pathlib.Path(dst)
    with src.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    # Exact byte-for-byte copy if the feature is unused (also preserves comments).
    if isinstance(document, dict) and "hardwareProfiles" not in document:
        shutil.copyfile(src, dst)
        return
    resolved = resolve(document, profiles_dir)
    with dst.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(resolved, stream, sort_keys=False, allow_unicode=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--profiles", required=True)
    args = parser.parse_args()
    preprocess(args.source, args.output, args.profiles)


if __name__ == "__main__":
    main()
