[Русский](README.md)

Main project: https://github.com/vahellame/russia-whitelist-routing

Filtered IPv4 ranges of whitelisted Russian CDN and DDoS-protection providers, compiled into a `geoip.dat` for Xray/V2Ray.

**How they're built:**

1. `scripts/fetch.py` retrieves each service's announced prefixes from RIPEstat and divides them into `/24`s, removing duplicates (a `/24` announced both on its own and inside a larger prefix) → `data/raw/`.
2. `scripts/scan.py` scans every `/24` on port 443 sequentially in a single thread (requires `python-nmap`) and is run twice: first without the whitelist → `data/normal/`, then routed through the whitelist → `data/wl/`. When running through the whitelist, it automatically skips subnets that had no active hosts during the normal scan.
3. Going through every `/24` by hand and submitting to [BSCHEKER](https://t.me/bschekbot), [Latency Lab](https://t.me/Latency_Lab_bot) and [Checkburnet](https://t.me/checkburbot) only those where the difference in reachable hosts between `normal` and `wl` stays within statistical noise
4. Going through every `/24` by hand and adding in those same bots only those where the difference between carriers stays within statistical noise
5. Collapsing `/24`s where possible
6. On every push into `main`, GitHub Actions compiles `data/final/` into `geoip.dat`.

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

## In progress

- `vk`, `yandex` — ranges are added one by one rather than by ASN
- `other`

## The scans folder

Raw dumps the subnet decisions were based on

## Download

```text
https://github.com/vahellame/russia-whitelist-geoip/releases/latest/download/geoip.dat
```

## Checksums

Every release ships two checksums in different formats.

`geoip.dat.sha256` holds the bare hash — 64 characters, no filename, no trailing newline. This is the format INCY expects: it fetches the file on subscription update and skips downloading `geoip.dat` when the hash matches the one it already has. More on it [here](https://docs.incy.cc/en/routing/#geo-files-optimized-downloading)

`geoip.dat.sha256sum` is the standard GNU coreutils format, for manual verification:

```sh
sha256sum -c geoip.dat.sha256sum
```
