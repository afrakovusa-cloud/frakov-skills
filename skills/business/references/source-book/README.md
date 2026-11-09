# source-book — тексты книг

Полные тексты книг, купленные владельцем, извлечены из PDF (`~/Desktop/Книги-бизнес/`) в markdown.
Скилл опирается на ЭТОТ текст, а не на память модели. Карта «тезис → книга» — в `../source-map.md`.

## Как использовать
Нужна точная цитата/факт из книги — не пересказывай по памяти, а **grep по файлу**:
```
grep -in "value equation" references/source-book/100m-offers.md
```
Не грузить книгу целиком в контекст — искать нужный кусок.

## Что лежит (14 книг)
Полные, чистые издания:
- `100m-offers.md` · `7-powers.md` · `e-myth-revisited.md` · `financial-intelligence.md` · `good-strategy-bad-strategy.md` · `hard-thing-about-hard-things.md` · `obviously-awesome.md` · `playing-to-win.md` · `sales-acceleration-formula.md` · `the-goal.md`

⚠️ Частичные / шумные (заменить при «переделаем скилл»):
- `traction.md` — ~20 из 229 стр, неполный.
- `profit-first.md`, `the-lean-startup.md` — извлечены из скрейпов документошаринга, содержат реальный текст, но не гарантированно полный/чистый.
- `high-output-management.md` — OCR-скан, шумный (опечатки распознавания).

## Конспекты (не полный текст, поднять при случае)
- `who.md` — Who: The A Method for Hiring (Smart & Street), Notes by Dave Kraft, ~10 стр. Метод найма A есть, полного текста нет.

## Чего НЕТ (докупить)
- Все 5 узлов покрыты источником. Полностью чистых оригиналов не хватает для: Who (конспект), Traction / Profit First (скрейпы), HOM (скан).

Дал владелец полные легальные файлы этих/заменных книг — переизвлечь и обновить `source-map.md`.
