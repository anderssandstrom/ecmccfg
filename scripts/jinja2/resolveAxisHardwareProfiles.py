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
        return {k: _substitute(v, master, slave, channel) for k, v in value.items()}
    return value


def select_profiles(document, profiles_dir, environ=None):
    """Select and validate hardware, returning metadata without merging axis YAML.

    The Jinja renderer uses this to emit hardware-specific command snippets;
    the legacy ECB adapter still uses resolve() below.
    """
    if not isinstance(document, dict):
        raise ValueError("Axis YAML root must be a mapping")
    if "hardwareProfiles" in document:
        raise ValueError("hardwareProfiles is not supported; use drive.slave/encoder.slave/input.slave")
    env = os.environ if environ is None else environ
    selected = {}
    for section in _SECTIONS:
        raw = document.get(section)
        # Limit inputs can use the drive's own terminal. Explicit input.slave
        # and input.channel always win, including external limit modules.
        if section == "input" and (not isinstance(raw, dict) or "slave" not in raw):
            drive = document.get("drive")
            if isinstance(drive, dict) and "slave" in drive:
                candidate = dict(raw) if isinstance(raw, dict) else {}
                candidate["slave"] = drive["slave"]
                candidate.setdefault("master", drive.get("master", env.get("ECMC_EC_MASTER_ID", "0")))
                candidate.setdefault("channel", drive.get("channel", 1))
                raw = candidate
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
        if profile is None and section == "input" and (
            not isinstance(document.get("input"), dict) or
            "slave" not in document["input"]
        ):
            # Some terminals (e.g. EL7041) expose no suitable limit input
            # through the standard process image. Require explicit input YAML.
            continue
        if profile is None:
            raise FileNotFoundError("Missing %s profile for %s (master %d, slave %d)" %
                                    (section, hardware, master, slave))
        with profile.open(encoding="utf-8") as stream:
            config = yaml.safe_load(stream)
        allowed = {section, "channels", "feedbacks"} if section == "encoder" else {section, "channels"}
        if not isinstance(config, dict) or not set(config).issubset(allowed) or section not in config or not isinstance(config[section], dict):
            raise ValueError("Invalid profile structure: %s" % profile)
        count = config.get("channels", 1)
        if type(count) is not int or count < 1:
            raise ValueError("Invalid channels count in %s" % profile)
        if channel > count:
            raise ValueError("%s.channel=%d exceeds %s supported channels (%d)" %
                             (section, channel, hardware, count))
        values = config[section]
        feedbacks = config.get("feedbacks")
        if section == "encoder" and feedbacks is not None:
            if not isinstance(feedbacks, dict) or "openloop" not in feedbacks:
                raise ValueError("Invalid encoder feedback mapping in %s" % profile)
            feedback = _expand_selector(raw.get("feedback", "openloop"), env, "encoder.feedback")
            if not isinstance(feedback, str) or feedback not in feedbacks:
                raise ValueError("Unknown encoder feedback %r for %s; choices: %s" %
                                 (feedback, hardware, ", ".join(sorted(feedbacks))))
            variant = feedbacks[feedback]
            if not isinstance(variant, dict):
                raise ValueError("Invalid encoder feedback %r in %s" % (feedback, profile))
            values = deep_merge(values, variant)
        elif section == "encoder" and "feedback" in raw:
            raise ValueError("Encoder profile for %s does not support feedback selection" % hardware)
        selected[section] = {
            "model": profile.parent.name,
            "data": _substitute(values, master, slave, channel),
            "provided": list(document.get(section, {})) if isinstance(document.get(section), dict) else [],
            "slave": slave,
            "master": master,
            "channel": channel,
            "snippet": (profile.parent / (section + ".jinja2")).is_file(),
        }
    return selected


def resolve(document, profiles_dir, environ=None):
    """Compatibility adapter: merge defaults for ECB's existing schema pipeline."""
    selections = select_profiles(document, profiles_dir, environ)
    out = copy.deepcopy(document)
    for section, profile in selections.items():
        raw = out.get(section, {})
        overrides = {k: v for k, v in raw.items() if k not in
                     ("slave", "master", "channel", "feedback")}
        out[section] = deep_merge(profile["data"], overrides)
    return out


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
