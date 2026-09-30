# SENS-BINARY-TRANSPORT-ONLY

**Дата:** 2026-09-28 (updated 2026-09-30)  
**Issue:** #1590 · post-M8 measure #1665  
**Статус:** confirmed для CI surface-bench **і** post-M8 three-way

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

Після M8: EN admitted surfaces також → `Call(SID)`.

### Post-M8 three-way (#1665) — виміряно

Evidence: `benchmarks/sens-surface/results/20260930-post-m8/report.md`  
SHA measure: `786c62b9` · PR #1951 · Cachegrind · connector host

| Порівняння | Результат (геом. середнє) |
|------------|---------------------------|
| EN text vs SENS text **steady execute** | **×1.001** (gap ≈ 0) |
| SENS text vs SENS FASL **steady execute** | **×0.997** (gap ≈ 0) |
| EN text **load** vs SENS FASL load | **×4.30** (parse vs 1-byte) |

**#1413 residual EN-runtime-name-cost на steady execute: resolved by M8.**  
Pre-M8 «+16% SENS vs EN execute» — історичний факт, не поточний claim.

Load-path перевага binary FASL лишається реальною (~×4.3).

## Acceptance цього запису

- [x] CI form=sens = fasl 1-byte path (confirmed in `ci_bench.sh`)
- [x] Core fasl/wire = 1 byte (audit #1592)
- [x] M8 removes EN runtime name tax for admitted surfaces
- [x] Post-M8 numeric remeasure (#1665 · `20260930-post-m8/`)
