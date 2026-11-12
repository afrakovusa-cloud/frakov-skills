#!/usr/bin/env python3
"""Магнит без браузера: корзина читается и правится запросами за 0,15–0,3 с.

Заголовки и куки берутся из ~/.magnit/magnit_api_headers.json — снимок делает
magnit_api_probe.py (браузер, один раз за сессию, ~2 мин).

    magnit_api.py --check                      # жива ли сессия и та ли корзина
    magnit_api.py --cart                       # что лежит в корзине
    magnit_api.py --add 3284010204 2047000007  # положить товары по кодам
    magnit_api.py --remove 1000035016          # убрать из корзины
    magnit_api.py --catalog молоко             # что из этого есть на главной точки
    magnit_api.py --slots                      # слоты доставки, цена и порог
    magnit_api.py --preview                    # превью заказа: сумма, доставка, недоступные
    magnit_api.py --bonus --coupons --orders   # баллы, купоны, заказы
    magnit_api.py --addresses                  # адреса доставки
    magnit_api.py --payments --cards --transactions  # оплата, карты, история баллов
    magnit_api.py --subscription --returns     # подписка (чтение), возвраты
    magnit_api.py --promocodes                 # промокоды аккаунта
    magnit_api.py --order 12345                # детали заказа
    magnit_api.py --cancel 12345 --confirm     # 🔒 отмена заказа
    magnit_api.py --reorder 12345 --confirm    # 🔒 повторить заказ в корзину

Любой сбой печатает причину по-русски и что делать; всё пишется в
~/.magnit/magnit_api.log (время, что делали, код, ответ сервера до 300 знаков).
Заказ НЕ оформляет.
"""
import argparse
import datetime
import json
import os
import re
import sys

import requests

HEADERS = os.environ.get("MAGNIT_HEADERS") or os.path.expanduser("~/.magnit/magnit_api_headers.json")
LOG = os.path.expanduser("~/.magnit/magnit_api.log")
URL = "https://magnit.ru/webgate/v1/carts/lite"
HOME = "https://magnit.ru/?shopCode=ВАШ_КОД_МАГАЗИНА&shopType=express"   # ваш магазин доставки
EXPRESS = ".express"


class Fail(Exception):
    """Понятный отказ: сообщение пользователю + подсказка, что делать."""

    def __init__(self, what, fix=""):
        super().__init__(what)
        self.what = what
        self.fix = fix


def log(line):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {line}\n")
    except OSError:
        pass


def die(e):
    print(f"❌ {e.what}")
    if e.fix:
        print(f"   что делать: {e.fix}")
    log(f"ОШИБКА {e.what} | {e.fix}")
    return 1


def session():
    if not os.path.exists(HEADERS):
        raise Fail(f"нет снимка заголовков {HEADERS}",
                   "снять заново: xvfb-run -a python3 magnit_api_probe.py")
    try:
        d = json.load(open(HEADERS, encoding="utf-8"))
        h = {k: v for k, v in d["headers"].items()
             if k.lower() not in ("cookie", "content-length", "host")}
        cookies = d["cookies"]
    except (ValueError, KeyError) as e:
        raise Fail(f"снимок заголовков битый: {e}", "снять заново через magnit_api_probe.py")
    if not h.get("x-device-id"):
        raise Fail("в снимке нет x-device-id — API такой запрос отвергает",
                   "снять заново через magnit_api_probe.py")
    h["x-service"] = "express"     # без этого API отдаёт другую, пустую корзину
    s = requests.Session()
    s.cookies.update(cookies)
    return s, h


def call(s, h, method, url, body=None):
    """Один запрос с разбором сбоев: сеть, 400, 401/403/498, 5xx, не-JSON."""
    try:
        r = s.request(method, url, headers=h, data=body, timeout=30)
    except requests.Timeout:
        raise Fail("Магнит не ответил за 30 секунд", "повторить; если повторяется — проверить сеть на VPS")
    except requests.ConnectionError as e:
        raise Fail(f"нет связи с magnit.ru: {str(e)[:120]}", "проверить, что сайт открывается с сервера")
    log(f"{method} {url.split('?')[0]} → {r.status_code} {len(r.text)}б")
    if r.status_code in (401, 403, 498):
        raise Fail(f"Магнит не пустил по этим кукам (код {r.status_code}) — сессия протухла",
                   "снять снимок заново: magnit_api_probe.py (браузер, ~2 мин)")
    if r.status_code == 400:
        try:
            msg = r.json().get("message", "")
        except ValueError:
            msg = r.text[:200]
        if "x-device-id" in msg or "x-service" in msg:
            raise Fail(f"API требует заголовок, которого нет в снимке ({msg})",
                       "снять снимок заново: magnit_api_probe.py")
        raise Fail(f"Магнит отверг запрос (400): {msg}", "проверить коды товаров; см. журнал")
    if r.status_code >= 500:
        raise Fail(f"сервер Магнита ответил {r.status_code}", "повторить позже; код 504 у Магнита бывает на /cart")
    if r.status_code != 200:
        raise Fail(f"неожиданный ответ Магнита: код {r.status_code}, {r.text[:200]}", "см. журнал ~/.magnit/magnit_api.log")
    try:
        return r.json()
    except ValueError:
        raise Fail("Магнит вернул не JSON (возможно, страницу-заглушку антибота)",
                   "снять снимок заново: magnit_api_probe.py; см. журнал")


