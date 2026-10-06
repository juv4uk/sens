# D8 recovery candidate map

**Статус:** research / provisional. **D8 не ратифікований.**

## Закон драбини

```text
1. необхідність
2. історична ранність
3. простий математичний/логічний закон
4. recovery того, що пропустили нижче
```

Ратифіковані D1–D7 не переставляються приховано. Похідна функція не отримує D8-слот лише тому, що для неї існує гарний окремий witness.

## Provisional ladder

```text
00000000  ERRORSET
00000001  ERROR
00000010  ENV-REFLECTION
00000011  READ
00000100  WRITE-TO-STRING
00000101  SYMBOL->STRING
00000110  STRING->SYMBOL
```

Це **candidate coordinates**, не ратифіковані residents.

`ERRORSET` стоїть першим, бо він історично ранній (Lisp 1.5, 1961–1962), фундаментально додає локальне відновлення після помилки й має дуже короткий закон:

```text
success -> LIST(value)
error   -> EMPTY
```

Звичайний D1–D7 `COND` не може перехопити помилку, яка не стала значенням. Тому error boundary є окремою capability.

`ERROR` — сусідня рання capability: навмисно сигналізувати language error із payload. Вона відрізняється від випадкової помилки типу неправильного `CAR`: програма явно заявляє про failure, а не маскує його під чужу partiality.

`ENV-REFLECTION` відділяється від самого evaluator environment:

```text
environment як контекст EVAL/closure
!=
ENV() як first-class enumeration/reflection
```

Current implementation: `(env)` існує, повертає всі видимі bindings, проходить frames outer→inner, shadowed name отримує innermost value, а результат сортується за ім'ям.

Споріднені історичні слова: `a`, `a-list`, `alist`, `association list`, `environment`, `env`. Ранній `a-list` не backdate-ить сучасну reflection-операцію.

Legacy implementation code `01001110` збережено лише як provenance, не як D8 donor coordinate.

## Recovery, який не витрачає слот

```text
EQUAL       DERIVED-NO-SLOT
PAIR        DERIVED-NO-SLOT
AND         DERIVED-NO-SLOT
OR          DERIVED-NO-SLOT
DIVIDE      DERIVED/FOREIGN-REVIEW-NO-SLOT
ONEP        DERIVED-NO-SLOT
MINUSP      DERIVED-NO-SLOT
FSUBR       HISTORICAL-MECHANISM-NO-SLOT
HART-MACRO/
TRANSFORMER LOWER-DOMAIN-FAMILY-COVERED-NO-SLOT
```

Короткі закони:

```text
EQUAL(a,b)  = structural recursion over ATOM/EQ/CAR/CDR
ONEP(x)     = ZEROP(DIFFERENCE(x,1))
MINUSP(x)   = LESSP(x,0)
DIVIDE(x,y) = pair(QUOTIENT(x,y), REMAINDER(x,y))
```

`PAIR`, `AND`, `OR` уже language-owned compositions.

`FSUBR` зберігається історично, але його user-visible raw+caller-env protocol уже належить тій самій сім'ї, що FEXPR; interpreted/subroutine implementation distinction сам по собі не є новим Core resident.

D5 вже має `MACRO`. Hart 1963 timing, whole-call packaging та інші protocol-axis відмінності збережені (#2567/#2588/#2591), але не дублюються автоматично новим D8 resident.

## Carrier/type recovery

```text
FIXP / FLOATP
LOGAND / LOGOR / LOGXOR / LEFTSHIFT
```

лишаються окремим Core-Math / machine-carrier review. Історична 36-bit/fixed/floating машина не повинна автоматично ставати сучасною Core-онтологією.

## Усі позитивні D8 research-family збережено

У `main` тепер є:

- TAKE/DROP × edge;
- ANY/ALL × predicate polarity;
- REDUCE/SCAN × direction;
- ZIP/UNZIP × orientation;
- DO/WHILE × condition/projection;
- NEG/ABS × RECIP;
- RASSOC/ACONS × association orientation;
- NTH/MAPLIST × traversal direction.

Новий ladder-висновок для них:

```text
GENERATED / DERIVED — NO D8 SLOT
```

Їхні geometric coordinates **не видаляються**. Вони залишаються доказами структури, генераторами, gauge/orientation evidence і можливими оптимізаційними законами.

Приклади:

```text
TAKE-right / DROP-right    <- REVERSE conjugation
ANY(NOT p) / ALL(NOT p)   <- NOT composition
NEG∘RECIP / ABS∘RECIP     <- arithmetic composition
NTH-right / MAPLIST-right  <- traversal-direction composition
```

Тобто попередня робота не втрачена — просто її роль уточнена: **law evidence, не primitive occupancy**.

## Негативні дослідження теж в main

Збережено falsifier-и:

- CURRY/FLIP × swapped arguments;
- INTEGERP/RATIONALP × sign;
- RECIP/EXPT reciprocal/sign;
- попередні п'ять відкинутих second-axis hypotheses.

Негативний результат захищає нас від повторення тієї самої дорогої помилки.

## Поточний accounting

```text
provisional D8 ladder candidates   7
provisional coordinates            00000000..00000110
ratified D8 residents              0
resolved recovery no-slot          9
unresolved recovery rows           2
preserved positive law families    8
preserved negative groups          4
```

## Наступне правило заповнення

Після `ERRORSET`, `ERROR`, `ENV-REFLECTION`, `READ` і `WRITE-TO-STRING` новий D8 slot видаємо тільки тоді, коли:

```text
capability не представлена D1-D7
AND не виводиться простою композицією нижчих residents
AND має сильну необхідність/історичне право
AND має дешевий зрозумілий witness
```

Отже D8 росте повільніше, але чистіше: верхній домен збирає справді пропущені можливості, а не копії вже наявної алгебри.


## Structure ↔ text recovery

`READ` тут не означає host stdin. Для D8-кандидата береться саме одноаргументний закон:

```text
READ(string) -> один структурний Lisp datum
```

без виконання цього datum.

`WRITE-TO-STRING` дає зворотну стрілку:

```text
WRITE(value) -> canonical readable text
```

Основний дешевий закон:

```text
READ(WRITE(x)) = x
```

на admitted readable-value carrier.

Зворотна композиція є canonicalization:

```text
WRITE(READ(t)) = canonicalize(t)
```

Отже це не console I/O, а мовний міст structure ↔ text.

### D7 blocker

Current mechanism використовує `Value::String`, а канонічний текстовий домен D7 — Text7/UPC-7. Тому обидва кандидати залишаються provisional до явного D7↔reader/writer bridge. Unicode/String representation не є D8 identity.

`READ-ALL` поки класифіковано як derived wrapper над тим самим reader mechanism; `PRINT` і `PRINC` лишаються host/transcript mechanisms.

## Symbol ↔ text recovery

Окремо від parser/serializer існує міст імені символу:

```text
SYMBOL->STRING(STRING->SYMBOL(s)) = s
STRING->SYMBOL(SYMBOL->STRING(sym)) = sym
```

Це не просто `READ`. Контрприклад:

```text
STRING->SYMBOL("strange symbol")  -> один Symbol з таким точним ім'ям
READ("strange symbol")            -> два top-level forms / InvalidForm
```

Історичні `PNAME`, `INTERN`, `OBLIST`, `REMOB` зберігаються окремо. Поточний `STRING->SYMBOL` не оголошується тотожним історичному `INTERN` без доказу symbol-table identity.

Як і READ/WRITE, ця пара provisional до явного мосту з D7/Text7.
