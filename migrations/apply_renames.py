#!/usr/bin/env python3
"""Rewrite deprecated variable names in the inventory files.

Usage: python3 migrations/apply_renames.py <inventory dir> [--check]

Reads the `renames` list of migrations/variable_renames.yml and, for every
*.yml file in <inventory dir>:
  - renames top-level keys (the variable definitions), and
  - renames references to those variables inside {{ ... }} and {% ... %}.
Everything else (values, comments, formatting) is left as it is.

Before the first change the inventory files are copied to
inventory/backups/<timestamp>/. Running it again is safe: files that are
already up to date are not touched. `--check` only reports what would change.

Uses only the Python standard library, so it runs with any python3.
"""
import glob
import os
import re
import shutil
import sys
import time

RENAMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "variable_renames.yml")
ENTRY = re.compile(r"^\s*-\s*\{\s*old:\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*new:\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\s*(#.*)?$")
JINJA = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.S)


def load_renames(path=RENAMES_FILE):
    """Return the {old: new} pairs of the top-level `renames` list."""
    renames = {}
    section = None
    with open(path) as handle:
        for line in handle:
            top = re.match(r"^([A-Za-z_]+):", line)
            if top:
                section = top.group(1)
                continue
            entry = ENTRY.match(line)
            if entry and section == "renames":
                renames[entry.group(1)] = entry.group(2)
    return renames


def top_level_keys(text):
    return set(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*):", text, re.M))


def migrate(text, renames, taken):
    """Return (new text, renamed keys, keys left alone because the new name is already set)."""
    renamed, skipped = [], []
    present = [old for old in renames if re.search(r"^%s:" % re.escape(old), text, re.M)]
    for old in present:
        new = renames[old]
        if new in taken:
            skipped.append(old)
            continue
        text = re.sub(r"^%s:" % re.escape(old), new + ":", text, flags=re.M)
        taken.add(new)
        renamed.append(old)

    names = sorted(renames, key=len, reverse=True)
    reference = re.compile(r"(?<![\w.'\"])(" + "|".join(map(re.escape, names)) + r")(?![\w'\"(])")

    # References are rewritten one top-level variable at a time, so that a variable whose value
    # falls back to its own old name ("{{ old_name | default(...) }}") is not turned into a
    # reference to itself.
    blocks = re.split(r"(?m)^(?=[A-Za-z_][A-Za-z0-9_]*:)", text)
    for index, block in enumerate(blocks):
        owner = re.match(r"([A-Za-z_][A-Za-z0-9_]*):", block)
        owner = owner.group(1) if owner else None

        def rename_reference(match, owner=owner):
            new = renames[match.group(1)]
            return match.group(0) if new == owner else new

        blocks[index] = JINJA.sub(lambda region: reference.sub(rename_reference, region.group(0)), block)
    return "".join(blocks), renamed, skipped


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    check = "--check" in argv
    if len(args) != 1:
        print(__doc__)
        return 2
    inventory = args[0]
    renames = load_renames()
    files = sorted(glob.glob(os.path.join(inventory, "*.yml")))
    if not files:
        print("No inventory files in %s, nothing to rename (run 'make config' first)" % inventory)
        return 0

    texts = {path: open(path).read() for path in files}
    taken = set()
    for text in texts.values():
        taken |= top_level_keys(text)

    changes = {}
    skipped_all = []
    total = 0
    for path, text in texts.items():
        new_text, renamed, skipped = migrate(text, renames, taken)
        skipped_all += [(path, old) for old in skipped]
        if new_text != text:
            changes[path] = new_text
            total += len(renamed)
            print("  %s: %d variable(s) renamed%s" % (os.path.basename(path), len(renamed), "" if renamed else " (references only)"))

    for path, old in skipped_all:
        print("  %s: '%s' was left alone because '%s' is already set, remove '%s' yourself"
              % (os.path.basename(path), old, renames[old], old))

    if not changes:
        print("  variable names are already up to date")
        return 0
    if check:
        print("  %d variable(s) in %d file(s) would be renamed" % (total, len(changes)))
        return 0

    backup = os.path.join(os.path.dirname(os.path.dirname(os.path.normpath(inventory))), "backups", time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(backup, exist_ok=True)
    for path in files:
        shutil.copy2(path, backup)
    for path, new_text in changes.items():
        with open(path, "w") as handle:
            handle.write(new_text)
    print("  %d variable(s) renamed in %d file(s), the previous files were saved to %s" % (total, len(changes), backup))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
