# -*- coding: utf-8 -*-
"""Замер метода без локальной модели: термины автора -> grep по всем книгам -> ранг ожидаемой книги."""
import os, re, csv

BOOKS = "/Users/alex/Documents/OBSIDIAN/.claude/skills/business/references/source-book"
OUT = "/Users/alex/Documents/OBSIDIAN/.claude/skills/business/eval/2026-09-24-books_test.tsv"

# вопрос -> (ожидаемая книга, термины автора, подобранные по вопросу)
CASES = [
 ("Как поднять цену на свои услуги, чтобы клиенты не ушли?", "100m-offers.md",
  ["value equation", "raise your prices", "premium price", "price to value"]),
 ("Где в процессе у меня всё тормозит и копится очередь заказов?", "the-goal.md",
  ["bottleneck", "constraint", "throughput"]),
 ("Деньги на счету вроде есть, а прибыли нет — почему?", "financial-intelligence.md",
  ["cash flow", "income statement", "profit is an opinion", "accrual"]),
 ("Как понять, что крупный конкурент не сможет скопировать мою модель?", "7-powers.md",
  ["counter-positioning", "switching costs", "barrier", "cornered resource"]),
 ("Как проверить идею нового продукта, не тратя много денег?", "the-lean-startup.md",
  ["minimum viable", "validated learning", "pivot"]),
 ("Как проводить регулярные встречи один на один с сотрудником?", "high-output-management.md",
  ["one-on-one", "supervisor", "subordinate"]),
 ("Как правильно уволить людей, когда приходится сокращать штат?", "hard-thing-about-hard-things.md",
  ["layoff", "firing", "demote"]),
 ("Как сделать гарантию, чтобы людям было не страшно купить?", "100m-offers.md",
  ["guarantee", "reversing risk", "money back"]),
 ("Клиенты не понимают, чем я отличаюсь от других — что делать?", "obviously-awesome.md",
  ["positioning", "competitive alternatives", "market category"]),
 ("Почему я выгораю, делая всё в бизнесе сам?", "e-myth-revisited.md",
  ["working on your business", "franchise prototype", "technician"]),
]

texts = {}
for f in sorted(os.listdir(BOOKS)):
    if f.endswith(".md") and f != "README.md":
        texts[f] = open(os.path.join(BOOKS, f), encoding="utf-8", errors="ignore").read().lower()

rows, hits, top3 = [], 0, 0
for q, expected, terms in CASES:
    scores = {}
    for f, t in texts.items():
        n = sum(len(re.findall(re.escape(term.lower()), t)) for term in terms)
        scores[f] = n / (len(t) / 100_000)   # попаданий на 100k символов
    rank_list = sorted(scores, key=lambda f: -scores[f])
    rank = rank_list.index(expected) + 1
    hits += rank == 1
    top3 += rank <= 3
    rows.append((q, expected, " · ".join(terms), rank_list[0], rank, round(scores[expected], 1)))

with open(OUT, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    w.writerow(["вопрос", "ожидаемая_книга", "термины_автора", "книга_топ1", "ранг_ожидаемой", "плотность_на_100k"])
    w.writerows(rows)

for r in rows:
    mark = "OK " if r[4] == 1 else ("~  " if r[4] <= 3 else "MISS")
    print(f"{mark} ранг {r[4]}  {r[0][:46]:<46} -> {r[3]}")
print(f"\nточно первая книга: {hits}/10   в тройке: {top3}/10   книг в корпусе: {len(texts)}")
