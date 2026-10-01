# #2092 — найслабша word algebra, перше executable порівняння

Лише дослідження.

## Моделі

Порівнюються чотири алгебри над однаковими bounded identity/path obligations:

```text
A  free semigroup Σ+
B  free monoid Σ*
C  opaque exact identities + external parent relation
D  productive paths з one-step refine/parent
```

## Головне питання

Чи потрібна мові повна операція:
```text
concat : W × W -> W
```
лише тому, що current carrier схожий на рядок?

Модель C показує, що exact identity + extent можливі взагалі без concatenation.

Модель D показує, що двогілкова productive family може мати лише:
```text
refine(parent, symbol)
parent(child)
```
без загального `W×W -> W`.

## Додаткова структура

Free semigroup/monoid додають сильніші закони:
- total concatenation;
- cancellation;
- а monoid ще й neutral `ε`.

Ці властивості можуть бути корисними, але current obligations поки не роблять їх семантичними аксіомами.

Framing також може жити зовні identity algebra через explicit extent/payload metadata.

Артефакт: `scripts/research-2092-word-algebra.py`.
