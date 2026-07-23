from __future__ import annotations

import ipaddress
import os
import sys
from pathlib import Path

import nmap

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


def get_active_normal_subnets(name: str) -> set[str] | None:
    """Возвращает множество подсетей, у которых в normal-скане был хотя бы один живой хост."""
    normal_file = NORMAL_DIR / name
    if not normal_file.exists():
        return None

    active = set()
    for line in normal_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "#" in line:
            cidr_part, _, hosts_part = line.partition("#")
            cidr = cidr_part.strip()
            hosts = hosts_part.split()
        else:
            parts = line.split()
            cidr = parts[0]
            hosts = parts[1:]

        if hosts:
            active.add(cidr)

    return active


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


def process(name: str, out_dir: Path, is_wl: bool) -> None:
    lines = (RAW_DIR / name).read_text().splitlines()
    subnets = list(dict.fromkeys(line.strip() for line in lines if is_ipv4_cidr(line)))

    total = len(subnets)
    index_width = len(str(total))
    subnet_width = max((len(subnet) for subnet in subnets), default=0)

    active_normal_subnets = get_active_normal_subnets(name) if is_wl else None
    if is_wl and active_normal_subnets is None:
        print(f"[{name}] warning: normal scan results not found in {NORMAL_DIR / name}, scanning all subnets",
              file=sys.stderr)

    results: dict[str, list[str]] = {}

    for completed, subnet in enumerate(subnets, start=1):
        prefix = f"[{name}]".ljust(NAME_WIDTH + 2)

        # Если сканируем через WL и сеть была полностью мертва на normal — пропускаем вызов nmap
        if is_wl and active_normal_subnets is not None and subnet not in active_normal_subnets:
            results[subnet] = []
            print(f"{prefix}  {subnet:<{subnet_width}}  443 open: 0 (skipped dead)  "
                  f"{completed:>{index_width}}/{total}", file=sys.stderr)
            continue

        results[subnet] = scan(subnet)
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

    is_wl = answer == "y"
    out_dir = WL_DIR if is_wl else NORMAL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"writing results to {out_dir}/", file=sys.stderr)

    for name in LISTS:
        process(name, out_dir, is_wl)


if __name__ == "__main__":
    main()
