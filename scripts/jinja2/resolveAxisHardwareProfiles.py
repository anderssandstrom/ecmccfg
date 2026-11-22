#!/usr/bin/env python3
"""Resolve axis hardware defaults from slave IDs registered by addSlave.cmd.

No explicit hardware type is needed in axis YAML. Without a section's 'slave'
selector, the original YAML is copied unchanged for legacy compatibility.
"""
import argparse
import copy
import os
import pathlib
import re
import shutil

import yaml

_SAFE_TYPE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_SLAVE_ID = re.compile(r"^[0-9]+$")
_MACRO = re.compile(r"\$\(([A-Za-z_][A-Za-z0-9_]*)(?:=([^()]*))?\)")
_SECTIONS = ("drive", "encoder", "input")


def deep_merge(defaults, overrides):
    """Merge maps recursively; explicit axis values always win."""
    if not isinstance(defaults, dict) or not isinstance(overrides, dict):
        return copy.deepcopy(overrides)
    out = copy.deepcopy(defaults)
    for key, value in overrides.items():
        out[key] = deep_merge(out[key], value) if key in out else copy.deepcopy(value)
    return out


def _expand_selector(value, environ, section):
    """Expand IOC environment macros in a slave/master selector.

    Only selector values are expanded here. Other axis YAML strings retain
    their existing IOC/EPICS macro handling. Support $(VAR) and $(VAR=default).
    """
    if not isinstance(value, str):
        return value
    resolved = value
    for _ in range(20):
        matches = list(_MACRO.finditer(resolved))
        if not matches:
            break
        def replacement(match):
            key, default = match.group(1), match.group(2)
            replacement_value = environ.get(key, default)
            if replacement_value is None:
                raise ValueError("Undefined IOC macro %s in %s selector" %
                                 (key, section))
            return str(replacement_value)
        expanded = _MACRO.sub(replacement, resolved)
        if expanded == resolved:
            raise ValueError("Recursive IOC macro in %s selector: %r" %
                             (section, value))
        resolved = expanded
    else:
        raise ValueError("Too many nested IOC macros in %s selector: %r" %
                         (section, value))
    if "$(" in resolved or ")" in resolved:
        raise ValueError("Invalid or unresolved IOC macro in %s selector: %r" %
                         (section, value))
    return resolved


def _slave_id(value, section, environ):
    value = _expand_selector(value, environ, section)
    if isinstance(value, bool) or not (
        isinstance(value, int) and value >= 0 or
        isinstance(value, str) and _SLAVE_ID.fullmatch(value)
    ):
        raise ValueError("%s must resolve to a nonnegative integer: %r" %
                         (section, value))
    return int(value)


def _master_id(section_data, environ):
    value = section_data.get("master", environ.get("ECMC_EC_MASTER_ID", "0"))
    return _slave_id(value, "master", environ)


def _profile_path(profiles_dir, hardware, section):
    # Prefer exact HW_DESC, then the base terminal model for variants.
    names = [hardware]
    model = re.match(r"^([A-Za-z]+[0-9]+)", hardware)
    if model and model.group(1) not in names:
        names.append(model.group(1))
    for name in names:
        profile = pathlib.Path(profiles_dir) / name / (section + ".yaml")
        if profile.is_file():
            return profile
    return None


def _substitute(value, master, slave, channel):
    """Substitute placeholders in profile-owned strings only."""
    if isinstance(value, str):
        return value.replace("$(MASTER)", str(master)).replace("$(SLAVE)", str(slave)).replace("$(CHANNEL)", "%02d" % channel)
    if isinstance(value, list):
        return [_substitute(v, master, slave, channel) for v in value]
    if isinstance(value, dict):
        return {k: _substitute(v, master, slave) for k, v in value.items()}
    return value


def resolve(document, profiles_dir, environ=None):
    if not isinstance(document, dict):
        raise ValueError("Axis YAML root must be a mapping")
    if "hardwareProfiles" in document:
        raise ValueError("hardwareProfiles is not supported; use drive.slave/encoder.slave/input.slave")
    env = os.environ if environ is None else environ
    result = copy.deepcopy(document)
    for section in _SECTIONS:
        raw = result.get(section)
        if not isinstance(raw, dict) or "slave" not in raw:
            continue
        slave = _slave_id(raw["slave"], section + ".slave", env)
        channel = _slave_id(raw.get("channel", 1), section + ".channel", env)
        if channel < 1:
            raise ValueError("%s.channel must be at least 1" % section)
        master = _master_id(raw, env)
        key = "ECMC_HW_M%d_S%d" % (master, slave)
        hardware = env.get(key)
        if not hardware:
            raise ValueError("Hardware type not registered for %s.slave=%d (master %d; expected %s)" %
                             (section, slave, master, key))
        if not _SAFE_TYPE.fullmatch(hardware):
            raise ValueError("Invalid registered hardware type: %r" % hardware)
        profile = _profile_path(profiles_dir, hardware, section)
        if profile is None:
            raise FileNotFoundError("Missing %s profile for %s (master %d, slave %d)" %
                                    (section, hardware, master, slave))
        with profile.open(encoding="utf-8") as stream:
            defaults = yaml.safe_load(stream)
        if not isinstance(defaults, dict) or not set(defaults).issubset({section, "channels"}) or section not in defaults or not isinstance(defaults[section], dict):
            raise ValueError("Invalid profile structure: %s" % profile)
        channel_count = defaults.get("channels", 1)
        if type(channel_count) is not int or channel_count < 1:
            raise ValueError("Invalid channels count in %s" % profile)
        if channel > channel_count:
            raise ValueError("%s.channel=%d exceeds %s supported channels (%d)" %
                             (section, channel, hardware, channel_count))
        defaults = _substitute(defaults[section], master, slave, channel)
        # Selector keys are not supported by the existing axis schema.
        overrides = {k: v for k, v in raw.items() if k not in ("slave", "master", "channel")}
        result[section] = deep_merge(defaults, overrides)
    return result


def preprocess(src, dst, profiles_dir, environ=None):
    src = pathlib.Path(src)
    dst = pathlib.Path(dst)
    with src.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    if isinstance(document, dict) and not any(
        isinstance(document.get(k), dict) and "slave" in document[k]
        for k in _SECTIONS
    ) and "hardwareProfiles" not in document:
        shutil.copyfile(src, dst)
        return
    resolved = resolve(document, profiles_dir, environ)
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
