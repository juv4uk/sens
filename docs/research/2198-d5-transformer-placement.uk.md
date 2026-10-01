# #2198 — D5 transformer placement witness

Статус: лише research. Кандидат `00101` **не ратифікований**.

## Найсильніший зв'язок: identity payload

Поточний surrogate-path:

```text
0010 LAMBDA
   -> Value::Closure(Rc<Closure>)
   -> make-macro
   -> Value::Macro(той самий Rc<Closure>)
```

Executable witness порівнює обидва runtime-values через `Rc::ptr_eq`.

Це важливо: TRANSFORMER не просто "схожий" на LAMBDA. Це інший invocation
mode над **тим самим closure payload**.

Такий зв'язок значно сильніший за звичайну dependency adjacency.

## Конкурентні D4-батьки

### DEFINE

DEFINE може прив'язати transformer-value, але також прив'язує багато інших
values. Він не створює і не уточнює тіло transformer.

### APPLY

APPLY споживає вже resolved callable. Він не створює transformer identity чи
raw-form invocation mode.

### EVAL

EVAL інтерпретує forms. Він не створює closure, яке стає transformer.

### LAMBDA

LAMBDA створює саме той payload, який приймає transformer constructor, і
constructor зберігає identity цього payload.

Тому LAMBDA зараз має найсильнішу підставу бути semantic parent.

## Кандидатна координата

```text
0010   LAMBDA
00101  TRANSFORMER   ; кандидат
```

Останній біт `1` поки гіпотеза. Він продовжує ратифіковану слабку D4-полярність:

```text
0 = current/focus/resolved
1 = continuation/context expansion
```

Transformer відкладає ordinary operand evaluation, породжує code і повторно
входить у evaluation в caller context, тому `1` зараз підходить краще.

Але це не універсальна доведена D5 suffix-theorem.

## Чому 00100 лишається порожнім

Ordinary closure construction вже має exact-width identity `0010`.
Призначити `00100` просто як "звичайна LAMBDA ще раз" означало б дублювати
семантику без нової observable capability.

Тому research-модель лишає:

```text
00100  unallocated
00101  TRANSFORMER candidate
```

доки не з'явиться counterevidence.

## Executable witnesses

- Closure -> transformer зберігає точну Rc payload identity.
- Non-closure materialization fail-closed.
- Те саме closure body має eager ordinary invocation і raw staged invocation.
- Candidate word не конфліктує з fixed D5 selector subtree.
- Zero-child лишається явно нерозподіленою research position.

## Принцип

**D5-child ставимо під операцією, value якої він уточнює, а не під операцією,
яка лише споживає чи прив'язує його.**
