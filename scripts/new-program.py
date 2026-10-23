#!/usr/bin/env python3
"""Запрошення писати нашою мовою: створити скелет програми одним рухом.

Навіщо: охоронець НЕ ДАЄ писати погано. Це — протилежне: ЗАПРОШУЄ писати добре.
Агент має почати програму одним рухом, як `cargo new`, а не тримати формат напам'ять.

Що робить:
  1) створює lib/<назва>.lisp з правильним заголовком і скелетом;
  2) вживає поверхні драбини (показує, ЯК це робиться на прикладі);
  3) проганяє охоронця — щоб скелет одразу був чистий;
  4) друкує наступні кроки.

    python3 scripts/new-program.py моя-функція
    python3 scripts/new-program.py моя-функція --body "(перше значення-аргументу)"
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEMPLATE = """\
; {name} — програма нашою мовою (укр-проєкція).
;
; Пишемо ІМЕНАМИ, не кодами: жодних числових голів.
; Беремо наявні поверхні драбини D1–D10, а не вигадуємо свої.
; Якщо потрібної функції немає — охоронець підкаже: вжити наявне або
; зареєструвати кандидата D11 (`; D11-пропозиція: <причина>` перед визначенням).
;
; Перевірити: python3 scripts/guard-domain-function-reuse.py --file lib/{name}.lisp --advise
(визначити {name}
  (функція (значення-аргументу)
    {body}))
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="створити скелет програми нашою мовою")
    ap.add_argument("name", help="ім'я програми (укр-проєкція, через дефіс)")
    ap.add_argument("--body", default="значення-аргументу",
                    help="тіло: вираз із поверхонь драбини (типово — тотожність)")
    args = ap.parse_args(argv)

    name = args.name.strip()
    if not name or any(c in name for c in " \t/\\"):
        print("ім'я мусить бути одним словом укр-проєкції, без пробілів і слешів", file=sys.stderr)
        return 2
    # ПОШУК ЗАПУСКАЄТЬСЯ САМ — до створення. Агент не мусить пам'ятати
    # про окрему команду: скафолд одразу показує, чи є схоже наявне.
    print("пошук наявного (щоб не вигадувати):")
    sr = subprocess.run([sys.executable, str(ROOT / "scripts" / "search-domain-function.py"), name],
                        cwd=ROOT, capture_output=True, text=True)
    out = (sr.stdout + sr.stderr).strip().splitlines()
    for line in out[:8]:
        print("  " + line)
    print()

    target = ROOT / "lib" / f"{name}.lisp"
    if target.exists():
        print(f"уже існує: lib/{name}.lisp — не перезаписую", file=sys.stderr)
        return 1
    target.write_text(TEMPLATE.format(name=name, body=args.body), encoding="utf-8")
    print(f"створено: lib/{name}.lisp")
    print("  заголовок пояснює правила; тіло — {0}".format(args.body))
    print()
    print("наступні кроки:")
    print(f"  1) допиши тіло у lib/{name}.lisp")
    print(f"  2) перевір: python3 scripts/guard-domain-function-reuse.py --file lib/{name}.lisp --advise")
    print(f"  3) якщо потрібної функції немає — scripts/add-d11-function.py <назва>")

    # Одразу прогнати охоронця, щоб скелет був чистий і агент побачив приклад відгуку.
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "guard-domain-function-reuse.py"),
         "--file", f"lib/{name}.lisp", "--advise"],
        cwd=ROOT, capture_output=True, text=True)
    print()
    print("охоронець каже:")
    for line in (r.stdout + r.stderr).splitlines()[-4:]:
        print("  " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
