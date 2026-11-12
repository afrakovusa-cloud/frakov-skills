#!/usr/bin/env python3
"""Собрать корзину Магнита под аккаунтом пользователя. Заказ НЕ оформляет — только кладёт товары.

Запуск (на VPS; экран обязателен — headless режет антифрод Магнита):
    xvfb-run -a python3 magnit_cart.py --add "молоко, хлеб"
    xvfb-run -a python3 magnit_cart.py --cart
    ... --show   — плюс скриншот в files_out/magnit_cart.png

Куки: ~/.magnit/magnit_cookies.txt (Netscape, снимаются с Chrome пользователя на домашней машины ).
Опционально: MAGNIT_PROXY=http://host:port — если сайт банит IP сервера, трафик идёт через ваш прокси.
С IP сервера Магнит отдаёт 403/498 — без туннеля не работать.
"""
import argparse
import json
import os
import subprocess
import sys

from playwright.sync_api import sync_playwright


def _find_chrome():
    """Chromium из Playwright — путь с версией зависит от установки."""
    import glob
    base = os.path.expanduser("~/.cache/ms-playwright")
    hits = sorted(glob.glob(base + "/chromium-*/chrome-linux64/chrome"))
    return hits[-1] if hits else ""


HOME = os.path.expanduser("~")
CHROME = os.environ.get("MAGNIT_CHROME") or _find_chrome()
COOKIES = f"{HOME}/.magnit/magnit_cookies.txt"
PROFILE = f"{HOME}/.magnit/profile"
PROXY = os.environ.get("MAGNIT_PROXY", "")   # опционально: если сайт банит IP сервера
ADDRESS = os.environ.get("MAGNIT_ADDRESS", "")   # часть адреса доставки, чтобы найти нужную точку в списке
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/157.0.0.0 Safari/537.36")
CART = {}


def jar():
    out = []
    with open(COOKIES, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            host, _tail, path, secure, exp, name, val = line.rstrip("\n").split("\t")
            out.append({"name": name, "value": val, "domain": host, "path": path,
                        "secure": secure == "TRUE", "httpOnly": False,
                        "expires": int(exp) if int(exp) > 0 else -1})
    return out


def tunnel_ok():
    if not PROXY:
        return True
    p = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "40",
                        "-x", PROXY, "https://api.ipify.org"], capture_output=True, text=True)
    return p.stdout.strip() == "200"


def hook_cart(pg):
    """Приложение само тянет GET /carts/lite на каждой странице — запоминаем последнее число позиций."""
    def hook(r):
        if "/carts/lite" in r.url and r.request.method == "GET":
            try:
                j = r.json()
            except Exception:
                return
            for k in ("items", "products", "positions", "lines"):
                if not isinstance(j.get(k), list):
                    continue
                CART["n"] = len(j[k])
                rows = []
                for it in j[k]:
                    g = it.get("good") or it
                    price = it.get("price") or it.get("totalPrice") or g.get("price")
                    rows.append((g.get("name") or it.get("name") or "?", it.get("qnty") or it.get("quantity") or 1, price))
                CART["rows"] = rows
                CART["sum"] = j.get("totalSum") or j.get("total") or j.get("sum")
                return
    pg.on("response", hook)


def pick_delivery(pg):
    """Жёстко поставить доставку на адрес пользователя.

    По умолчанию сайт ставит магазин по IP («Самовывоз • Гипер, Краснодар»), поэтому идём через чип в шапке.
    После «Подтвердить» ждём, пока в URL появится shopCode — это признак, что контекст магазина встал.
    """
    el = (pg.query_selector('button:has-text("Самовывоз")')
          or pg.query_selector('button:has-text("Доставка")')
          or pg.query_selector('button:has-text("Выберите магазин")'))
    if el is None:
        # второй вид: всплывающее окно «Выберите магазин или адрес» → «Выбрать»
        for b in pg.query_selector_all("button"):
            if (b.inner_text() or "").strip() == "Выбрать":
                el = b
                break
    if el is None:
        el = pg.query_selector('text=Выберите магазин или')     # в этом состоянии подпись — span, не кнопка
    if el is None:
        return "ОШИБКА: нет ни чипа магазина, ни кнопки «Выбрать»"
    el.click()
    pg.wait_for_timeout(4000)
    segs = pg.query_selector_all('input[data-test-id="v-segment-control"]')
    if segs:
        segs[0].check(force=True)        # [0] = «Доставка»
        pg.wait_for_timeout(5000)
    a = pg.query_selector(f"text={ADDRESS}")
    if a is None:
        return f"ОШИБКА: адрес «{ADDRESS}» не найден среди сохранённых"
    a.click()
    pg.wait_for_timeout(1500)
    for b in pg.query_selector_all("button"):
        if "Подтвердить" in (b.inner_text() or ""):
            b.click()
            break
    for _ in range(30):                  # ждём контекст магазина в URL
        if "shopCode=" in pg.url:
            break
        pg.wait_for_timeout(2000)
    pg.wait_for_timeout(12000)           # страница дорисовывается
    head = " ".join(pg.inner_text("body").split())[:220]
    if ADDRESS not in head:
        return f"ОШИБКА: в шапке не {ADDRESS}: {head[:140]}"
    return f"доставка выбрана, {pg.url.split('?')[-1]}"


