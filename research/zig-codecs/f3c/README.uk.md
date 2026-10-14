# Zig Frame3 Carrier (F3C) · exact-width SENS

**Статус:** реалізовано дослідний Zig source, **ще не підтверджено фактичним Zig 0.17.0 компілятором чи Rust↔Zig parity**. Він доповнює поточний T5, не замінює Rust production.

Контракт: [#5520](https://github.com/juv4uk/sens/issues/5520), [#5768](https://github.com/juv4uk/sens/issues/5768); Rust [frame3_small.rs](../../../crates/sens/src/frame3_small.rs) і [senc.rs](../../../research/framed3/rust_codec/senc.rs). Zig модуль `f3c.zig` незалежно від Rust FFI повторює bounded rank/unrank за таблицею допустимих тритових суфіксів, групує довжини у фізичні byte buckets, зберігає D1–D9 exact-width, а decode *fail-closed* перевіряє канонічність й перепаковує точний T5.

- Вхід encode — фізичні канонічні T5 `.sens` байти. Повертає `null` на unsupported/неекономному випадку; **не перезаписує** вхід.
- F3C допускається лише як повний `.senc` файл з першим байтом `0xf3`; тільки одна D3-profile форма, T5 ≤16 фізичних байтів, повний F3C **строго менший**, і відновлення T5 **точно побайтно**.
- Decode F3C — тільки явно вибраний режим; жодного byte sniff, T5 fallback чи альтернативної семантики.
- Провідні нулі бітових слів, D2 структуру, QUOTE-дані збережено. Транспортні 2 не є семантичними цифрами. У Zig використовується `u256` для bounded математики rank — це арифметика **фізичних номерів рамок**, не семантичний десятковий посередник.
- F3C без внутрішньої CRC/MAC. Зовнішні довірені SHA-256 manifest/signature перед виконанням залишаються завданням loader/security.

## Механічні тести, Zig 0.17.0

```bash
zig test research/zig-codecs/t5/t5.zig
zig test research/zig-codecs/f3c/f3c.zig
```

Golden vector: T5 `63 89 06 a1` ↔ F3C `f3 40 60`; вкладена програма T5 `66 38 67 89 89 3b 35` ↔ F3C `f3 36 5f 1b d0 c9`. Є rank/unrank boundary checks, негативні carrier checks і перевірка D3 invalid empty frame.

Це **механічні** тести, не нативна SENS-семантика, не фактичні результати CI. Для DONE потрібен **запущений** Rust↔Zig parity harness на pinned corpus та реальні benchmark numbers T5/F3C із #5771.