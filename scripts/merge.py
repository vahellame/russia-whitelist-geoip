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

        # Если есть решетка, делим по ней
        if "#" in line:
            cidr_part, _, hosts_part = line.partition("#")
            cidr = cidr_part.strip()
            hosts = hosts_part.split()
        else:
            # Если решетки нет, первое слово — это CIDR, остальные — хосты
            parts = line.split()
            cidr = parts[0]
            hosts = parts[1:]

        if cidr:
            result[cidr] = hosts

    return result

def decide(normal_hosts: list[str], wl_hosts: list[str]) -> tuple[str, list[str]]:
    if not normal_hosts and not wl_hosts:
        return "dead", []

    if not normal_hosts and wl_hosts:
        # Недоступно снаружи, но работает через вайтлист
        return "wl-only", wl_hosts

    if normal_hosts and not wl_hosts:
        # Доступно снаружи, но полностью заблокировано/недоступно через вайтлист
        return "blocked", []

    # Если доступны оба скана, смотрим на отношение доступных хостов через WL к обычному скану
    ratio = len(wl_hosts) / len(normal_hosts)
    if ratio >= MIN_MATCH_RATIO:
        return "kept", []  # Оставляем подсеть /24 целиком

    return "reduced", wl_hosts


def sort_key(entry: str) -> tuple[int, int]:
    network = ipaddress.ip_network(entry, strict=False)
    return (int(network.network_address), network.prefixlen)


def merge(name: str) -> None:
    normal = parse(NORMAL_DIR / name)
    wl = parse(WL_DIR / name)

    # Собираем все уникальные CIDR из обоих сканов
    all_cidrs = sorted(set(normal.keys()) | set(wl.keys()), key=sort_key)

    out: list[str] = []
    counts = {"kept": 0, "reduced": 0, "wl-only": 0, "blocked": 0, "dead": 0}

    for cidr in all_cidrs:
        normal_hosts = normal.get(cidr, [])
        wl_hosts = wl.get(cidr, [])

        outcome, hosts = decide(normal_hosts, wl_hosts)
        counts[outcome] += 1

        if outcome == "kept":
            out.append(cidr)
        elif outcome in ("reduced", "wl-only"):
            out.extend(f"{host}/32" for host in hosts)

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    (FINAL_DIR / name).write_text("\n".join(sorted(out, key=sort_key)) + ("\n" if out else ""))

    print(
        f"{name}: {counts['kept']} kept as /24, "
        f"{counts['reduced']} reduced to /32, "
        f"{counts['wl-only']} wl-only /32, "
        f"{counts['blocked']} blocked, "
        f"{counts['dead']} dead",
        file=sys.stderr
    )


def main() -> None:
    if not NORMAL_DIR.is_dir() and not WL_DIR.is_dir():
        sys.exit("Ни один из каталогов с результатами сканирования не найден.")

    lists = sorted({
        entry.name for d in (NORMAL_DIR, WL_DIR) if d.is_dir()
        for entry in d.iterdir() if entry.is_file() and not entry.name.startswith(".")
    })

    if not lists:
        sys.exit("Файлы результатов не найдены.")

    for name in lists:
        merge(name)


if __name__ == "__main__":
    main()