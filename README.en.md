[Русский](README.md)

More: https://github.com/vahellame/russia-whitelist-routing

Filtered IPv4 **/24** ranges of whitelisted Russian CDN and DDoS-protection providers, compiled into a `geoip.dat` for Xray/V2Ray routing.

**How they're built:** `fetch.py` retrieves each service's announced prefixes from RIPEstat and divides them into /24s. `scan.py` then checks every /24 and keeps only those where at least one host answers ICMP or a TCP SYN on port 443; unreachable /24s are excluded.

Scanning requires the python-nmap library.

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
https://github.com/vahellame/russia-whitelist-routing/releases/latest/download/geoip.dat
```