def find_cart_buttons(pg, timeout_ms=90000):
    """Кнопки «В корзину» на странице; ждём появления (спутник рисует страницу долго)."""
    import time
    end = time.time() + timeout_ms / 1000
    while time.time() < end:
        btns = [b for b in pg.query_selector_all("button")
                if "корзину" in (b.inner_text() or "").lower()]
        if btns:
            return btns
        pg.wait_for_timeout(2000)
    return []


def nav(pg, url, wait_ms=18000, tries=2):
    """Переход с повтором: на спутнике страница иногда падает в «Проблема соединения»."""
    for i in range(tries):
        pg.goto(url, wait_until="commit", timeout=180000)
        pg.wait_for_timeout(wait_ms)
        body = " ".join(pg.inner_text("body").split())
        if "Проблема соединения" not in body:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--add", default="", help="через запятую: что положить в корзину")
    ap.add_argument("--cart", action="store_true", help="только показать корзину")
    ap.add_argument("--show", action="store_true", help="скриншот в files_out")
    a = ap.parse_args()

    if not tunnel_ok():
        print("ОШИБКА: MAGNIT_PROXY не отвечает — прокси недоступен. "
              "Скажи пользователю прямо, работу не изображай.")
        return 2
    if not os.path.exists(CHROME):
        print("ОШИБКА: нет Chromium", CHROME)
        return 2

    os.makedirs(PROFILE, exist_ok=True)
    for f in os.listdir(PROFILE):                 # после убитого браузера остаётся замок профиля
        if f.startswith("Singleton"):
            os.remove(os.path.join(PROFILE, f))

    res = {"items": {}, "cart": None}
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, executable_path=CHROME, headless=False, locale="ru-RU",
            user_agent=UA, viewport={"width": 430, "height": 900},
            **(dict(proxy={"server": PROXY}) if PROXY else {}),
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                  "--no-first-run", "--no-default-browser-check"])
        # канал спутниковый: картинки/шрифты не нужны, кнопки и данные нужны
        ctx.route("**/*", lambda r: r.abort() if r.request.resource_type in ("image", "media", "font")
                  else r.continue_())
        ctx.add_cookies(jar())        # сессия пользователя
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        hook_cart(pg)
        nav(pg, "https://magnit.ru/", 20000)
        print("url:", pg.url)
        who = pick_delivery(pg)
        print("адрес:", who)
        if who.startswith("ОШИБКА"):
            print("Стоп: без нужного адреса товар не кладу — иначе уйдёт в магазин по IP (Краснодар).")
            ctx.close()
            return 3
        if not a.cart:
            queries = [x.strip() for x in a.add.split(",") if x.strip()]
            for i, q in enumerate(queries, 1):
                print(f"[{i}/{len(queries)}] ищу: {q}", flush=True)
                try:
                    pg.goto(f"https://magnit.ru/search?target={q}", wait_until="commit", timeout=180000)
                    btns = find_cart_buttons(pg)
                    if not btns:
                        res["items"][q] = "нет кнопки «В корзину» на странице поиска"
                        continue
                    # текст карточки — оттуда имя и цена для отчёта пользователю
                    btns[0].click(timeout=25000)
                    pg.wait_for_timeout(5000)
                    res["items"][q] = "положено"
                    print(f"[{i}/{len(queries)}] положено: {q}", flush=True)

                except Exception as e:
                    res["items"][q] = f"ошибка: {str(e)[:80]}"
        if not a.show:
            nav(pg, "https://magnit.ru/", 12000)
        n = CART.get("n")
        res["cart"] = f"{n} позиций" if n is not None else "корзина не ответила"
        res["link"] = "https://magnit.ru/cart"      # откроется в его аккаунте с уже выбранным магазином
        if CART.get("sum") is not None:
            res["сумма"] = CART["sum"]
        if a.show:
            out = f"{HOME}/.magnit/files_out/magnit_cart.png"
            os.makedirs(os.path.dirname(out), exist_ok=True)
            nav(pg, "https://magnit.ru/cart", 15000, tries=1)
            body = " ".join(pg.inner_text("body").split())
            if "Gateway" in body or "ничего не нашлось" in body:   # страница корзины не отдалась — снимаем шапку с бейджем
                nav(pg, "https://magnit.ru/", 12000, tries=1)
            pg.screenshot(path=out, full_page=False)
            res["shot"] = out
            res["shot_text"] = " ".join(pg.inner_text("body").split())[:200]
        ctx.close()

    print(json.dumps(res, ensure_ascii=False, indent=1))
    print("Заказ НЕ оформлен — подтверждает владелец.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
