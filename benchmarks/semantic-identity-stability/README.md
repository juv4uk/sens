# Semantic identity stability benchmark

Цей benchmark відповідає на вузьке питання:

> Чи залишається canonical semantic identity незмінною, коли змінюються лише поверхневі назви (`en`, `укр`, `sa`, `sym`)?

## Що він робить

1. Читає **canonical authority** `lib/surface/semantic-registry.lisp`, а не generated Rust projection.
2. Перевіряє, що canonical binary identities у corpus-і унікальні.
3. Рахує:
   - кількість identity rows;
   - кількість surface entries;
   - повні `en`/`укр`/`sa` projection rows;
   - UTF-8 ціну поверхонь;
   - lower bound для 8-бітового identity payload.
4. Детерміновано перейменовує кожну surface spelling і перевіряє, що кожна нова surface все ще вказує на ту саму identity.

## Запуск

```bash
python3 benchmarks/semantic-identity-stability/run.py \
  --out /tmp/semantic-identity-stability
cat /tmp/semantic-identity-stability/report.md
```

## Evidence discipline

Це **source-level representation invariant**, а не benchmark швидкодії та не доказ runtime callability. Позитивний результат доводить лише те, що в заданій canonical registry-моделі identity не залежить від surface spelling. Він не стверджує, що кожен runtime loader приймає довільне перейменування.

Кожен результат містить SHA-256 authority-файла. Будь-яка зміна registry створює новий evidence boundary.
