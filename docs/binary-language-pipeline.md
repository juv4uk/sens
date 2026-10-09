# Двійковий pipeline SENS

Цей документ фіксує порядок виконання вже наявних binary witness/generator/guard-скриптів.

## Канонічний потік

```
F−1 neutral carrier
        ↓
F0 exact bounded word identity
        ↓
ratified domain law
        ↓
witness / falsifier
        ↓
generated projection
        ↓
backend mechanism
```

Точка входу:

```sh
bash scripts/test-binary-language-pipeline.sh
```

Скрипт свідомо не запускає нову семантичну генерацію. Він лише:

- перевіряє нейтральні властивості двійкового carrier;
- перевіряє exact width + exact bits;
- перевіряє актуальний D3/bīja3 authority;
- перевіряє D1–D9 canonical domain tables;
- перевіряє binary-domain governance;
- блокує повернення semantic identity до raw `u8`/Sid8.

## Що не є authority

Physical `u8`, byte packing, FPGA/register width, generated projections, Rust enums і transport framing — механізми/проекції. Вони не надають semantic meaning бітовому слову.

## Negative controls

Pipeline має зберігати такі відмінності:

```
1   ≠ 01   ≠ 001
001 ≠ 0010
01  ≠ 10
```

Внутрішня послідовність `00` є payload, а не автоматичним delimiter. Значення не виводиться лише з ширини слова.

## Межа цього gate

Цей gate не ратифікує нових residents і не змінює `language-contract.lisp`. Він лише зв'язує наявні докази в один перевірюваний integration entrypoint.
