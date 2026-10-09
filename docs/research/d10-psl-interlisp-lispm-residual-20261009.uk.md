# D10: незлиті історичні Lisp, окремий первинний зріз PSL / Interlisp / Lisp Machine

**Дата: 2026-10-09. Статус: RESEARCH/HOLD. Додавання відібраних кодів = 0, координат = 0, ратифікованих = 0.**

## Що перевірено
- Git-гілки `research/2344-historical-ledger`, `research/2678-historical-unplaced-handoff`, `research/2718-d1-d6-historical-gap-audit`, `research/d10-psl-interlisp-historical-20261009` і `feat/d8-historical-full-occupancy`. У старому PSL/Interlisp донорі відпрацьовані `PUTD`, `GETD`, `COPYD`, `REMD`, `UNDO` тощо — **не вибирати вдруге**.
- Канонічні реєстри `knowledge/d1-d9-foundation.json` (blob `09d1d71c39d1484dfd005a5068dbb18b76f0f0d4`), `knowledge/d10-v1-semantic-inventory.json` (blob `73dd518469f972c55411e004b70b054ba8b3ec86`). **625/1024 selected, 0 D10 ratified**.
- Відокремлено від відкритих PR #4837 (глобальний історичний gap), #4838 (R7RS), #4839 (R6RS), #4841 (масиви/бітові поля) та #4842 (CLOS/Interlisp). Окреме написання НЕ доводить незалежного семантичного значення.

## PSL (9 історичних операцій, пізня документована редакція)
**[PSL Users Manual version 4.2, 1997](https://reduce-algebra.sourceforge.io/lisp-docs/allman1.pdf)**: §8.2.2, друковані сторінки 103–105 (PDF 110–112); §7.4, сторінка 91 (PDF 98).

- `WRAP`, `REMOVE-WRAPPER`: функціональні обгортки з базовим визначенням і типом, з можливістю інспекції та вибіркового видалення. На відміну від `GETD` / `PUTD`, перевірити **композиційний порядок** і обходження рекурсивного перехоплення. **HOLD**: переважно language-control D2 + налагоджувач, не автоматичні D10.
- `WRAPPED?`, `WRAPPER-OF-TYPE?`, `WRAPPER-TYPES`: запити поверх уже наявного стану обгорток; найімовірніше похідні.
- `FUNCTION-LAMBDA-LIST`, `FUNCTION-BASIC-DEFINITION`: reflection API; у скомпільованій функції реальні текстові імена аргументів можуть бути недоступні.
- `CATCH-ALL`, `UNWIND-ALL`: PSL §7.4 — explicit `(tag,value)` handler на нелокальному переході; `UNWIND-ALL` також викликає handler на звичайному поверненні. **Власник керування: D2**, порівняти D10 CATCH і D8 UNWIND-PROTECT.

**Версійна обережність:** джерело 1997 року є нащадком PSL 3.2 (1984); цей аудит НЕ приписує ці точні API 1984 року без окремого підтвердження. Збережено посилання на [історичний каталог PSL 3.2](https://www.softwarepreservation.org/projects/LISP/standard_lisp_family).

## Interlisp (5 історичних операцій)
**[Interlisp Reference Manual, October 1978](https://softwarepreservation.computerhistory.org/LISP/interlisp/Interlisp-Oct_1978.pdf)**: §5, Changing and Restoring System State, друковані стор. 5.7–5.9.

- `RESETLST`, `RESETSAVE`: рамка відновлення стану і реєстрація undo операцій, коли scope завершується нормально, помилкою або системним RESET/control-D у гарантованих межах. **Посібник прямо не гарантує відновлення при всіх інших нелокальних переходах**.
- `RESETVAR`, `RESETVARS`, `RESETFORM`: спеціальні проєкції для глобальних змінних і setter, що повертає попередню настройку. Перевірити, чи composition of D8 UNWIND-PROTECT + D8 PROGV already suffices, не створювати обхід D2.

## Lisp Machine (7 історичних операцій)
**[Lisp Machine Manual, 4th Edition, 1981](https://tumbleweed.nu/r/lm-3/uv/chinual4th.html)**, §5.12. **[Пізніша редакція](https://tumbleweed.nu/r/lm-3/uv/chinual.html)**, §5.12.2.

- `DEFRESOURCE`, `ALLOCATE-RESOURCE`, `DEALLOCATE-RESOURCE`: pool object, compatibility matcher, constructor, release; відокремлювати життєвий цикл об'єкта від адреси/GC/allocator backend. Поки **mechanism / ownership HOLD**.
- `USING-RESOURCE`: гарантоване повернення ресурсу по виходу через `UNWIND-PROTECT`; очевидний кандидат на доведення DERIVABLE, а не новий D10.
- `CLEAR-RESOURCE`: цікаве спостереження **stale lease після очистки**: об'єкт, що був in-use під час clear, не можна тихо повертати до нового pool; пізнє звільнення сигналізує помилку. Це може бути чіткою мовно-видимою відмінністю від простого `DEALLOCATE-RESOURCE`. **Найвищий пріоритет для незалежного falsifier**, але якщо семантика належить виключно allocator island, не вносити до Core.
- `MAP-RESOURCE`, `DEALLOCATE-WHOLE-RESOURCE` явно зустрічаються в пізнішій редакції; не приписувати їх четвертому виданню без первинної перевірки.

## Перевірка і пропозиції
Всі 21 записи мають `historical_name`, два українські варіанти `surface_uk` / `surface_ukr`, історичне першоджерело й розділ, positive witness, falsifier, conceptual neighbors, owner, priority, triage. Усі `selected=false`, `ratified=false`, `coordinate=null`. Код у `.sens` не утворюється, зміни D1–D9 заборонені.

Найцікавіші *три незалежні запитання*:
1. `CLEAR-RESOURCE`: чи потрібна семантична мітка покоління оренди (lease epoch) для fail-closed release?
2. `RESETLST`: чи відновлює SENS потрібний набір історичних виходів через уже ратифікований D8 UNWIND-PROTECT і структуру D2?
3. `WRAP`: чи існує спостережуване API впорядкованих перехоплювачів функції, не похідне від наявних GETD/PUTD і функцій D5?

**Незавершене дослідження:** первинні посібники **[T / Scheme](https://softwarepreservation.computerhistory.org/LISP/scheme_family.html)**, **[Le_Lisp](https://softwarepreservation.computerhistory.org/LISP/le_lisp.html)**, **[Franz / NIL / Spice](https://softwarepreservation.computerhistory.org/LISP/)** залишаються на наступні по-секційні passes; не оголошувати повними до повного функціонального census.

Запуск fail-closed дослідницького gate: `python3 scripts/check_d10_psl_interlisp_lispm_residual.py --self-test`. Перевірка machine census **не є oracle реалізацією**: потрібні порівняльні виконання у донорних реалізаціях.
