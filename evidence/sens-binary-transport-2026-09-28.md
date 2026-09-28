# SENS-BINARY-TRANSPORT-ONLY

**Дата:** 2026-09-28  
**Issue:** #1590  
**Статус:** confirmed для CI surface-bench; post-M8 remeasure — pending agent with valgrind

## Що вже чинне (не гіпотеза)

### Runtime / AST

- `ExprKind::Sid(Sens8)` / `Call(Sens8, …)` — 1 байт identity
- FASL `TAG_BINARY` + `packed_byte()` — 1 байт (`syntax.rs`)
- Wire `TAG_BINARY` + 1 байт — 1 байт
- M8 (#1593): admitted surface (`+`/`-`/…) → `Call(SID)` при lower

### CI bench path

`benchmarks/sens-surface/ci_bench.sh` (коментар у файлі):

> Форма `sens` спершу кодується в двійковий вигляд (fasl, функція = 1 байт)
> самим бінарником — цей крок не міряється.

Тобто **identity claim у CI для form=sens уже йде через 1-byte fasl**, не через
8-символьний текстовий сурогат як transport.

8-символьний `00001100` у source files лишається **reader surface** (як і
`sens!` macro) — це дозволено аксіомою source routing, не є transport identity.

## Що змінилось після M8

До M8: EN names лишали `+`/`-` як runtime lookup → execute gap EN vs SENS ≈ +16%.

Після M8: EN admitted surfaces також → `Call(SID)`. Очікування:

| Порівняння | Очікування post-M8 |
|------------|---------------------|
| EN text vs SENS text (same binary) execute | gap ≈ 0 (обидва Call) |
| EN text load vs SENS binary fasl load | SENS load все ще ×~3–4 (parse vs 1 byte) |
| SENS text vs SENS binary execute | ≈ 0 (lower already SID) |

## Pending (потрібна машина з valgrind)

1. Повторити `benchmarks/sens-surface` three-way на main ≥ `37f31edd` (M8).
2. Записати results dir `YYYYMMDD-post-m8/`.
3. Якщо execute EN≈SENS — закрити residual claim з #1413 як **resolved by M8**.

## Acceptance цього запису

- [x] CI form=sens = fasl 1-byte path (confirmed in `ci_bench.sh`)
- [x] Core fasl/wire = 1 byte (audit #1592)
- [x] M8 removes EN runtime name tax for admitted surfaces
- [ ] Post-M8 numeric remeasure (agent with hardware)
