#!/usr/bin/env python3
"""Датчик меток `факт` в выдаче (HTML/MD). Код 0 — чисто, 1 — есть нарушения.

Нарушение: `факт` без источника; `факт` со ссылкой на закон без «сверено».
Ловит небрежность, не ложь: верность самого источника не проверяет.
Правил датчик → прогнать check_facts_test.py и .claude/hooks/bash-guard_test.py.
"""
import re
import sys

BLOCK = r'</?(td|th|tr|li|p|div|br|h\d|section|table|ul|ol)\b[^>]*>'
LAW = re.compile(r'ФЗ|РЗ|\bНК\b|\bст\.|[Зз]акон|[Пп]остановлени')


def segments(text):
    text = re.sub(r'<(script|style)\b.*?</\1>', ' ', text, flags=re.S)
    text = re.sub(BLOCK, ' | ', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    for m in re.finditer(r'(?<![\w-])факт(?![\w-])', text):
        tail = re.split(r'\||\.\s+(?=[А-ЯA-Z])', text[m.end():], maxsplit=1)[0].strip()
        if tail.startswith(('—', '/')):
            continue
        yield text[max(0, m.start() - 60):m.start()].strip(), tail


def main(path):
    text = open(path, encoding='utf-8').read()
    total, bad = 0, []
    for before, tail in segments(text):
        total += 1
        src = re.sub(r'^(,|\(|·|по\b)\s*', '', tail) if re.match(r'(,|\(|·|по\b)', tail) else ''
        if not src:
            bad.append(f'✗ нет источника: «…{before} факт»')
        elif LAW.search(src.split(')', 1)[0]) and 'сверено' not in src:
            bad.append(f'✗ закон без «сверено по тексту»: «…{before} факт, {src[:80]}»')
    for line in bad:
        print(line)
    print(f'Итого: {len(bad)} нарушений из {total} меток `факт`')
    return 1 if bad else 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: check_facts.py <файл.html|.md>')
    sys.exit(main(sys.argv[1]))
