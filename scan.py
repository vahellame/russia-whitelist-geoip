from __future__ import annotations

import ipaddress
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import NamedTuple

import nmap

WORKERS = 1
HTTPS_PORT = 443
GAP = 4

NMAP_TIMING = "-T4"

DATA_DIR = Path("data")
LISTS = tuple(sorted(
    entry.name for entry in DATA_DIR.iterdir() if entry.is_file() and not entry.name.startswith(".")
)) if DATA_DIR.is_dir() else ()
NAME_WIDTH = max((len(name) for name in LISTS), default=0)

_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0
PORT_SCAN = "-sS" if _ROOT else "-sT"
NMAP_OPTS = f"-n {NMAP_TIMING}"


class Tally(NamedTuple):
    icmp: int
    https: int
    seconds: float


def duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes}m{rest:02d}s"


def is_ipv4_cidr(line: str) -> bool:
    text = line.strip()
    if not text or text.startswith("#"):
        return False
    try:
        return isinstance(ipaddress.ip_network(text, strict=False), ipaddress.IPv4Network)
    except ValueError:
        return False


def scan(subnet: str) -> Tally:
    start = time.monotonic()
    scanner = nmap.PortScanner()

    scanner.scan(hosts=subnet, arguments=f"-sn -PE {NMAP_OPTS}")
    icmp = sum(1 for host in scanner.all_hosts() if scanner[host].state() == "up")

    scanner.scan(hosts=subnet, ports=str(HTTPS_PORT), arguments=f"-Pn {PORT_SCAN} {NMAP_OPTS}")
    https = sum(
        1
        for host in scanner.all_hosts()
        if scanner[host].get("tcp", {}).get(HTTPS_PORT, {}).get("state") == "open"
    )
    return Tally(icmp=icmp, https=https, seconds=time.monotonic() - start)


def align(lines: list[str], results: dict[str, Tally]) -> list[str]:
    annotated = [(line.strip(), results[line.strip()]) for line in lines if is_ipv4_cidr(line)]
    if not annotated:
        return lines

    def head(cidr: str, tally: Tally) -> str:
        return cidr if tally.https > 0 else f"# {cidr}"

    anno_col = max(len(head(cidr, tally)) for cidr, tally in annotated) + GAP
    https_width = max(len(str(tally.https)) for _, tally in annotated)

    out = []
    for line in lines:
        if not is_ipv4_cidr(line):
            out.append(line)
            continue
        cidr = line.strip()
        tally = results[cidr]
        body = f"tcp-{HTTPS_PORT}: {tally.https:<{https_width}}  icmp: {tally.icmp}"
        out.append(f"{head(cidr, tally).ljust(anno_col)}# {body}")
    return out


def process(path: Path, pool: ThreadPoolExecutor) -> None:
    lines = path.read_text().splitlines()
    subnets = list(dict.fromkeys(line.strip() for line in lines if is_ipv4_cidr(line)))

    total = len(subnets)
    index_width = len(str(total))
    subnet_width = max((len(subnet) for subnet in subnets), default=0)

    results: dict[str, Tally] = {}
    futures = {pool.submit(scan, subnet): subnet for subnet in subnets}
    for completed, future in enumerate(as_completed(futures), start=1):
        subnet = futures[future]
        results[subnet] = future.result()
        tally = results[subnet]
        prefix = f"[{path.name}]".ljust(NAME_WIDTH + 2)
        print(f"{prefix}  {subnet:<{subnet_width}}  "
              f"tcp-{HTTPS_PORT}: {tally.https:<3}  icmp: {tally.icmp:<3}  "
              f"time: {duration(tally.seconds):<6}  {completed:>{index_width}}/{total}", file=sys.stderr)

    path.write_text("\n".join(align(lines, results)) + "\n")
    print(f"edited {path}", file=sys.stderr)


def preflight() -> None:
    try:
        nmap.PortScanner()
    except nmap.PortScannerError:
        sys.exit("nmap binary not found; install it (apt install nmap / brew install nmap).")
    if not _ROOT:
        print("note: run with sudo — ICMP (-PE) and SYN scan (-sS) need root; "
              "without it ICMP is unreliable and 443 falls back to a full connect",
              file=sys.stderr)


def main() -> None:
    preflight()
    if not LISTS:
        sys.exit(f"no files in {DATA_DIR}/ — run fetch_split.py first")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for name in LISTS:
            process(DATA_DIR / name, pool)


if __name__ == "__main__":
    main()