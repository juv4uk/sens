# Nirṇaya (निर्णय) · D11 SRFI-1 list= · відмежувати Type від D1 · 2026-10-25

## Доведена першопричина
У GitHub Actions #40157137603 (точний SHA `02894a101cfc`),
нітивний SENS runner: `checked=500 passed=491 failed=9`.
Три з дев'яти відмов мають ідентифікатори:
`d11-srfi1-list-equality-positive`,
`d11-srfi1-list-equality-structure-positive`,
`d11-srfi1-list-equality-structure-mutant`.
Діагностика SENS: `car expects a non-empty list`.

Причина не в потребі пом'якшити бібліотеку.
`lib/d11-srfi1-list-equality.lisp` уже правильно
встановлює закон: кінець правильного D3-списку — тільки
D3:`()`; пізній D1:ні, сторонній атом або неправильний
зовнішній перелік мають *відмовити з Type* ще до callback.
Старі позитивні свідки помилково стверджували
`хибне? (правильний-список-для-рівності? (сполучити ... ні))`,
немов Type-відмова є поверненим D1:ні. Мутант робив
таку саму неправильну підміну. Це хибний тест, не функція.

## Зміни
- Повний закон `tests/semantic/d11-srfi1-list-equality-law.lisp`
  перевіряє 10 дійсних сценаріїв власне SENS, включно із
  `()`, вкладеними правильними списками, впорядкованою
  нерівністю та нульовим/одиничним N без виклику callback.
- Ізольована `structure-law.lisp` перевіряє лише
  **правильні** вхідні значення.
- `structure-mutant.lisp` висуває хибну, але типізовану
  гіпотезу: правильний перелік списків є неправильним.
  Результат рівно D1:ні, без свідомого викликання Type.
- Чотири негативи у `tests/fixtures/d11-srfi1-list-equality-*`:
  неправильний D1-корінь, неправильний пізній хвіст,
  неправильний зовнішній хвіст, неправильний вкладений
  аргумент перед отруєним callback.
- `scripts/prove-lisp-semantic-t5m.sh`: кожен Type-негатив
  проганяється direct / Zig mint+open+verify / paired /
  standalone Core4; очікувана точна D3 CAR Type.
  Збережено SHA256 усіх нових SENS-входів.
- `scripts/execute_changed_lisp_t5m.sh`: ті самі
  DEFINE із `lib/d11-srfi1-list-equality.lisp` присутні у
  всіх фізичних перевірках змінених файлів;
  `UnknownSymbol` не може замінити потрібний Type.
  Позитиви й мутант перевіряються проти D1 1/0 без
  вигадування семантики хостом.

## Підтвердження та невизначеність
Статично перевірено баланс дужок усіх семи змінених або
нових SENS-файлів і адресність точних механізмів запуску.
Нативного SENS/Zig toolchain у агентському оточенні немає.
**Жоден новий native PASS не заявляється без CI.**
Прохання не переписувати Type-на-ні задля зеленого тесту.

## Стек наступному swarm-агентові
1. Знайти CI на точному SHA цього коміту; перевірити
   `d11-srfi1-list-equality-positive`,
   `structure-positive`, `structure-mutant` та чотири
   `d11-list-equality-*-Type` на всіх трьох виконуваних носіях.
2. Перевірити, що новий changed-file guard не приймає
   `UnknownSymbol` та не помилково повертає D1:ні
   замість D3 CAR Type.
3. Незалежні RED: D6 LET/LET* трипольова форма;
   D10 CLIPS ASSERT/PRINTOUT; фізичний F6;
   `Core4 .lisp/.sens/view` drift. Звірити новіші
   коміти колег до будь-якого дублювання.
4. Відсутні повні механізми D6 MACROEXPAND-1/MACROEXPAND,
   частини D10–D12+ та D24+: не оголошувати release GO.
   Право ратифікації лишається у власника.
5. Інваріант: D1:ні ≠ D3:`()` ≠ Type-відмова;
   дійсність списку доводиться повністю **до** callback.

**Deutsch:** Falsche D11-Tests korrigiert: Fehler Typ ist kein
D1-Falsch. Vier native Negativzeugen und unverändertes SENS-Gesetz.

**English:** Correct D11 list-equality witnesses without relaxing
the Type contract. Four native improper-input negative cases;
CI proof pending.
