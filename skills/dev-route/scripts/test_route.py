#!/usr/bin/env python3
"""Тест забора: python3 test_route.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

R = Path(__file__).resolve().parent / "route.py"


def run(*args):
    return subprocess.run([sys.executable, str(R), *map(str, args)], capture_output=True, text=True)


with tempfile.TemporaryDirectory() as d:
    f = Path(d) / "ROUTE.md"
    assert run("init", str(f), "--name", "t", "--track", "lite").returncode == 0
    text = f.read_text()
    assert "## 2." not in text and "## 5." not in text and "## 3." in text, "лёгкий трек без 2 и 5"
    assert run("init", str(f), "--name", "t").returncode != 0, "не затирает существующий"

    assert run("gate", str(f), 1).returncode == 0, "первый этап открыт всегда"
    r = run("gate", str(f), 3)
    assert r.returncode == 1 and "Пользователь" in r.stdout, "этап 3 закрыт, пока 1 не отмечен"
    assert run("gate", str(f), 2).returncode != 0, "этапа 2 нет в лёгком треке"

    s1 = text.split("## 3.")[0]
    f.write_text(s1.replace("- [ ]", "- [x]") + "## 3." + text.split("## 3.", 1)[1])
    assert run("gate", str(f), 3).returncode == 0, "этап 1 отмечен — этап 3 можно"
    assert run("gate", str(f), 4).returncode == 1, "этап 3 не отмечен — этап 4 нельзя"
    assert "3. Прожарка" in run("status", str(f)).stdout

print("ok")
