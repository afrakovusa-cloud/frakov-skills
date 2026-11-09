---
name: бизнес
description: Use when the user works on building or running a real business — strategy and positioning, offer design, customer acquisition channels, operations and systems, unit economics and financial statements, cash management, hiring and org, validating a new venture, pricing, or scaling. Distilled operator-grade frameworks from a no-fluff business canon (7 Powers, Playing to Win, $100M Offers, Traction, High Output Management, E-Myth, The Goal, Financial Intelligence, Profit First, Hard Thing, Lean Startup). Триггеры — "бизнес", "как построить бизнес", "стратегия", "оффер", "юнит-экономика", "каналы привлечения", "как считать прибыль", "нанимать", "масштабировать", "анализ конкурентов", "конкуренты", "проходимость", "поток места", "стоит ли открывать тут", "бренд", "брендинг", "готовый бизнес-план", "план под ключ". Do NOT use for мотивацию/коучинг, инвест-советы по бумагам (не сюда; скилл t-invest запаркован 2026-09-12), или маркетинг-копирайт под конкретный пост.
---

# Бизнес — операторские фреймворки

Строй бизнес как **проверяемую машину**, а не как «идея плюс усилия». Машина = 5 узлов: **стратегия → оффер/привлечение → операции → финансы → люди/масштаб**. Сбой ищи по узлам, не по настроению. Опора — канон операторских книг (`references/booklist.md`), синтез по темам, а не пересказ по книгам.

**Тексты книг лежат локально** (`references/source-book/`, куплены владельцем). Нужен точный факт/цитата/цифра из книги — не по памяти, а **grep по source-book** (карта «тезис → файл» в `references/source-map.md`). Пример: `grep -in "value equation" references/source-book/100m-offers.md`. Функции ниже — индекс-выжимка; source-book — первоисточник.

## Рабочий контракт

> ⚠️ **ГЛАВНОЕ ПРАВИЛО (архиважно, не пропускать НИКОГДА).** Любой бизнес-разбор/совет/анализ строится **из книг**, не из головы. Перед выводом:
> 1. Определи узел → метод → **grep нужный метод в `references/source-book/`** (карта `source-map.md`).
> 2. **Назови книгу и приём явно** («по методу X из <книга>»), приведи опору из текста.
> 3. Применяй метод дальше — в т.ч. лезь в веб (конкуренты, рынок, цифры) **через призму этого приёма**, а не по наитию.
>
> В карте нет строки под вопрос или grep пуст → смысловой поиск по книгам: `/Users/alex/video_env/bin/python3 scripts/books.py "вопрос по-русски" -n 5` (выдаёт куски текста; нужен GPU без 35B). Замер 2026-09-24: карта+grep 7/10, смысл 9/10, вместе 10/10.
>
> Нет опоры в source-book под тезис → так и скажи «в каноне этого нет, ниже — вне книг». Отвечать «из памяти» под видом книги — запрещено. Это относится ко ВСЕМ узлам, не только к конкурентам.

1. Сначала факты о конкретном бизнесе: цифры (выручка, маржа, CAC, отток), кто клиент, что уже пробовали. Не давай совет «вообще» — привязывай к его числам.
2. Разделяй:
   - **факт** — что подтверждено цифрой/договором/повторяемым наблюдением;
   - **гипотеза** — вероятное объяснение, требует проверки;
   - **неизвестно** — что надо измерить/спросить.
3. Начинай с решения или диагноза. Потом — минимальный план и как проверить, что сработало.
4. Никакой мотивации и «верь в себя». Только механика: что сделать, какая цифра должна сдвинуться, за какой срок.
5. Книжные фреймворки — устойчивые эвристики, не законы. Рынок, цены, регуляторику проверяй по текущим источникам.
6. По умолчанию ответ ≤ 800 слов. Приоритет — решение, число, следующий шаг; не вываливай весь чеклист.
7. **Эскалация пробела базы** (правило `kb-gap`). Пометил «в каноне этого нет» (см. ГЛАВНОЕ ПРАВИЛО) и это узнаваемый повторяемый приём (не разовая местная конкретика) — не останавливайся на пометке: предложи дописать в `references/functions/` или добавить книгу в `booklist.md`. База растёт там, где были дыры. Разовую нишевую конкретику (местный рынок, частный случай) в базу не тащить.

## Маршрут по задаче

