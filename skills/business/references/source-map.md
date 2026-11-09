# Source-map — тезис → книга

Связывает выжимку в `functions/*.md` с реальным текстом книг в `source-book/`.
Владелец купил файлы → текст лежит локально. Для точной цитаты: `grep -i "фраза" source-book/<файл>.md`.

Уровень — концепт/раздел (не строка): source-book это извлечённый текст, нумерация строк нестабильна. Grep по концепту находит место.

## Стратегия (`functions/strategy.md`)
| Тезис | Книга | Концепт для grep |
|---|---|---|
| Стратегия = диагноз → направляющая политика → согласованные действия | `source-book/good-strategy-bad-strategy.md` | "kernel", "diagnosis", "guiding policy" |
| Каскад из 5 выборов | `source-book/playing-to-win.md` | "where to play", "how to win", "cascade" |
| 7 источников устойчивого преимущества | `source-book/7-powers.md` | "counter-positioning", "switching costs", "scale economies", "cornered resource" |
| Позиционирование как метод | `source-book/obviously-awesome.md` | "competitive alternatives", "positioning" |

## Анализ конкурентов (`functions/competitors.md`)
| Тезис | Книга | Концепт для grep |
|---|---|---|
| 10-шаговый процесс позиционирования; конкурентные альтернативы | `source-book/obviously-awesome.md` | "10-step", "competitive alternatives", "unique attributes" |
| Оценка барьера конкурента по 7 силам | `source-book/7-powers.md` | "counter-positioning", "switching costs", "branding", "cornered resource" |
| Прочитать чужую стратегию (5 выборов) | `source-book/playing-to-win.md` | "where to play", "how to win" |
| Диагноз слабого места расклада | `source-book/good-strategy-bad-strategy.md` | "diagnosis", "guiding policy" |
| Оценка проходимости (прокси) | — операционный метод, не из книг | — |

## Бренд (`functions/brand.md`)
| Тезис | Книга | Концепт для grep |
|---|---|---|
| Бренд = актив, поднимающий willingness to pay; affective valence + uncertainty reduction | `source-book/7-powers.md` | "branding is", "willingness to pay", "affective valence", "uncertainty reduction" |
| Бренд-обещание, brand building | `source-book/playing-to-win.md` | "brand promise", "brand building", "brand equity" |
| Позиционирование = фундамент бренда | `source-book/obviously-awesome.md` | "positioning", "market category" |

## Оффер / привлечение (`functions/offer-gtm.md`)
| Тезис | Книга | Концепт |
|---|---|---|
| Уравнение ценности, Grand Slam Offer | `source-book/100m-offers.md` | "value equation", "grand slam", "dream outcome" |
| 19 каналов, метод Bullseye | `source-book/traction.md` ⚠️частичный (скрейп ~20/229 стр) | "bullseye", "traction channels" |
| Предсказуемая система продаж на данных | `source-book/sales-acceleration-formula.md` | "hiring formula", "sales metrics" |
| Гарантия и реверс риска как рычаг конверсии | `source-book/100m-offers.md` | "guarantee", "reversing risk", "money back" |

## Операции (`functions/operations.md`)
| Тезис | Книга | Концепт |
|---|---|---|
| Работать НАД, а не В бизнесе; франшизная логика | `source-book/e-myth-revisited.md` | "working on your business", "franchise prototype" |
| Рычаг менеджера, выход команды | `source-book/high-output-management.md` | "managerial leverage", "output" |
| Встречи один на один с подчинённым | `source-book/high-output-management.md` | "one-on-one", "1:1", "supervisor" |
| Теория ограничений, узкое место, throughput | `source-book/the-goal.md` | "bottleneck", "throughput", "constraint" |

## Финансы (`functions/finance.md`)
| Тезис | Книга | Концепт |
|---|---|---|
| Три отчёта; прибыль — мнение, кэш — факт | `source-book/financial-intelligence.md` | "income statement", "cash", "art of finance" |
| Прибыль забирай первой; счета-конверты | `source-book/profit-first.md` ⚠️частичный (скрейп) | "profit first", "allocation", "Parkinson" |

## Основатель / масштаб (`functions/founder-scaling.md`)
| Тезис | Книга | Концепт |
|---|---|---|
| Build–Measure–Learn, MVP, pivot, validated learning | `source-book/the-lean-startup.md` ⚠️частичный (скрейп) | "validated learning", "minimum viable", "pivot" |
| Реальность управления, решения в кризис | `source-book/hard-thing-about-hard-things.md` | "struggle", "peacetime", "wartime" |
| Увольнения и сокращение штата | `source-book/hard-thing-about-hard-things.md` | "layoff", "firing", "demote" |
| Найм A-игроков | `source-book/high-output-management.md` + `hard-thing...md` (частично) | "hiring", "interview" |
| Метод найма A Method (Scorecard/Source/Select/Sell) | `source-book/who.md` ⚠️конспект (Notes, не полный текст) | "scorecard", "select", "interview" |

## Симуляция рисков (`functions/simulation.md`)
| Тезис | Книга | Концепт |
|---|---|---|
| Пороги «что должно быть правдой» | `source-book/playing-to-win.md` | "have to be true" |
| Прыжки веры, baseline после MVP | `source-book/the-lean-startup.md` | "leap-of-faith", "baseline", "innovation accounting" |
| Колебания + зависимые события (игра с кубиком) | `source-book/the-goal.md` | "statistical fluctuations", "dice" |
| Чувствительность 80/90%, прибыль без денег | `source-book/financial-intelligence.md` | "sensitivity analysis", "profit without cash" |
| Монте-Карло | — вне канона (Hubbard, Savage — `booklist.md`) | — |

## Статус текстов (полные / частичные / конспект / докупить)
Единственный источник — `source-book/README.md`. Метки ⚠️ в таблицах выше — напоминание на месте, не замена.
