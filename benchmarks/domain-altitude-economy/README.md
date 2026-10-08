# Domain altitude economy

**Research authority:** #4403  
**Current semantic authority:** Contract 11.8 / D1–D9 ratified.  
**Semantic effect:** none.

Цей стенд вимірює дві незалежні властивості **вже еквівалентних** canonical program variants:

```text
semantic_altitude = максимальна exact-domain ширина слова у програмі
semantic_bits     = сума exact-domain ширин усіх слів
```

Варіант A Pareto-домінує B лише якщо він не гірший по обох осях і строго кращий хоча б по одній.

Жодного weighted score немає.

## Equivalence first

Порівняння дозволене лише всередині одного `case_id`, де всі variants мають однакові:

- `observable_digest`;
- `result_kind`.

Якщо digest або result kind розходяться, harness завершується помилкою і не видає економічного висновку.

## Input JSONL

Обов'язкові поля:

```text
case_id
variant_id
program             # binary exact-domain words, розділені пробілами
observable_digest
result_kind
role                # resident | expanded | alternate
```

Для `resident` і `expanded` також потрібен `resident_id`.

На один `case_id + resident_id` дозволена рівно одна resident-form і одна expanded-form. Це не дає випадково двічі порахувати один semantic use.

## Gross residency dividend

Для перевіреної пари:

```text
gross_dividend_bits
  = semantic_bits(expanded)
  - semantic_bits(resident)
```

Інтерпретація:

- > 0 — resident реально заощадив canonical semantic bits;
- = 0 — bit-економії немає;
- < 0 — expanded form коротша.

Це **gross**, не “чиста окупність”.

Law certificate bits, proof cost, mechanism code bytes, allocations, Cachegrind I-refs та інші витрати не переводяться у біти довільним курсом. Вони мають залишатися окремими Pareto coordinates.

## Synthetic controls

`fixtures/synthetic.jsonl` перевіряє три режими:

1. resident коротший у бітах, але вищий по domain altitude — обидва variants лишаються на Pareto frontier;
2. lower expanded form краща і по висоті, і по бітах — вона домінує resident;
3. однакова кількість бітів, але expanded form нижча — dividend = 0, lower form домінує по altitude.

Guard також перевіряє, що різні observable digests fail closed.

## Запуск

```sh
python3 benchmarks/domain-altitude-economy/run.py \
  benchmarks/domain-altitude-economy/fixtures/synthetic.jsonl \
  --out /tmp/domain-altitude-economy.json

python3 scripts/check-domain-altitude-economy.py
```

## Наступний науковий крок

Synthetic controls не є доказом користі resident-ів.

Потрібен corpus із приблизно 20 owner-ratified D8/D9 residents, для кожного з яких є:

1. explicit lower-form expansion;
2. executable parity;
3. однаковий observable digest;
4. відсутність legacy Sens8/Sid8 route.

Лише після цього можна публікувати реальні residency-dividend числа.

## Межа влади

Benchmark може сказати:

```text
цей resident у цьому corpus заощадив N bits
цей resident підняв max domain width з X до Y
```

Він **не може** сказати:

```text
цей resident треба видалити
цей resident треба перемістити
ця surface форма тепер семантично краща
```

Такі рішення лишаються окремою semantic/owner authority.
