# Мапінг: `staged-out/ternary_transport` → чинний Zig T5M

Автор: агент Saṃyojaka, 2026-10-26. Для виконавця з `cargo`.

## Навіщо

Коміт `f5a5b213` вивів `crates/sens/src/staged-out/ternary_transport.rs` зі збірки,
але 45 файлів його досі викликають. Нижче — **точна відповідність**, щоб перепис
був механічним, а не творчим.

## Таблиця

| старе | чинне | примітка |
|---|---|---|
| `encode_ternary_words(&[BinarySourceWord])` → `Result<Vec<u8>, TernaryTransportError>` | `sens_cli::zig_transport::encode_t5m_direct(&[BinarySourceWord])` → `Result<Vec<u8>, String>` | **сигнатура збігається**; різниця лише в типі помилки |
| `decode_ternary_words(&[u8])` → `Result<Vec<BinarySourceWord>, TernaryTransportError>` | `sens_cli::zig_transport::decode_t5m_words(&[u8])` → `Result<Vec<BinarySourceWord>, String>` | те саме |
| `decode_ternary_program(&[u8])` | `sens_cli::zig_transport::decode_t5m_words(&[u8])` | та сама функція, інше ім'я |
| `open_ternary_program(&[u8])` → `Result<String, …>` | `render_binary_words_spaced(&zig_transport::decode_t5m_words(bytes)?)` | текст віддає **SENS**, не Rust |
| `encode_binary_projection_ternary(&str)` → `Result<Vec<u8>, …>` | `parse_binary_source_words(text)?` → `.map(\|t\| t.word)` → `zig_transport::encode_t5m_direct(&words)` | текст розбирає **SENS** |
| `render_ternary_words_vertical`, `ternary_transport_accounting`, `*_ternary_coordinates`, `*_d7_uk_t5` | **немає прямого відповідника** | див. нижче |

## Дві функції без відповідника

`encode_d7_uk_t5` / `decode_d7_uk_t5` **не мають** прямого еквівалента в
`zig_transport` — їх треба писати локально, як це вже зроблено в
`crates/sens-cli/tests/d7_keyboard_t5.rs:16,25`:

```rust
fn encode_d7_uk_t5(source: &str) -> Result<Vec<u8>, D7CodecError> {
    let words = /* W7-координати з keyboard projection */;
    Ok(zig_transport::encode_t5m_direct(&words)?)
}
```

Це **не механічна заміна** — потрібне рішення про проєкцію клавіатури.

## Обмеження, яке я не можу зняти

**`crates/sens/tests/` бачить `sens_cli` лише завдяки `54314b9ff`** (dev-dependency).
Без нього 21 файл фізично недосяжний — саме тому перепис і застряг.

## Чого НЕ робити

- Не повертати `pub use` зі `staged-out` — це відкат рішення `f5a5b213`
  («без Rust fallback»).
- Не міняти тип помилки на `TernaryTransportError` — він теж staged-out.
  `zig_transport` віддає `String`.
- Не переписувати `frame3_small.rs` наосліп: він у `src/`, його виклик усередині
  `#[cfg(test)]`, тому помилка там не ламає `cargo build`, але ламає `cargo test`.

## Перевірка після перепису

```bash
cargo test --locked -p sens --test translation_boundary
cargo test --locked --workspace
grep -rn "open_ternary_program\|encode_binary_projection_ternary" crates/ \
  | grep -v staged-out   # має бути порожньо
```

Deutsch: exakte Zuordnung der ausgemusterten Ternary-API auf den Zig-T5M-Pfad.
English: exact mapping of the retired ternary API onto the Zig T5M path.