def get_cart(s, h):
    j = call(s, h, "GET", URL)
    if not isinstance(j, dict) or "items" not in j:
        raise Fail(f"в ответе нет поля items: {str(j)[:200]}", "см. журнал")
    cid = j.get("id") or ""
    if EXPRESS not in cid:
        raise Fail(f"API отдал чужую корзину ({cid or 'без id'}) — не экспресс-корзина пользователя",
                   "сессия протухла: снять снимок заново через magnit_api_probe.py")
    return j


def put_cart(s, h, items):
    # increment — ТОЛЬКО весовым. Со штучными Магнит молча игнорирует весь PUT (200 и без
    # изменений), проверено 11.11. Позиции из get_cart приходят с increment: apiece — его снимаем.
    body = {"items": [{"goodId": i["goodId"], "offerId": i["offerId"], "qnty": i["qnty"],
                       **({"increment": i["increment"]}
                          if (i.get("increment") or {}).get("unit") == "weight" else {})}
                      for i in items]}
    call(s, h, "PUT", URL, json.dumps(body))
    j = get_cart(s, h)
    want = sum(1 for i in items if i["qnty"] > 0)
    got = sum(1 for i in j["items"] if i["qnty"] > 0)
    if got < want:
        log(f"ВНИМАНИЕ после PUT: ожидалось {want} позиций, стало {got}")
        print(f"⚠️ после записи позиций меньше, чем отправляли: {want} → {got}")
        print("   часть товаров Магнит не принял — сверься с --cart и журналом")
    return j


def show(j):
    live = [i for i in j.get("items") or [] if i["qnty"] > 0]
    zeros = [i for i in j.get("items") or [] if i["qnty"] == 0]
    print(f"корзина {j.get('id')}: {len(live)} позиций" + (f", {len(zeros)} нулевых строк" if zeros else ""))
    for i in live:
        print(f"  {i['goodId']}  qnty={i['qnty']} {i.get('increment', {}).get('unit', '')}")
    if zeros:
        print("   нулевые строки = товара нет в магазине точки; на сумму не влияют, в интерфейсе висят до удаления")


def catalog(s, h, word):
    html = call_text(s, h, HOME)
    cards = re.findall(r'<a title="([^"]{3,90})" class="pl-hover-base" href="/product/(\d+)-', html)
    if not cards:
        raise Fail("на главной точки нет ни одной карточки товара",
                   "снять снимок заново: magnit_api_probe.py (без сессии главная отдаёт урезанный каталог)")
    seen, rows = set(), []
    for name, gid in cards:
        if gid in seen:
            continue
        seen.add(gid)
        if re.search(word, name, re.I):
            rows.append((name, gid))
    print(f"на главной точки совпадений «{word}»: {len(rows)} (всего карточек {len(seen)})")
    for name, gid in rows:
        print(f"  {gid}  {name}")
    return rows


def find(s, h, term, store):
    """Поиск по ассортименту точки: POST /webgate/v2/goods/search (снято с сайта 10.11)."""
    body = {"includeAdultGoods": True, "pagination": {"offset": 0, "limit": 10},
            "sort": {"order": "desc", "type": "popularity"}, "term": term,
            "storeCode": store, "storeType": "express", "catalogType": "2"}
    hh = dict(h, **{"content-type": "application/json"})
    try:
        r = s.post("https://magnit.ru/webgate/v2/goods/search", headers=hh,
                   data=json.dumps(body), timeout=25)
    except requests.RequestException as e:
        raise Fail(f"поиск не связался с Магнитом: {str(e)[:100]}", "повторить")
    log(f"POST /webgate/v2/goods/search «{term}» → {r.status_code}")
    if r.status_code != 200:
        raise Fail(f"поиск ответил {r.status_code}", "см. журнал; повторить позже")
    items = r.json().get("items") or []
    print(f"«{term}» в точке {store}: найдено {len(items)}")
    for it in items:
        p = it.get("price")
        price = f"{p / 100:.2f} ₽" if isinstance(p, (int, float)) else "?"
        stock = it.get("quantity")
        if stock is None:
            flag = ""
        elif stock <= 0:
            flag = " ⛔ нет в наличии"
        elif stock <= 3:
            flag = f" ⚠️ остаток {stock} — может не быть"
        else:
            flag = "" if stock > 10 else f"  ост.{stock}"
        w = it.get("weighted") or {}
        if w.get("isWeighted"):
            step = w.get("step") or w.get("minStep")
            if step:
                flag += f" (шаг {step} г)"
        print(f"  {it.get('id')}  {price:>10}  {it.get('name', '')[:55]}{flag}")
    return items


JOURNAL = os.path.expanduser("~/.magnit/magnit_prices.jsonl")
WATCH = ["молоко", "творог", "яйца", "картофель", "морковь", "лук", "томаты", "огурцы",
         "гречка", "рис", "макароны", "сахар", "масло подсолнечное", "сыр", "курица", "бананы", "хлеб"]


def search_items(s, h, term, store, discount=False, limit=20):
    body = {"includeAdultGoods": True, "pagination": {"offset": 0, "limit": limit},
            "sort": {"order": "desc", "type": "popularity"}, "term": term,
            "storeCode": store, "storeType": "express", "catalogType": "2",
            "onlyDiscount": bool(discount)}
    hh = dict(h, **{"content-type": "application/json"})
    r = s.post("https://magnit.ru/webgate/v2/goods/search", headers=hh,
               data=json.dumps(body), timeout=25)
    if r.status_code != 200:
        raise Fail(f"поиск «{term}» ответил {r.status_code}", "повторить; см. журнал")
    log(f"POST search «{term}» disc={discount} → 200")
    return r.json().get("items") or []


