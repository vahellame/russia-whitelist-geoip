from __future__ import annotations

import ipaddress
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import nmap

WORKERS = 1
HTTPS_PORT = 443
NMAP_TIMING = "-T4"

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
NORMAL_DIR = BASE_DIR / "data" / "normal"
WL_DIR = BASE_DIR / "data" / "wl"

LISTS = tuple(sorted(
    entry.name for entry in RAW_DIR.iterdir() if entry.is_file() and not entry.name.startswith(".")
)) if RAW_DIR.is_dir() else ()
NAME_WIDTH = max((len(name) for name in LISTS), default=0)

_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0
PORT_SCAN = "-sS" if _ROOT else "-sT"
NMAP_OPTS = f"-n {NMAP_TIMING}"


def is_ipv4_cidr(line: str) -> bool:
    text = line.strip()
    if not text or text.startswith("#"):
        return False
    try:
        return isinstance(ipaddress.ip_network(text, strict=False), ipaddress.IPv4Network)
    except ValueError:
        return False


def scan(subnet: str) -> list[str]:
    scanner = nmap.PortScanner()
    scanner.scan(hosts=subnet, ports=str(HTTPS_PORT), arguments=f"-Pn {PORT_SCAN} {NMAP_OPTS}")
    hosts = [
        host for host in scanner.all_hosts()
        if scanner[host].get("tcp", {}).get(HTTPS_PORT, {}).get("state") == "open"
    ]
    return sorted(hosts, key=ipaddress.IPv4Address)


def render(subnet: str, hosts: list[str]) -> str:
    return f"{subnet}  #" + (" " + " ".join(hosts) if hosts else "")


def process(name: str, out_dir: Path, pool: ThreadPoolExecutor) -> None:
    lines = (RAW_DIR / name).read_text().splitlines()
    subnets = list(dict.fromkeys(line.strip() for line in lines if is_ipv4_cidr(line)))

    total = len(subnets)
    index_width = len(str(total))
    subnet_width = max((len(subnet) for subnet in subnets), default=0)

    results: dict[str, list[str]] = {}
    futures = {pool.submit(scan, subnet): subnet for subnet in subnets}
    for completed, future in enumerate(as_completed(futures), start=1):
        subnet = futures[future]
        results[subnet] = future.result()
        prefix = f"[{name}]".ljust(NAME_WIDTH + 2)
        print(f"{prefix}  {subnet:<{subnet_width}}  443 open: {len(results[subnet]):<3}  "
              f"{completed:>{index_width}}/{total}", file=sys.stderr)

    body = "\n".join(render(subnet, results[subnet]) for subnet in subnets)
    (out_dir / name).write_text(body + "\n")
    print(f"wrote {out_dir / name}", file=sys.stderr)


def preflight() -> None:
    try:
        nmap.PortScanner()
    except nmap.PortScannerError:
        sys.exit("nmap binary not found; install it (apt install nmap / brew install nmap).")
    if not _ROOT:
        print("note: run with sudo for a SYN scan (-sS); without root, 443 is checked with a full connect (-sT)",
              file=sys.stderr)


def main() -> None:
    preflight()
    if not LISTS:
        sys.exit(f"no files in {RAW_DIR}/ — run fetch.py first")

    try:
        answer = input("Scan through the whitelist? [y/N] ").strip().lower()
    except EOFError:
        answer = ""
    out_dir = WL_DIR if answer == "y" else NORMAL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"writing results to {out_dir}/", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for name in LISTS:
            process(name, out_dir, pool)


if __name__ == "__main__":
    main()