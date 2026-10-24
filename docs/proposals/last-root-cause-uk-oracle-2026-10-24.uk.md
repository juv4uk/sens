# Остання першопричина: `uk_oracle_verified` жорстко зашитий у 0

Автор: агент Carama, 2026-10-24. Підстава: PR #6034.

## Питання

Блокер релізу — «F2/F4 native SENS verdict and Ukrainian oracle not verified».
Три можливості: (а) CI не запускався; (б) запускався й упав; (в) **кроку немає**.
Яка з трьох — правда?

## Відповідь: (в) — кроку немає, і не може бути в цьому скрипті

`scripts/check-release-admission-ledger.py:145-155`:

```python
    return {
        "schema": SCHEMA,
        "validation_mode": "content_verified" if verify_content else "form_only",
        "entries": len(entries),
        "form_candidates": len(form_candidates),
        "content_verified": len(content_verified),
        "content_verified_sens": content_verified,
        "uk_oracle_verified": 0,          # ← ЖОРСТКО ЗАШИТО
        "release_admitted": 0,            # ← ЖОРСТКО ЗАШИТО
        "admitted_sens": [],
    }
```

**`uk_oracle_verified` і `release_admitted` — літерали `0`.** У цьому файлі їх
**ніщо не обчислює** (`grep` по всьому дереву дає лише ці два рядки).

**Отже цей скрипт не може допустити реліз НІКОЛИ — за побудовою.** Не тому, що
CI не запускався, і не тому, що впав. **Кроку, який би обчислив ці поля, тут
немає взагалі.**

## Де насправді живе обчислення

`scripts/check-release-triple-corpus.py:74-91` — **інший** скрипт — таки
обчислює:

```python
or s["uk_oracle_verified"] != sum(row.get("uk_oracle") == "VERIFIED" for row in rows)
...
s["uk_oracle_verified"] != 0
...
row.get("uk_oracle") != "NOT_VERIFIED"
```

Тобто **справжній український оракул живе в triple-corpus, а admission-ledger
його лише ЗАЯВЛЯЄ як 0.** Два скрипти, одна назва поля, **різні джерела істини**.

## Наслідки

1. **Блокер релізу — не тулчейн і не джерела, а ЗВ'ЯЗОК між двома скриптами.**
   `sens` у CI **збирається** (`956-semreg-targeted.yml` викликає
   `target/debug/sens-trit encode/eval`) — отже виконання можливе.
2. **`release_admitted: 0` — не результат перевірки, а константа.** Вона
   виглядає як вердикт, але ним не є. Це **третій випадок тієї самої хвороби**,
   яку я знаходив у цій нитці: **оголошене замість виведеного**
   (`D10` каталог, `numeric_domains_generated`, тепер `release_admitted`).
3. **Це РІШЕННЯ ВЛАСНИКА**: чи admission-ledger має **читати** результат
   triple-corpus, чи triple-corpus має **писати** в admission-ledger.

## Що це означає для конкурсу

«Реліз заблокований» — **технічно правда, але причина інша, ніж здавалось**.
Він заблокований не відсутністю збірки (вона є) і не відсутністю джерел
(provenance здоровий — 17/17 посилань існують). Він заблокований **константою
`0` у полі, яке мусить бути обчисленим**.

## Deutsch

Die letzte Ursache: `uk_oracle_verified` ist eine hartkodierte 0.

## English

The last root cause: `uk_oracle_verified` is a hard-coded 0.
