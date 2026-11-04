#!/usr/bin/env python3
"""Забор маршрута разработки: этап N не начинается, пока в предыдущих есть пустой чекбокс.

  route.py init <ROUTE.md> --name X [--track full|lite|feature]
  route.py status <ROUTE.md>
  route.py gate <ROUTE.md> <N>      exit 0 — можно начинать этап N, exit 1 — нельзя
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "references" / "route-template.md"
TRACKS = {"full": [1, 2, 3, 4, 5, 6, 7, 8], "lite": [1, 3, 4, 6, 7, 8], "feature": [3, 4, 6, 7]}
HEAD = re.compile(r"^## (\d+)\. ", re.M)


def split(text):
    """-> (шапка, [(номер, текст_секции)])"""
    parts = HEAD.split(text)
    return parts[0], [(int(parts[i]), f"## {parts[i]}. {parts[i + 1]}") for i in range(1, len(parts), 2)]


def open_items(section):
    return [l.strip()[6:] for l in section.splitlines() if l.strip().startswith("- [ ] ")]


def cmd_init(a):
    p = Path(a.route)
    if p.exists():
        sys.exit(f"{p} уже есть — не затираю")
    head, secs = split(TEMPLATE.read_text())
    head = head.format(name=a.name, track=a.track, date=datetime.date.today().isoformat())
    p.write_text(head + "".join(s for n, s in secs if n in TRACKS[a.track]))
    print(f"создан {p}, этапы {TRACKS[a.track]}")


def cmd_status(a):
    _, secs = split(Path(a.route).read_text())
    for n, s in secs:
        items = open_items(s)
        if items:
            print(f"Текущий этап: {s.splitlines()[0][3:]}")
            for i in items:
                print(f"  [ ] {i}")
            return
    print("Все этапы закрыты.")


def cmd_gate(a):
    _, secs = split(Path(a.route).read_text())
    nums = [n for n, _ in secs]
    if a.stage not in nums:
        sys.exit(f"этапа {a.stage} нет в этом маршруте (есть {nums})")
    blocked = [(s.splitlines()[0][3:], open_items(s)) for n, s in secs if n < a.stage and open_items(s)]
    if not blocked:
        print(f"Этап {a.stage}: можно.")
        return
    print(f"Этап {a.stage}: НЕЛЬЗЯ. Не закрыто:")
    for title, items in blocked:
        print(f"  {title}")
        for i in items:
            print(f"    [ ] {i}")
    sys.exit(1)


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
p = sub.add_parser("init")
p.add_argument("route")
p.add_argument("--name", required=True)
p.add_argument("--track", choices=TRACKS, default="full")
p.set_defaults(f=cmd_init)
p = sub.add_parser("status")
p.add_argument("route")
p.set_defaults(f=cmd_status)
p = sub.add_parser("gate")
p.add_argument("route")
p.add_argument("stage", type=int)
p.set_defaults(f=cmd_gate)
a = ap.parse_args()
a.f(a)
