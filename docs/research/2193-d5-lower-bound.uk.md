# #2193 — нижня межа семантики D5

Статус: лише research.

## Результат

Звичайне closure і raw-form transformer мають спостережувану різницю
**ще до виконання body**.

Беремо однакову форму виклику:

```text
(f (quote ok) never-defined)
```

Для звичайного closure:

```text
(lambda (a b) a)
```

звичайна call-semantics спершу обчислює обидва operands, тому
`never-defined` мусить впасти ще до того, як body проігнорує `b`.

Для transformer/macro з тією самою формою параметрів/body існуючий conformance
вимагає протилежного: невикористаний другий operand лишається сирою формою, і
виклик повертає `ok`.

## Повний перебір one-mode моделі

Без semantic discriminator є лише дві глобальні політики:

```text
1. eager
2. raw
```

Таблиця:

```text
                 ordinary closure   transformer
eager                 PASS             FAIL
raw                   FAIL             PASS
```

Жодна one-mode модель не задовольняє обидві поведінки.

Модель з одним discriminator працює:

```text
ordinary closure -> eager
transformer      -> raw
```

Отже нижня межа:

> для збереження обох семантик під однаковим call syntax потрібен щонайменше
> один спостережуваний stage/call-mode discriminator.

## Значення для D5

Строгий Model C із #2185 — тільки D4, без прихованої різниці — спростований,
якщо цей lower-bound переживе review.

Це **не доводить**, що discriminator обов'язково має бути:

```text
00101 TRANSFORMER
```

Він може бути представлений як:
- окремий transformer value kind;
- exact binary identity;
- call-site stage marker;
- явна compiler/reader phase.

Але прихований Rust tag чи environment flag теж є новою семантичною відмінністю;
його не можна чесно називати "D4 only".

## Відтворення

```sh
python3 scripts/research-2193-d5-lower-bound.py
```

Очікуваний заголовок:

```text
D5 semantic lower-bound witness: PASS
one-mode-satisfies-both=0
one-discriminator-model: ordinary=PASS transformer=PASS
STRICT-D4-ONLY-WITHOUT-DISCRIMINATOR=FALSIFIED
```

## Принцип

**Якщо однакова форма виклику мусить вибирати дві різні політики до виконання
body, ця відмінність повинна явно існувати десь у семантиці.**
