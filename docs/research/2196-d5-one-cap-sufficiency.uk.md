# #2196 — one-capability D5 sufficiency witness

Статус: лише research. Жодна D5-адреса тут не ратифікується.

## Питання

Чи може одна staged transformer capability відтворити спостережувану
macro-семантику SENS, чи потрібна окрема мовна identity на кшталт `EXPAND` /
`MACROEXPAND`?

Поточний тимчасовий `make-macro` використовується тільки як сурогат
кандидатної здібності.

## Виконувані witnesses

### W1 — raw operands

Transformer ігнорує невизначений другий operand:

```text
(first-transformer (quote ok) never-defined) -> ok
```

### W2 — nested expansion

Зовнішній transformer повертає виклик внутрішнього transformer. Звичайний
evaluator повторно входить у transformer dispatch і доходить до результату без
окремої операції MACROEXPAND.

### W3 — caller environment

Transformer розгортається у символ, який існує лише в lexical frame виклику.
Результат резолвиться саме там. Отже post-expansion execution може бути
частиною transformer call semantics, а не другою identity.

### W4 — ordinary LAMBDA лишається eager

Відповідне звичайне closure все одно обчислює невикористаний
`never-defined` operand і повертає `UnknownSymbol`.

Це зберігає lower-bound із #2193.

### W5 — DEFMACRO лишається похідним

Живий macro library далі складається з DEFINE + LAMBDA + одного transformer
materializer, а мовний DEFMACRO зберігає raw arguments.

## Поточний висновок

Для поточного runtime SENS одна first-class transformer value mode достатня,
щоб відтворити:

```text
raw operand capture
nested expansion
post-expansion caller evaluation
derived DEFMACRO
```

Жодна окрема executable SENS identity MACROEXPAND цими witnesses не потрібна.

Це ще не доводить, що compiler consumers можуть видалити свою незалежну macro
authority. CML #408 лишається ecosystem-falsifier.

## Кандидат під перевіркою

```text
0010  LAMBDA
00101 TRANSFORMER   ; лише кандидат
```

## Принцип

**Одна staged value capability достатня лише тоді, коли nested expansion і
caller execution виникають із повторного входу в звичайний evaluator, а не з
прихованого другого semantic operator.**
