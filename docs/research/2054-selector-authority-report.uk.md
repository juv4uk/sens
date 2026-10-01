# #2054 — інвентар semantic authority selector-family, перший slice

Статус: research/read-only migration inventory. Runtime, parser, registry, compiler і contracts не змінюються.

## Головна знахідка

Поточна selector-family уже не має однієї монолітної authority. Вона розділена на кілька шарів:

1. **CAR/CDR semantic operations** — current Canon primitives із сильними runtime witnesses.
2. **Legacy exact-8 root identities** — `00000101` / `00000110`.
3. **Derived descendant mechanisms** — pure-Lisp definitions `caar`, `cadr`, `cddr` і alias `cadddr -> fourth`.
4. **Legacy descendant identities/surfaces** — registry rows `00110011..00110110`.
5. **Generated projections/docs/tests**.
6. **CML duplicate mechanisms** — explicit descendant SID branches і dedicated IR vocabulary.

Це добре: міграція не мусить міняти все одночасно.

## Критичний authority split

Selector pilot має зберегти таке розділення:

```text
CAR/CDR semantic operations
    лишаються primitive semantic meaning

старі 8-bit CAR/CDR IDs
    стають checked compatibility projection

selector descendant meaning
    стає ordered family law / proof

старі descendant 8-bit rows
    стають compatibility projection, потім deletion/archive candidates

backend CAR/CDR primitives
    лишаються корисними mechanisms
```

Тобто відхід від exact-8 identity **не означає видалення CAR/CDR primitives**.

Ми видаляємо лише припущення, що їхня поточна one-byte адреса є вічним semantic universe.

## Найсильніші deletion targets

### SENS

`lib/core.lisp` зараз реалізує:

```text
caar = CAR(CAR(x))
cadr = CAR(CDR(x))
cddr = CDR(CDR(x))
```

а `cadddr` прив'язує до того самого closure, що й `fourth`.

Repository audits уже класифікують їх як pure-Lisp derived functions, а не потрібні backend primitives.

Після authoritative parity у #2055/#2060 explicit descendant execution definitions стають сильними deletion candidates.

Human surfaces можуть лишатися, але повинні проєктуватися на canonical variable-width selector identity/proof без dedicated closure definition.

### CML

CML дублює selector knowledge через:

- legacy SID branches у `src/compiler.rs`;
- C backend special cases;
- x86 special cases;
- dedicated descendant `PrimOp` variants;
- name-special lowering для `caddr`.

Це mechanisms, не language authority.

Target:

```text
canonical selector word/proof
    -> ordered CAR/CDR recipe
    -> existing primitive lowering
```

Після cml#397/#2058 parity descendant-specific SID branches — сильні deletion targets.

## Важливий non-collapse law

Поточний код уже показує небезпечну різницю:

`cadddr` і `fourth` ділять один closure mechanism.

Це саме по собі **не** доводить semantic identity.

Так само repository doctrine тримає `second` окремо від structural `cadr`, попри поведінкове перекриття.

Отже:

```text
mechanism equivalence
!=
semantic identity
```

## Рекомендований reversible order

```text
1. current authority inventory (#2054)
2. shadow ordered selector resolver (#2055)
3. dual oracle / rollback (#2060)
4. FunctionWord carrier лише на proven selector path (#2056)
5. selector-family authority transfer
6. legacy 8-bit rows -> projections
7. compile static selector proofs away (#2058)
8. delete descendant closure/SID-special mechanisms
9. лише потім broaden parser/wire/carrier migration
```

Це навмисно уникає global carrier-first rewrite.

## Перший authority-transfer invariant

У кожному migration state для конкретного selector meaning має бути рівно одна declared semantic authority.

Shadow:

```text
old route = authority
new route = oracle candidate
```

Після transfer:

```text
new ordered selector law = authority
old row = compatibility / rollback evidence only
```

Якщо обидва лишаються sovereign — migration failed.

## Principle

**Зберігаємо primitive operation; мігруємо identity law; видаляємо duplicated descendant machinery.**
