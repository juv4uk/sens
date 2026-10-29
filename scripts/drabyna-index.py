#!/usr/bin/env python3
"""Охоронець драбини: індекс усіх визначень SENS.

Навіщо: агент, який пише програму, мусить знати, які функції вже є в
драбині д1-10, ПЕРЕД тим як писати нові. Цей скрипт будує такий індекс
з джерел, а не з пам'яті.

Що дає на кожну функцію:
  домен   — д1..д11 за назвою, або «загальна»
  файл    — де визначено
  рядок   — точний рядок
  уживань — скільки разів ім'я зустрічається в lib/**
  арність — кількість параметрів у формі визначення, якщо її видно

Чому домен за назвою, а не за файлом: файли lib/domains/d*.lisp — це
ТАБЛИЦІ доменів (проєкції, координати), а не визначення функцій.
Визначення живуть у lib/**. Тому прив'язка до домену йде через префікс
назви (д1-, д7-, д10-) або через явну таблицю нижче.

Вихід:
  knowledge/drabyna-index.json  — машинний індекс
  knowledge/drabyna.md          — людський довідник (укр проєкція)
"""
import collections
import json
import pathlib
import re
import sys

# Префікси назв -> домен. Порядок важливий: довші першими.
DOMAIN_PREFIXES = [(f"д{n}-", f"д{n}") for n in range(12, 0, -1)]


def domain_of(name: str) -> str:
    for prefix, domain in DOMAIN_PREFIXES:
        if name.startswith(prefix):
            return domain
    return "загальна"


