[English](README.en.md)

Подробнее: https://github.com/vahellame/russia-whitelist-geoip

Отфильтрованные IPv4 диапазоны находящихся в белых списках российских CDN и DDoS-защит, собранные в `geoip.dat` для Xray/V2Ray.

**Как формируются:**

1. `scripts/fetch.py` получает анонсируемые префиксы каждого сервиса из RIPEstat и делит их на /24, убирая дубликаты (когда /24 анонсируется и отдельно, и в составе более крупного префикса) → `data/raw/`.
2. `scripts/scan.py` сканирует каждую /24 на 443 (нужна библиотека `python-nmap`) и запускается дважды: без white-листа → `data/normal/`, и через white-лист → `data/wl/`. Перед стартом скрипт спрашивает `Scan through the whitelist? [y/N]`.
3. `scripts/merge.py` сравнивает оба результата и пишет `data/final/`: если через white-лист доступно примерно столько же хостов, сколько и без него — /24 остаётся целиком; если заметно меньше — в финал попадают только реально доступные через white-лист хосты, отдельными /32; если недоступна ни там, ни там — диапазон исключается.
4. На каждый push GitHub Actions собирает `data/final/` в `geoip.dat`.

## Список сервисов

| Сервис | ASN |
|---|---|
| `cdnvideo` | AS57363, AS204720 |
| `curator` | AS51115 |
| `ddos-guard` | AS57724 |
| `edgecenter` | AS210756 |
| `ngenix` | AS34879 |
| `servicepipe` | AS201706 |
| `stormwall` | AS43298 |

## Скачать

```
https://github.com/vahellame/russia-whitelist-geoip/releases/latest/download/geoip.dat
```