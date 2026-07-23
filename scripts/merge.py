from __future__ import annotations

import ipaddress
import sys
from pathlib import Path

# Коэффициент совпадения для сохранения всей /24
MIN_MATCH_RATIO = 0.5

BASE_DIR = Path(__file__).resolve().parent.parent
NORMAL_DIR = BASE_DIR / "data" / "normal"
WL_DIR = BASE_DIR / "data" / "wl"
FINAL_DIR = BASE_DIR / "data" / "final"


def parse(path: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    if not path.exists():
        return result

    for line in path.read_text().splitlines():
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

        if cidr:
            result[cidr] = hosts

    return result


def decide(normal_hosts: list[str], wl_hosts: list[str]) -> tuple[str, list[str]]:
    if not normal_hosts:
        return "dead", []

    if not wl_hosts:
        return "blocked", []

    ratio = len(wl_hosts) / len(normal_hosts)
    if ratio >= MIN_MATCH_RATIO:
        return "kept", []

    return "reduced", wl_hosts


def sort_key(net: ipaddress.IPv4Network) -> tuple[int, int]:
    return (int(net.network_address), net.prefixlen)


def merge(name: str) -> None:
    normal = parse(NORMAL_DIR / name)
    wl = parse(WL_DIR / name)

    # Сортируем исходные /24 по IP
    all_cidrs = sorted(
        normal.keys(),
        key=lambda x: int(ipaddress.ip_network(x, strict=False).network_address),
    )

    raw_networks: list[ipaddress.IPv4Network] = []
    counts = {"kept": 0, "reduced": 0, "blocked": 0, "dead": 0}

    for cidr in all_cidrs:
        normal_hosts = normal.get(cidr, [])
        wl_hosts = wl.get(cidr, [])

        outcome, hosts = decide(normal_hosts, wl_hosts)
        counts[outcome] += 1

        if outcome == "kept":
            raw_networks.append(ipaddress.ip_network(cidr, strict=False))
        elif outcome == "reduced":
            for host in hosts:
                raw_networks.append(ipaddress.ip_network(f"{host}/32"))

    # Схлопываем смежные /32 в /31, /30, /29 и т.д.
    collapsed_networks = sorted(
        ipaddress.collapse_addresses(raw_networks), key=sort_key
    )

    out_lines = [str(net) for net in collapsed_networks]

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    (FINAL_DIR / name).write_text(
        "\n".join(out_lines) + ("\n" if out_lines else "")
    )

    print(
        f"{name}: {counts['kept']} kept as /24, "
        f"{counts['reduced']} reduced to /32, "
        f"{counts['blocked']} blocked, "
        f"{counts['dead']} dead "
        f"-> collapsed to {len(out_lines)} subnets",
        file=sys.stderr,
    )


def main() -> None:
    if not NORMAL_DIR.is_dir() and not WL_DIR.is_dir():
        sys.exit("Ни один из каталогов с результатами сканирования не найден.")

    lists = sorted(
        {
            entry.name
            for d in (NORMAL_DIR, WL_DIR)
            if d.is_dir()
            for entry in d.iterdir()
            if entry.is_file() and not entry.name.startswith(".")
        }
    )

    if not lists:
        sys.exit("Файлы результатов не найдены.")

    for name in lists:
        merge(name)


if __name__ == "__main__":
    main()