[English](README.en.md)

Основной проект: https://github.com/vahellame/russia-whitelist-routing

Отфильтрованные IPv4 диапазоны находящихся в белых списках российских CDN и DDoS-защит, собранные в `geoip.dat` для Xray/V2Ray.

**Как формируются:**

1. `scripts/fetch.py` получает анонсируемые префиксы каждого сервиса из RIPEstat и делит их на `/24`, убирая дубликаты (когда `/24` анонсируется и отдельно, и в составе более крупного префикса) → `data/raw/`.
2. `scripts/scan.py` сканирует каждую `/24` на 443 порт последовательно в один поток (нужна библиотека `python-nmap`) и запускается дважды: сначала без вайтлиста → `data/normal/`, затем через вайтлист → `data/wl/`. При сканировании через вайтлист скрипт автоматически пропускает подсети, в которых в `normal` не было найдено ни одного активного хоста. 
3. 
4. На каждый push в `main` GitHub Actions собирает `data/final/` в `geoip.dat`.

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

```text
https://github.com/vahellame/russia-whitelist-geoip/releases/latest/download/geoip.dat
```