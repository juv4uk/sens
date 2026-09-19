# Історичне узгодження допуску машинних форм — 2026-09-20

Батьківська задача: #813.

Цей запис завершує аудит історичних гілок без копіювання застарілого машинного коду. Усі збережені закони вже мають свідчення в поточному `main`.

| Збережений закон | Свідчення в поточному main | Рішення |
| --- | --- | --- |
| Семантичний зміст спочатку опускається до структурованих машинних форм | `lib/machine/lowering/semantic-x86-64.lisp` | уже поглинуто |
| Закритий admission є єдиним шляхом від структурованих форм до байтів/host | `lib/machine/admission/x86-64.lisp` + `machine-lowering-boundary.lisp` | уже поглинуто |
| Машинна ідентичність не може створювати або перевизначати мовні SID | `machine-lowering-boundary.lisp` + `crates/my-lisp/tests/machine_lowering_boundary.rs` | уже поглинуто |
| Неприйняті/некоректні машинні форми відхиляються до виконання host | `crates/my-lisp/tests/machine_admission_adversarial.rs` | уже поглинуто |
| Відхилена форма не робить жодного виклику host executor | `crates/my-lisp/tests/machine_admission_adversarial.rs` | уже поглинуто |
| Після native admission помилка не маскується повторним evaluator retry | `tests/fixtures/native-first-execution-witness.lisp` + `scripts/test-current-semantic-slice.sh` | уже поглинуто |
| Структуроване lowering є канонічним; байти є пізнішою проєкцією | `lib/machine/dispatch/native-first-execute.lisp` + шлях lowering/admission/encoding | уже поглинуто |

## Історичні донори

- `research/machine-inst-semantic-contract`: закон межі авторитету збережений; поточний main тепер має сильнішу вертикальну межу ISA/апаратури.
- `feat/machine-admission-1`: закритий admission збережений; поточний main містить розширений канонічний каталог допуску.
- `feat/machine-admission-2-structured-lowering`: structured lowering збережений; поточний main містить ширший профіль lowering.
- `test/machine-admission-adversarial-evidence`: негативне свідчення admission збережене й посилене поточним adversarial-набором.

## Рішення щодо replay

Жодна donor-гілка не зливається цілком. Історичні ідеї вважаються узгодженими тоді, коли кожен збережений закон має поточне виконуване або контрактне свідчення. Цей запис є лише документацією; він не створює другої machine-authority таблиці чи семантичного registry.

## Gate S2

Перед merge батьківської #813:

1. перевірити, що ці witness-и проходять на точному поточному head;
2. перевірити, що новий Rust semantic matcher або дубльований admission authority не з'явилися;
3. перевірити, що поверхні #504/#508 лишаються діагностичними/gateway witness-ами, а не другою семантичною registry.
