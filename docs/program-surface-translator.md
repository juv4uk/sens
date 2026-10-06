# Перекладач програмних поверхонь · Program surface translator

`scripts/translate-domain-program.py` механічно переписує **зареєстровані program symbols** між human surfaces, не змінюючи exact-domain identity.

Поточний translator працює з D1–D5 source-routable surfaces і читає canonical domain files напряму:

```text
lib/domains/d1.lisp … lib/domains/d5.lisp
```

Він не використовує historical flat Sens8/Sid8 byte як semantic authority.

Підтримувані назви мов:

```text
en
uk
ukr
san
```

`sa` приймається як alias для `san`.

## Приклади

```bash
python3 scripts/translate-domain-program.py --from en --to uk program.lisp
python3 scripts/translate-domain-program.py --from uk --to san program.lisp -o program.san.lisp
python3 scripts/translate-domain-program.py --from san --to en -
python3 scripts/translate-domain-program.py --self-test
```

Наприклад:

```lisp
; en
(define f (lambda (x) (car x)))

; uk
(визначити f (функція (x) (перше x)))

; san
(nirvacana f (phalana (x) (ādi x)))
```

D5 selector-приклад:

```text
caddr  →  п-р-р  →  ādi-śeṣa-śeṣa
```

## Що перекладається

Перекладаються лише symbols, для яких canonical domain table має відповідні source/target surfaces. Невідомі користувацькі identifiers лишаються незмінними.

Не переписуються:

- коментарі;
- string data;
- числа;
- layout/whitespace;
- D2 structural labels;
- D3 structural empty.

Цитовані code-symbols можуть переписуватися, бо пізніше можуть бути виконані через `eval`; string data на кшталт `"car"` не переписується.

## Межа семантики

Translator робить:

```text
source spelling
      ↓
exact (domain,bits) row
      ↓
target spelling
```

Він **не** робить:

```text
surface → historical byte → meaning
```

Human spelling — routing projection. Semantic authority лишається exact bits + exact domain + ratified law.

D6–D8 canonical human tables уже існують і повні, але цей конкретний translator поки навмисно обмежений D1–D5 source-routable набором. Розширення coverage має робитися окремо з runtime/conformance tests, а не через мовчазне прийняття всіх display surfaces.
