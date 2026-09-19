# ADR-005: Open Primitive Admission and Kernel Archipelago
# ADR-005: Відкрите прийняття примітивів та архіпелаг ядер

**Статус:** Прийнято / Accepted
**Дата / Date:** 2026-09-19
**Влада / Authority:** пряма настанова власника / Owner directive
**Supersedes:** ADR-004 only where ADR-004 permanently closes the primitive set to McCarthy-7.

---

## 1. Контекст

Попередній етап проєкту навмисно замкнув семантичний фундамент на Canon 0 + сім операцій Маккарті. Це допомогло відокремити семантику від випадкових host/runtime можливостей.

Подальші експерименти з незалежними execution kernels показали іншу потребу: мова не повинна дублювати повну логіку Prolog, Datalog, CLIPS або Common Lisp лише для збереження історичної чистоти.

Проєкт переходить від питання:

> «Чи можна все звести до семи примітивів?»

до питання:

> «Які операції справді заслуговують окремої semantic identity у системі, що координує незалежні ядра?»

---

## 2. Нормативне рішення

1. `()` лишається Canon 0.
2. Сім класичних операцій Маккарті лишаються ратифікованим історичним і мінімальним коренем.
3. Вони більше **не є максимальною допустимою множиною примітивів**.
4. Нові примітиви можуть отримувати semantic ID, якщо їхня окрема identity підтверджена executable experiment або необхідністю чесної композиції.
5. Наявність host helper, hardware opcode або kernel-internal concept **сама по собі не робить** операцію примітивом my-lisp.
6. Один 8-бітний semantic-ID простір лишається чинним експериментальним обмеженням: максимум 256 identities, доки executable evidence не покаже його недостатність.
7. Примітиви не визначаються наперед за кількістю. Їх число є результатом аудиту та експериментів.
8. my-lisp зберігає semantic authority: Canon, identities, surfaces, laws, composition.
9. Execution kernels володіють своїм native mechanism/result model:
   - Common Lisp — Lisp execution/runtime;
   - Prolog — unification/backtracking/0..N answers;
   - Datalog — relational closure/fixpoint;
   - CLIPS — production rules/working memory/agenda.
10. Kernel не може перепризначати значення SID. SID може лише адресувати/позначати семантичну identity, яку визначає my-lisp.
11. Один SID може мати 0..N execution witnesses.
12. Один kernel може свідчити 0..N semantic identities.

---

## 3. Критерій прийняття нового примітива

Новий primitive/SID виправданий, якщо принаймні одне з тверджень підтверджене:

- distinction externally observable;
- ordinary data + existing primitive недостатні без прихованої semantic machinery;
- identity потрібна для композиції кількох kernels;
- кілька незалежних witnesses потребують стабільної спільної identity;
- executable experiment показує, що злиття з наявною identity втрачає поведінку або provenance.

Пропозиція відхиляється, якщо:

- це лише alias;
- це лише приватний concept одного kernel;
- це можна чесно представити ordinary data;
- primitive додається тільки для зручності implementation;
- distinction існує лише в документації, але не спостерігається у виконанні.

---

## 4. Що лишається від ADR-004

ADR-004 лишається історичним і чинним у таких частинах:

- Canon 0 як ground object;
- McCarthy-7 identities як стабільні канонічні identities;
- surface spelling не є semantic identity;
- implementation convenience не створює language ontology;
- hardware opcode / ABI function / runtime builtin не стає primitive автоматично;
- conformance має перевіряти semantic identity, а не ASCII spelling.

Скасовуються лише твердження:

- «No eighth primitive may be admitted»;
- «exactly seven operations may ever have primitive status»;
- fail-closed правило `PRIMITIVE_SET_VIOLATION` тільки через кількість > 7.

---

## 5. Архіпелаг

```text
                  my-lisp
        Canon / SID / laws / surfaces
                     |
       +-------------+-------------+
       |             |             |
  local language   routing      observation
                     |
       +-------------+-------------+-------------+
       |             |             |             |
 Common Lisp      Prolog        Datalog        CLIPS
```

my-lisp не мусить дублювати native algorithm кожного kernel.

Результат острова зберігається таким, яким він реально є:
- 0 answers;
- 1 answer;
- N answers;
- fixpoint closure;
- rule activations;
- native Lisp value;
- opaque/native payload when no lossless bridge exists.

---

## 6. Пірамідальна логіка

Пірамідальна/many-valued логіка більше не є обов'язковим фундаментом усіх reasoning-result.

Вона може лишатися:
- explicit projection над evidence;
- compatibility layer;
- research tool для contradiction/incompleteness;
- локальним Lisp helper.

Prolog, Datalog і CLIPS не повинні бути перетворені на одну універсальну truth ladder.

---

## 7. Acceptance

- [ ] language contract більше не забороняє >7 primitives;
- [ ] McCarthy-7 лишається стабільним історичним коренем;
- [ ] primitive admission має executable/evidence criterion;
- [ ] 8-bit SID budget лишається чинним;
- [ ] kernel-native result models не переписуються в одну універсальну семантику;
- [ ] ADR-004 явно позначено superseded у частині closed primitive set;
- [ ] conformance tests перестають вважати >7 identities автоматичною помилкою.
