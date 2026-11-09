# -*- coding: utf-8 -*-
"""Слепой замер: термины дала чистая сессия (не видела книг и ожидаемых ответов)."""
import os, re, csv

BOOKS = "/Users/alex/Documents/OBSIDIAN/.claude/skills/business/references/source-book"
OUT = "/Users/alex/Documents/OBSIDIAN/.claude/skills/business/eval/2026-09-24-books_blind.tsv"

QUESTIONS = [
 ("Как поднять цену на свои услуги, чтобы клиенты не ушли?", "100m-offers.md"),
 ("Где в процессе у меня всё тормозит и копится очередь заказов?", "the-goal.md"),
 ("Деньги на счету вроде есть, а прибыли нет — почему?", "financial-intelligence.md"),
 ("Как понять, что крупный конкурент не сможет скопировать мою модель?", "7-powers.md"),
 ("Как проверить идею нового продукта, не тратя много денег?", "the-lean-startup.md"),
 ("Как проводить регулярные встречи один на один с сотрудником?", "high-output-management.md"),
 ("Как правильно уволить людей, когда приходится сокращать штат?", "hard-thing-about-hard-things.md"),
 ("Как сделать гарантию, чтобы людям было не страшно купить?", "100m-offers.md"),
 ("Клиенты не понимают, чем я отличаюсь от других — что делать?", "obviously-awesome.md"),
 ("Почему я выгораю, делая всё в бизнесе сам?", "e-myth-revisited.md"),
]

BLIND = [
 ["value-based pricing", "price anchoring", "grandfathering existing clients", "price increase letter", "willingness to pay"],
 ["bottleneck", "theory of constraints", "work-in-progress (WIP) queue", "throughput", "process mapping"],
 ["cash flow vs. profit", "Profit First", "accrual accounting", "phantom profit", "gross margin"],
 ["moat", "defensibility", "barriers to entry", "counter-positioning", "switching costs"],
 ["minimum viable product (MVP)", "smoke test", "fake door test", "customer validation", "build-measure-learn"],
 ["one-on-ones", "manager tools", "performance conversation", "coaching cadence", "feedback loop"],
 ["layoffs done right", "severance package", "reduction in force (RIF)", "termination meeting", "survivor guilt"],
 ["risk reversal", "money-back guarantee", "unconditional guarantee", "de-risking the offer", "irresistible offer"],
 ["differentiation", "unique value proposition", "positioning statement", "category of one", "commoditization"],
 ["owner burnout", "working in the business vs. on the business", "E-Myth", "delegation", "systems dependency"],
]

texts = {}
for f in sorted(os.listdir(BOOKS)):
    if f.endswith(".md") and f != "README.md":
        texts[f] = open(os.path.join(BOOKS, f), encoding="utf-8", errors="ignore").read().lower()

rows, hits, top3, dead = [], 0, 0, 0
for (q, expected), terms in zip(QUESTIONS, BLIND):
    live = [t for t in terms if any(t.lower() in txt for txt in texts.values())]
    dead += len(terms) - len(live)
    scores = {}
    for f, t in texts.items():
        n = sum(len(re.findall(re.escape(term.lower()), t)) for term in live)
        scores[f] = n / (len(t) / 100_000)
    ranked = sorted(scores, key=lambda f: -scores[f])
    if scores[ranked[0]] == 0:
        rank = 0
    else:
        rank = ranked.index(expected) + 1
    hits += rank == 1
    top3 += 1 <= rank <= 3
    rows.append((q, expected, " · ".join(terms), f"{len(live)}/{len(terms)}", ranked[0], rank))
    mark = "OK  " if rank == 1 else ("~   " if 1 < rank <= 3 else "MISS")
    print(f"{mark} ранг {rank}  живых терминов {len(live)}/{len(terms)}  {q[:40]:<40} -> {ranked[0]}")

with open(OUT, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    w.writerow(["вопрос", "ожидаемая_книга", "термины_слепые", "живых_терминов", "книга_топ1", "ранг_ожидаемой"])
    w.writerows(rows)

print(f"\nслепой прогон: первая книга {hits}/10, в тройке {top3}/10, мёртвых терминов {dead} из 50")
