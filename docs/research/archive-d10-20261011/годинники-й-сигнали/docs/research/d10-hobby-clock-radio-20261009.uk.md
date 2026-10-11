# D10: інтереси, часомірство, радіозв'язок і цифрові сигнали — 630→634
Дата: 2026-10-09. Статус: SELECTED-RESEARCH-CANDIDATES, жодного нового призначеного біткоду / D10 ратифікації / фізичного T5.

## Нові математичні закони
**ALLAN-VARIANCE** (ук: дисперсія-Аллана, укр: дсп-алн) — NIST SP 1065 §5.2.2, equation (6). Не підміняти класичною дисперсією або перекривною Allan variance. Для N>=2 рівномірних без пропусків усереднених за τ дробових частот: Σ(y[i+1]-y[i])² / (2(N−1)). Точний раціональний контракт, tau metadata відомі від вимірювальної апаратури. [NIST оригінал](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication1065.pdf).

**DIFFERENTIAL-ENCODE** (ук: диференційно-кодувати, укр: диф-код) — модульна накопичувальна схема GNU Radio: y[n]=(x[n]+y[n−1]) mod M. Повертає коди та останній стан y. [GNU Radio Encoder](https://wiki.gnuradio.org/index.php/Differential_Encoder).

**DIFFERENTIAL-DECODE** (ук: диференційно-декодувати, укр: диф-дек) — модульний декодер: x[n]=(y[n]-y[n−1]) mod M. Повертає декодовані значення і останній *закодований вхід*. Стани encode/decode визначено різними аргументними контрактами, порушення зламає безперервність по межі чанків. [GNU Radio Decoder](https://wiki.gnuradio.org/index.php/Differential_Decoder).

**DIFFERENTIAL-PHASOR** (ук: диференційний-фазор, укр: диф-фаз) — (I/Q) y[n]=x[n]×conjugate(x[n−1]), без обов'язкової нормалізації амплітуди; повертає нові значення і останній *вхідний* комплексний відлік. [GNU Radio Phasor](https://wiki.gnuradio.org/index.php/Differential_Phasor).

## Контроль і обмеження
Всі чотири функції мають **однакове право на перевірку** за правилами #4013/#4463, але жодна не доведена необхідним низькорівневим примітивом: усі можуть бути похідними обчисленнями на чинному ядрі. Обрана семантика — запропонована мовно видима поведінка, а не апаратний драйвер або новий opcode. Дозвіл на D10 ратифікацію належить власнику після перевірки; D2 контролює структуру й керування. Потрібне незалежне порівняння з реальною GNU Radio реалізацією та NIST числовими тестами, не вважати Python-референс виконанням SENS.

Стан: **634/1024 selected research**, **378 selected but unplaced**, **390 remaining**, **256 law-forced**, **0 ratified**. Попередні 630 рядків і два попередні transition proofs захищені byte-exact SHA через `scripts/check_d10_selection_transition_history.py`. Нове джерельне підтвердження: `knowledge/d10-clock-radio-math-selection-20261009.json`.

## Що з інших інтересів
Вивчені також: астрономія й астрофотографія, маятник, MIDI та акустика, мікроконтролери ESP32 і FPGA, ADS1115/AS5600, аналогові обчислення і Spanda, санскрит/Паніні та українська фонетика, проєкт WSM-OS-Lisp, шахи, радіомодеми, Пролог і Advice Taker, космічна симуляція. Вони **не втрачені**: `knowledge/d10-interest-proposal-v1.json` має 52 ідеї із 7 родин, а `knowledge/d10-clock-radio-math-selection-20261009.json` містить ще 12 тематичних напрямів з рішеннями HOLD/PEER-OWNED. Не створювати кодів для кожного гаджета/алгоритму тільки за тематикою.

## Перевірки
`python3 scripts/check_d10_hobby_clock_radio_selection.py --self-test`: exhaustive bounded encoding/decoding + chunk continuity, exact fractions for Allan, Gaussian-rational complex phasor, 10 adversarial metadata tests. `python3 scripts/check_d10_selection_transition_history.py --self-test`: відновлює 630 і 627 і 625 попередні SHA. Контракт зміни власника/середовища запуску залишається окремим.
