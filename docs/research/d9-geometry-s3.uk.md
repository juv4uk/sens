# D9 geometry S3 — strong laws, zero coordinate consequence

**Статус:** research / unratified  
**Issue:** #4003  
**Semantic inventory:** 512/512  
**S2 geometry:** 128 fixed / 384 free

Перевірено сім сильних локальних semantic families.

## Результат

```text
families tested              7
semantic members covered    38
proved families              7
FIXED coordinate effects     0
ORBIT coordinate effects     0
NONE coordinate effects      7
ratified D9                  0
```

## Доведені semantic laws

- persistent vector roundtrip/coherence;
- persistent map insertion/get/contains coherence;
- UTF-8 / Unicode roundtrip and invalid-sequence rejection;
- controlled understand ↔ narrate fact roundtrip;
- content-store put/get/contains/idempotent-address coherence;
- result-status constructor/projection algebra;
- exact quantity/unit exponent algebra.

## Чому координати не фіксуються

Для кожної сімʼї виконано permutation attack.

Якщо переставити координати всіх involved UNPLACED meanings, semantic equation лишається істинним, бо закон говорить про значення та відношення, а не про біти.

Тому:

```text
strong semantic law
!=
absolute coordinate law
```

і для всіх семи сімей:

```text
placement_consequence = NONE
```

## Геометрія після S3

Не змінилась:

```text
fixed selector coords  128
free coords            384
unplaced meanings      384
```

Це вже позитивний результат: залишкова свобода не є наслідком відсутності semantic structure. Вона переживає сильні semantic equations і тому під current evidence є справжнім gauge.

Наступний крок — один deterministic S4 representative, чітко позначений як gauge convention, а не theorem.
