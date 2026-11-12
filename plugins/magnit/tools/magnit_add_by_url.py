#!/usr/bin/env python3
"""Положить в корзину Магнита конкретные товары по прямым ссылкам — с проверкой, что позиция реально добавилась.

Зачем: magnit_cart.py --add ищет по слову и жмёт первую «В корзину» на странице поиска;
если страница не догрузилась, он жмёт кнопки с прошлой страницы и молча рапортует «положено».
Здесь товар открывается карточкой по URL, а результат сверяется по /carts/lite (растёт ли число позиций).

    xvfb-run -a python3 magnit_add_by_url.py <url1> <url2> ...
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import magnit_cart as m            # noqa: E402
from playwright.sync_api import sync_playwright   # noqa: E402

SHOP = "shopCode=ВАШ_КОД_МАГАЗИНА&shopType=express"   # ваш магазин доставки
STATE = {"n": None, "total": None}


def clean(url):
    return url.split("?")[0] + "?" + SHOP


def main(urls):
    os.makedirs(m.PROFILE, exist_ok=True)
    for f in os.listdir(m.PROFILE):
        if f.startswith("Singleton"):
            os.remove(os.path.join(m.PROFILE, f))
    res = []
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            m.PROFILE, executable_path=m.CHROME, headless=False, locale="ru-RU",
            user_agent=m.UA, viewport={"width": 430, "height": 900},
            **(dict(proxy={"server": m.PROXY}) if m.PROXY else {}),
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                  "--no-first-run", "--no-default-browser-check"])
        ctx.route("**/*", lambda r: r.abort() if r.request.resource_type in ("image", "media", "font")
                  else r.continue_())
        ctx.add_cookies(m.jar())
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()

        def hook(r):
            if "/carts/lite" in r.url and r.request.method == "GET":
                try:
                    j = r.json()
                except Exception:
                    return
                if isinstance(j.get("items"), list):
                    STATE["n"] = len(j["items"])
                    STATE["total"] = j.get("totalFinalPrice")
        pg.on("response", hook)

        m.nav(pg, "https://magnit.ru/", 20000)
        print("адрес:", m.pick_delivery(pg), flush=True)
        pg.wait_for_timeout(6000)
        print("в корзине было:", STATE["n"], "позиций, сумма", STATE["total"], flush=True)

        for url in urls:
            before = STATE["n"]
            name = ""
            try:
                m.nav(pg, clean(url), 12000, tries=1)
                h1 = pg.query_selector("h1")
                name = " ".join(h1.inner_text().split()) if h1 else ""
                btn = None
                for b in pg.query_selector_all("button"):
                    if "корзину" in (b.inner_text() or "").lower():
                        btn = b
                        break
                if btn is None:
                    res.append({"url": url, "name": name, "result": "нет кнопки «В корзину»"})
                    continue
                btn.click(timeout=25000)
                for _ in range(15):                 # ждём, пока число позиций вырастет
                    pg.wait_for_timeout(2000)
                    if STATE["n"] is not None and before is not None and STATE["n"] > before:
                        break
                ok = STATE["n"] is not None and before is not None and STATE["n"] > before
                res.append({"url": url, "name": name,
                            "result": "добавлено" if ok else "НЕ добавлено (счётчик не вырос)",
                            "cart": STATE["n"]})
                print(f"[{name[:40] or url[-30:]}] {'ОК' if ok else 'НЕТ'}, в корзине {STATE['n']}", flush=True)
            except Exception as e:
                res.append({"url": url, "name": name, "result": f"ошибка: {str(e)[:90]}"})
                print("ошибка:", str(e)[:90], flush=True)

        print(json.dumps({"items": res, "cart": STATE["n"], "сумма_коп": STATE["total"]},
                         ensure_ascii=False, indent=1), flush=True)
        ctx.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