def arity_of(line: str) -> int | None:
    """Арність із ЧИННОЇ форми визначення SENS.

    Справжня форма (lib/core.lisp):
        (визначити друге
          (функція (значення-функції)
            (перше (решта значення-функції))))

    Тобто параметри всередині (функція ...), а не одразу після імені.
    Перша версія цього не враховувала і давала () майже завжди.
    """
    match = re.search(r"\(\s*функція\s*\(([^()]*)\)", line)
    if not match:
        return None
    body = match.group(1).strip()
    if not body:
        return 0
    return len([part for part in body.split() if part])


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    lib = root / "lib"
    if not lib.is_dir():
        print(f"немає {lib}", file=sys.stderr)
        return 1

    definitions: dict[str, dict] = {}
    usage: collections.Counter = collections.Counter()
    files = sorted(lib.rglob("*.lisp"))

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(path.relative_to(root))
        for number, line in enumerate(text.splitlines(), 1):
            found = re.search(r"\(\s*визначити\s+\(?\s*([^\s()]+)", line)
            if found and found.group(1) not in definitions:
                name = found.group(1)
                definitions[name] = {
                    "домен": domain_of(name),
                    "файл": rel,
                    "рядок": number,
                    "арність": arity_of(line),
                }
            for token in re.findall(r"[^\s()\[\]]+", line):
                usage[token] += 1

    for name, entry in definitions.items():
        entry["уживань"] = usage[name]

    by_domain = collections.Counter(e["домен"] for e in definitions.values())

    knowledge = root / "knowledge"
    knowledge.mkdir(exist_ok=True)
    (knowledge / "drabyna-index.json").write_text(
        json.dumps(
            {
                "визначень": len(definitions),
                "файлів": len(files),
                "домени": dict(sorted(by_domain.items())),
                "функції": definitions,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )

    # Людський довідник: найуживаніші, щоб було видно, на чому стоїть мова.
    top = sorted(definitions.items(), key=lambda kv: -kv[1]["уживань"])[:120]
    lines = [
        "# Драбина доменів — довідник охоронця",
        "",
        f"Визначень: **{len(definitions)}** у **{len(files)}** файлах.",
        "",
        "## Скільки в кожному домені",
        "",
        "| домен | визначень |",
        "|---|---|",
    ]
    for domain, count in sorted(by_domain.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {domain} | {count} |")
    lines += [
        "",
        "## Найуживаніші — на чому стоїть мова",
        "",
        "| функція | домен | уживань | де |",
        "|---|---|---|---|",
    ]
    for name, entry in top:
        lines.append(
            f"| `{name}` | {entry['домен']} | {entry['уживань']} | "
            f"{entry['файл']}:{entry['рядок']} |"
        )
    lines += [
        "",
        "## Як користуватись",
        "",
        "Перед тим як писати нову функцію — спитай охоронця, чи вона вже є:",
        "",
        "```lisp",
        "(драбина-є? помножити)        ; істина",
        "(драбина-де помножити)        ; файл і рядок",
        "(драбина-домен помножити)     ; д1",
        "(драбина-уживань помножити)   ; 139",
        "(драбина-звіт)                ; скільки всього",
        "```",
        "",
        "Якщо функції немає — це кандидат у д11, а не привід писати дубль.",
    ]
    (knowledge / "drabyna.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"визначень: {len(definitions)}")
    print(f"файлів: {len(files)}")
    for domain, count in sorted(by_domain.items(), key=lambda kv: -kv[1]):
        print(f"  {domain}: {count}")
    return 0




# ---------------------------------------------------------------------------
# Доменні таблиці: lib/domains/d<N>.lisp
#
# ВАЖЛИВО: це НЕ визначення функцій. Це таблиці координат:
#   (domain-table-1
#     (0 (ук ні) (укр ні) (san na) (en no) (LISP NIL) (sym ()))
#     (1 (ук так) (укр так) (san ām) (en yes) (LISP T) (sym ())))
# Тому «домен функції» — не властивість функції, а властивість координати.
# Охоронець це розрізняє й не змішує.
# ---------------------------------------------------------------------------

PROJECTIONS = ["ук", "укр", "san", "en", "LISP", "sym"]


def index_domains(root: pathlib.Path) -> dict:
    """Порахувати координати й перевірити шість проєкцій у кожній таблиці."""
    result = {}
    for path in sorted((root / "lib" / "domains").glob("d*.lisp")):
        match = re.search(r"d(\d+)\.lisp$", path.name)
        if not match:
            continue
        domain = "д" + match.group(1)
        text = path.read_text(encoding="utf-8")
        # Кожен рядок координати: ( <число> (ук ...) (укр ...) ... )
        coords = re.findall(r"^\s*\((\d+)\s+\(ук ", text, re.MULTILINE)
        missing = [p for p in PROJECTIONS if f"({p} " not in text]
        result[domain] = {
            "файл": str(path.relative_to(root)),
            "координат": len(coords),
            "перша": coords[0] if coords else None,
            "остання": coords[-1] if coords else None,
            "проєкцій": len(PROJECTIONS) - len(missing),
            "відсутні": missing,
        }
    return result


def write_domains(root: pathlib.Path) -> int:
    domains = index_domains(root)
    if not domains:
        print("доменних таблиць не знайдено", file=sys.stderr)
        return 1
    out = [
        "# Драбина доменів — таблиці координат",
        "",
        "Домен тут — **координата**, а не простір імен функцій.",
        "Кожен рядок таблиці має шість проєкцій: ук · укр · san · en · LISP · sym.",
        "",
        "| домен | координат | проєкцій | перша | остання | файл |",
        "|---|---|---|---|---|---|",
    ]
    total = 0
    for domain, entry in sorted(domains.items(), key=lambda kv: int(kv[0][1:])):
        total += entry["координат"]
        out.append(
            f"| {domain} | {entry['координат']} | {entry['проєкцій']}/6 | "
            f"{entry['перша']} | {entry['остання']} | {entry['файл']} |"
        )
    out += [
        "",
        f"**Разом координат: {total}**",
        "",
        "Якщо в рядку проєкцій менше шести — таблиця неповна, і це видно тут,",
        "а не виявляється під час виконання.",
    ]
    (root / "knowledge" / "drabyna-domains.md").write_text(
        "\n".join(out) + "\n", encoding="utf-8"
    )
    for domain, entry in sorted(domains.items(), key=lambda kv: int(kv[0][1:])):
        print(
            f"{domain}: {entry['координат']} координат, "
            f"{entry['проєкцій']}/6 проєкцій"
            + (f", ВІДСУТНІ {entry['відсутні']}" if entry["відсутні"] else "")
        )
    return 0


def write_lisp_data(root: pathlib.Path) -> int:
    index = json.loads((root / "knowledge" / "drabyna-index.json").read_text(encoding="utf-8"))
    functions = index["функції"]
    out_dir = root / "lib" / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "; Згенеровано scripts/drabyna-index.py — не правити руками.",
        "; Індекс драбини для охоронця: (ім'я файл рядок уживань арність).",
        "",
        "(визначити (драбина-записи)",
        "  (список",
    ]
    for name, entry in sorted(functions.items(), key=lambda kv: -kv[1]["уживань"]):
        arity = entry["арність"]
        arity_text = "()" if arity is None else str(arity)
        lines.append(
            f'    (список "{name}" "{entry["файл"]}" {entry["рядок"]} '
            f'{entry["уживань"]} {arity_text})'
        )
    lines += ["  ))"]
    (out_dir / "drabyna-data.lisp").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"lib/generated/drabyna-data.lisp: {len(functions)} записів")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--lisp":
        raise SystemExit(write_lisp_data(pathlib.Path(".")))
    if len(sys.argv) > 1 and sys.argv[1] == "--domains":
        raise SystemExit(write_domains(pathlib.Path(".")))
    raise SystemExit(main())


# ---------------------------------------------------------------------------
# Генерація Lisp-даних для охоронця.
#
# Навіщо: щоб охоронцем користувались ІЗ REPL, а не лише з Python.
# Формат — звичайний список SENS, без JSON: наша мова не залежить від
# чужих форматів.
# ---------------------------------------------------------------------------
