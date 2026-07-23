[Русский](README.md)

More: https://github.com/vahellame/russia-whitelist-geoip

Filtered IPv4 ranges of whitelisted Russian CDN and DDoS-protection providers, compiled into a `geoip.dat` for Xray/V2Ray.

**How they're built:**

1. `scripts/fetch.py` retrieves each service's announced prefixes from RIPEstat and divides them into `/24`s, removing duplicates (a `/24` announced both on its own and inside a larger prefix) → `data/raw/`.
2. `scripts/scan.py` scans every `/24` on port 443 (needs the `python-nmap` library) and is run twice: without the whitelist → `data/normal/`, and routed through the whitelist → `data/wl/`. It prompts `Scan through the whitelist? [y/N]` on start.
3. `scripts/merge.py` compares both results into `data/final/`: if the whitelist reaches roughly as many hosts as without it, the `/24` is kept whole; if it reaches meaningfully fewer, only the hosts actually reachable through the whitelist are kept, as individual /32s; if neither reaches anything, the range is dropped.
4. On every push, GitHub Actions compiles `data/final/` into `geoip.dat`.

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

```
https://github.com/vahellame/russia-whitelist-geoip/releases/latest/download/geoip.dat
```