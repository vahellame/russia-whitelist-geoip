from __future__ import annotations

import ipaddress
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Iterator

RIPESTAT = "https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{asn}"
REQUEST_DELAY = 0.3
DATA_DIR = Path("data")

PROVIDERS: dict[str, tuple[int, ...]] = {
    "cdnvideo": (57363, 204720),
    "curator": (51115,),  # 197068, 200449, 209671, 211112 are not in whitelists
    "ddos-guard": (57724,),
    "edgecenter": (210756,),
    "ngenix": (34879,),
    "servicepipe": (201706,),
    "stormwall": (43298,),  # 59796 are not in whitelists
}


def announced_ipv4(asn: int) -> list[ipaddress.IPv4Network]:
    request = urllib.request.Request(RIPESTAT.format(asn=asn), headers={"User-Agent": "prefix-fetch/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    networks = {
        network
        for prefix in payload["data"]["prefixes"]
        if isinstance(network := ipaddress.ip_network(prefix["prefix"], strict=False), ipaddress.IPv4Network)
    }
    return sorted(networks, key=lambda net: (int(net.network_address), net.prefixlen))


def expand(networks: list[ipaddress.IPv4Network], emitted: set[str]) -> Iterator[str]:
    for network in networks:
        if network.prefixlen < 24:
            fresh = [str(subnet) for subnet in network.subnets(new_prefix=24) if str(subnet) not in emitted]
            if not fresh:
                continue
            yield f"# {network} exposed"
            for subnet in fresh:
                emitted.add(subnet)
                yield subnet
        else:
            key = str(network)
            if key not in emitted:
                emitted.add(key)
                yield key


def render(asns: tuple[int, ...]) -> str:
    emitted: set[str] = set()
    blocks = []
    for asn in asns:
        try:
            networks = announced_ipv4(asn)
        except Exception as error:
            print(f"failed AS{asn}: {error}", file=sys.stderr)
            networks = []
        time.sleep(REQUEST_DELAY)
        blocks.append("\n".join([f"# https://stat.ripe.net/AS{asn}", *expand(networks, emitted)]))
    return "\n\n".join(blocks) + "\n"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, asns in PROVIDERS.items():
        target = DATA_DIR / name
        target.write_text(render(asns))
        subnet_count = sum(1 for line in target.read_text().splitlines() if line and not line.startswith("#"))
        print(f"{target}: {subnet_count} /24 subnets", file=sys.stderr)


if __name__ == "__main__":
    main()