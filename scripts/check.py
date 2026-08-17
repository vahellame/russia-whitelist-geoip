from __future__ import annotations

import ipaddress
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

API = "https://bsbord.com/v1"
TOKEN = os.environ.get("BSCHEKER_TOKEN", "")
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SKIP = {"trash", "private", "category-public-dns"}
BATCH = 10
PAUSE = 1.2
RETRIES = 3


def call(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
        headers["Idempotency-Key"] = str(uuid.uuid4())
    request = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def call_retrying(method: str, path: str, body: dict | None = None) -> dict:
    for attempt in range(RETRIES):
        try:
            return call(method, path, body)
        except urllib.error.HTTPError as exc:
            payload = {}
            try:
                payload = json.load(exc)
            except Exception:
                pass
            error = payload.get("error", {})
            code = error.get("code", str(exc.code))
            if exc.code in (429, 503) or code in ("busy", "request_in_progress"):
                delay = error.get("details", {}).get("retry_after") or 60
                if attempt == RETRIES - 1:
                    raise SystemExit(f"{code}: попытки исчерпаны")
                print(f"  {code}, повтор через {delay} с", file=sys.stderr)
                time.sleep(delay)
                continue
            raise SystemExit(f"{code}: {error.get('message', exc.reason)}")
    raise SystemExit("недостижимо")


def first_host(cidr: str) -> str:
    network = ipaddress.ip_network(cidr, strict=False)
    if network.num_addresses <= 2:
        return str(network.network_address)
    return str(next(network.hosts()))


def targets() -> list[tuple[str, str, str]]:
    out = []
    for path in sorted(DATA_DIR.iterdir()):
        if not path.is_file() or path.name in SKIP:
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if line:
                out.append((path.name, line, first_host(line)))
    return out


def main() -> None:
    if not TOKEN:
        raise SystemExit("нет BSCHEKER_TOKEN")

    wanted = set(sys.argv[1:])
    checks = [t for t in targets() if not wanted or t[0] in wanted]
    if not checks:
        raise SystemExit("нечего проверять")

    operators = [o["op_key"] for o in call_retrying("GET", "/v1/operators")["operators"]
                 if o["channel_state"] == "DPI_ON"]
    if not operators:
        raise SystemExit("нет операторов с включённым белым списком")
    print(f"операторов: {len(operators)}, целей: {len(checks)}\n")

    failures = []
    for start in range(0, len(checks), BATCH):
        chunk = checks[start:start + BATCH]
        answer = call_retrying("POST", "/v1/probe", {
            "targets": [host for _, _, host in chunk],
            "operators": operators,
            "probes": {"icmp": True, "tcp": True},
            "dpi": "on",
        })
        if answer.get("outcome") == "no_dpi_on":
            raise SystemExit("все каналы без белого списка")

        for category, cidr, host in chunk:
            by_operator = answer["by_target"].get(host, {}).get("by_operator", {})
            ok = sorted(op for op, r in by_operator.items() if r["ok"])
            bad = sorted(op for op, r in by_operator.items() if not r["ok"])
            mark = "OK  " if not bad else ("FAIL" if not ok else "PART")
            print(f"{mark} {category:20} {cidr:20} {len(ok)}/{len(by_operator)}"
                  + (f"  нет: {', '.join(bad)}" if bad else ""))
            if bad:
                failures.append((category, cidr, bad))
        time.sleep(PAUSE)

    print()
    if failures:
        print(f"проблемных сетей: {len(failures)}")
        for category, cidr, bad in failures:
            print(f"  {category}/{cidr}: {', '.join(bad)}")
    else:
        print("все сети доступны у всех операторов")


if __name__ == "__main__":
    main()
