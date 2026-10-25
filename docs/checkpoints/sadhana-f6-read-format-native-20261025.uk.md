# Sādhana (साधन) · D9/F6 READ/WRITE: точні мітки кореня й об'єкта

Дата 25.10.2026.

## Причинний сигнал CI

Короткий workflow `40167865589` (SHA `06b762488cf50f9c5a6d075ed5a2fa4b9b4d6ccf`) мав
`SENS_LAW_BENCHMARK_SUMMARY measured=529 failed=1`:
`d9-f6-package-key-canonicalization-positive`, expected D1:так, actual D1:ні.

Окремий `sens-cli` producer→consumer фізичний тест відхилив кореневе
відновлення: `rejected / invalid-format`. Ця відмова — сигнал про
значення поля `format` після фізичного D8 READ, а не доказ збою
Zig CRC чи хостового транспорту. Пізніші SHA `66e4d378` і
`a81ffef3` вже виправляли іншу проблему з D7-ключами.
Не відкочувати їхніх змін.

## Зміна SENS

`lib/lisp-fs.lisp`: два функціональні предикати
`фс-формат-кореня?` і `фс-формат-об'єкта?` лишають точні
критерії D7-джерельного маркера та D8 символу, додаючи **лише**
точний результат `(прочитати "wsm-fs-root")` або
`(прочитати "wsm-fs-object")`. Не вводити новий opcode,
евристику URL, текстові псевдоніми чи довільні рядки.

`tests/semantic/d9-f6-package-key-canonicalization-law.lisp`:
у вже зареєстрований фізичний SENS-закон додано два позитивні
закони READ-відповідності, два заперечення перехресної підміни,
два відхилення невідомого маркера. Наявний мутант збережено.

## Атестація та границі

- Статично перевірено баланс джерельних SENS-форм та відсутність
  подвійних визначень.
- Нові перевірки **ще не виконані** в нативному SENS на коміті.
- NATIVE_SENS_POSITIVE=NOT_VERIFIED.
- NATIVE_SENS_MUTANT=NOT_VERIFIED.
- F6_PRODUCER_CONSUMER=NOT_VERIFIED.
- PHYSICAL_T5M=STALE_UNTIL_NATIVE_REGEN.
- RELEASE=l0.42.0:NO-GO.

## Наступний агент

1. На одному точному SHA прочитати автоматичний CI SENS native.
   Зафіксувати D1, source SHA, physical SHA, stage і failing form.
2. Звірити `wsm_fs_f6_pipeline` прямий producer→consumer:
   `accepted` з D9 `фс-відновити-корінь`, точна реконструкція.
   Якщо далі `invalid-format`, не маскувати; вивести SENS-вміст
   формату через чинний механізм свідків.
3. Тільки через SENS/Zig regenerate
   `lib/lisp-fs.sens` і `lib/lisp-fs` з SHA256 та байтовою парністю.
4. Виправити решту незалежних RED D3–D8 та D11 і провести D12
   числові контракти; жодних ручних rerun чи нового workflow.
5. Рішення про `l0.42.0` — лише власник за зеленим повним доказом.
