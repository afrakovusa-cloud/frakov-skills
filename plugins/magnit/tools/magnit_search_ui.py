#!/usr/bin/env python3
"""Что реально продаётся в магазине доставки пользователя: страница поиска Магнита в контексте его точки.

Нужно, когда API кладёт товар, а корзина показывает 0 шт: значит, этой позиции в магазине нет.
Печатает карточки (название, цена, признак наличия, ссылка с кодом товара).

    xvfb-run -a python3 magnit_search_ui.py "молоко 2.5" "творог 5"
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import magnit_cart as m            # noqa: E402
from playwright.sync_api import sync_playwright   # noqa: E402

JS = """() => [...document.querySelectorAll('a[href*="/product/"]')].slice(0, 40).map(a => {
    let box = a; for (let i = 0; i < 5 && box.parentElement; i++) box = box.parentElement;
    return {href: a.getAttribute('href'), text: (box.innerText || '').replace(/\\s+/g, ' ').slice(0, 220)};
})"""


def main(queries):
    os.makedirs(m.PROFILE, exist_ok=True)
    for f in os.listdir(m.PROFILE):
        if f.startswith("Singleton"):
            os.remove(os.path.join(m.PROFILE, f))
    out = {}
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
        m.nav(pg, "https://magnit.ru/", 20000)
        print("адрес:", m.pick_delivery(pg), flush=True)
        for q in queries:
            url = f"https://magnit.ru/search?target={q}&shopCode=ВАШ_КОД_МАГАЗИНА&shopType=express"
            m.nav(pg, url, 12000, tries=1)
            for _ in range(12):                      # ждём карточки до 90 с
                if pg.query_selector('a[href*="/product/"]'):
                    break
                pg.wait_for_timeout(8000)
            rows = pg.evaluate(JS)
            out[q] = rows
            print(f"\n== {q}: карточек {len(rows)}", flush=True)
            for r in rows[:8]:
                t = r["text"]
                flag = "есть" if "В корзину" in t else ("НЕТ" if "Нет в наличии" in t or "Закончился" in t else "?")
                print(f"  [{flag}] {t[:150]} | {r['href'][:60]}", flush=True)
        pg.screenshot(path=os.path.expanduser("files_out/magnit_search.png"))
        ctx.close()
    with open("/tmp/magnit_search_ui.json", "w") as f:
        json.dump(out, f, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
