# ADR-012 — Nondeterministic witness invariant law

## Українське резюме

Недетермінований hardware/runtime witness не має права перетворювати випадкове, часовe або залежне від планувальника спостереження на фіксоване «очікуване значення».

Чинне правило:

```text
nondeterministic witness
        =>
assert guaranteed invariant
never sampled value
```

Status: accepted witness-methodology boundary · 2026-10-07 · #4154

Це правило керує **силою доказового твердження**, а не створює нову семантику SENS.

## Context

#4086 уже застосовує правильну дисципліну до owner-silicon evidence. Для RDRAND/RDSEED фізичне виконання є корисним witness, але конкретне випадкове слово не є стабільним oracle. Відтворюваним твердженням є лише те, що інструкція допустима на заявленій платформі та повертає архітектурно дозволений статус/форму результату.

Та сама проблема виникає для clocks, RDTSC, performance counters, GPU timing/counters, concurrency schedules і майбутніх фізичних/asynchronous witnesses.

Без загального правила тест легко стає сильнішим за специфікацію: один випадково отриманий sample перетворюється на константу, а наступний коректний запуск помилково оголошується regression.

## Decision

Для будь-якого witness, чий observable result не є детермінованим контрактом, тест зобов'язаний явно назвати:

1. **source of nondeterminism** — що саме може змінюватися між коректними запусками;
2. **preconditions / feature gate** — за яких умов witness взагалі допустимий;
3. **guaranteed invariant** — єдине твердження, яке тест має право assert-ити;
4. **admissible observation shape** — множину, діапазон, relation або status class допустимих результатів;
5. **explicit non-claim** — що конкретно цей witness не доводить.

Фіксоване sampled value не може ставати semantic oracle constant, benchmark truth або cross-substrate identity лише тому, що воно було спостережене на одному запуску.

## Nondeterministic Witness Observation v1

Мінімальна machine-readable форма evidence повинна бути еквівалентною таким полям:

```text
witness_kind
source_of_nondeterminism
precondition_or_feature_gate
invariant_kind
admissible_observation
observed
explicit_non_claim
```

Назви полів у конкретному artifact schema можуть відрізнятися, але ці інформаційні осі не можна мовчки втрачати.

Якщо artifact використовує коротший schema, `witness_kind` має однозначно вказувати, що рядок недетермінований, а expected/observed не повинні маскувати sample як exact-value oracle.

## Canonical examples

### RDRAND / RDSEED

Дозволено:

```text
feature gate: rdrand / rdseed
observation: architectural status bit CF
invariant: CF ∈ {0,1}
non-claim: no fixed random word is asserted
```

Заборонено:

```text
expected random word = 0x...
```

або будь-яка replay-вимога до конкретного випадкового payload.

### RDTSC / clocks

Дозволений лише invariant, який реально випливає з оголошених platform/precondition assumptions, наприклад relation між двома впорядкованими readings у контрольованій lane.

Заборонено перетворювати конкретний timestamp/tick count на expected constant.

### Performance counters

Можна перевіряти оголошену shape/range/relation для конкретно налаштованого counter scope.

Не можна вимагати exact cross-run count без окремого доказу, що така точність гарантована вимірювальним протоколом.

### GPU timing / asynchronous devices

Можна свідчити допустимий status, завершення, shape, bounded relation або інший гарантований invariant.

Не можна робити один latency sample semantic або performance constant.

### Concurrency

Witness може перевіряти дозволену множину outcomes або ordering constraints.

Він не має права канонізувати один scheduler interleaving, якщо контракт допускає кілька.

## Relation to deterministic witnesses

Цей ADR не послаблює deterministic evidence.

Якщо результат повністю визначений admission law + inputs + declared environment, exact-value assertion лишається правильною і бажаною.

Тобто:

```text
deterministic witness    -> exact expected observation where specified
nondeterministic witness -> invariant / admissible set / relation only
```

## Relation to semantic authority

Native hardware, clocks, counters, schedulers і GPUs залишаються witnesses/mechanisms. Вони не отримують права визначати SENS semantics через власні unstable observations.

Цей ADR тому не:

- додає semantic resident;
- змінює domain identity;
- змінює admission law;
- ратифікує hardware sample як language value;
- створює другий oracle.

Він лише обмежує, **яку силу claim може мати evidence**.

## Conformance rule

Будь-який рядок, позначений як nondeterministic witness, вважається некоректним evidence, якщо:

- assert-ить sampled payload як fixed expected value;
- не називає feature/precondition, коли вона потрібна;
- не має явного invariant/admissible shape;
- замовчує, що observed sample не є semantic constant;
- проходить через silent skip замість явної класифікації BLOCKED / gated / unsupported.

Перший чинний consumer цього правила — #4086 / #4111 RDRAND/RDSEED silicon lane. Його правильна форма: `nondeterministic-status-invariant`, feature-gated execution і перевірка лише `CF ∈ {0,1}`.

## Consequences

- RDRAND/RDSEED, clocks, counters і GPU timing можуть давати сильні physical witnesses без фальшивої детермінізації.
- Replay зберігає методологію та schema/provenance, але не вимагає повторити випадковий sample.
- Negative/BLOCKED results лишаються first-class evidence.
- Майбутні substrate lanes отримують один спільний закон замість локальних ad hoc правил.
- Benchmark і silicon evidence можуть бути відтворюваними навіть тоді, коли саме фізичне число не повторюється.

## Implementation handoff

#4111 уже містить перший concrete consumer у `crates/sens-host/tests/real_silicon_sweep.rs`. Його execution harness не треба fork-ати. Після landing schema guard має перевіряти nondeterministic rows downstream від того самого ledger/harness, а не створювати окрему таблицю.