def real_promo(it):
    pr = it.get("promotion") or {}
    if not (pr.get("isPromotion") and pr.get("oldPrice")):
        return None
    end = (pr.get("endDate") or "")[:10]
    if end[:4] and not ("2026" <= end[:4] < "2099"):   # заглушки 1970 и 4000-01-01 — не даты акции
        end = ""
    return {"pct": pr.get("discountPercent"), "old": pr["oldPrice"], "end": end}


def promos(s, h, store, top=12):
    seen, rows = set(), []
    for term in WATCH:
        for it in search_items(s, h, term, store, discount=True, limit=15):
            if it["id"] in seen:
                continue
            seen.add(it["id"])
            pr = real_promo(it)
            if pr:
                rows.append({**pr, "id": it["id"], "name": it.get("name", ""), "price": it["price"]})
    rows.sort(key=lambda x: -(x["pct"] or 0))
    print(f"настоящих акций по отслеживаемым категориям: {len(rows)} (точка {store})")
    for r in rows[:top]:
        print(f"  −{r['pct']}%  {r['old'] / 100:7.2f} → {r['price'] / 100:7.2f} ₽  "
              f"{r['name'][:45]}  [{r['id']}]" + (f"  до {r['end']}" if r["end"] else ""))
    return rows


def load_journal():
    hist = {}
    if not os.path.exists(JOURNAL):
        return hist
    with open(JOURNAL, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            hist.setdefault(row["id"], []).append((row["d"], row["p"]))
    return hist


def snapshot(s, h, store):
    today = datetime.date.today().isoformat()
    # повторный запуск в тот же день не должен плодить дубли (11.11: было 332 записи на 168 товаров)
    already = set()
    if os.path.exists(JOURNAL):
        with open(JOURNAL, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("d") == today:
                    already.add(r.get("id"))
        if already:
            print(f"за {today} снимок уже есть ({len(already)} позиций) — не дублирую")
            return
    n = 0
    seen = set()
    with open(JOURNAL, "a", encoding="utf-8") as f:
        for term in WATCH:
            for it in search_items(s, h, term, store, limit=10):
                if it["id"] in seen:
                    continue
                seen.add(it["id"])
                f.write(json.dumps({"d": today, "id": it["id"], "p": it["price"],
                                    "n": it.get("name", "")[:80]}, ensure_ascii=False) + "\n")
                n += 1
    print(f"снимок цен за {today}: {n} позиций в журнал {JOURNAL}")


def deals(s, h, store, min_pct=15, top=12):
    hist = load_journal()
    if not hist:
        print("журнал пуст — сначала снимок: --snapshot")
        return []
    rows = []
    for term in WATCH:
        for it in search_items(s, h, term, store, discount=True, limit=15):
            pr = real_promo(it)
            if not pr:
                continue
            past = [p for _d, p in hist.get(it["id"], [])]
            if len(past) < 3:
                continue                    # истории мало: честно не знаем обычную цену
            past.sort()
            median = past[len(past) // 2]
            if it["price"] < median * 0.95:
                rows.append((pr["pct"], median, it["price"], it.get("name", ""), it["id"]))
    rows.sort(key=lambda x: -(x[0] or 0))
    print(f"реально дешевле своей медианы: {len(rows)}")
    for pct, med, price, name, gid in rows[:top]:
        print(f"  −{pct}%  медиана {med / 100:7.2f} → {price / 100:7.2f} ₽  {name[:45]}  [{gid}]")
    return rows


def call_text(s, h, url):
    try:
        r = s.get(url, headers=h, timeout=30)
    except requests.RequestException as e:
        raise Fail(f"не смогла открыть {url.split('?')[0]}: {str(e)[:120]}", "проверить сеть")
    if r.status_code != 200:
        raise Fail(f"страница {url.split('?')[0]} ответила {r.status_code}", "повторить позже")
    log(f"GET {url.split('?')[0]} → {r.status_code} {len(r.text)}б")
    return r.text


WG = "https://magnit.ru/webgate"
ADDR_URL = "https://magnit.ru/webgate/customer_addresses/v1/address_book"


def wget(s, h, path, what, extra_headers=None, timeout=25):
    """GET к webgate с понятным отказом; путь без домена: /v1/..."""
    hh = dict(h, **(extra_headers or {}))
    r = s.get(WG + path, headers=hh, timeout=timeout)
    log(f"GET {path.split('?')[0]} → {r.status_code}")
    if r.status_code in (401, 403, 498):
        raise Fail(f"Магнит не пустил по кукам ({r.status_code}) в {what}",
                   "снять снимок заново: magnit_api_probe.py")
    if r.status_code != 200:
        raise Fail(f"{what}: код {r.status_code}, {r.text[:200]}", "см. журнал")
    try:
        return r.json()
    except ValueError:
        raise Fail(f"{what}: ответ не JSON — похоже на заглушку антибота", "снять снимок заново")


def rub(k):
    return f"{k / 100:.2f} ₽" if isinstance(k, (int, float)) else "?"


def slots(s, h):
    """Слоты доставки: цена, бесплатная от суммы, ближайшее окно, наценка за перегруз."""
    j = wget(s, h, "/v1/carts/delivery-conditions", "условия доставки")
    costs = j.get("deliveryCosts") or []
    for c in costs:
        price = c.get("deliveryPrice")
        free_from = c.get("orderSumFrom")
        print(f"доставка {rub(price)}" + (f", бесплатно от {rub(free_from)}" if free_from else ""))
    w = j.get("deliverySlot") or {}
    for k in ("datetimeFrom", "datetimeTo"):
        if w.get(k):
            print(f"  окно: {k.replace('datetime', '').lower()} {w[k][:16].replace('T', ' ')}")
    if j.get("orderSumMinimal"):
        print(f"  минимальный заказ: {rub(j['orderSumMinimal'])}")
    if j.get("serviceFee"):
        print(f"  сервисный сбор: {rub(j['serviceFee'])}")
    if j.get("isSurged"):
        print("  ⚠️ повышенный спрос — слот может вырасти в цене")
    extra = [k for k in j if k not in ("deliveryCosts", "deliverySlot", "isSurged",
                                       "orderSumMinimal", "serviceFee")]
    if extra:
        print(f"  ещё поля: {', '.join(extra[:6])}")
    return j


def preview(s, h):
    """Превью заказа: сумма, доставка, адрес, недоступные позиции. Заказ НЕ оформляет."""
    j = wget(s, h, "/v1/checkout/preview", "превью заказа",
             extra_headers={"x-delivery-type": "delivery"})
    sm = j.get("summary") or {}
    n = sm.get("itemsCount")
    total = sm.get("itemsTotalSalePrice")
    print(f"к оформлению: {n} позиций на {rub(total)}")
    for p in (sm.get("prices") or [])[:6]:
        v = p.get("value", p.get("price"))
        print(f"  {p.get('title', '?')}: {rub(v)}")
    di = j.get("deliveryInfo") or {}
    adr = di.get("address") or {}
    if adr.get("fullAddress"):
        print(f"  адрес: {adr['fullAddress']}")
    for k, v in di.items():
        if k != "address" and isinstance(v, (str, int, float)):
            print(f"  {k}: {v}")
    bad = j.get("unavailableItems") or []
    if bad:
        print(f"  ⛔ недоступны в этот слот: {len(bad)}")
        for it in bad[:5]:
            print(f"     {it.get('name') or it.get('goodId')}")
    for note in (j.get("restrictions") or [])[:3]:
        if isinstance(note, dict) and note.get("title"):
            print(f"  ⚠️ {note['title']}")
    print(f"  промокодов в галерее: {j.get('galleryPromoCodesCount', 0)}")
    return j


def bonus(s, h):
    """Баллы Магнита (обычные и экспресс)."""
    j = wget(s, h, "/v3/user/balance", "бонусы")
    print(f"баллов всего: {j.get('totalPointBalance', '?')}, по экспрессу: {j.get('totalExpressPoints', '?')}")
    for it in j.get("items") or []:
        if it.get("points"):
            print(f"  {it.get('type')}: {it['points']}")
    return j


def coupons(s, h, top=12):
    """Купоны: сколько, какие сгорят первыми."""
    j = wget(s, h, "/v3/user/coupons/list", "купоны", timeout=40)
    rows = j.get("coupons") or []
    dated = [c for c in rows if c.get("expirationDate")]
    dated.sort(key=lambda c: c["expirationDate"])
    print(f"купонов: {len(rows)}, с датой: {len(dated)}")
    for c in dated[:top]:
        d = (c.get("expirationDate") or "")[:10]
        t = (c.get("title") or c.get("description") or "").split("\n")[0][:60]
        print(f"  до {d}  {t}")
    return rows


def orders(s, h, top=8):
    """Активные заказы и история (поля печатаются как есть — сервис может добавить свои)."""
    act = wget(s, h, "/v2/orders/active/list", "активные заказы")
    print(f"активных: {act.get('count', 0)}")
    for o in (act.get("items") or [])[:top]:
        print(f"  {o.get('id') or o.get('number')}  {o.get('status') or ''}  {rub(o.get('total') or o.get('sum'))}")
    hist = wget(s, h, "/v2/orders/history/list?page=1&perPage=%d" % top, "история заказов")
    print(f"в истории: {hist.get('count', 0)}")
    for o in (hist.get("items") or [])[:top]:
        print(f"  {o.get('id') or o.get('number')}  {str(o.get('createdAt') or o.get('date') or '')[:10]}  "
              f"{rub(o.get('total') or o.get('sum'))}")
    return act




def addresses(s, h):
    """Адреса доставки из аккаунта."""
    j = wget(s, h, "/customer_addresses/v1/address_book", "адреса", timeout=25)
    rows = j.get("data") or []
    print(f"адресов: {len(rows)}")
    for a in rows:
        at = a.get("attributes") or {}
        print(f"  {at.get('shortFormatted') or at.get('fullAddress')}"
              + ("" if at.get("isActive", True) else "  (неактивен)"))
    return rows


def _km(a, b):
    """Расстояние по прямой между (lat, lon), км — формула гаверсинуса."""
    import math
    r = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = math.radians(b[0] - a[0])
    dl = math.radians(b[1] - a[1])
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))


def _my_point(s, h):
    """Точка «я» — активный адрес доставки из аккаунта; не вышло — центр города по гео."""
    try:
        j = wget(s, h, "/customer_addresses/v1/address_book", "адреса", timeout=20)
        for a in j.get("data") or []:
            at = a.get("attributes") or {}
            if at.get("isActive") and at.get("latitude") and at.get("longitude"):
                return (at["latitude"], at["longitude"]), at.get("shortFormatted") or ""
    except Fail:
        pass
    return None, ""


TYPES = {"MM": "Магнит", "MC": "Магнит Косметик", "DG": "Дикси", "MA": "Магнит Аптека"}


def stores(s, h, top=5):
    """Ближайшие магазины к активному адресу: расстояние, адрес, часы, доставка."""
    hh = dict(h, **{"content-type": "application/json"})
    city = wget(s, h, "/v1/cities/define", "город", timeout=20)
    fias, name = city.get("cityFiasId") or city.get("cityFIASID"), city.get("city") or ""
    if not fias:
        raise Fail("не поняла город из API", "см. журнал")
    body = {"filters": {"query": name, "cityFIASID": fias}, "pagination": {"size": 400}}
    r = s.post(WG + "/v1/stores-facade/search/detail", headers=hh, data=json.dumps(body), timeout=40)
    log(f"POST /v1/stores-facade/search/detail {name} → {r.status_code}")
    if r.status_code != 200:
        raise Fail(f"поиск магазинов: код {r.status_code}, {r.text[:200]}", "повторить позже")
    rows = r.json().get("data") or []
    me, my_addr = _my_point(s, h)
    out = []
    for st in rows:
        t = st.get("storeTypeV2") or ""
        if t not in TYPES or not st.get("isActive", True):
            continue
        c = st.get("coordinates") or {}
        if not c.get("latitude"):
            continue
        dist = _km(me, (c["latitude"], c["longitude"])) if me else None
        out.append((dist, t, st.get("address") or "", st.get("externalId", {}).get("storeCode") or "",
                    st.get("deliveryTypeList") or []))
    if me:
        out.sort(key=lambda x: x[0])
    print(f"город {name}: магазинов {len(out)}" + (f", считаю от «{my_addr}»" if my_addr else ""))
    for dist, t, addr, code, dtypes in out[:top]:
        d = f"{dist:4.1f} км" if dist is not None else "  ?  "
        deliv = "доставка" if "DELIVERY_TYPE_DELIVERY" in dtypes else "только самовывоз"
        print(f"  {d}  {TYPES[t]:<15} {addr}  [{code}] {deliv}")
    return out


def store_points(s, h, top=15):
    """Магазины города с расстоянием, отсортированные от адреса. Общий сбор для --stores и --compare."""
    hh = dict(h, **{"content-type": "application/json"})
    city = wget(s, h, "/v1/cities/define", "город", timeout=20)
    fias, name = city.get("cityFiasId") or city.get("cityFIASID"), city.get("city") or ""
    body = {"filters": {"query": name, "cityFIASID": fias}, "pagination": {"size": 400}}
    r = s.post(WG + "/v1/stores-facade/search/detail", headers=hh, data=json.dumps(body), timeout=40)
    log(f"POST /v1/stores-facade/search/detail {name} → {r.status_code}")
    if r.status_code != 200:
        raise Fail(f"список магазинов: код {r.status_code}", "повторить позже")
    me, _ = _my_point(s, h)
    out = []
    for st in r.json().get("data") or []:
        t = st.get("storeTypeV2") or ""
        if t not in TYPES or not st.get("isActive", True):
            continue
        c = st.get("coordinates") or {}
        if not c.get("latitude"):
            continue
        dist = _km(me, (c["latitude"], c["longitude"])) if me else 999
        out.append({"dist": dist, "type": t, "address": st.get("address") or "",
                    "code": st.get("externalId", {}).get("storeCode") or "",
                    "delivery": "DELIVERY_TYPE_DELIVERY" in (st.get("deliveryTypeList") or [])})
    out.sort(key=lambda x: x["dist"])
    return out[:top]


def _price_in(s, h, store_code, goods):
    """Цены и наличие набора товаров в одной точке: {goodId: (price, qty, step)}."""
    hh = dict(h, **{"content-type": "application/json"})
    body = {"pagination": {"offset": 0, "limit": len(goods)}, "storeCode": store_code,
            "storeType": "express", "catalogType": "2",
            "goods": [{"goodId": g, "offerId": g} for g in goods]}
    r = s.post(WG + "/v2/goods/get", headers=hh, data=json.dumps(body), timeout=30)
    if r.status_code != 200:
        return {}
    res = {}
    for it in r.json().get("items") or []:
        w = it.get("weighted") or {}
        step = (w.get("step") or w.get("minStep")) if w.get("isWeighted") else None
        res[str(it.get("id"))] = (it.get("price"), it.get("quantity"), step)
    return res


def compare(s, h, term, top=8):
    """Сравнить цену товара по ближайшим магазинам: где дешевле и на сколько.
    Работает через поиск (v2/goods/search) — id товара одинаков в разных точках."""
    pts = store_points(s, h, top)
    if not pts:
        raise Fail("не нашла магазинов рядом", "проверить адрес: --addresses")
    table = {}
    for p in pts:
        for it in search_items(s, h, term, p["code"], limit=15):
            iid = str(it.get("id"))
            row = table.setdefault(iid, {"name": str(it.get("name") or "")[:44], "p": {}})
            if (it.get("quantity") or 0) > 0 and it.get("price"):
                row["p"][p["code"]] = it["price"]
    print(f"«{term}»: товаров {len(table)}, точек {len(pts)}")
    winners = {}
    shown = 0
    for iid, row in table.items():
        cand = [(pr, code) for code, pr in row["p"].items()]
        if len(cand) < 2:
            continue
        lo, hi = min(cand), max(cand)
        if hi[0] - lo[0] < 1:          # разница меньше копейки — шум
            continue
        pct = (hi[0] - lo[0]) * 100 / hi[0]
        where = next(x for x in pts if x["code"] == lo[1])
        winners[lo[1]] = winners.get(lo[1], 0) + 1
        print(f"  −{pct:4.0f}%  {rub(hi[0]):>9} → {rub(lo[0]):>9}  {row['name']}  [{where['address'][:30]}]")
        shown += 1
        if shown >= 10:
            break
    if not shown:
        print("  разницы в ценах между точками нет")
    elif winners:
        best = max(winners, key=winners.get)
        where = next(x for x in pts if x["code"] == best)
        print(f"  чаще всего дешевле: {TYPES[where['type']]}, {where['address'][:45]} ({winners[best]} поз.)")
    return table


def session_at(code, typ="MM"):
    """Сессия, привязанная к другой точке. Точку задают три вещи сразу (проверено 12.11):
    cookie shopCode в кавычках на домене .magnit.ru, cookie x_shop_type и заголовок x-store-code.
    Адрес доставки при этом не меняется."""
    s, h = session()
    s.cookies.set("shopCode", f'"{code}"', domain=".magnit.ru")
    s.cookies.set("x_shop_type", typ, domain=".magnit.ru")
    h["x-store-code"] = code
    return s, h


def cart_compare(s, h, top=8):
    """НЕ РАБОТАЕТ как сравнение: preview отдаёт одну сумму на все точки — цены фиксируются
    в существующей корзине при добавлении. Оставлено как заготовка, в CLI не выведено."""
    """Сравнить корзину по ближайшим точкам: сумма и чего нет. Точка — через session_at."""
    cart = get_cart(s, h)
    live = sum(1 for i in cart.get("items") or [] if i["qnty"] > 0)
    if not live:
        print("корзина пуста — сравнивать нечего")
        return []
    pts = store_points(s, h, top)
    rows = []
    for p in pts:
        try:
            s2, h2 = session_at(p["code"], p["type"])
            j = wget(s2, h2, "/v1/checkout/preview", "превью",
                     extra_headers={"x-delivery-type": "delivery"}, timeout=35)
        except Fail as e:
            rows.append({**p, "total": None, "bad": [], "err": e.what})
            continue
        sm = j.get("summary") or {}
        rows.append({**p, "total": sm.get("itemsTotalSalePrice"), "bad": j.get("unavailableItems") or [],
                     "err": ""})
    good = [r for r in rows if r["total"] is not None and not r["bad"]]
    good.sort(key=lambda x: x["total"])
    base = good[-1]["total"] if good else None
    print(f"корзина: {live} позиций, точки рядом: {len(rows)}")
    for r in sorted(good, key=lambda x: x["total"])[:6]:
        save = f"  −{rub(int(base - r['total']))}" if base and r["total"] < base else ""
        print(f"  {rub(int(r['total'])):>9}  {r['dist']:4.1f} км  {TYPES[r['type']]:<15} {r['address'][:34]}{save}")
    partial = [r for r in rows if r["bad"]]
    if partial:
        print(f"  ещё {len(partial)} точек не могут собрать весь набор (чего-то нет)")
    errs = [r for r in rows if r["err"]]
    if errs:
        print(f"  сбоев: {len(errs)} ({errs[0]['err'][:60]})")
    if good:
        b = good and min(good, key=lambda x: x["total"])
        if base and b["total"] < base:
            print(f"\nвыгоднее всего: {TYPES[b['type']]}, {b['address'][:45]} — экономия {rub(int(base - b['total']))}")
    return rows


def address_del(s, h, aid, confirm):
    """🔒 Удалить адрес доставки. Без --confirm печатает «это удаление» и выходит."""
    if not confirm:
        raise Fail(f"удаление адреса {aid} — вернуть можно только вводом заново",
                   "повторить с флагом --confirm, если точно надо")
    hh = dict(h, **{"content-type": "application/json"})
    r = s.delete(WG + f"/customer_addresses/v1/address_book/{aid}", headers=hh, timeout=25)
    log(f"DELETE /customer_addresses/v1/address_book/{aid} → {r.status_code}")
    if r.status_code not in (200, 204):
        raise Fail(f"адрес не удалён: код {r.status_code}, {r.text[:200]}", "см. журнал")
    print(f"✅ адрес {aid} удалён")
    return True


def payments(s, h):
    """Способы оплаты, доступные аккаунту."""
    j = wget(s, h, "/v2/payment-methods", "методы оплаты")
    for m in j.get("available") or []:
        if m.get("isHidden"):
            continue
        info = ((m.get("additionalInfo") or {}).get("description") or {}).get("text") or ""
        print(f"  {m.get('title') or m.get('id')}  [{m.get('id')}]" + (f"  {info}" if info else ""))
    return j


def cards(s, h):
    """Карты Магнита (номера балльных карт аккаунта)."""
    j = wget(s, h, "/v2/user/cards", "карты Магнита")
    ids = j.get("identifiers") or []
    print(f"карт: {len(ids)}")
    for c in ids:
        no = str(c.get("identifierNo") or "")
        print(f"  {no[:4]}…{no[-4:]}  {c.get('identifierTypeCode')}"
              + ("  (виртуальная)" if c.get("isIdentifierTypeVirtual") else ""))
    return j


def transactions(s, h, page=1):
    """История начислений и списаний баллов."""
    j = wget(s, h, f"/v5/user/transactions?page={page}", "история баллов", timeout=30)
    rows = j.get("transactions") or j.get("items") or []
    print(f"страница {j.get('page', page)}: записей {len(rows)}"
          + (f", есть следующая" if j.get("nextPage") else ""))
    for t in rows[:20]:
        print(f"  {str(t.get('createdAt') or t.get('date') or '')[:10]}  "
              f"{t.get('amount') or t.get('points') or ''}  {str(t.get('title') or t.get('description') or '')[:50]}")
    if not rows:
        print("  (пусто — операций по баллам нет)")
    return j


def subscription(s, h):
    """Подписка Магнит Плюс: статус и тарифы."""
    st = wget(s, h, "/v2/subscription/status", "статус подписки")
    cur = st.get("currentStatus")
    print(f"подписка: {cur}")
    if cur == "notSubscribed":
        tar = wget(s, h, "/v2/subscription/tariffs", "тарифы подписки")
        for t in (tar.get("tariffs") or [])[:5]:
            # priceWithVat у подписки в рублях, не в копейках (99 = 99 ₽)
            print(f"  {t.get('name')}  {t.get('priceWithVat')} ₽/{t.get('frequencyTitle')}"
                  + (f"  пробный {t['trialDays']} дн." if t.get("trialDays") else ""))
    return st


def returns_view(s, h):
    """Заявки на возврат."""
    j = wget(s, h, "/v2/returns", "возвраты")
    rows = j.get("returns") or []
    print(f"возвратов: {len(rows)}")
    for r in rows[:10]:
        print(f"  {r.get('orderId') or r.get('id')}  {r.get('status') or ''}  {str(r.get('createdAt') or '')[:10]}")
    return j


def cancel_reasons(s, h):
    """Почему можно отменить заказ (коды для --cancel)."""
    r = s.get(WG + "/v2/orders/cancel-reasons?deliveryMethod=delivery", headers=h, timeout=20)
    if r.status_code != 200:
        raise Fail(f"причины отмены: код {r.status_code}", "повторить позже")
    rows = r.json() if isinstance(r.json(), list) else (r.json().get("items") or [])
    for c in rows[:15]:
        print(f"  {c.get('code')}  {c.get('description')}")
    return rows


def order_info(s, h, oid):
    """Детали заказа по номеру."""
    j = wget(s, h, f"/v2/orders/info/{oid}", "детали заказа")
    print(json.dumps(j, ensure_ascii=False)[:1200])
    return j


def promo_gallery(s, h):
    """Промокоды, доступные аккаунту (в т.ч. на первый заказ)."""
    j = wget(s, h, "/v3/promo-gallery/promo-codes?service=express&deliveryType=delivery",
             "промокоды", timeout=30)
    rows = j.get("promocodes") or []
    print(f"промокодов: {len(rows)}")
    for p in rows[:15]:
        cond = " · ".join(x for x in (p.get("condition"), p.get("period")) if x)
        print(f"  {p.get('value') or p.get('code') or '?'}  {str(p.get('title') or '')[:45]}"
              + (f"  ({cond})" if cond else ""))
    return rows


def cancel_order(s, h, oid, confirm):
    """🔒 Отмена заказа. Без --confirm только говорит, что будет."""
    if not confirm:
        raise Fail(f"отмена заказа {oid} — действие, которое уже не отменить",
                   "повторить с флагом --confirm, если точно надо")
    j = wget(s, h, f"/v2/orders/cancel/{oid}", f"отмена заказа {oid}")
    print(f"✅ заказ {oid} отменён")
    return j


def reorder(s, h, oid, confirm):
    """🔒 Повторить заказ: товары снова кладутся в корзину (денег не тратит, корзину меняет)."""
    if not confirm:
        raise Fail(f"повтор заказа {oid} перезапишет текущую корзину",
                   "повторить с флагом --confirm, если точно надо")
    hh = dict(h, **{"content-type": "application/json"})
    r = s.post(WG + f"/v2/orders/reorder/{oid}", headers=hh, timeout=30)
    log(f"POST /v2/orders/reorder/{oid} → {r.status_code}")
    if r.status_code != 200:
        raise Fail(f"повтор заказа: код {r.status_code}, {r.text[:200]}", "проверить номер заказа")
    print(f"✅ заказ {oid} снова в корзине")
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="жива ли сессия и та ли корзина")
    ap.add_argument("--cart", action="store_true")
    ap.add_argument("--add", nargs="+", default=[])
    ap.add_argument("--weigh", nargs="+", default=[], metavar="КОД:ГРАММ",
                    help="весовой товар: 9072651210:2000 — 2 кг картофеля")
    ap.add_argument("--remove", nargs="+", default=[])
    ap.add_argument("--catalog", default="")
    ap.add_argument("--find", default="", help="поиск товара по точке (ассортимент, цены, наличие)")
    ap.add_argument("--promos", action="store_true", help="настоящие акции по отслеживаемым категориям")
    ap.add_argument("--snapshot", action="store_true", help="записать сегодняшние цены в журнал")
    ap.add_argument("--deals", action="store_true", help="акции, которые ниже своей медианы по журналу")
    ap.add_argument("--store", default=os.environ.get("MAGNIT_STORE", ""),
                    help="код магазина для --find (по умолчанию <код-магазина>, как сайт ставит по адресу)")
    ap.add_argument("--slots", action="store_true", help="слоты доставки: цена, порог, ближайшее окно")
    ap.add_argument("--preview", action="store_true", help="превью заказа: сумма, доставка, недоступные")
    ap.add_argument("--bonus", action="store_true", help="баллы Магнита")
    ap.add_argument("--coupons", action="store_true", help="купоны: сколько и что сгорит первым")
    ap.add_argument("--orders", action="store_true", help="активные заказы и история")

    ap.add_argument("--addresses", action="store_true", help="адреса доставки")
    ap.add_argument("--stores", type=int, nargs="?", const=5, default=0, metavar="N",
                    help="ближайшие магазины к адресу (по умолчанию 5)")
    ap.add_argument("--compare", default="", metavar="ТОВАР",
                    help="сравнить цену товара по ближайшим магазинам")
    ap.add_argument("--compare-top", type=int, default=8, metavar="N",
                    help="по скольким точкам сравнивать (по умолчанию 8)")
    ap.add_argument("--address-del", default="", metavar="ID", help="🔒 удалить адрес (нужен --confirm)")
    ap.add_argument("--payments", action="store_true", help="доступные способы оплаты")
    ap.add_argument("--cards", action="store_true", help="карты Магнита")
    ap.add_argument("--transactions", action="store_true", help="история баллов")
    ap.add_argument("--page", type=int, default=1, help="страница для --transactions")
    ap.add_argument("--subscription", action="store_true", help="подписка Магнит Плюс: статус и тарифы")
    ap.add_argument("--returns", action="store_true", help="возвраты")
    ap.add_argument("--cancel-reasons", action="store_true", help="причины отмены заказа")
    ap.add_argument("--order", default="", metavar="ID", help="детали заказа")
    ap.add_argument("--promocodes", action="store_true", help="промокоды аккаунта")
    ap.add_argument("--cancel", default="", metavar="ID", help="🔒 отменить заказ (нужен --confirm)")
    ap.add_argument("--reorder", default="", metavar="ID", help="🔒 повторить заказ (нужен --confirm)")
    ap.add_argument("--confirm", action="store_true", help="подтверждение необратимого действия")
    a = ap.parse_args()

    try:
        s, h = session()
        if a.slots:
            slots(s, h)
            return 0
        if a.preview:
            preview(s, h)
            return 0
        if a.bonus:
            bonus(s, h)
            return 0
        if a.coupons:
            coupons(s, h)
            return 0
        if a.orders:
            orders(s, h)
            return 0
        if a.addresses:
            addresses(s, h)
            return 0
        if a.stores:
            stores(s, h, a.stores)
            return 0
        if a.compare:
            compare(s, h, a.compare, a.compare_top)
            return 0
        if a.address_del:
            address_del(s, h, a.address_del, a.confirm)
            return 0
        if a.payments:
            payments(s, h)
            return 0
        if a.cards:
            cards(s, h)
            return 0
        if a.transactions:
            transactions(s, h, a.page)
            return 0
        if a.subscription:
            subscription(s, h)
            return 0
        if a.returns:
            returns_view(s, h)
            return 0
        if a.cancel_reasons:
            cancel_reasons(s, h)
            return 0
        if a.order:
            order_info(s, h, a.order)
            return 0
        if a.promocodes:
            promo_gallery(s, h)
            return 0
        if a.cancel:
            cancel_order(s, h, a.cancel, a.confirm)
            return 0
        if a.reorder:
            reorder(s, h, a.reorder, a.confirm)
            return 0
        if a.catalog:
            catalog(s, h, a.catalog)
            return 0
        if a.find:
            find(s, h, a.find, a.store)
            return 0
        if a.promos:
            promos(s, h, a.store)
            return 0
        if a.snapshot:
            snapshot(s, h, a.store)
            return 0
        if a.deals:
            deals(s, h, a.store)
            return 0
        j = get_cart(s, h)
        if a.check:
            live = sum(1 for i in j["items"] if i["qnty"] > 0)
            print(f"✅ сессия жива: корзина {j.get('id')}, позиций {live}")
            return 0
        if not (a.add or a.weigh or a.remove):
            show(j)
            return 0

        # Удаление — это qnty=0 в теле, а НЕ отсутствие строки: PUT без позиции Магнит
        # молча игнорирует (проверено 11.11). Весовым при удалении тоже 0.
        drop = set(a.remove)
        items = []
        for src in j["items"]:
            gid = src["goodId"]
            it = {"goodId": gid, "offerId": src["offerId"],
                  "qnty": 0 if gid in drop else src["qnty"]}
            if (src.get("increment") or {}).get("unit") == "weight":
                it["increment"] = {"unit": "weight", "value": it["qnty"]}
            items.append(it)
        by_id = {i["goodId"]: i for i in items if i["qnty"] > 0}

        def with_inc(item, inc):
            """increment кладём ТОЛЬКО весовым: со штучными Магнит молча игнорирует весь PUT
            (проверено 11.11: PUT с increment у штучных → 200 и корзина без изменений)."""
            if inc.get("unit") == "weight":
                item["increment"] = inc
            else:
                item.pop("increment", None)
            return item

        def put_item(gid, qnty, inc):
            """Новая позиция или оживление нулевой строки (товар кончился, потом появился снова)."""
            if gid in by_id:
                if by_id[gid]["qnty"] > 0:
                    print("уже в корзине:", gid)
                    return
                by_id[gid]["qnty"] = qnty
                with_inc(by_id[gid], inc)
                print(f"оживляю нулевую строку: {gid}")
                return
            items.append(with_inc({"goodId": gid, "offerId": gid, "qnty": qnty}, inc))
            by_id[gid] = items[-1]
            print(f"добавляю: {gid}" + (f" — {qnty / 1000:g} кг" if inc["unit"] == "weight" else ""))

        for gid in a.add:
            put_item(gid, 1, {"unit": "apiece", "value": 1})
        for pair in a.weigh:
            gid, _, grams = pair.partition(":")
            if not grams.isdigit():
                raise Fail(f"не поняла вес в «{pair}»", "писать так: 9072651210:2000 (код:граммы)")
            put_item(gid, int(grams), {"unit": "weight", "value": int(grams)})
        j2 = put_cart(s, h, items)
        print("--- после записи:")
        show(j2)
        # Сверка: что просили добавить, но не появилось живым (qnty>0). Магнит кладёт
        # недоступный товар нулевой строкой (проверено 11.11: молоко с остатком 1 на полке).
        want_ids = set(a.add) | {p.split(":", 1)[0] for p in a.weigh}
        live_ids = {i["goodId"] for i in j2["items"] if i["qnty"] > 0}
        missing = sorted(want_ids - live_ids)
        if missing:
            print("❌ нет в наличии в этой точке: " + ", ".join(missing))
            print("   подбери замену: --find «название» (покажет остаток), потом --add/--remove")
        return 0
    except Fail as e:
        return die(e)


if __name__ == "__main__":
    sys.exit(main())
