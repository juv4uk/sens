# Nyāya (न्याय) · D6 REDUCE · пріоритет D3 над користувацьким callback

Дата: 25.10.2026. Джерела: `juv4uk/sens`, чинна гілка `main`.

## Першопричина

Ратифікована D6:101110 `згорнути` (санскритська поверхня береться тільки з `lib/domains/d6.lisp`) у колишній реалізації обробляла поточну пару й викликала `операція` до виявлення неправильного *пізнішого* хвоста. Вхід `(сполучити так ні)` із callback `(функція (стан елемент) (решта (як-є ())))` міг породити `CDR Type` раніше, ніж структура повідомить нормативний `CAR Type`. Це не помилка D1:ні та не дозвіл трактувати його як D3:().

## Зміни, реально записані в GitHub

1. `6cc42f3412942f2b7b28f162a15e7cd4629b3b7f` — `lib/core4.lisp`. Існуючий `підтвердити-д6-список` перенесено перед D6 REDUCE та використано як єдиний спільний валідатор REDUCE і D6 NTH. Новий `згорнути-ядро` зберігає ліве згортання, публічний `згорнути` передає в нього тільки повністю перевірений D3-список.
2. `636bd846925b1a10e38cf13c4546b37dc9cf32de` — тотожне SENS-визначення в `lib/core4-parts/core4-language.lisp`. Старого другого визначення `підтвердити-д6-список` немає.
3. `548919a337072daec087de5143f4646ed6f14552` — `tests/semantic/d6-reduce-improper-tail-negative.lisp`. Тепер callback навмисно викликає `решта` від `()`: правильна відмова має бути `car expects a non-empty list`, а не `cdr expects a non-empty list`.

Окремого нового D6/D11 коду не введено. Rust/Zig семантику не змінювали; D1 `ні` не ототожнювали з D3 `()`.

## Перевірки й чесний статус

- `STATIC_SENS_PARENS=PASS`: у двох змінених SENS-джерелах і негативному свідку баланс дужок залишився нульовим.
- `SENS_SOURCE_RECHECK=PASS`: після комітів GitHub повернув рівно по одному визначенню `підтвердити-д6-список` і `згорнути-ядро` в обох файлах. Тіло ядра в обох джерелах збігається.
- `NATIVE_SENS_POSITIVE=NOT_VERIFIED`; `NATIVE_SENS_NEGATIVE=NOT_VERIFIED`; `ZIG_T5M=NOT_VERIFIED`. Підключений Desktop Commander комп'ютер був offline; нативного SENS цього ходу не запускали. Статичний PASS не є семантичним PASS.
- `CORE4_SPLIT_EXACT=FAIL`: після змін реконструкція з усіх п'яти `lib/core4-parts/*.lisp` і `lib/core4.lisp` не тотожні (315071 проти 317399 символів у перевіреному знімку; перша відмінність на символьному індексі 48883). Конкретно `core4` вже використовує `частка-через-подвоєння` у T5M3, тоді як застаріла частина кодека ще містить `частка`. Не приписувати цю незалежну розбіжність REDUCE; не робити сліпий `--build`.
- `lib/core4.sens` та бітове подання потрібно перемінтити нативним SENS/Zig/T5M. Не створювати байти вручну.
- `RELEASE=NO-GO`. Немає підтвердженого кандидатного SHA з повним виконанням.

## Черга наступному Swarm-агенту

1. Прочитати актуальний `main` і переконатися, що трійка комітів лишилася його предком; не перезаписувати новіші зміни інших агентів.
2. Перевірити SENS `згорнути` на позитивних законах (`tests/semantic/d6-reduce-left-law.lisp`), мутанті (`d6-reduce-left-mutant.lisp`) та отруйному негативі `d6-reduce-improper-tail-negative.lisp`. Чинний маршрут — `scripts/prove-lisp-semantic-t5m.sh`, профіль `core4`. Очікування: D1:так / D1:ні / D3 CAR Type. Записати прямий, paired і standalone результати з SHA та stderr. Не використовувати Python як SENS-оракул.
3. Обережно відновити проєкції `core4-parts` з авторитетного `core4.lisp`, з'ясувавши всі інші розбіжності та фіксовані межі у `scripts/split-core4.py`; довести `--check` на тому самому SHA. НЕ робити `--build` зі старих частин.
4. Нативно перемінтити `lib/core4.sens` і бітовий view; перевірити source → exact-domain → T5M → decoded identity → SENS execution. Окремо повернутися до D6:000000/000001 LENGTH/LENGTH-ONTO (раніше CAR/CDR і resident admission), D6:000010/000011 MIN/MAX, D8 права згортка, D10 механізми та D12+ точні математичні величини.
5. Залишити один автоматичний workflow на commit, не запускати дорогий ручний `runtime-shards` без рішення власника. Червоні результати маркувати точним шаром і SHA; не перевизначати ратифіковану семантику заради зеленого CI.

## Deutsch

D6 REDUCE validiert jetzt die vollständige D3-Listenstruktur vor dem ersten Benutzer-Callback. Native SENS- und T5M-Nachweise fehlen. Die bereits vorhandene Drift zwischen Core4 und den geteilten Codec-Dateien bleibt offen.

## English

D6 REDUCE now validates the full D3 list spine before invoking user callbacks. Native SENS/T5M proofs are pending. The pre-existing Core4 split/codec drift remains unresolved.
