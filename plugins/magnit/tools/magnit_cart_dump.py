#!/usr/bin/env python3
"""Разовый дамп корзины Магнита: что реально лежит, с именами и ценами. Только чтение, ничего не меняет.

Использует настройки и функции magnit_cart.py (профиль, куки, адрес, поиск магазина).
    xvfb-run -a python3 magnit_cart_dump.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import magnit_cart as m            # noqa: E402
from playwright.sync_api import sync_playwright   # noqa: E402


def main():
    os.makedirs(m.PROFILE, exist_ok=True)
    for f in os.listdir(m.PROFILE):
        if f.startswith("Singleton"):
            os.remove(os.path.join(m.PROFILE, f))
    raw = []
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
            if "/carts/lite" in r.url and r.request.method == "GET":
                try:
                    raw.append(r.json())
                except Exception:
                    pass
        pg.on("response", grab)
        m.nav(pg, "https://magnit.ru/", 20000)
        print("адрес:", m.pick_delivery(pg), flush=True)
        # /cart на сервере пустой («Здесь ничего не нашлось») — пробуем выдвижную мини-корзину из нижнего меню
        clicked = False
        try:
            clicked = pg.evaluate("""() => {
                const els = [...document.querySelectorAll('a,button,div,span')]
                    .filter(e => e.textContent.trim() === 'Корзина' && e.getBoundingClientRect().top > 700);
                if (!els.length) return false;
                els[els.length - 1].click();
                return true;
            }""")
        except Exception as e:
            print("клик не вышел:", e, flush=True)
        print("клик по корзине:", clicked, flush=True)
        pg.wait_for_timeout(15000)
        body = " ".join(pg.inner_text("body").split())
        print("страница корзины (начало):", body[:800], flush=True)
        out = os.path.expanduser("files_out/magnit_cart_dump.png")
        pg.screenshot(path=out, full_page=True)
        print("скриншот:", out, flush=True)
        if raw:
            j = raw[-1]
            print("ключи /carts/lite:", list(j.keys())[:12], flush=True)
            print("RAW:", json.dumps(j, ensure_ascii=False)[:1200], flush=True)
        else:
            print("carts/lite не ответил", flush=True)
        ctx.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
