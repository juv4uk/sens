# Core-Math binary growth and demand derivation — #2460

## English

This benchmark implements autonomous binary growth and on-demand derivation under the canonical ontology of #2490:
```text
semantic object = binary number + domain + proved law
```

### Growth Rule
```text
known bits + proved law -> new bits -> reuse new bits
```

### Core Architecture
- **Semantic Object**: `BinaryNumber` scoped strictly within an explicit `Domain` (`SelectorPath`, `QGroupFactor`, `AffineFunctionGF2`).
- **Chained Derivation**: Generated binary objects are immediately reusable as parents or operands for subsequent law applications without human names, registry tables, or lookup rows.
- **On-Demand Derivation (Demand Construction)**: Given a derivation target, the engine constructs ONLY the necessary DAG of intermediate binary nodes, avoiding exponential closure enumeration.
- **Parity with Bounded Eager Closure**: Bit-for-bit exact identity match between on-demand derived objects and nodes in the bounded eager closure.
- **Domain Firewall (#2508)**: Every derivation step carries the exact domain of its law. Cross-domain growth is rejected fail-closed with `DomainMismatch`.
- **Zero External Dependencies**: Pure Rust standard library, zero external crate dependencies, no Lisp, JSON, AST, hashes, or registries required.

### Falsifiers
1. **Missing Seed**: Omitting a required seed causes derivation to fail closed with `GrowthError::MissingSeed`.
2. **Missing Law**: Using an unknown law causes derivation to fail closed with `GrowthError::MissingLaw`.
3. **Domain Mismatch (#2508)**: Applying a law from Domain A to an object from Domain B fails closed with `GrowthError::DomainMismatch`.
4. **Order Invariance**: The order in which independent targets are derived does not alter their semantic objects or bit strings.
5. **Cache Invariance**: Memoization caching does not affect semantic identity; cold vs warm cache executions produce identical binary objects.
6. **Anti-Numerology**: Arbitrary bit permutation or axis swapping destroys the mathematical law and is rejected.

---

## Українська (Ukrainian)

Цей бенчмарк реалізує автономне зростання двійкових об'єктів та виведення за вимогою (on-demand derivation) в рамках канонічної онтології #2490:
```text
семантичний об'єкт = двійкове число + домен + доведений закон
```

### Закон зростання (#2460)
```text
відомі біти + доведений закон -> нові біти -> повторне використання нових бітів
```

### Ключова архітектура
- **Семантичний об'єкт**: `BinaryNumber`, обмежений точним доменом `Domain` (`SelectorPath`, `QGroupFactor`, `AffineFunctionGF2`).
- **Ланцюгове виведення (Chained Derivation)**: Новостворені двійкові об'єкти одразу стають вхідними даними для наступних кроків закону без людських імен, таблиць пошуку чи реєстрів.
- **Виведення за вимогою (Demand Construction)**: Замість експоненційного переліку всього замикання, рушій матеріалізує лише необхідний DAG проміжних бітових вузлів (наприклад, 4 вузли для глибини 3 замість 15 у повному замиканні).
- **Паритет із повним замиканням**: Біт-у-біт точна відповідність між об'єктом, виведеним за вимогою, і відповідним вузлом у повному замиканні.
- **Доменний фаєрвол (#2508)**: Кожне виведення зберігає точний домен свого закону. Міждоменне застосування відхиляється помилкою `DomainMismatch`.
- **Нуль зовнішніх залежностей**: Тільки чистий Rust, без зовнішніх крейтів, без Lisp/JSON/AST/гешів чи кешів для семантики.

### Набір фальсифікаторів
1. **Відсутність насіння (Missing Seed)**: Виведення без обов'язкового насіння падає з `GrowthError::MissingSeed`.
2. **Відсутність закону (Missing Law)**: Спроба використати незареєстрований закон падає з `GrowthError::MissingLaw`.
3. **Міждоменна ізоляція (Domain Mismatch #2508)**: Застосування закону до об'єкта іншого домену блокується `GrowthError::DomainMismatch`.
4. **Інваріантність порядку (Order Invariance)**: Порядок обчислення незалежних цілей не впливає на підсумкові біти й семантичні об'єкти.
5. **Інваріантність кешу (Cache Invariance)**: Кешування є лише оптимізацією; холодний і теплий кеш дають біт-у-біт ідентичний результат.
6. **Антинумерологія (Anti-Numerology)**: Довільні перестановки бітів руйнують закон і відхиляються.
