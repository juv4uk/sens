# #2630 — мінімізація explicit caller environment

Статус: лише SENS-DERIVATION research.

## Результат під перевіркою

explicit-caller-env = CARRIER-PREMISE

Witness розділяє операції над environment-shaped data та отримання фактичного поточного caller context.

Core1 уже має явні environment operations:

    C1-LOOKUP(NAME, ENV, GLOBAL)
    C1-BIND(PARAMS, ARGS, ENV)

Якщо environment-value уже передано явно, ordinary lookup повністю відтворює body-level спостереження caller-only binding.

## Відсутній канал

Ordinary closure application обчислює expressions у caller, але будує callee frame з:

    closure.environment + explicit argument slots

calling_environment не вставляється в parameter slots.

Тому два виклики з однаковими explicit args, але різними caller-only bindings, мають однаковий явний payload для callee.

FEXPR-like explicit-caller-env protocol розрізняє їх лише тому, що actual caller environment передається додатковим semantic input.

## Три моделі

A — без environment channel:
однакові explicit args під caller x=42 і x=99 колапсують.

B — environment-shaped data передано явно:
environment є ordinary data, D4-style LOOKUP відтворює спостереження.

C — автоматична ін'єкція caller environment:
спостереження відтворюється, але reification/injection actual context є новим acquisition channel.

## Класифікація

Не PROVEN-ROOT: lookup над явним environment data уже виражається.

Не повністю DERIVED: ordinary D1-D4 call не може отримати actual current caller environment з однакових explicit arguments.

Тому чесна bounded classification — CARRIER-PREMISE.

    width      = UNKNOWN
    coordinate = UNPLACED
    residents  = 0

## Відтворення

    python3 scripts/research-2630-explicit-caller-env-root.py

Очікувано:

    R3-EXPLICIT-CALLER-ENV=PASS
    root-status=CARRIER-PREMISE

## Принцип

LOOKUP над явним environment — операція. Отримання actual caller environment — carrier/acquisition premise. Приховати його в host reflection — не означає derive.