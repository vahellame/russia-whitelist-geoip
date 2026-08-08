#!/usr/bin/env python3
import json
import pathlib
import sys

SKIP = {"trash"}


def read_cidrs(path):
    values = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        values.append(line if "/" in line else line + "/32")
    return sorted(set(values))


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: ruleset.py <data/final dir> <outdir>")

    src = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)

    for path in sorted(src.iterdir()):
        if not path.is_file() or path.name in SKIP:
            continue
        cidrs = read_cidrs(path)
        if not cidrs:
            print(f"skip empty: {path.name}")
            continue
        name = f"geoip-{path.name}"

        srs = {"version": 3, "rules": [{"ip_cidr": cidrs}]}
        (out / f"{name}.srs.json").write_text(
            json.dumps(srs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (out / f"{name}.mrs.txt").write_text("\n".join(cidrs) + "\n", encoding="utf-8")
        (out / f"{name}.list").write_text(
            "\n".join(f"IP-CIDR,{c},no-resolve" for c in cidrs) + "\n", encoding="utf-8"
        )
        print(f"{name}: {len(cidrs)} cidr")


if __name__ == "__main__":
    main()
