[Русский](README.md)

Main project: https://github.com/vahellame/russia-whitelist-routing

Filtered IPv4 ranges of whitelisted Russian CDN and DDoS-protection providers, compiled into a `geoip.dat` for Xray/V2Ray.

**How they're built:**

1. `scripts/fetch.py` retrieves each service's announced prefixes from RIPEstat and divides them into `/24`s, removing duplicates (a `/24` announced both on its own and inside a larger prefix) → `data/raw/`.
2. `scripts/scan.py` scans every `/24` on port 443 sequentially in a single thread (requires `python-nmap`) and is run twice: first without the whitelist → `data/normal/`, then routed through the whitelist → `data/wl/`. When running through the whitelist, it automatically skips subnets that had no active hosts during the normal scan.
3. `scripts/merge.py` compares both results into `data/final/`. The decision to keep a subnet is based on a reachability coefficient (`ratio` = available hosts in `wl` / available hosts in `normal`). Analysis of real scans revealed a clear bimodal distribution: a gap between ~0.16 (actual whitelist restrictions) and ~0.80+ (scanning noise). Based on this, a threshold of `MIN_MATCH_RATIO = 0.5` is set, sitting right in the middle of this gap. If `ratio` ≥ 0.5, the `/24` is kept whole (interpreted as noise, not a real restriction); if `ratio` < 0.5 but `wl > 0`, only the hosts actually reachable through the whitelist are kept as individual `/32`s, which are then automatically collapsed into optimal CIDR blocks (`/31`, `/30`, etc.); if neither reaches anything, the range is dropped.
4. On every push into `main`, GitHub Actions compiles `data/final/` into `geoip.dat`.

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

## Download

```text
https://github.com/vahellame/russia-whitelist-geoip/releases/latest/download/geoip.dat
```