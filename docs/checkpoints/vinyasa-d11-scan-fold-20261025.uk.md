# Vinyāsa · Д11 SCAN / PAIR-FOLD · 25.10.2026

## Що змінено
- Авторитетне джерело: `lib/d11-historical-scan-fold.lisp`.
- Виявлена першопричина: `накопичити-проміжні-стани` та лівий `pair-fold` викликали користувацький крок до доказу повного D3-суфікса. На пізньому D1:ні отруйний callback міг маскувати обов'язкову структурну відмову.
- Здійснено один загальний SENS-доказ правильного скінченного D3-списку перед обчисленням будь-якого кроку, три окремі рекурсивні ядра без повторної валідації, незмінні публічні імена й порядок.
- Нові негативні свідки: `tests/semantic/d11-scan-fold-structure-before-step-scan-negative.lisp`, `tests/semantic/d11-scan-fold-structure-before-step-left-negative.lisp`. Очікувано `D3 CAR Type` раніше за `D3 CDR Type` callback.
- Чинний позитив: `tests/semantic/d11-scan-fold-d3-tail-law.lisp`. Чинні негативні: `tests/semantic/d11-scan-fold-d3-tail-{scan,left,right}-improper-negative.lisp`.

## Доказовий стан
- Статичні перевірки: парність круглих дужок і точне розташування публічних DEFINE — виконано до Git-коміту.
- NATIVE_SENS_POSITIVE=NOT_VERIFIED.
- NATIVE_SENS_NEGATIVE=NOT_VERIFIED.
- ZIG_T5M_ROUNDTRIP=NOT_VERIFIED.
- COMMITTED_PHYSICAL_PAIR=STALE_UNTIL_REGENERATED.
- RELEASE=NO-GO; candidate SHA не встановлювати за цим комітом.

## Наступний Swarm-таргет
1. На актуальному SHA `main` виконати чинний позитив і всі п'ять негативних D11 SCAN/PAIR-FOLD свідків справжнім SENS із DEFINE бібліотеки; розрізнити CAR Type, CDR Type, parse error та unknown binding.
2. Регенерувати трійку `lib/d11-historical-scan-fold.lisp`, `lib/d11-historical-scan-fold.sens`, `lib/d11-historical-scan-fold` тільки чинним SENS/Zig/T5M; перевірити byte exact + окреме фізичне виконання на одному SHA.
3. Не створювати дубльованих машинних кодів D11, тривалих гілок, workflow або host-оракулів.
4. Окремо перевірити D3/D4 → D5/6 → D8/10 та точний числовий D12 з явними негативними Type-свідками.
5. Оновити релізний доказ лише після реального позитивного й негативного native PASS; зберегти NO-GO до рішення власника.
