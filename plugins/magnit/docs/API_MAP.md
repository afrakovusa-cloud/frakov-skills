# Карта API Магнита (собрана 12.11.2026, второй заход — подключено почти всё)

Источник: JS-бандлы `magnit.ru/_nuxt/*.js` (495 чанков, API-слой — `B9phFMAA.js`),
проверка — живыми запросами с куками `~/.magnit/magnit_api_headers.json`.
База: `https://magnit.ru/webgate` + путь. Обязательно `x-service: express`; для превью ещё `x-delivery-type: delivery`.

Пометки: ✅ проверено запросом · 🔒 пишет данные/деньги (в клиенте — только с `--confirm`).

## Корзина
| GET | /v1/carts/lite | корзина | ✅ |
| PUT | /v1/carts/lite | изменить корзину | ✅ |
| DELETE | /v1/carts/lite | очистить | 🟡 |
| GET | /v1/carts/delivery-conditions | цена, порог, слот, сервисный сбор | ✅ `--slots` |
| GET | /v2/carts/lite | корзина v2 | 🟡 |

## Оформление заказа
| GET | /v1/checkout/preview | сумма, доставка, недоступные (нужен `x-delivery-type: delivery`) | ✅ `--preview` |
| GET | /v1/checkout/preview/promo-codes | промокоды к заказу | 🟡 |
| GET/PUT/POST | /carts/v1/order/{id}/draft, /draft/commit | черновик и фиксация | ⛔ не подключено: draft отдаёт 422 (`INTERNAL_GET_CART_ERROR_CODE`), 3 попытки; commit = списание |

## Заказы
| GET | /v2/orders/active/list | активные | ✅ `--orders` |
| GET | /v2/orders/history/list | история | ✅ `--orders` |
| GET | /v2/orders/info/{id} | детали | ✅ код `--order` (не проверено: заказов нет) |
| GET | /v2/orders/cancel-reasons?deliveryMethod=delivery | причины отмены | ✅ `--cancel-reasons` |
| GET | /v2/orders/cancel/{id} | 🔒 отмена | ✅ код `--cancel --confirm` (не проверено: заказов нет) |
| POST | /v2/orders/reorder/{id} | 🔒 повторить в корзину | ✅ код `--reorder --confirm` (не проверено) |
| GET | /v2/returns | возвраты | ✅ `--returns` |

## Оплата
| GET | /v2/payment-methods | способы оплаты (у пользователя — «Новый СБП») | ✅ `--payments` |
| POST | /v2/payment-methods/{sbp,sberpay}/bind, /cards/bind | привязка | ⛔ не делаю: платёжные данные и 3DS |
| GET | /v2/payment-processing/orders/{id} | платёж по заказу | 🔒 |

## Товары и каталог
| POST | /v2/goods/search | поиск, цены, наличие по точке | ✅ `--find`, `--compare` |
| POST | /v2/goods/get | ⛔ **не работает по ids**: отвечает одним и тем же товаром (1000378229) на любое тело. Команда `--product` убрана 12.11 — она врала. |
| GET | /v2/goods/{id}/stores/{storetype}?storetype=&catalogtype=&cityFiasId= | карточка + магазин | 🟡 отдаёт карточку, цены по точке получить не удалось |

**Сравнение цен:** цены на один и тот же товар (`id` одинаков во всех точках) отличаются между магазинами на 5–29 % (проверено 12.11 на «шоколад» и «молоко», 8 точек). Команда `--compare "товар" [--compare-top N]`.

