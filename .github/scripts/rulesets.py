#!/usr/bin/env python3
import json
import pathlib
import sys

CATEGORIES = [
    "cdnvideo",
    "curator",
    "ddos-guard",
    "edgecenter",
    "ngenix",
    "other",
    "servicepipe",
    "stormwall",
    "vk",
    "yandex",
    "category-public-dns",
    "private",
]


def read_cidrs(path):
    values = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        values.append(line if "/" in line else line + "/32")
    return sorted(set(values))


def write_set(name, cidrs, outdir):
    srs = {"version": 3, "rules": [{"ip_cidr": cidrs}] if cidrs else []}
    (outdir / f"{name}.srs.json").write_text(
        json.dumps(srs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (outdir / f"{name}.mrs.txt").write_text("\n".join(cidrs) + "\n", encoding="utf-8")
    (outdir / f"{name}.list").write_text(
        "\n".join(f"IP-CIDR,{c},no-resolve" for c in cidrs) + "\n", encoding="utf-8"
    )
    print(f"{name}: {len(cidrs)} cidr")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: rulesets.py <data/final> <outdir>")
    src = pathlib.Path(sys.argv[1])
    outdir = pathlib.Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    for category in CATEGORIES:
        path = src / category
        if not path.exists():
            raise SystemExit(f"missing category: {path}")
        write_set(f"geoip-{category}", read_cidrs(path), outdir)


if __name__ == "__main__":
    main()
