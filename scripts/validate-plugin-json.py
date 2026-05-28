#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^0|[1-9]\d*\.0|[1-9]\d*\.0|[1-9]\d*$")
STRICT_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
CONTRIBUTION_KEYS = {
    "uiPanels",
    "commands",
    "editorExtensions",
    "sidebarItems",
    "toolbarActions",
    "backgroundServices",
}


def fail(errors, path, message):
    errors.append(f"{path}: {message}")


def expect_type(errors, data, key, expected, path, required=True):
    if key not in data:
        if required:
            fail(errors, path, f"missing required field '{key}'")
        return None
    value = data[key]
    if not isinstance(value, expected):
        name = expected.__name__ if hasattr(expected, "__name__") else str(expected)
        fail(errors, path, f"field '{key}' must be {name}")
        return None
    return value


def validate_contribution_items(errors, items, path):
    if not isinstance(items, list):
        fail(errors, path, "must be an array")
        return
    seen = set()
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            fail(errors, item_path, "must be an object")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            fail(errors, item_path, "missing string id")
        elif item_id in seen:
            fail(errors, item_path, f"duplicate id '{item_id}'")
        else:
            seen.add(item_id)
        title = item.get("title")
        if title is not None and not isinstance(title, str):
            fail(errors, item_path, "title must be a string")


def validate_plugin_manifest(path):
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return [f"{path}: root must be an object"]

    name = expect_type(errors, data, "name", str, path)
    if name and not NAME_RE.match(name):
        fail(errors, path, "name must be lowercase kebab-case")
    expect_type(errors, data, "displayName", str, path)
    version = expect_type(errors, data, "version", str, path)
    if version and not STRICT_SEMVER_RE.match(version):
        fail(errors, path, "version must be semantic versioning, for example 0.1.0")
    expect_type(errors, data, "description", str, path)

    entry = expect_type(errors, data, "entry", str, path, required=False)
    if entry:
        if Path(entry).is_absolute() or ".." in Path(entry).parts:
            fail(errors, path, "entry must be a relative path inside the plugin package")
        if not entry.endswith(".py"):
            fail(errors, path, "entry must be a Python .py file in this plugin version")

    permissions = expect_type(errors, data, "permissions", list, path)
    if isinstance(permissions, list):
        for index, permission in enumerate(permissions):
            if not isinstance(permission, str) or not permission.strip():
                fail(errors, path, f"permissions[{index}] must be a non-empty string")

    contributes = expect_type(errors, data, "contributes", dict, path, required=False)
    if contributes is not None:
        for key, value in contributes.items():
            if key not in CONTRIBUTION_KEYS:
                fail(errors, path, f"unknown contribution key '{key}'")
                continue
            validate_contribution_items(errors, value, f"{path}: contributes.{key}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate a Jottr plugin.json manifest.")
    parser.add_argument("path", nargs="?", default="plugin.json")
    args = parser.parse_args()
    errors = validate_plugin_manifest(Path(args.path))
    if errors:
        print("plugin.json validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Validated {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
