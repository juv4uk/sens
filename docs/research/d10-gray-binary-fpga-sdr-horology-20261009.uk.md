# D10 — універсальні функції відбитого двійкового коду Грея

## Походження та мотивація

Наші теми **FPGA/ESP32, радіо/SDR, акустика, годинники, цифрова/аналогова електроніка, двійкова мова SENS** мають спільний об'єкт — скінченне слово з явно визначеною бітністю. Замість окремих функцій для магнітного енкодера, фізичного буфера FPGA, радіоканалу та синхронізації пропонуються дві взаємно-обернені **універсальні математичні** операції.

Джерело: Frank Gray, [*Pulse code communication*, US2632058A, 1953](https://patents.google.com/patent/US2632058A/en). Додаткове математичне дослідження конверсії: [IBM Research Johnsson/Ho (1995)](https://research.ibm.com/publications/on-the-conversion-between-binary-code-and-binary-reflected-gray-code-on-binary-cubes).

### Правила
1. `GRAY-ENCODE-WORD(w,n)` → `g = n XOR (n>>1)` для беззнакового рангу `0<=n<2^w`.
2. `GRAY-DECODE-WORD(w,g)` → `n` через префіксний XOR бітів від MSB до LSB.
3. `w=0, n=0` — нульова ширина без аномального нескінченного слова; позамежові `n,g` відхиляються.
4. Для `w>=1` послідовні (і крайні в циклі) ранги мають **Hamming distance = 1** між Gray-кодовими словами.
5. Обидві операції оборотні для кожної `w` і зберігають явну ширину даних.

Це відрізняється від `DIFFERENTIAL-ENCODE/DECODE` (потокова/фазорна інформація в інших відкритих PR), від `PRIMITIVE-BINARY-WORD-ROOT` (періодичність слова) і від `D8 ROTATE` (перестановка бітів). **XOR і SHIFT можуть зробити перетворення бібліотечно похідним**, отже окрема потреба в резиденті D10 лишається предметом owner-review. За самим збігом або незбігом написання доведення немає.

## Координація, джерела, тести

- Дослідницький знімок `knowledge/d10-gray-reflected-binary-research-v1.json` за комітом `0cf23c95660aa7ae199e6f683bc76f14eabbf958`, точні записи `36` і `58`.
- Ратифікована D1–D9 недоторканна; контроль семантики D2 недоторканний.
- Базовий реєстр D10 `631` (після Spanda); нові research-selected `633`, 256 law-forced, 377 unplaced, 391 remaining, 0 ratified. Записи мають `coordinate=null`.
- Git-SHA-ланцюг від 625 до 633 через `knowledge/d10-selection-transition-history.json`; дві нові `D10P-0007/0008` пропозиції з pin доказів у `knowledge/d10-proposal-ledger.tsv`.
- `scripts/check_d10_gray_word_selection.py --self-test`: exhaustive `0..10` біт roundtrip/adjacency і 8 adversarial proof guards.
- `tests/d10_gray_word_r6rs.ss` у workflow запускає **реальний Chez Scheme R6RS oracle**, не Python-імітацію, із тестами перетворень та відхилення помилкових чисел.
- Жодної претензії на об'єктний код FPGA, драйвер або physical `.sens` до окремого дозволу.

**Паралельна робота:** #4919 ALLAN/DIFFERENTIAL, #4916 Prolog, #4923 primitive binary word, #4890 astronomy/metrology залишаються окремими власниками й не дублюються.
