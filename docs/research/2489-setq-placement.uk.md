# #2489 — розміщення SETQ-core

Статус: лише дослідження.

## Що вже доведено

Попередні історичні й семантичні задачі вже ізолювали нову спостережувану здатність:

~~~text
оновити найближчий уже існуючий shared binding/location
~~~

Тут перевіряється лише одне: чи є ця здатність чесною однобітною дитиною якогось D4-батька.

## Найсильніший кандидат — DEFINE

D4 DEFINE має політику:

~~~text
scope = поточний frame
miss  = створити binding
~~~

SETQ-core:

~~~text
scope = найближчий існуючий binding
miss  = помилка
~~~

Коли X уже є в поточному frame, обидві операції оновлюють ту саму location. Тому DEFINE — справжній семантичний кандидат на батька, а не просто схожа назва.

## Фальсифікатор двох осей

Модель виконує весь квадрат:

~~~text
                 create          fail
current          DEFINE          current-fail
nearest          nearest-create  SETQ-core
~~~

Перша незалежна вісь — scope пошуку.

Для X у зовнішньому frame:

~~~text
current-create -> створює/shadow inner X; зовнішній observer бачить OLD
nearest-create -> оновлює outer X; observer бачить NEW
~~~

Друга незалежна вісь — поведінка при відсутньому імені.

Коли X немає ніде:

~~~text
current-create -> створює inner X
current-fail   -> явна помилка
~~~

Усі чотири кути мають різні спостережувані сигнатури.

Отже:

~~~text
DEFINE -> SETQ-core
змінює:
  1. search scope
  2. missing-name policy
~~~

За законом #2236 один додатковий біт має нести одну незалежну delta-вісь. Тому прямий D5-нащадок DEFINE не проходить:

~~~text
00110 / 00111 = вільні фізично
але не зароблені цією семантичною лінією
~~~

Поточний результат:

~~~text
DEFINE-parent = NEEDS-WIDER-WIDTH
~~~

Це не призначає D6-код. Для більшої ширини треба окремо довести порядок і генератор двох осей.

## Контрбатьки

LOOKUP уже має nearest-existing/fail resolution, але є операцією читання, тоді як SETQ-core — state transition shared location. Спільного resolution-law недостатньо для same-base-operation.

BIND будує нову/batch структуру середовища й не оновлює одну вже існуючу shared location.

## Принцип

**Вільного слова недостатньо. Якщо DEFINE і SETQ відрізняються на двох незалежних осях binding-policy, один suffix-біт не повинен приховувати обидві.**
