# Тиха доба SENS: стабілізація 10 жовтня 2026

**Пропозиція координаційного режиму:** 10.10.2026, 00:00–24:00 Europe/Kyiv.
Цей текст — не GitHub branch protection. Доки designated single-writer та агенти
не приймуть режим, він є настановою, а не технічно примусовою забороною.

## Межі дозволених робіт

Дозволені тільки ремонт наявних RED CI/Vertical Day, точне відновлення
вже ратифікованої D1/D3 семантики, мінімальні регресійні свідчення,
перевірка SHA/бенчмарк-процесів, triage і документація. **Жодних нових
резидентів, фіч, великих мерджів, переписування Lisp на Rust, нових
benchmark workflow чи бездоказового прискорення.**

Один writer для `main`; жодного force-push, disable-guard, self-hosted
owner-PC runner чи `skipped` як `PASS`. Дорогі бенчмарки, які вже
запущені, зберігають результати; відмова в CI не замінюється зеленим
benchmark run.

## Точна початкова контрольна точка

`main@79e85d2a45f6134d74ee46476b8361bb900705a1`:
- GREEN: [T5 end-to-end](https://github.com/juv4uk/sens/actions/runs/37987060972),
  [Triple projection](https://github.com/juv4uk/sens/actions/runs/37987061030),
  [Hosted runner routing](https://github.com/juv4uk/sens/actions/runs/37987061085).
- RED: [Hosted CI](https://github.com/juv4uk/sens/actions/runs/37987060964),
  [Vertical Day immutable L0](https://github.com/juv4uk/sens/actions/runs/37987061110),
  [Vertical Day non-cancelling smoke](https://github.com/juv4uk/sens/actions/runs/37987061003),
  [domain ladder](https://github.com/juv4uk/sens/actions/runs/37987059280).

Logs identify a common blocking class: `D3:110 COND requires exactly
(test expression)`. Native witnesses still transit legacy three-field
COND in machine Lisp sources; Hosted CI also fails while loading
`lib/time.lisp`. A loader error naming time.lisp does **not** prove
that every legacy clause originates in time.lisp: verify dependencies
and exact source spans before touching semantic code.

## Інваріант регресії COND

Existing `scripts/cond-modernize.py` AST inventory is reused,
not copied into another parser. The hosted check pins an upper
bound on three-field clauses in three active sources:
- `lib/time.lisp`: 0;
- `lib/machine/admission/x86-64.lisp`: 42;
- `lib/machine/lowering/semantic-x86-64.lisp`: 2.

**Це лічильник боргу, не список дозволених законів.**
Debt may only shrink; this narrow gate is not proof of runtime correctness.
`HOLD` on `0`, `t`, or any uncertain predicate means no automatic rewrite.
Only a Lisp-owned D1 law and independent oracle evidence can retire a clause.
Vertical Day continues to fail until the real dependency chain is repaired.

## Виміряні числа — без підміни фаз

[Typed T5](https://github.com/juv4uk/sens/blob/main/docs/benchmarks/2026-10-09-typed-t5-scoreboard.uk.md):
at 1,024 D3 QUOTE forms, 3,482 physical bytes, direct
T5→typed→D2 median **289,818 ns per packet** on
`2cf0c2c4f7df492aca6a617ef4aa4e540f25b2ba`.
It is reader throughput, not evaluator/GPU speed.

[Occupancy masks](https://github.com/juv4uk/sens/blob/main/docs/benchmarks/2026-10-09-domain-occupancy-bitmask.uk.md):
D7 `132.771 → 5.326 ns/lookup` on **different** hosted runs
`d3b729253c9506f7e659892c9376566b4b0c04cd` versus
`290ff0b86f6bfb891ce9177b7deb5e4b9cb397d9`;
this is *not* paired same-machine A/B or whole-language speedup.

## Правило виходу зі stability window

Для exact current HEAD SHA: Hosted CI, Vertical Day L0,
non-cancelling native smoke, binary T5, domain ladder та runner
policy мають бути повністю **GREEN**, без cancelled/skipped
substitution. Якщо ні — freeze завершується в часі, але випуск
залишається `BLOCKED`, а ремонт продовжується окремими PR.

Місце актуального короткого зведення рою:
[issue #1599](https://github.com/juv4uk/sens/issues/1599).
