#!/usr/bin/env python3
import collections
import ipaddress
import pathlib
import subprocess
import sys

DATA = "data"
INDEX = "index"
MAX_ITEMS = 25
MAX_SCOPES = 3


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")


def out(*args):
    r = git(*args)
    if r.returncode != 0:
        raise SystemExit(r.stderr.strip())
    return r.stdout


def data_files(rev):
    if rev == INDEX:
        listing = out("ls-files", "--", DATA)
    elif rev is None:
        root = pathlib.Path(DATA)
        return sorted(p.name for p in root.iterdir() if p.is_file())
    else:
        listing = out("ls-tree", "-r", "--name-only", rev, f"{DATA}/")
    return sorted(line.rsplit("/", 1)[1] for line in listing.splitlines() if line.strip())


def read(rev, name):
    if rev is None:
        path = pathlib.Path(DATA) / name
        return path.read_text(encoding="utf-8") if path.exists() else ""
    spec = f":{DATA}/{name}" if rev == INDEX else f"{rev}:{DATA}/{name}"
    r = git("show", spec)
    return r.stdout if r.returncode == 0 else ""


def parse(text):
    rules = collections.OrderedDict()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        i = line.find("#")
        value, comment = (line[:i].strip(), line[i + 1:].strip()) if i >= 0 else (line, "")
        if not value:
            continue
        rules[value] = comment
    return rules


def snapshot(rev):
    return {name: parse(read(rev, name)) for name in data_files(rev)}


def index_of(tree):
    return {(name, value): comment
            for name, rules in tree.items()
            for value, comment in rules.items()}


def hosts(value):
    try:
        return ipaddress.ip_network(value, strict=False).num_addresses
    except ValueError:
        return 0


def compare(old, new):
    old_flat, new_flat = index_of(old), index_of(new)
    added = {k: new_flat[k] for k in set(new_flat) - set(old_flat)}
    removed = {k: old_flat[k] for k in set(old_flat) - set(new_flat)}

    moved = []
    by_value = collections.defaultdict(list)
    for name, value in removed:
        by_value[value].append(name)
    for key in list(added):
        name, value = key
        sources = by_value.get(value)
        if not sources:
            continue
        src = sources.pop(0)
        moved.append((src, name, value))
        del added[key]
        del removed[(src, value)]

    new_files = set(new) - set(old)
    return {"added": added, "removed": removed, "moved": moved, "new_files": new_files}


def render_group(title, items, new_files=None):
    if not items:
        return []
    grouped = collections.defaultdict(list)
    for (name, value), comment in sorted(items.items()):
        grouped[name].append((value, comment))
    lines = [f"### {title}", ""]
    for name, entries in sorted(grouped.items()):
        mark = " (новый)" if new_files and name in new_files else ""
        lines.append(f"**{name}**{mark}")
        for value, comment in entries[:MAX_ITEMS]:
            note = f" — {comment}" if comment else ""
            lines.append(f"- {value}{note}")
        rest = len(entries) - MAX_ITEMS
        if rest > 0:
            lines.append(f"- …и ещё {rest}")
        lines.append("")
    return lines


def totals(tree):
    nets = sum(len(rules) for name, rules in tree.items() if name != "trash")
    addrs = sum(hosts(v) for name, rules in tree.items() if name != "trash" for v in rules)
    return nets, addrs


def changelog(old_rev, new_rev):
    old, new = snapshot(old_rev), snapshot(new_rev)
    diff = compare(old, new)

    lines = []
    lines += render_group("Добавлено", diff["added"], diff["new_files"])
    lines += render_group("Удалено", diff["removed"])

    if diff["moved"]:
        lines += ["### Перенесено", ""]
        for src, dst, value in sorted(diff["moved"], key=lambda m: m[2])[:MAX_ITEMS]:
            lines.append(f"- {value}: {src} → {dst}")
        rest = len(diff["moved"]) - MAX_ITEMS
        if rest > 0:
            lines.append(f"- …и ещё {rest}")
        lines.append("")

    before_nets, before_addrs = totals(old)
    after_nets, after_addrs = totals(new)
    delta = after_nets - before_nets
    sign = f"+{delta}" if delta > 0 else str(delta)
    tail = f"Сетей: {after_nets} ({sign})" if delta else f"Сетей: {after_nets}"
    lines += ["---", "", f"{tail}, адресов: {after_addrs}"]

    body = "\n".join(lines).strip()
    return body or "Без изменений в списках"


def subject(old_rev, new_rev):
    args = ["diff", "--name-only", old_rev]
    if new_rev == INDEX:
        args = ["diff", "--cached", "--name-only", old_rev]
    elif new_rev:
        args.append(new_rev)
    changed = out(*args).split()
    non_data = [p for p in changed if not p.startswith(f"{DATA}/")]

    old, new = snapshot(old_rev), snapshot(new_rev)
    diff = compare(old, new)

    touched = set()
    for name, _ in list(diff["added"]) + list(diff["removed"]):
        touched.add(name)
    for src, dst, _ in diff["moved"]:
        touched.add(src)
        touched.add(dst)

    if not touched:
        if not non_data:
            return ""
        names = ", ".join(sorted(pathlib.Path(p).name for p in non_data)[:MAX_SCOPES])
        return f"fix: {names}"

    if diff["added"] and not diff["removed"]:
        verb = "add"
    elif diff["removed"] and not diff["added"]:
        verb = "del"
    else:
        verb = "fix"

    names = sorted(touched)
    if len(names) > MAX_SCOPES:
        head = ", ".join(names[:MAX_SCOPES])
        return f"{verb}: {head} +{len(names) - MAX_SCOPES}"
    return f"{verb}: {', '.join(names)}"


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: changes.py changelog|subject [old] [new]")
    mode = sys.argv[1]
    old_rev = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    new_rev = sys.argv[3] if len(sys.argv) > 3 else None
    if mode == "changelog":
        print(changelog(old_rev, new_rev))
    elif mode == "subject":
        print(subject(old_rev, new_rev))
    else:
        raise SystemExit(f"unknown mode: {mode}")


if __name__ == "__main__":
    main()
