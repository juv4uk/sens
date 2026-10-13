# Інвентаризація десяткових мостів у шляхах ідентичності SENS

Базовий знімок: `7d2a8d685070091385c60e088f77f3e4ae6ea792` (2026-10-13). Обсяг: активні canonical reader/domain carrier/codec/loader/migration paths, перелічені у `crates/sens/tests/identity_decimal_ratchet.rs`; архівні знімки/vendor не заявляються як повністю проскановані.

Правило: ідентичність — пара `(точна ширина, бітове слово)`. `format!("{:0width$b}")` і `int(bits, 2)` з явною перевіркою ширини — бітові трансформації, не decimal bridges. Трійкова цифра 2 у T5 — фізичний separator/padding, не числова identity.

## Зміни

| Файл | SHA базового знімка | Дія |
|---|---|---|
| `crates/xtask/src/compiler_export.rs` | `8d8afb359f9f7adb35c4c76f662189226b5a332a` | Прибрано проміжний `u8`: тепер використовуються `parse_binary_source_words` і typed `BinarySourceWord::W3/W4`. |
| `crates/sens/src/semantic_registry.rs` | `38259cbab96231857ef5e9172ea8a91aa856629a` | `semantic_id.to_string()` замінено явним 8-бітовим `format!("{:08b}", packed_byte)`. Старе `Display` і так друкувало біти, але це більше не прихована конвенція. |
| `scripts/domain_tables.py` | `b3a807c3669f0ba27bda601d78061ca827bc3703` | Позначено `human_number` як `projection-human`; helper приймає тільки явно типізовані D24+ ширини. |

## Carrier, reader та codec

| Файл | SHA базового знімка | Класифікація |
|---|---|---|
| `crates/sens/src/domain_identity.rs` | `610ab63c7fbb804ea3acdc271a9de512cc368ee8` | Безпечний width-tag у enum variant; форматування `{:0width$b}`. |
| `crates/sens/src/domain_ladder.rs` | `bf8da3c3b284459bda1639928dc3a727411e7131` | Координата `(width,bits)`; parser читає лише 0/1 і зберігає довжину слова. |
| `crates/sens/src/canonical_reader.rs` | `20b066ab1f82f2ccc678ca149a7318c965d38a21` | Прямий binary reader; генератор має явну ширину. |
| `crates/sens/src/source_words.rs` | `b6484826b029dbc7de12983b3d58ceab2ee8f93b` | `BinarySourceWord::W1..W9` фізично утримує точну ширину. |
| `crates/sens/src/packed_bits.rs` | `7449654192d90dd4dad31eddf95db334f6eec8d1` | Пряме пакування бітів та окремий schedule меж слів. |
| `crates/sens/src/frame3_domain.rs` | `87812c9a4440a659914d6c81df1cfaef4363aa15` | Width і payload передаються явними полями. |
| `crates/sens/src/universal_frame3.rs` | `528690c88bf29afcfc3ff645c9764dd8b0bf490a` | Width-qualified framing; десяткового рядка між identity немає. |
| `crates/sens/src/binary_framing.rs` | `4e963f7253116c0fba5a16b3e0aa3ff5b31cbf21` | Identity frame має explicit width tag; numeric frame є окремим типізованим шляхом. |
| `scripts/sens_t5_codec.py` | `c9a1fc3dae75014583baa9e34989e42834aa6d44` | T5 base-3 separator/padding; typed digest включає ширину. |
| `scripts/d7_symbol_codec.py` | `ed0fdad20c383223da6b7768c4b151d7ee132c6d` | D7 coordinate — рівно 7 біт із перевіреної таблиці. |

## Loaders і migrators: активний scan scope

У цих шляхах слова лишаються бітовими рядками з явною довжиною або проходять фізичний T5 codec з round-trip і typed-width digest. Знайдені `int(..., 2)`, `format(..., "b")`, `from_str_radix(..., 2)` є явними двійковими трансформаціями; `int(..., 16)` працює з SHA/physical bytes, не з identity payload.

| Файл | SHA базового знімка |
|---|---|
| `scripts/migrate-domain-ladder-source-batch.py` | `60e40e20da0a297c5526ad093f8dd94393f224c6` |
| `scripts/migrate-exact-domain.py` | `eaf243b0460e721161a3f4fc7584de7c4302ed8e` |
| `scripts/migrate-selected-lisp.py` | `74de37bb5f87304b57b8d9cae3a238ecec7fc5c5` |
| `scripts/admit-t5-migration.py` | `822fbe52a638874dd785de92655ee55b63fb3788` |
| `scripts/migrate-t5-batch.py` | `b3929f8063feb99d862751451296228b0e578001` |
| `scripts/migrate-approved-t5.py` | `baddcd70cb3b3ddda9af25aec54db1ed9f0abf22` |
| `scripts/migrate-three-pass.py` | `77068e03e7ca5df9684655ce69898ee9264818dd` |
| `scripts/migrate-to-sens-codes.py` | `ba3d03efbd11160fdadee62a051a26a186eddf74` |
| `scripts/translate-domain-program.py` | `ffce09d1f04b032cc3a95286be20744ca2da421e` |

Таблиці `lib/domains/d1.lisp`–`d10.lisp` є бітовими даними, не decimal payloads. SHA: D1 `6700f6680046e1d610f2ff269407d440ca44c2e3`, D2 `484451cf3c73047158a7886e0874335a9bf8d7f9`, D3 `55b837d05a5772a65c89c6c0d5a8305d2db34256`, D4 `03bca09faf5a5299384a5413b0a16ba42eb0a741`, D5 `c186b589e10cafce7817f7bec5eb5adada6a9c09`, D6 `b7882a5c06625d1818d69a21d507e41f801332eb`, D7 `568bdf3ced54a635c0cd82257fa5f19234dff213`, D8 `97cdd8e8509214468f340492aff71f19da8720b7`, D9 `b013ad78384ebb0174e0c73205e4b6c85dc344db`, D10 `71faa77d69aad537a280b0d5a4680579f1506d92`.

## CI-ратчет

`crates/sens/tests/identity_decimal_ratchet.rs` сканує перелічені активні identity paths: default decimal `.parse::<integer>()`, base-10 `from_str_radix`, підозрілий `to_string()` і implicit decimal formatting. Виняток — лише явна мітка `projection-human` поруч із рядком. Негативні/позитивні контрольні приклади перевіряють сам scanner.

Ратчет не забороняє десяткову арифметику загалом: числові домени D24+ і їхні людські/UI проєкції лишаються легальними у власному контракті. Scope захищає identity paths, а не відключає числові функції SENS.