| Запрос выглядит как | Начни с | Добери |
|---|---|---|
| стоит ли вообще это делать, проверить идею | [functions/founder-scaling.md](references/functions/founder-scaling.md) | [functions/finance.md](references/functions/finance.md) |
| где играть, в чём наше преимущество | [functions/strategy.md](references/functions/strategy.md) | [cheatsheet.md](references/cheatsheet.md) |
| анализ конкурентов, занятый рынок, стоит ли сюда | [functions/competitors.md](references/functions/competitors.md) | [functions/strategy.md](references/functions/strategy.md) |
| оценить проходимость/поток места | [functions/competitors.md](references/functions/competitors.md) → «Оценка проходимости» | — |
| собрать план / «готовый бизнес» под ключ | [playbooks/full-plan.md](references/playbooks/full-plan.md) → все узлы + [templates/plan.html](references/templates/plan.html) | нужные functions/*.md |
| бренд: почему берут дороже, как отстроиться | [functions/brand.md](references/functions/brand.md) | [functions/strategy.md](references/functions/strategy.md) |
| собрать оффер, поднять цену, продавать | [functions/offer-gtm.md](references/functions/offer-gtm.md) | [functions/finance.md](references/functions/finance.md) |
| проверить оффер/цену ДО выката, на симуляции клиентов | [functions/offer-gtm.md](references/functions/offer-gtm.md) → «Синтетическая валидация оффера» | — |
| откуда брать клиентов, какой канал | [functions/offer-gtm.md](references/functions/offer-gtm.md) | [templates/unit-economics.md](references/templates/unit-economics.md) |
| бизнес держится на мне, нет систем | [functions/operations.md](references/functions/operations.md) | — |
| где узкое место, почему не растёт выпуск | [functions/operations.md](references/functions/operations.md) | — |
| читать отчёты, считать прибыль/кэш | [functions/finance.md](references/functions/finance.md) | [cheatsheet.md](references/cheatsheet.md) |
| налоги, какой режим (самозанятый/ИП/УСН/патент/ООО), взносы, НДС | [functions/taxes-ru.md](references/functions/taxes-ru.md) — живые данные, сверить дату | [functions/finance.md](references/functions/finance.md) |
| считать юнит-экономику, LTV/CAC | [functions/finance.md](references/functions/finance.md) | [templates/unit-economics.md](references/templates/unit-economics.md) |
| нанимать, увольнять, расти командой | [functions/founder-scaling.md](references/functions/founder-scaling.md) | — |
| какую книгу читать по теме | [booklist.md](references/booklist.md) | нужный functions/*.md |
| точная цитата/факт из книги | [source-map.md](references/source-map.md) → grep [source-book/](references/source-book/) | — |
| нужен красивый бизнес-план в HTML | заполни [templates/plan.html](references/templates/plan.html), сохрани как `.html` | — |
| быстрый термин или формула | [cheatsheet.md](references/cheatsheet.md), [glossary.md](references/glossary.md) | — |

Грузи только нужный файл. Не тяни весь скилл в контекст. Playbooks/templates под конкретные задачи добавляй по мере надобности — сейчас есть `templates/unit-economics.md`.

## Ядро: бизнес как машина

> **Бизнес = кто-то платит больше, чем стоит его обслужить, повторяемо.**

Разложи в 5 узлов и проверяй по одному:

1. **Стратегия** — где играть и почему именно ты выигрываешь (устойчивое преимущество, не «лучше стараемся»).
2. **Оффер/привлечение** — насколько ценность > цены в глазах клиента, и по какому каналу они приходят предсказуемо.
3. **Операции** — работает ли оно без основателя; где узкое место, ограничивающее выпуск.
4. **Финансы** — сходится ли на единице (юнит-экономика) и не кончается ли кэш.
5. **Люди/масштаб** — рычаг менеджера, найм A-игроков, что ломается при росте ×10.

**Правило локализации сбоя:** «не растёт / не зарабатывает» → пройди узлы по порядку. Нет спроса (2) важнее плохих операций (3). Дырявая юнит-экономика (4) убивает раньше, чем стратегия (1). Не чини узел 3, пока не подтверждён узел 2.

## Грань достаточности

Малому бизнесу не нужен Porter Five Forces на 40 страниц. Бери минимальный фреймворк, который двигает решение: одна проверяемая гипотеза → один эксперимент → одна цифра. Разворачивай тяжёлую артиллерию (7 Powers, теория ограничений) только когда простое не объясняет провал.
