# Siddhānta · поточна контрольна точка релізу · 25.10.2026

## Докази, які вже існують

- Поточне source-HEAD на момент checkpoint: `9ddd50c4d2973429b8b37848cdac456834ca1ac6` (D9/F6: закритий набір D7 ключів протоколу).
- `tests/fixtures/wsm-fs-record-producer.lisp` замінено на SENS-level `фс-записати-із-адресою` комітом `980109e87c3a3bd844f79f1ae77239fecb0e7c00`. Прямий виклик D9 `FS-WRITE` вилучено.
- Remint job `40210496888/121220494435` завершився success і видав `T5M_REPAIR_OK` для `lib/core4.lisp`, `lib/lisp-fs.lisp` та `tests/fixtures/wsm-fs-record-producer.lisp`, кожен із Zig/SENS exact round-trip. Однак цей remint був на попереднішій версії коду; він НЕ засвідчує pair після HEAD `9ddd50c4`.
- Новіша зміна `lib/lisp-fs.lisp` у `9ddd50c4` додає десять закритих D7-подань protocol keys у `фс-пакет-ключ-допустимий?`. На новому source потрібен native test, а не перенос історичного результату.
- Звичайні CI запуски на старших SHA `fb86b232`, `92bf131c` та інші залишались у черзі/виконанні довше за звичайне. Їх не слід оголошувати доказом поточного HEAD.

## Головні невирішені блокери

1. Фізична відповідність `lib/lisp-fs.lisp ↔ lib/lisp-fs.sens` після D9/F6 commit `9ddd50c4`.
2. Фізична відповідність producer fixture після останнього source change.
3. Кінець-у-кінець `wsm_fs_f6_pipeline::producer_records_are_reconstructed_by_the_physical_f6_consumer`.
4. У загальному CI останні видимі failed summaries містили structure guard, ownership guard та Rust mechanism. Точних завершених stderr на current HEAD не було; не вигадувати причину та не переносити RED між SHA.
5. D6 LENGTH/LET/NTH, D11 LIST-INDEX і D12 numeric ladder потребують окремих точних результатів прямого нативного SENS та фізичного T5M.

## Операційна передача

- Підключений локальний Desktop Commander — offline; локального SENS/Zig тут не виконано.
- Не редагувати .sens байти вручну й не обходити action/commit protections. Потрібен дозволений канонічний remint на актуальному main.
- Після remint зберегти source SHA, physical SHA, Zig inverse, paired/standalone result та негативний mutant на одному commit.
- Не вимикати owner guards; не рахувати queued/cancelled/NOT_CERTIFIED як PASS.
- Реліз лишається NO-GO до green Rust/Zig/SENS, F6 producer-consumer, exact physical receipts і рішення власника.
