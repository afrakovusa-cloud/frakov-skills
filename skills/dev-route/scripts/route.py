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
TRACKS = {"full": [1, 2, 3, 4, 5, 6, 7, 8], "lite": [1, 3, 4, 6, 7, 8], "feature": [3, 4, 5, 6, 7]}
HEAD = re.compile(r"^## (\d+)\. ", re.M)
# Файлы, которые этап обязан оставить рядом с ROUTE.md: галочка без файла — не закрытый этап.
FILES = {1: ["BRIEF.md"], 2: ["RESEARCH.md"], 3: ["GRILL.md"], 4: ["PRD.md", "CONTEXT.md", "PHILOSOPHY.md"],
         5: ["REVIEW.md"], 6: ["CHECKLIST.md"]}
# Фича живёт в своей папке; словарь и философия — общие файлы проекта, их фича не заводит.
FILES_FEATURE = {3: ["FEATURE.md", "GRILL.md"], 4: ["PRD.md"], 5: ["REVIEW.md"], 6: ["CHECKLIST.md"]}
# Этап пропущен решением пользователя: строка `- [~] пропущено пользователем: … (дата)` — файлы этапа не нужны.
SKIPPED = re.compile(r"^\s*- \[~\] .*пропущено", re.M)


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
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(head + "".join(s for n, s in secs if n in TRACKS[a.track]))
    print(f"создан {p}, этапы {TRACKS[a.track]}")


def stages(route):
    """-> [(номер, заголовок, незакрытое)]: открытые галочки + нет файла этапа (если этап не пропущен)."""
    head, secs = split(Path(route).read_text())
    files = FILES_FEATURE if "Трек: feature" in head else FILES
    root = Path(route).parent
    out = []
    for n, s in secs:
        need = [] if SKIPPED.search(s) else files.get(n, [])
        out.append((n, s.splitlines()[0][3:], open_items(s) + [f"нет файла {f}" for f in need if not (root / f).exists()]))
    return out


def cmd_status(a):
    for n, title, items in stages(a.route):
        if items:
            print(f"Текущий этап: {title}")
            for i in items:
                print(f"  [ ] {i}")
            return
    print("Все этапы закрыты.")


def cmd_gate(a):
    st = stages(a.route)
    nums = [n for n, _, _ in st]
    if a.stage not in nums:
        sys.exit(f"этапа {a.stage} нет в этом маршруте (есть {nums})")
    blocked = [(title, items) for n, title, items in st if n < a.stage and items]
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
