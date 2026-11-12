#!/usr/bin/env python3
"""Разовый снимок заголовков API корзины Магнита: один заход браузером, потом тот же GET через requests.

Нужен, чтобы дальше класть товары в корзину без браузера (секунды вместо минут).
Секреты в чат не печатаются: заголовки и куки пишутся в /tmp, на экран — только имена и цифры.

    xvfb-run -a python3 magnit_api_probe.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import magnit_cart as m            # noqa: E402
import requests                    # noqa: E402
from playwright.sync_api import sync_playwright   # noqa: E402

CAP = {"headers": None, "url": None, "json": None}


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

        def on_req(r):
            if "/carts/lite" in r.url and r.method == "GET" and CAP["headers"] is None:
                CAP["headers"] = dict(r.headers)
                CAP["url"] = r.url

        def on_resp(r):
            if "/carts/lite" in r.url and r.request.method == "GET":
                try:
                    CAP["json"] = r.json()
                except Exception:
                    pass
        pg.on("request", on_req)
        pg.on("response", on_resp)

        m.nav(pg, "https://magnit.ru/", 20000)
        print("адрес:", m.pick_delivery(pg), flush=True)
        pg.wait_for_timeout(8000)
        cookies = ctx.cookies()
        ctx.close()

    hdr = CAP["headers"] or {}
    print("перехвачено заголовков:", len(hdr), "| имена:", ", ".join(sorted(hdr))[:400], flush=True)
    print("корзина в браузере:", len((CAP["json"] or {}).get("items") or []), "позиций, id:",
          (CAP["json"] or {}).get("id"), flush=True)

    req_hdr = {k: v for k, v in hdr.items()
               if not k.startswith(":") and k.lower() not in ("cookie", "content-length", "host")}
    cookies_simple = {c["name"]: c["value"] for c in cookies if c["domain"].endswith("magnit.ru")}
    with open(os.path.expanduser("~/.magnit/magnit_api_headers.json"), "w") as f:
        json.dump({"headers": req_hdr, "cookies": cookies_simple, "url": CAP["url"]}, f)
    print("снимок записан в ~/.magnit/magnit_api_headers.json (секреты на экран не вывожу)", flush=True)

    if not CAP["url"]:
        print("ОШИБКА: приложение не запросило /carts/lite — нечего повторять", flush=True)
        return 1

    s = requests.Session()
    s.cookies.update(cookies_simple)
    r = s.get(CAP["url"], headers=req_hdr, timeout=30)
    print("повтор через requests: http", r.status_code, flush=True)
    try:
        j = r.json()
        print("id:", j.get("id"), "| позиций:", len(j.get("items") or []),
              "| сумма, коп:", j.get("totalFinalPrice"), flush=True)
    except Exception:
        print(r.text[:200], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
