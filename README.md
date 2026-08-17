Основной проект: https://github.com/vahellame/russia-whitelist-routing

## Что это

Отфильтрованные IPv4 диапазоны, находящиеся в белых списках РФ. Собираются в `geoip.dat` для Xray и в rule-set форматов `.srs`, `.mrs` и `.list` для sing-box, mihomo и Shadowrocket, отдельным набором на каждую категорию

К релизу прикладываются две контрольные суммы: `geoip.dat.sha256` с голым хешем на 64 символа, по которому INCY определяет, изменился ли файл ([подробнее](https://docs.incy.cc/routing/#геофайлы-оптимизированное-скачивание)), и `geoip.dat.sha256sum` в формате GNU coreutils

## Категории

`vk` и `yandex` содержат диапазоны этих сервисов, `other` — адреса, не попавшие в отдельные категории

`category-public-dns` содержит публичные DoH- и HTTPDNS-резолверы, их блокируют, чтобы клиент не резолвил домены в обход правил

`private` — локальные и служебные диапазоны

`trash` не входит ни в один профиль и существует ради того, чтобы `geoip.dat` не оказался меньше килобайта: Happ и INCY считают такой файл битым и показывают ошибку скачивания. Заполняется документационной сетью из RFC 5737, которая не маршрутизируется нигде

```sh
python3 scripts/trash.py                  # 192.0.2.0/24 по адресу
python3 scripts/trash.py 198.51.100.0/24  # другая сеть
```

## Проверка

`scripts/check.py` прогоняет сети из `data` через [BSCHEKER API](https://bsbord.com/llms.txt) и показывает, у каких операторов они не отвечают

```sh
export BSCHEKER_TOKEN=bsk_live_...
python3 scripts/check.py       # все категории
python3 scripts/check.py other # только одна
```

Из каждой сети берётся первый адрес, проверка идёт только по каналам с включённым белым списком. Списание с баланса аккаунта

Выгрузки из [BSCHEKER](https://t.me/bschekbot), [Latency Lab](https://t.me/Latency_Lab_bot) и [Чекбурнета](https://t.me/checkburbot), по которым принимались решения по подсетям, сохраняются в `scans`

Каждый push в `main` GitHub Actions собирает `data` в `geoip.dat` и rule-set
