# Ukrainian surface naming

The canonical domain tables use two Ukrainian columns for different jobs:

- `ук` — compact coding surface;
- `укр` — expanded Ukrainian explanation.

The compact surface must stay guessable from the expanded one. We shorten structure, not word roots.

## Stable compact grammar

- predicates keep `?`;
- destructive/in-place operations use `!` in all programming surfaces: `ук`, `укр`, and `en`; `укр` may retain the expanded `-на-місці!` wording;
- composite selectors use a path alphabet:
  - `п` = `перше`;
  - `р` = `решта`;
  - examples: `CAAR → п-п`, `CADR → п-р`, `CDAR → р-п`, `CDDR → р-р`;
- D7 omits redundant domain context such as `звук-` and `текст-` when the resident remains unambiguous;
- standard mathematical abbreviations are allowed when conventional and unambiguous: `нсд`, `нск`;
- do not invent clipped stems such as `відобр`, `посл`, `заст`, `елем`.

## Examples

| ук | укр |
|---|---|
| `п-р` | `перше-від-решти` |
| `видалити!` | `видалити-на-місці!` |
| `нсд` | `найбільший-спільний-дільник` |
| `а-короткий` | `звук-голосний-а-ротовий-короткий` |
| `цифра-8` | `текст-цифра-8` |

The compact form is a human surface only. It never changes exact domain identity, resident coordinates, or law.

## Додаток 2026: норма скорочень і захист смислу (D10)

Перевірено за чинним стандартом державної мови **«Український правопис» (2026)**,
§ 61–62: <https://mova.gov.ua/storage/app/sites/19/2026/rishennja-komisiji/01-03/sdm-ukrayinskii-pravopis-vidannia.pdf>.
Про набрання чинності 28 березня 2026:
<https://mova.gov.ua/news/ukrainskyi-pravopys-iak-standart-derzhavnoi-movy-nabrav-chynnosti>.

**Не плутати**: офіційні графічні скорочення (звичайно з крапкою) й
лексичні абревіатури (§ 61–62) — інша річ, ніж ідентифікатори програм.
`ук` не зобов'язаний наслідувати газетне «знач.»; у SENS `.` є
структурним знаком, отже графічне `поч.` не слід механічно переносити
на кодовий alias. Програмна поверхня — умовна однозначна назва,
**не нова нормативна форма українського слова**.

Точне джерело програмних умовностей — R7RS § 1.3.5:
<https://standards.scheme.org/corrected-r7rs/r7rs-Z-H-3.html>.
Тут `?` — предикат, `!` — мутація, `->` — перетворення подань
(наприклад, `вектор->список`). У Common Lisp донорські назви предикатів
традиційно закінчуються `P` або `-P`, але **`LISP` залишається
точним іменем донора**, а `ук/укр/en` можуть застосовувати читабельне
`?`: <https://google.github.io/styleguide/lispguide.html>.

**Правила свідомого скорочення D10**:

1. У `ук` скорочуємо синтаксичні конструкції й зайвий контекст,
   але зберігаємо цілий упізнаваний корінь; `укр` дає повну розгорнуту
   дію або значення, не копіює механічно складені англійські іменники.
2. Стандартизовані технічні позначення (`utf8`, `gf2`, `crc`,
   `avl`, `ntp`, `mcts`, `ацп`) в ідентифікаторах допустимі як
   предметні символи, **але це не графічні скорочення § 62**.
3. Заборонені випадкові відрізані корені типу `дсп-алн`, `диф-дек`,
   `св-різн`, `замчас`. Натомість `дисперсія-аллана`,
   `диференційно-декодувати`, `сертифікат-скінченних-різниць`,
   `часове-замикання`.
4. Тільки явно позначене перетворення між видами/поданнями дає
   `->` у `ук`; знаки `?` і `!` визначає **поведінка**, а не
   схожість назви донора. Наприклад `REMPROP` повертає булевий
   результат **і змінює список властивостей**, тому це
   `вилучити-властивість!`, а не предикат:
   <https://www.cs.cmu.edu/Groups/AI/html/hyperspec/HyperSpec/Body/fun_remprop.html>.
5. Кожне нове скорочення треба перевірити на однозначність серед
   **усіх D1–D10** і на збереження `bits ↔ LISP ↔ law`.
   Скорочення не дає нового коду і не змінює фізичного виконання.

**Санскрит — окремий контроль якості.** Класичний `samāsa` має
власні морфологічні правила, зокрема будову основ, семантичні відношення
та `sandhi` між компонентами; довільно з'єднані рисками транслітеровані
терміни не можна оголошувати перевіреними санскритськими словами:
<https://ubcsanskrit.ca/lesson12/samasa1.html>.
Наявний `san` у D10 — робоча IAST-орієнтована
**термінологічна поверхня**, доки не виконано окрему граматичну вичитку.
