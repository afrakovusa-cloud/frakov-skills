#!/usr/bin/env python3
"""Страж цен Магнита: сказать пользователю, когда товар реально подешевел.

Зачем (11.11, просьба пользователя: «Страж цен круто»): у нас копится журнал цен
(~/.magnit/magnit_prices.jsonl, его наполняет magnit-prices.timer в 09:00).
Страж сравнивает сегодняшнюю цену с медианой прошлых дней и пишет только о
настоящих падениях — молчит, когда сказать нечего.

Правила:
  - нужно ≥3 прошлых дня, иначе не знаем, что «обычно» (пишем об этом в лог и молчим);
  - падение = цена ниже медианы больше чем на порог (по умолчанию 15%);
  - одна и та же позиция с той же ценой второй раз не присылается (state-файл);
  - если цена упала ещё ниже прежней — присылается снова;
  - отправка — через remind.py notify (служебное сообщение, без ⏰).

Запуск: python3 magnit_watch.py [--min-pct 15] [--days 3] [--dry]
"""
import argparse
import json
import os
import subprocess
import sys

JOURNAL = os.path.expanduser("~/.magnit/magnit_prices.jsonl")
STATE = os.path.expanduser("~/.magnit/magnit_watch_state.json")
NOTIFY = os.path.expanduser("remind.py")


def load_journal(path=JOURNAL):
    """{id: {'name': str, 'days': [(дата, цена), ...]}} — битые строки пропускаем."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                gid, d, p = r["id"], r["d"], r["p"]
            except (ValueError, KeyError):
                continue
            item = out.setdefault(gid, {"name": r.get("n", ""), "days": []})
            if r.get("n"):
                item["name"] = r["n"]
            item["days"].append((d, p))
    return out


def find_drops(journal, min_pct=15, need_days=3):
    """Список падений: (id, имя, медиана, цена, скидка_%) — по свежей дате журнала."""
    rows = []
    for gid, item in journal.items():
        days = sorted(item["days"])
        if len(days) < need_days + 1:
            continue
        today = days[-1]
        past = sorted(p for _d, p in days[:-1])
        if not past or today[1] <= 0:
            continue
        median = past[len(past) // 2]
        if median <= 0:
            continue
        pct = round((1 - today[1] / median) * 100)
        if pct >= min_pct:
            rows.append((gid, item["name"], median, today[1], pct))
    rows.sort(key=lambda r: -r[4])
    return rows


def load_state(path=STATE):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state, path=STATE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
    os.replace(tmp, path)


def fresh(rows, state):
    """Только то, о чём ещё не говорили (или цена стала ниже прежней)."""
    out = []
    for gid, name, median, price, pct in rows:
        if state.get(gid) == price:
            continue
        out.append((gid, name, median, price, pct))
    return out


def message(rows, limit=5):
    lines = ["💰 Магнит: реально подешевело"]
    for gid, name, median, price, pct in rows[:limit]:
        lines.append(f"• {name[:42]} — {price / 100:.2f} ₽ (−{pct}%, обычно {median / 100:.2f})")
    if len(rows) > limit:
        lines.append(f"…и ещё {len(rows) - limit}")
    return "\n".join(lines)


def send(text):
    try:
        subprocess.run(["python3", NOTIFY, "notify", text], capture_output=True, timeout=20)
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-pct", type=int, default=15)
    ap.add_argument("--days", type=int, default=3, help="сколько прошлых дней нужно")
    ap.add_argument("--dry", action="store_true", help="только показать, не отправлять")
    a = ap.parse_args()

    journal = load_journal()
    if not journal:
        print("журнала нет — сначала снимок: magnit_api.py --snapshot")
        return 0
    rows = find_drops(journal, a.min_pct, a.days)
    if not rows:
        print("падений нет — молчу")
        return 0
    state = load_state()
    rows = fresh(rows, state)
    if not rows:
        print(f"падений {len(find_drops(journal, a.min_pct, a.days))}, но о всех уже говорили")
        return 0
    text = message(rows)
    print(text)
    if a.dry:
        return 0
    if send(text):
        for gid, _n, _m, price, _p in rows:
            state[gid] = price
        save_state(state)
        print(f"отправлено: {len(rows)}")
    else:
        print("не смогла отправить — состояние не меняю, попробую в следующий раз")
    return 0


if __name__ == "__main__":
    sys.exit(main())
