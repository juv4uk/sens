# #2077 — Foundation-0: закон exact bounded binary word

Статус: **candidate successor foundation**, лише research/shadow.  
Цей документ сам по собі не скасовує Contract 10.

## Чому це перед доменами, графами й компілятором

Поточний ratified contract каже, що весь function identity universe — рівно 256 восьмибітних форм.

Новий доказовий напрям потребує слабшого й фундаментальнішого закону:

> language identity carrier може бути exact bounded binary word, але з цього не випливає, що кожне слово є функцією або що ширина визначає значення.

Це треба визначити раніше, ніж вирішувати:
- які існують domains;
- чи root+path універсальний;
- як graph пояснює meaning;
- як compiler lowering працює;
- як wire framing зберігає межі;
- чи слово взагалі admitted семантично.

## Candidate Foundation-0

Canonical word:

```text
w ∈ {0,1}+
```

з явною межею слова. Чи є порожня бітова послідовність `ε` семантично допустимою, навмисно лишається unresolved у #2106.

Два слова тотожні тоді й лише тоді, коли збігаються всі bits і exact width:

```text
w1 == w2
iff
len(w1) == len(w2)
and
bits(w1) == bits(w2)
```

Тому:

```text
1 != 01 != 001
001 != 0010
```

Prefix relation не зливає identity:

```text
001 prefix-of 0010
001 != 0010
```

## Boundary law

```text
10 001 01
```

— три вже bounded words.

Це не `1000101`.

Internal `00` — звичайні bits слова, не separator.

Source/container/transport можуть кодувати boundaries, але framing bits/bytes не стають semantic bits.

## Epsilon — відкрите semantic питання

На carrier-рівні порожню послідовність можна представити й round-trip без суперечності. Це не робить її admitted SENS identity. Але й її заборона ще не виведена.

Тому Foundation-0 механічно переносить `ε`, а semantic admission лишає відкритим для #2106.

## Semantic admission окремо

Syntactic validity не створює meaning:

```text
valid binary word
!=
admitted semantic identity
```

Word може бути:
- admitted proven law;
- admitted irreducible residue;
- reserved;
- unknown/unallocated.

Width сама по собі цього не визначає.

Тому ми не вводимо випадково нову ontology типу:

```text
3 bits -> domain A
4 bits -> domain B
8 bits -> functions
```

без незалежного semantic proof.

## Projection law

Оптимізований mechanism дозволений:

```text
width == 8
  -> checked Sens8/u8 projection
```

але projection не є language universe.

Witness доводить:
- exact width-8 projection reversible;
- non-8-bit words явно не проходять Sens8 projection, але це не semantic rejection;
- integer representation не може бути canonical identity через втрату leading zeroes.

## Межа `()`

Structural `()` автоматично не є binary word.

Foundation-0 навмисно не вирішує, чи якесь future admitted word може означати `()`.

Це окремий semantic theorem/admission problem.

## Executable witness

`scripts/research-2077-binary-word-law.py`:

```text
FOUNDATION-0 binary-word witness: PASS
small exhaustive round-trips: 8190
leading-zero distinctness: PASS
prefix-without-equality-collapse: PASS
multi-word boundary round-trip: PASS
internal-00-is-data: PASS
7/8/9 and 64/65 widths: PASS
4096-bit round-trip: PASS
Sens8 checked projection: PASS
numeric-collapse-detected: PASS
semantic-admission-independent-of-width: PASS
```

Witness framing навмисно non-authoritative.

## Що зберігається від SID8 doctrine

Сильні закони лишаються:

- binary identity не є human name;
- leading zeroes важливі;
- host integer/opcode/enum не володіє meaning;
- surfaces — projections;
- execution substrates — mechanisms;
- exact identity мусить round-trip.

Під сумнівом лише одне старе припущення:

> exact width 8 як постійна semantic стеля.

## Порядок до contract transfer

```text
Foundation-0 witness
 -> authority conflict inventory
 -> framing proof
 -> width-neutral carrier witness
 -> selector shadow migration
 -> rollback evidence
 -> successor contract ratification
 -> exact8 ontology guard replacement
 -> retirement old exact8-only prose/guards
```

Rust type або parser не повинні неявно створити новий закон раніше за contract.

## Принцип

**Bits визначають слово; evidence визначає meaning; machinery лише переносить або виконує його.**
