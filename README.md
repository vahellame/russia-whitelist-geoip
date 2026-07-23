Подробнее: https://github.com/vahellame/russia-whitelist-geoip

Отфильтрованные IPv4 диапазоны находящихся в белых списках российских CDN и DDoS-защит, собранные в `geoip.dat` для Xray/V2Ray.

**Как формируются:**

1. `scripts/fetch.py` получает анонсируемые префиксы каждого сервиса из RIPEstat и делит их на /24, убирая дубликаты (когда /24 анонсируется и отдельно, и в составе более крупного префикса) → `data/raw/`.
2. `scripts/scan.py` сканирует каждую /24 на 443 порт (нужна библиотека `python-nmap`) и запускается дважды: без вайтлиста → `data/normal/`, и через вайтлист → `data/wl/`. Перед стартом скрипт спрашивает `Scan through the whitelist? [y/N]`.
3. `scripts/merge.py` сравнивает оба результата и пишет `data/final/`: если через вайтлист доступно примерно столько же хостов, сколько и без него — /24 остаётся целиком; если заметно меньше — сохраняются только реально доступные `wl` `/32`, которые затем автоматический схлопываются в оптимальные CIDR-блоки (/31, /30 и т.д.); если диапазон недоступен — он исключается.
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