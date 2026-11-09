# -*- coding: utf-8 -*-
"""Тот же слепой набор, но фраза разбита на отдельные слова (>4 букв, без стоп-слов)."""
import os, re, sys
sys.path.insert(0, "/tmp")
from biz_blind import BOOKS, QUESTIONS, BLIND, texts  # noqa

STOP = {"vs.", "vs", "the", "and", "with", "your", "their", "into", "done", "right", "business"}

hits = top3 = 0
for (q, expected), terms in zip(QUESTIONS, BLIND):
    words = set()
    for t in terms:
        for w in re.findall(r"[a-z\-]{5,}", t.lower()):
            if w not in STOP:
                words.add(w)
    live = [w for w in words if any(w in txt for txt in texts.values())]
    scores = {f: sum(len(re.findall(re.escape(w), t)) for w in live) / (len(t) / 100_000)
              for f, t in texts.items()}
    ranked = sorted(scores, key=lambda f: -scores[f])
    rank = ranked.index(expected) + 1 if scores[ranked[0]] else 0
    hits += rank == 1
    top3 += 1 <= rank <= 3
    mark = "OK  " if rank == 1 else ("~   " if 1 < rank <= 3 else "MISS")
    print(f"{mark} ранг {rank}  живых слов {len(live)}/{len(words)}  {q[:38]:<38} -> {ranked[0]}")
print(f"\nпо словам: первая книга {hits}/10, в тройке {top3}/10")
