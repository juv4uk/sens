# Переприв'язка всіх фізичних шляхів SENS на Zig · аудит 14.10.2026

**Точний знімок гілки:** `676dba2b143138b57090f34be4f231ad58da2a37` (до створення цього документа). Головний епік [#5766](https://github.com/juv4uk/sens/issues/5766), P0 [#5779](https://github.com/juv4uk/sens/issues/5779). `PRODUCTION_CUTOVER=OFF`, у `main` ці зміни ще не злиті.

## Незмінний закон межі

```text
Rust / інший host: файлове/мережеве I/O, capability, виклик зовнішнього механізму
    ↓/↑ тільки фізичні bytes, довжина та transport status
Zig 0.16.0: єдина фізична ABI-прокладка, T5/F3C, конверт, CRC, bounds
    ↓/↑ тільки ратифікована двійкова репрезентація SENS та metadata
SENS: власні точні домени, callability, закони, D2, логіка, eval, результат
```

**Жоден Rust `enum`/`ExprKind`/`Value`, `bool`, `Option/Result`, історичний `Sens8/SID8`, host `usize`/endianness/ABI layout не створює мовної ідентичності.** Довжини та транспортні error-code — тільки механізми; помилка Zig ≠ D1:NO. Zig також **не** отримує права тлумачити чи змінювати семантику SENS.

## Що вже реально прив'язано в експериментальному `zig-transport` режимі

| Споживач | Поточний маршрут | Доказ/межа |
|---|---|---|
| `sens program.sens` та `my-lisp program.sens` | `src/main.rs` → `zig_transport_gateway::validate_t5` → чинний canonical reader/evaluator | Zig спершу фізично відкидає неправильні T5 bytes; Rust reader досі механізм виконання |
| `sens-trit open/view/decode/explain/eval/eval-core4` | `read_sens` → Zig physical validation → існуюча SENS grammar/eval | Zig не підмінює D2/SENS рішення |
| `sens-trit encode` | SENS exact source reader → `PackedBitstream` + точні `widths[]` → **Zig `sens_zig_t5_encode_dense` виконує T5 encode** → `.sens` | Не передає Rust `Word` ABI, не викликає Rust T5 encode в primary physical pack; Rust лише незалежний verifier |
| `sens-trit encode-d7-uk` | SENS-owned D7 glyph→W7 перевірка `d7_uk_keyboard_words` → dense exact bits+widths → **Zig T5 encode** | D7 цифри не перетворюються на D24, Rust фізичний reference окремо |
| `sens-trit verify` | Zig physical validation → SENS канонічний verifier | Відмову Zig не обходить Rust codec |
| `sens-trit encode-f3/open-f3/eval-f3/decode-f3` | Zig explicit F3C → T5 physical validation → SENS reader/eval | Явний tiny F3C, жодного sniffing/decode fallback |
| `sens-trit` та `sens/my-lisp` feature-gated | Один `crates/sens-cli/src/zig_transport_gateway.rs` → `research/zig-codecs/transport_abi.zig` | Єдина бібліотечна прокладка для двох CLI, без другого Rust ABI |

**Доказ:** [Actions 38511431211](https://github.com/juv4uk/sens/actions/runs/38511431211) має фокусний `Zig→Rust SENS CLI` і механічні тестові кроки. Кінцевий стан усього workflow треба читати окремо; на старому історичному D8/SID8 міграторі є RED [#5778](https://github.com/juv4uk/sens/issues/5778).

## Перевірений залишковий обсяг (НЕ називати міграцію завершеною)

1. **Core T5 API:** `crates/sens/src/ternary_transport.rs` містить `encode_ternary_words`, `decode_ternary_words`, D7 T5 encode/decode — прямі Rust *фізичні* механізми. Вони не стають нормативною семантикою; потрібне окреме [#5777](https://github.com/juv4uk/sens/issues/5777) переорієнтування реальних споживачів на Zig + незалежний Rust reference. Не вводити небезпечний глобальний default без доказу.
2. **Core binary executor:** `crates/sens/src/binary_execution.rs::PhysicalT5Program::decode` містить Rust T5 decode **разом із SENS canonical reader**. Розділити фізичний decode і SENS admission, зберегти exact typed domain/width/structure. Міняти семантику evaluator тут **заборонено**; поступово винести Rust-derived law до SENS-owned executable definition у #5606/#2817/#2943.
3. **Small F3C Rust reference:** `crates/sens/src/frame3_small.rs` містить Rust фізичні F3C/T5 encode/decode. Feature-gated `sens-trit` уже йде через Zig, але **інші** споживачі й тести можуть користуватися Rust reference. Не видаляти незалежний паритетний еталон до закриття #5770.
4. **Source projection / D7:** у feature-gated CLI **Zig фізично пакує** source exact words і D7 W7. Але SENS reader/grammar/glyph→W7 table **поки реалізовані Rust-механізмом**, а `encode_binary_projection_ternary`, `encode_d7_uk_t5` залишаються незалежними Rust фізичними reference API. Наявний Zig transport pass НЕ доводить, що всі нормативні семантичні визначення вже виконуються програмою SENS.
5. **Historical tool:** `crates/sens-cli/src/bin/sens-to-sens.rs` містить `Sens8` та `ExprKind::Sid`: це насамперед борг **семантичної історичної міграції**, НЕ привід копіювати його правило на Zig. Координація #5778/#5605/#5606; без W8→D8 через байтову колізію.
6. **Host/REPL/LSP/islands/FPGA/GPU/інші crates:** Rust-виклики, що виконують SENS або звертаються до native backend, необхідно інвентаризувати **за викликом та file SHA**. Текстовий REPL або host capability сам по собі не є фізичним `.sens` кодеком; заборонено механічно оголосити кожну host API дію обов'язком Zig або переносити її семантику в Zig.
7. **Freestanding:** теперішній `transport_abi.zig` використовує `std.heap.c_allocator` і `usize/isize` на C ABI; це **hosted**. ESP32-S3, точні ABI, endianness та scratch/stack budget залежать від #5775/#5776.
8. **Конверт:** E1/E2/E3 як profile/length/block/CRC у Zig — відкриті #5772/#5773/#5774; не створювати новий wire-law без власника.

## Обов'язкова драбина прийняття

- [x] Обидва `sens` та `sens-trit` транспортують фізичний `.sens` у Zig feature-mode, використовуючи один спільний ABI.
- [x] `sens-trit encode` і `encode-d7-uk` отримують typed exact-bit words від SENS parser/glyph projection та пакують фізичний T5 у Zig зі щільних бітів + exact width schedule, без передавання host `repr(C) Word`.
- [x] Один workflow має позитивний tracked T5, transport-invalid байт, граматично заборонений D2 CLOSE та `sens`/`sens-trit` parity.
- [ ] Розділити `sens` core фізичний T5 API й semantic reader, залишити незалежний Rust parity-reference.
- [ ] Повний інвентар усіх downstream physical clients із file+SHA, в т.ч. GPU/FPGA та Python glue, без імітації семантичного PASS.
- [ ] SENS-owned semantic self-verdict на парних позитивному й single-bit мутанті через новий шлях з SHA.
- [ ] Zig E1/E2/E3 explicit envelope fields та Rust differential mutational corpus.
- [ ] Freestanding Zig caller-buffer API й реальний ESP32(-S3) device receipt.
- [ ] Production cutover лише після exact-SHA CI, повного корпусу, незалежної owner GO.

**Жодного другого автоматичного workflow, жодного самовільного merge/release.**

## Другий атомарний зріз: Zig реально пакує T5

Примітив `sens_zig_t5_encode_dense(payload_bits, meaningful_bit_len, widths, word_count, out, capacity)` реалізовано в Zig (існуючий `transport_abi.zig`). Зовнішнє ABI бачить два непрозорі буфери, точну довжину, кількість слів та вихідну місткість, а не Rust-структури та не SENS semantic enum. Відхиляються неканонічний tail, short buffer, невірна ширина, несумісна кількість значущих бітів. Позитив: 12 бітів `10 001 00 000 01` → фізичні байти `63 89 06 A1`; різна бітність `1` та `01` → різні T5 байти. Zig сам формує вихідний T5.

У Rust CLI є лише тимчасовий mechanical адаптер `sens::pack_binary_source_words` та width-schedule зі вже SENS-прийнятих слів. **SENS закон цим адаптером не ратифікується**. `verify_companion` все ще використовує Rust reference, тож незалежні Rust↔Zig receipts залишаються, але Rust output НЕ є входом нового Zig T5 encode. Для D7 — незмінну допущену SENS glyph→W7 перевірку винесено в `d7_uk_keyboard_words` без фізичного упаковування; Rust-only шлях лишився референсом. CI для D7 з `Кіт` і негативом `Кі🙂` включено до чинного Zig ABI кроку (фактичний результат лише після завершення SHA-run).


## Третій атомарний зріз — фізичний T5 decode також належить Zig

**Дата:** 14.10.2026; гілка `zig-codecs-t5-f3c-bench-20261014`; cutover лише під `--features zig-transport`. Повний SHA verdict див. #5779; не вважати старі CI-кроки підтвердженням наступного коміту.

- Zig `sens_zig_t5_decode_dense` розпаковує **тільки фізичний T5** в MSB-first щільні payload bits + точний `widths[]`, повертає дві довжини в caller-owned outputs. Probe+fill, no host Word/ExprKind layout у FFI. Невірна фізика → -1, замалі буфери → -2; жодне не означає SENS D1:NO.
- Спільний Rust ABI gateway відновлює `PackedBitstream::from_parts` із перевіркою канонічного tail та передає `widths[]` чинному SENS `unpack_binary_source_words` / `parse_canonical_packed_words`, не робить Rust T5 base-3 декодування.
- `PhysicalT5Program::from_packed_words` у `crates/sens/src/binary_execution.rs` зводить отримані SENS exact words до **тих самих** canonical D2 parsing, lowering, executable-head gate та evaluator, що й наявний Rust-донор; нових admission rules немає.
- `sens` / `my-lisp` та `sens-trit open/view/decode/explain/eval/eval-core4`, explicit F3C open/decode/eval/pack → Zig physical decode → SENS canonical reader. `verify` так само більше не використовує Rust T5 decoder у feature-mode.
- D7 `decode-d7-uk` тепер викликає SENS-owned `decode_d7_uk_words` на точних W7-словах, які розпакував Zig. Незалежний `decode_d7_uk_t5` як Rust reference збережено.
- Прибрано зайвий попередній Zig-validate з `read_sens`: усі її фактичні Zig-mode споживачі роблять явне повне Zig decode або F3C → Zig T5 → SENS без тихого Rust fallback.

**Focused receipts:** Zig `opaque decoder recovers exact SENS dense bits and widths` (golden 63 89 06 A1, width 2/3/2/3/2, query/short buffer/invalid 0xf3, D1:1 ≠ D2:01). Інтеграційний CI крок перевіряє `sens`/`my-lisp`/`sens-trit`, фізичний мутант, самотній D2 CLOSE, open/decode/explain/F3C parity й друкує `ZIG_DENSE_T5_DECODE_TO_SENS_D2_PASS`; run [38513286305](https://github.com/juv4uk/sens/actions/runs/38513286305) підтвердив механічний step PASS, але whole-run FAILURE у незалежному старому D8/SID8 migration test #5778. D7 iteration compile error E0277 з проміжного SHA виправлено комітом `e07dd78f9672135016b30866c46e5a2e139e96eb`, новий combined CI receipt має підтвердити саме цей SHA.

**Що ще НЕ реалізовано:** єдиний Zig ABI для **всіх бібліотечних Rust-core споживачів** поза CLI; E1/E2/E3, heapless freestanding, ESP32-S3, повне відділення host Rust machinery від ратифікованого semantic law. Rust `decode_ternary_words` лишається незалежним еталонним транспортним кодеком (не source of SENS meaning). Full no-leakage та native binary SENS-oracle cutover НЕ DONE; production OFF.
