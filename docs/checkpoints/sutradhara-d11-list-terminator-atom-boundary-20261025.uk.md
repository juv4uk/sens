# Sūtradhāra · D11 LIST-TERMINATOR · 25.10.2026

## Первинна причина
У `lib/d11-list-terminator-evidence.lisp` структурний кінець перевірявся D4 `порожній?` перед D3 `атом?`. Точний SENS-закон термінатора не повинен залежати від черговості D4: спершу D3 ATOM, потім D3 EQ із D3:(). Це архітектурне уточнення, а не доказ уже спостереженої native-помилки.

## Внесено
- D3-атом `()` → `(так ())`, будь-який інший атом, включно D1:ні/так → `(ні атом)`.
- D3-пара → рекурсія виключно через `решта`, вкладена голова є даними.
- `tests/semantic/d11-list-terminator-law.lisp` доповнений двома SENS регресіями: D1:так-атом і правильна пара з D3:().
- Жодних нових D11-кодів, зовнішньої семантики, CI workflow або нової ратифікації.

## Доказовий стан
- Статична перевірка: збалансований SENS-синтаксис, унікальне DEFINE.
- `SENS_SOURCE=lib/d11-list-terminator-evidence.lisp`
- `NATIVE_SENS_POSITIVE=NOT_VERIFIED`
- `NATIVE_SENS_NEGATIVE=NOT_VERIFIED`
- `ZIG_T5M_ROUNDTRIP=NOT_VERIFIED`
- `COMMITTED_PHYSICAL_PAIR=STALE_UNTIL_REGENERATED`
- `RELEASE=NO-GO` до власницького GO та незалежного фізичного доказу.

## Наступний Swarm-таргет
1. На SHA цього коміту виконати `tests/semantic/d11-list-terminator-law.lisp` і чинні `tests/semantic/d11-list-terminator-{mutant,nested-mutant}.lisp` на **реальному SENS**.
2. Перезгенерувати `lib/d11-list-terminator-evidence.sens` та бітовий перегляд `lib/d11-list-terminator-evidence` офіційним Zig/T5M. Перевірити roundtrip і виконання на одному SHA.
3. Продовжити D3/D4→D5/D6→D8/D10: окремо описувати `ВІДСУТНІЙ_МЕХАНІЗМ`, `ВІДСУТНЯ_ФІЗИЧНА_ПРОЄКЦІЯ`, `ПОМИЛКА_ВИКОНАННЯ` й `НЕПЕРЕВІРЕНО`.
4. D12 числовий, а не функціональний домен. Нема ратифікації D11-кандидатів, нових branch/workflow, хост-оракулів чи релізного тегу.
