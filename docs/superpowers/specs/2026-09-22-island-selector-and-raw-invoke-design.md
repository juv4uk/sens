# Острови: selector, lowering і raw invoke

**Статус:** затверджений дизайн, очікує review implementation plan.

## Мета

`my-lisp` має мати дві різні, чесно відокремлені дороги до execution islands.

Звичайне виконання належить мові: Canon SID та його law визначають вибір
механізму й lowering. Діагностичний `invoke` не визначає семантику: він
передає вже існуючий SID і непрозорий native payload до явно зареєстрованої
host capability та повертає producer-native observation.

## Дві дороги

```text
ordinary Lisp expression
  → Canon SID
  → #1047 Lisp-owned mechanism selector
  → #1048 Lisp-owned lowering
  → selected island executor

raw invoke / викликати
  → SID 10101000
  → SID-keyed registered host capability
  → opaque native payload
  → selected island executor
  → island-native observation
```

`invoke` не залежить від #1048 lowering. Він є diagnostic escape hatch і не
може стати альтернативним механізмом для звичайної семантики мови.

## Порядок інтеграції

1. Restack [#1078](https://github.com/juv4uk/my-lisp/pull/1078) (#1047) на
   current `main`; усунути конфлікти та довести exact new head green.
2. Restack [#1081](https://github.com/juv4uk/my-lisp/pull/1081) (#1048) на
   exact restacked head #1078; довести його окремо green.
3. Зі старого [#1058](https://github.com/juv4uk/my-lisp/pull/1058) зробити
   fresh replay #1006, базований на restacked #1078. Коли #1078 злитий,
   replay базується прямо на `main`.
4. Закрити #1058 як `superseded` після появи fresh replay.

## Межа fresh #1006 replay

Replay переносить лише:

- SID-keyed capability seam;
- CLI `island_invoke` adapter;
- dependencies чотирьох kernels;
- invoke/REPL witnesses;
- authority classification.

Replay не переносить:

- старий `mechanism-selector.lisp`;
- generated artifacts зі старого stack;
- сторонній `uk_surface` repair;
- commits старого #1047 або #1063 stack.

## Інваріанти

- Canon/registry лишаються єдиним джерелом semantic SID і значення.
- Host capability маршрутизує лише вже admitted SID; unknown SID fail-closed.
- Host не інтерпретує law, domain або payload islands.
- Native result не нормалізується у спільну truth/result семантику.
- Selector та lowering лишаються Lisp-owned для ordinary execution.
- `invoke` не є шляхом обходу Canon для нового semantic admission.

## Evidence

Кожен із трьох зрізів має записати exact head SHA і green CI.

- #1078: selector witnesses та authority guards.
- #1081: lowering witnesses поверх exact #1078 head.
- fresh #1006: один raw invoke для Common Lisp, Prolog, CLIPS і Datalog;
  unknown kernel/SID та unsupported payload мають fail-closed witness-и.
