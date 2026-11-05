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
    r = run("gate", str(f), 3)
    assert r.returncode == 1 and "BRIEF.md" in r.stdout, "галочки есть, BRIEF.md нет — нельзя"
    (Path(d) / "BRIEF.md").write_text("бриф")
    assert run("gate", str(f), 3).returncode == 0, "этап 1 отмечен и BRIEF.md есть — этап 3 можно"
    assert run("gate", str(f), 4).returncode == 1, "этап 3 не отмечен — этап 4 нельзя"
    assert "3. Прожарка" in run("status", str(f)).stdout

# находка 14: этап пропущен решением пользователя — забор пускает без файлов этапа
with tempfile.TemporaryDirectory() as d:
    f = Path(d) / "ROUTE.md"
    run("init", str(f), "--name", "t", "--track", "full")
    text = f.read_text()
    s1, rest = text.split("## 3.", 1)
    s1 = s1.replace("- [ ]", "- [x]")
    s1 = s1.replace("- [x] Пользователь сказал «этап закрыт»\n\n## 3", "- [x] Пользователь сказал «этап закрыт»\n\n## 3")
    head, s2 = s1.split("## 2.", 1)
    s2 = s2.replace("- [x] Пользователь сказал «этап закрыт»", "- [~] пропущено пользователем: исследование не нужно (2026-11-04)")
    f.write_text(head + "## 2." + s2 + "## 3." + rest)
    (Path(d) / "BRIEF.md").write_text("бриф")
    r = run("gate", str(f), 3)
    assert r.returncode == 0, "этап 2 пропущен пользователем — RESEARCH.md не нужен: " + r.stdout

# находка 15: фича в своей папке — основные файлы проекта ей не засчитываются
with tempfile.TemporaryDirectory() as d:
    for name in ["GRILL.md", "PRD.md", "CONTEXT.md", "PHILOSOPHY.md"]:
        (Path(d) / name).write_text("основной проект")
    f = Path(d) / "features" / "x" / "ROUTE.md"
    assert run("init", str(f), "--name", "x", "--track", "feature").returncode == 0, "init создаёт папку фичи"
    assert "## 5." in f.read_text(), "в треке фичи есть второе мнение"
    text = f.read_text()
    s3, rest = text.split("## 4.", 1)
    f.write_text(s3.replace("- [ ]", "- [x]") + "## 4." + rest)
    r = run("gate", str(f), 4)
    assert r.returncode == 1 and "GRILL.md" in r.stdout, "GRILL.md основного проекта фиче не засчитан"
    (f.parent / "GRILL.md").write_text("прожарка фичи")
    assert run("gate", str(f), 4).returncode == 1, "без FEATURE.md этап 3 фичи не закрыт"
    (f.parent / "FEATURE.md").write_text("описание фичи")
    assert run("gate", str(f), 4).returncode == 0, "свой GRILL.md есть — этап 4 можно"

# аудит-2, №7: status видит отсутствующий файл так же, как gate
with tempfile.TemporaryDirectory() as d:
    f = Path(d) / "ROUTE.md"
    run("init", str(f), "--name", "t", "--track", "lite")
    text = f.read_text()
    s1, rest = text.split("## 3.", 1)
    f.write_text(s1.replace("- [ ]", "- [x]") + "## 3." + rest)
    out = run("status", str(f)).stdout
    assert "1. Голос" in out and "BRIEF.md" in out, "status ведёт на этап без файла, а не дальше: " + out

print("ok")
