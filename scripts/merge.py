from __future__ import annotations

import ipaddress
import sys
from pathlib import Path

# Two scans of the same /24 rarely return the exact same count even when the
# subnet is fully reachable both ways — nmap loses a handful of replies to
# timing/rate-limiting. Comparing raw scan pairs shows a clean split: subnets
# that are genuinely as reachable through the whitelist sit at 80-100% of the
# non-whitelist count, while subnets the whitelist actually restricts drop to
# under ~20%. MIN_MATCH_RATIO sits in that gap.
MIN_MATCH_RATIO = 0.5

BASE_DIR = Path(__file__).resolve().parent.parent
NORMAL_DIR = BASE_DIR / "data" / "normal"
WL_DIR = BASE_DIR / "data" / "wl"
FINAL_DIR = BASE_DIR / "data" / "final"

LISTS = tuple(sorted(
    entry.name for entry in NORMAL_DIR.iterdir() if entry.is_file() and not entry.name.startswith(".")
)) if NORMAL_DIR.is_dir() else ()


def parse(path: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    if not path.exists():
        return result
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        cidr, _, rest = line.partition("#")
        result[cidr.strip()] = rest.split()
    return result


def decide(normal_hosts: list[str], wl_hosts: list[str]) -> tuple[str, list[str]]:
    if not normal_hosts and not wl_hosts:
        return "dead", []
    if not normal_hosts:
        # unreachable outside the whitelist but reachable through it — keep the hosts we found
        return "wl-only", wl_hosts
    if len(wl_hosts) / len(normal_hosts) >= MIN_MATCH_RATIO:
        return "kept", []  # caller substitutes the whole /24
    if wl_hosts:
        return "reduced", wl_hosts
    return "dead", []


def sort_key(entry: str) -> tuple[int, int]:
    network = ipaddress.ip_network(entry, strict=False)
    return (int(network.network_address), network.prefixlen)


def merge(name: str) -> None:
    normal = parse(NORMAL_DIR / name)
    wl = parse(WL_DIR / name)

    out: list[str] = []
    counts = {"kept": 0, "reduced": 0, "wl-only": 0, "dead": 0}
    for cidr, normal_hosts in normal.items():
        outcome, hosts = decide(normal_hosts, wl.get(cidr, []))
        counts[outcome] += 1
        if outcome == "kept":
            out.append(cidr)
        elif outcome in ("reduced", "wl-only"):
            out.extend(f"{host}/32" for host in hosts)

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    (FINAL_DIR / name).write_text("\n".join(sorted(out, key=sort_key)) + "\n")
    print(f"{name}: {counts['kept']} kept as /24, {counts['reduced']} reduced to /32, "
          f"{counts['wl-only']} wl-only /32, {counts['dead']} dead", file=sys.stderr)


def main() -> None:
    if not NORMAL_DIR.is_dir():
        sys.exit(f"no {NORMAL_DIR}/ — run scan.py without the whitelist first")
    if not WL_DIR.is_dir():
        sys.exit(f"no {WL_DIR}/ — run scan.py through the whitelist too")
    if not LISTS:
        sys.exit(f"no files in {NORMAL_DIR}/")
    for name in LISTS:
        merge(name)


if __name__ == "__main__":
    main()