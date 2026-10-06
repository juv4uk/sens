# Sens8 / Function8 — повне покриття сучасною доменною драбиною

**Статус:** audit complete  
**Authority:** #4021  
**Поточна foundation:** D1–D9 owner-ratified (#4008 / Contract 11.8)  
**D10:** research / unratified

Старий `lib/generated/function-table.lisp` більше не використовується як semantic або coordinate authority. Але як donor/provenance він тепер перевірений повністю.

## Старий 256-cell простір

```text
total cells                          256
named semantic rows                  182
unnamed legacy identity 00000000       1
blank / unused cells                  73
```

Тобто старе число **183 assigned** означало 182 named meanings плюс unnamed zero identity.

## Покриття 182 named meanings

```text
DIRECT-CURRENT-IDENTITY              153
CURRENT-PROJECTION / DERIVED          20
INTERNAL-NO-SEMANTIC-SLOT              4
D10-RECOVERY-CANDIDATE                  4
MECHANISM-HOLD                          1
-----------------------------------------
TOTAL                                 182
```

Отже **100% старих named Sens8 rows мають сучасне рішення**.

## Що це означає практично

### 153 — уже прямі сучасні identities

Вони мають current D1–D9 resident або збережену source-проєкцію на ратифікований D9 resident.

### 20 — покриті current semantics без окремого resident

Приклади:

```text
atom?          -> D3 ATOM
eq?            -> D3 EQ
def            -> D4 DEFINE
lessp?         -> D5 LESSP
greaterp?      -> D5 GREATERP
equalp?/equal? -> D8 EQUAL
not?           -> D4 NOT
member?        -> D5 MEMBER
second         -> D4 CADR
third          -> D5 CADDR
fourth         -> D6 CADDDR
env            -> D8 ENV-REFLECTION
null?          -> D4 NULL
```

Також:

```text
defmacro
-> D5 MACRO + D4 DEFINE surface packaging

codepoint->string
-> D8 CODE-CHAR

string->codepoint
-> D8 CHAR-CODE
```

Це не semantic gaps.

### 4 — internal helpers

```text
largest-chunk
nondecreasing-from?
nonincreasing-from?
digit->string
```

Вони не потребують domain resident.

### 4 — уже відновлені в D10

```text
MONO-NS
UNIX-TIME-NOW
NTP-QUERY-RAW
TIMEZONE-DECLARATIONS-RAW
```

Вони вже є unplaced D10 research candidates через #4016. Цей audit не додає їх повторно.

### 1 — mechanism HOLD

```text
INVOKE
```

Це post-semantics mechanism selector. Без незалежного language law він не займає semantic slot.

## Висновок

Sens8 **вичерпаний як donor**.

```text
старий meaning
-> або current D1-D9 semantic
-> або current surface/derived projection
-> або internal helper
-> або вже D10 recovery
-> або mechanism HOLD
```

Немає жодного старого named Sens8 meaning, який просто «загубився».

Найважливіше:

```text
Sens8 donor exhausted
!=
Sens8 coordinates restored
```

Старі 8-бітні коди мають **нульову placement authority**.
