# D9 geometry S4 — full 512/512 candidate map

**Статус:** research / unratified  
**Issue:** #4005  
**Semantic inventory:** 512/512 complete  
**S2:** 128 fixed / 384 free  
**S3:** 7 proved semantic families, 0 coordinate consequences

## Full candidate

```text
LAW-FORCED   128
GAUGE-FIXED  384
----------------
TOTAL        512
```

## Canonical gauge rule

1. Зберегти всі 128 selector-law coordinates.
2. Взяти 384 UNPLACED meanings із coordinate-independent stable IDs.
3. Відсортувати stable IDs лексикографічно.
4. Відсортувати 384 free 9-bit coordinates лексикографічно.
5. Зʼєднати їх one-to-one.

## Що це означає

```text
GAUGE-FIXED != semantic theorem
```

S3 показав, що сильні semantic laws переживають перестановку coordinate labels. Тому поточна абсолютна адреса решти 384 meanings не випливає з відомої семантики.

S4 просто вибирає один відтворюваний представник equivalence class.

## Заборонені inputs

Gauge не використовує:

- legacy Sens8/Sid8/Function8 coordinates;
- semantic-registry/source codes;
- source-file order;
- human preference for names;
- runtime addresses;
- D8-prefix proximity;
- migration distance.

## Authority boundary

`knowledge/d9-v1-gauge-fixed-candidate.json` — повна карта-кандидат, але **D9 ще не ратифікований**.

Owner ratification має бути окремим явним рішенням.

До цього моменту сильніший coordinate-sensitive law може замінити будь-який GAUGE-FIXED row, але не LAW-FORCED selector rows.
