# russia-whitelist-routing

[English](README.en.md)

Подробнее: https://github.com/vahellame/russia-whitelist-routing

Отфильтрованные IPv4 **/24** диапазоны находящихся в белых списках российских CDN и DDoS-защит, собранные в `geoip.dat` для роутинга Xray/V2Ray.

**Как формируются:** `fetch.py` получает анонсируемые префиксы каждого сервиса из RIPEstat и делит их на /24. `scan.py` проверяет каждую /24 и оставляет только те, где хотя бы один хост ответил на ICMP или TCP-SYN на порт 443; недоступные /24 исключаются.

Для сканирования необходима библиотека `python-nmap`

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
https://github.com/vahellame/russia-whitelist-routing/releases/latest/download/geoip.dat
```