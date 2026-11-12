#!/usr/bin/env python3
"""Разовый снимок: каким запросом сайт Магнита ищет товары (чтобы потом искать без браузера).

Открывает главную, ставит доставку пользователя, вводит слово в поле поиска, ловит XHR,
в ответе которого есть название товара, и печатает адрес запроса + образец тела.
Секреты на экран не выводятся.

    xvfb-run -a python3 magnit_search_probe.py картофель
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import magnit_cart as m            # noqa: E402
from playwright.sync_api import sync_playwright   # noqa: E402

WORD = sys.argv[1] if len(sys.argv) > 1 else "картофель"
HITS = []


os.makedirs(os.path.expanduser("~/.magnit"), exist_ok=True)


def main():
    os.makedirs(m.PROFILE, exist_ok=True)
    for f in os.listdir(m.PROFILE):
        if f.startswith("Singleton"):
            os.remove(os.path.join(m.PROFILE, f))
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

        def grab(r):
            if r.request.method != "GET" and r.request.method != "POST":
                return
            if "/webgate/" not in r.url:
                return
            try:
                body = r.text()
            except Exception:
                return
            if WORD.lower()[:5] in body.lower() and len(body) < 400000:
                HITS.append({"method": r.request.method, "url": r.url,
                             "post": r.request.post_data, "sample": body[:300]})
        pg.on("response", grab)
        m.nav(pg, "https://magnit.ru/", 20000)
        print("адрес:", m.pick_delivery(pg), flush=True)

        box = (pg.query_selector('input[placeholder*="Искать"]')
               or pg.query_selector('input[type="search"]'))
        if box is None:
            print("ОШИБКА: нет поля поиска")
            ctx.close()
            return 1
        box.click()
        box.type(WORD, delay=60)
        pg.wait_for_timeout(1500)
        box.press("Enter")
        pg.wait_for_timeout(15000)
        print("карточек на странице:", len(pg.query_selector_all('a[href*="/product/"]')), flush=True)
        ctx.close()

    seen = set()
    for h in HITS:
        key = h["url"].split("?")[0]
        if key in seen:
            continue
        seen.add(key)
        print("\nURL:", h["url"][:300])
        if h["post"]:
            print("POST:", h["post"][:300])
        print("ответ:", " ".join(h["sample"].split())[:250])
    with open(os.path.expanduser("~/.magnit/magnit_search_probe.json"), "w") as f:
        json.dump(HITS, f, ensure_ascii=False)
    print("\nвсего попаданий:", len(HITS), "| уникальных адресов:", len(seen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