**Переключение точки доставки (12.11).** Точку задают три вещи **одновременно**, иначе сервер держит старую:
1. cookie `shopCode` = `"КОД"` (с кавычками, домен `.magnit.ru`);
2. cookie `x_shop_type` = `MM` / `MC` / `DG` / `MA`;
3. заголовок `x-store-code` = код.
Проверено: при этих трёх `checkout/preview` показывает `deliveryInfo.store.storeCode = <код-магазина>`. Адрес доставки при этом не меняется. Функция `session_at(code, typ)`.
Попутно: смена адреса активным **не** меняет точку; `PUT /v1/checkout/preview` игнорирует присланный store.
⛔ Сумма корзины по точкам **не** пересчитывается: `preview` отдаёт одну и ту же сумму 574.14 ₽ на всех точках — цены фиксируются в корзине при добавлении. Чтобы сравнить всю корзину, нужна новая корзина в другой точке (риск потерять набор) — не сделано.
| POST | /v1/goods/filters | фильтры категории | 🟡 |
| GET | /catalog-bdui/v2/shelf | полка категории | 🟡 |
| GET | /v1/selections/store/{id} | подборки точки | 🟡 |
| GET | /v3/categories/store/{id} | категории точки | 🟡 |

## Магазины и города
| GET | /v1/cities/define | город по гео (даёт `cityFiasId`) | ✅ |
| POST | /v1/stores-facade/search | список точек города: тело `{"filters":{"query":"<город>","cityFIASID":"<fias>"}}` | ✅ |
| POST | /v1/stores-facade/search/detail | то же + полный адрес, `timetableList`, `deliveryTypeList`; требует `"pagination":{"size":N}` | ✅ `--stores N` |
Тело — только в обёртке `filters`; `query`/`circle`/`geo_bounding_box`/`cityFIASID` в корне не принимаются. Типы точек: `MM` (Магнит), `MC` (Косметик), `DG` (Дикси), `MA` (Аптека), `DISTR_PHARMACY`, `RTE_*` (рестораны). Количество точек зависит от города.

## Баллы, купоны, карты
| GET | /v3/user/balance | баллы | ✅ `--bonus` |
| GET | /v3/user/coupons/list | купоны (297 шт) | ✅ `--coupons` |
| GET | /v2/user/cards | карты (1 виртуальная) | ✅ `--cards` |
| GET | /v5/user/transactions?page=N | история баллов (пусто) | ✅ `--transactions` |
| GET | /v2/user/benefits?device_date=<unix> | персональные предложения | 🟡 |

## Промокоды
| GET | /v3/promo-gallery/promo-codes?service=express&deliveryType=delivery | ✅ `--promocodes` |
У пользователя: `БЫСТРО` (−35% на первый заказ, от 1000 ₽, до 18.11), `МАГНИТ` (до −35%, от 1700 ₽, до 15.11), `РУБЛЬ` (товар за 1 ₽, от 1500 ₽, до 15.11).

## Адреса
| GET | /customer_addresses/v1/address_book | ✅ `--addresses` |
| POST | /customer_addresses/v1/address_book | добавить адрес | 🟡 |
| DELETE | /customer_addresses/v1/address_book/{id} | 🔒 удалить адрес | ✅ `--address-del ID --confirm` (12.11 удалён «Бумажников, 17») |
| PATCH | /customer_addresses/v1/address_book/{id} | изменить адрес | 🟡 |

## Подписка «Магнит Плюс»
| GET | /v2/subscription/status, /v2/subscription/tariffs | ✅ `--subscription` (не подписан; тариф 99 ₽/мес, пробный 30 дн.) |
| POST | /v2/subscription/{subscribe,unsubscribe,tariff/change} | ⛔ не делаю: деньги |

## Не подключено — почему
- Оформление (`draft`/`commit`) — черновик не отдался, а фиксация списывает деньги. Нужна отдельная сессия с реальным заказом и подтверждением.
- Привязка карт/СБП, подписка — платёжные данные, 3DS, деньги.
- Отзывы, статьи, опросы — не нужны в быту.

## Ограничения
- Публичной доки API нет; карта = что реально шлёт сайт. Новая версия может переименовать путь.
- Куки протухают → `magnit_api_probe.py` (браузер, ~2 мин).
- Цены товаров — копейки; `priceWithVat` у подписки — рубли.
