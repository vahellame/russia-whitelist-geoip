[Русский](README.md)

Main project: https://github.com/vahellame/russia-whitelist-routing

## What this is

Filtered IPv4 ranges of whitelisted Russian CDN and DDoS-protection providers. Compiled into a `geoip.dat` for Xray and into `.srs`, `.mrs` and `.list` rule sets for sing-box, mihomo and Shadowrocket, one set per category

Every release ships a `geoip.dat.sha256` — the bare hash, 64 characters with no filename. INCY uses it to tell the file has not changed and skips re-downloading it. More on it [here](https://docs.incy.cc/en/routing/#geo-files-optimized-downloading). Alongside it, `geoip.dat.sha256sum` in the standard GNU coreutils format

## How they are built

1. `scripts/fetch.py` retrieves each service's announced prefixes from RIPEstat and divides them into `/24`s, removing duplicates (a `/24` announced both on its own and inside a larger prefix) → `data/raw/`
2. `scripts/scan.py` scans every `/24` on port 443 sequentially in a single thread (requires `python-nmap`) and is run twice: first without the whitelist → `data/normal/`, then routed through the whitelist → `data/wl/`. When running through the whitelist, it automatically skips subnets that had no active hosts during the normal scan
3. Going through every `/24` by hand and submitting to [BSCHEKER](https://t.me/bschekbot), [Latency Lab](https://t.me/Latency_Lab_bot) and [Checkburnet](https://t.me/checkburbot) only those where the difference in reachable hosts between `normal` and `wl` stays within statistical noise
4. Going through every `/24` by hand and adding in those same bots only those where the difference between carriers stays within statistical noise
5. Collapsing `/24`s where possible
6. On every push into `main`, GitHub Actions compiles `data/final/` into `geoip.dat` and the rule sets

The bot dumps behind the decisions in steps 3 and 4 are kept in `scans`

## Services

| Service | ASNs |
|---|---|
| `cdnvideo` | AS57363, AS204720 |
| `curator` | AS51115 |
| `ddos-guard` | AS57724 |
| `edgecenter` | AS210756 |
| `ngenix` | AS34879 |
| `servicepipe` | AS201706 |
| `stormwall` | AS43298 |

The `vk`, `yandex` and `other` categories are in progress, ranges there are added one by one