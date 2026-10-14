# Міжмовні бенчмарки — статус 2026-10-14

**Не performance claim.** Це карта, де що можна порівнювати після
exact-domain / Zig-transport оновлень.

## Аксіоми (щоб не змішати шари)

1. **Width = identity.** Різна ширина бітового рядка — різна ідентичність.
2. **Zig = турнікет, не реєстр.** Фізичний T5/F3C; не закон і не eval.
3. **W8 / Function8 / FASL-era** — provenance, не чинний оракул швидкості.
4. Timing лише після **semantic parity + independent oracle**; інакше
   `BLOCKED-MECHANISM`, ніколи silent fallback.

## Що *є* чинними числами (transport, не «мови»)

| Лейн | Що порівнює | Де | Статус |
|------|-------------|-----|--------|
| Zig ↔ Rust T5/F3C | фізичний encode/decode однакових typed words | `research/zig-codecs/RESULTS-2026-10-14.uk.md` | **виміряно** на pinned runner; p50 нс/оп; **не** universal language ranking |
| migration-zig-gate | purity + authority width + optional codec bridge | `scripts/migration-zig-gate.py` | підготовка, не bench |

Цифри Zig/Rust **не** переносяться на CPython/Lua/Racket і не доводять
«SENS швидший за Python».

## Що лишається BLOCKED для *мовного* порівняння

| Лейн | Корпус | Чому BLOCKED |
|------|--------|----------------|
| `benchmarks/cross-language/` | fib, loop, ackermann, closures, evenodd | harness ще на historical Function8/FASL SENS lane; немає Contract 11.9 canonical replay + oracle |
| `benchmarks/current-en-vs-d1d8/` | 11 workloads | production corpus explicit BLOCKED на reader/runtime boundary |
| `docs/benchmarks.md` (my-lisp) | historical microbench | **HISTORICAL**; не Contract 11.9 |

Маніфест: `bench.json` → `status: BLOCKED-CURRENT-CANONICAL-REPLAY-NOT-IMPLEMENTED`.

## Що вже близьке (surface, не cross-language)

| Лейн | Питання | Нотатка |
|------|---------|---------|
| `benchmarks/sens-surface/` | en vs sens vs uk vs wrap **тієї самої** програми | SURFACES на драбину (D3/D4…); числа D24 (`#d24:…`); post-M8 three-way окремо. Це **внутрішні поверхні SENS**, не CPython. |

## Шлях розблокувати cross-language (без костилів)

1. Згенерувати п’ять workloads з **exact-domain** / current reader (не W8 FASL).
2. Independent oracle (як у sens-surface: Python expected) на ті самі N.
3. Semantic parity: однакові відповіді SENS / CPython / Lua / Racket **до** timing.
4. Зафіксувати: main SHA, CPython/Lua/Racket versions, env, raw samples.
5. Фази окремо: startup / load / ready / repeat(N) / one-shot — як у чинному `run.py`.
6. Physical wire (якщо потрібен) — лише через Zig/Rust T5 після byte parity
   (`scripts/zig_codec_bridge.py`, pin `.zig-version`).

Поки кроки 1–3 не зелені — **жодних ratio SENS:Python у README/CI**.

## Пов’язані issue / handoff

- #1546 CPython, #1547 Lua, #1548 Racket, #1549 binary-trees
- EPIC Zig transport #5766; T5 byte-exact #5767
- `docs/zig-migration-scripts-handoff-2026-10-14.uk.md`
- `docs/migration/semantic-chronology-handoff-2026-10-14.uk.md`

## Команда самоперевірки статусу

```sh
python3 -m unittest benchmarks.cross-language.test_current_gate -v
python3 scripts/migration-zig-gate.py --skip-ladder-identity
# (числа Zig↔Rust — лише з RESULTS + artifact SHA, не з цього файла)
```
