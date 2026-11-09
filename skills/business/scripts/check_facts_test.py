import os, subprocess, tempfile
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_facts.py")
# (текст выдачи, ждём код) — каждое правило датчика отдельным случаем (Урок 67, Л7)
cases = [
    ("<td>Касса</td><td>факт</td>", 1),
    ("<td>Касса</td><td>факт, 54-ФЗ ст. 4.3</td>", 1),
    ("<td>Касса</td><td>факт, 54-ФЗ ст. 4.3, сверено по тексту 2026-10-04</td>", 0),
    ("<td>Курс</td><td>факт · ЦБ РФ на 2026-09-29</td>", 0),
    ("<p>Цифра (факт, Минсельхоз Коми, 2026), а закон 19-РЗ ввёл запрет</p>", 0),
    ("<footer>Метки: факт / гипотеза.</footer>", 0),
    ("<p>Таблица план-факт</p>", 0),
]
bad = 0
for text, want in cases:
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(text)
    rc = subprocess.run(["python3", S, f.name], capture_output=True).returncode
    os.unlink(f.name)
    bad += rc != want
    print("OK " if rc == want else "BAD", rc, repr(text[:60]))
print("ошибок:", bad)
