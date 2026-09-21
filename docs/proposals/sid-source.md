# Пропозиція: 8-бітний SID як вихідна форма

**Статус:** PROPOSED · не є зміною `language-contract.lisp`.

## Проблема

`lib/surface/semantic-registry.lisp` уже встановлює 8-бітний SID як
канонічну ідентичність: наприклад, `define` має `00001001`. Проте цей SID
ще не є написанням, яке reader приймає як executable operator. Нинішня
таблиця тому є повним реєстром identity, але не повним контуром source →
reader → evaluator.

## Два автори SID-подання

1. **Generated artifact.** Компілятор або конвертер може генерувати SID-source
   для артефактів, diff-ів та перевірок. Тут допустимі символи, які людина
   не вводить вручну.
2. **Handwritten source.** SID має бути рівноправною поверхнею для автора.
   Він мусить друкуватися на українській ЙЦУКЕН-розкладці без перемикання
   розкладки. Інакше SID стане закритою формою лише для генераторів.

Людські aliases (`визначити`, `define`, символічні surface-и) не зникають:
вони й SID мають резолвитись до однієї canonical identity.

## Reader token: критерії

Reader token для SID має одночасно виконувати три вимоги:

| Критерій | Вимога |
| --- | --- |
| ЙЦУКЕН | Друкується без перемикання розкладки. |
| Однозначність | Лексер однозначно відрізняє token від десяткових чисел, quote, predicate- та mutation-позначок. |
| Семантична читабельність | Знак продовжує чинні conventions: `'`, `.?`, `=?`, `:`, `:п`, `:р`, `?:`, `?`, `!`. |

### Кандидати

| Token | Плюси | Мінуси | Статус |
| --- | --- | --- | --- |
| `=00001001` | `=` доступний на ЙЦУКЕН; продовжує лінію `=?` як exact identity; 8 біт видно буквально | Потрібне окреме lexer rule для `=` + восьми бітів | **Рекомендований кандидат** |
| `==00001001` | Візуально відділений від звичайного `=` | Дублює знак без доданої семантики | Альтернатива |
| `~00001001` | Короткий префікс | `~` має конотацію приблизності, тоді як SID exact | Не рекомендовано |

`#00001001` не є рекомендованим handwritten syntax: на українській
розкладці ця клавіша пов'язана з `№`, тому він не проходить критерій
доступного ручного введення. Для generated artifact він міг би бути
технічно допустимим, але одна shared form краща за два паралельні формати.

SID source має лише одну числову форму: **рівно вісім двійкових бітів**.
Форма на кшталт `=9` не допускається: вона створила б другий lexer format і
розмила б саму обіцянку byte SID.

## Потрібний контракт до implementation

Перед reader/evaluator змінами owner має ратифікувати:

1. точний token;
2. чи SID дозволений лише в operator position;
3. error для malformed або unknown SID;
4. рівність observable behavior між surface call і SID call;
5. правило quoted data: `(quote (define x 1))` не конвертується у
   executable SID call.

Після ратифікації потрібні reader/evaluator dispatch, Lisp AST-конвертер і
witnesses surface ↔ SID. Масово переписувати `.lisp`-файли до цього не можна.

## English summary

This is a proposal, not a language-contract change. It recommends `=SEQ`,
where `SEQ` is exactly eight binary digits, as a SID reader-token candidate.
The token must be typeable on Ukrainian keyboard layout, lexically unambiguous,
and consistent with the existing punctuation conventions. The owner chooses the
final token before any reader, evaluator, or source-conversion implementation.
