# Релізний чекпоінт: F6, Core4, D5 — нативне відновлення

Дата: 2026-10-25. Статус: **NO-GO** до зеленого поточного CI.

## Перевірені факти

Завершений CI `40191821188` (коміт `d56157480a3f19b511ddca34617b2cffcce5d7f5`):
- Нативні SENS-закони: **559/563**, чотири RED:
  `d9-f6-package-key-canonicalization-positive`,
  `d5-member-hidden-tail`,
  `d5-assoc-hidden-tail`,
  `d5-assoc-late-record`.
- Історичні сирі викличні голови D5 `11100`/`11101` спричиняли SOURCE_ENCODED_LITERAL_GUARD_FAIL, а не право запускати числові коди. Виправлені окремими комітами колег.
- Core4 не відповідав фізичному `lib/core4.sens`; статичний поділ Core4 проходив крізь середину D3 форм. Розбиття вже виправлене окремими комітами.
- Rust F6 consumer: `root reconstruction rejected`, фактичний SENS вердикт `(rejected invalid-format)`.
- `lib/lisp-fs.lisp` змінювався 25 жовтня, а останній коміт `lib/lisp-fs.sens` був 24 жовтня. Свіжий фізичний bootstrap необхідний, не можна приймати дрейф як PASS.

## Дії

- Коміт `6a66e78f45eeddcdce8e6a88d916aa3e4cda6625` додає **лише на відмові** SENS D1 докази трьох точних форм `format`: цитованого символу, D8 READ та зовнішнього String. Rust тільки транспортує результат; не ухвалює семантичних рішень і не друкує вхідний payload.
- Цей коміт **навмисне** активує наявний у `.github/workflows/ci.yml` reusable `remint-targeted` через позначку `SENS_PAIR_REGEN`. Точний маніфест: `lib/core4.lisp`, `lib/lisp-fs.lisp`. Виконання тільки штатним SENS/Zig T5M, не ручне редагування `.sens`.
- Старі невдалі workflow не перезапускати. Перевіряти новий SHA та його діагностику.

## Наступний агент

1. Перевірити статус remint-targeted та його коміт, точні фізичні SHA обох пар.
2. Після remint підтвердити `producer_records_are_reconstructed_by_the_physical_f6_consumer`; якщо F6 все ще RED, зіставити трійку D1 `F6_FORMAT_BRIDGE_D1` і виправити саме SENS READ/WRITE-ідентичність, не підміняти accepted/rejected.
3. Підтвердити D5 MEMBER/ASSOC: правильність повного D3 хребта перед раннім збігом; негативи дають справжній D3 Type. Окремо від фізичного F6.
4. Для D1–D12+ рахувати не лише визначення, а й native law/mutant, точний source/physical SHA, виконуваність та числові D24+ границі.
5. Без green на поточному main, без дозвілу власника та без фізичних квитанцій — **NO-GO**.

Deutsch: Die physischen F6/Core4-Paare sind ausschließlich mit dem kanonischen Zig/T5M-Workflow zu erneuern.
English: Repair F6/Core4 physical drift only with the repository's canonical remint workflow.
