# Pramāṇa (प्रमाण) · 25.10.2026 · D11 доказ двома свідками

## Нормативний стан
Контракт SENS 12.0 зберігає D1:1/D1:0 як дві істини; D3:000 є лише структурною порожнечею. Коміт `8a529d2719ea1f069986614d60c1585d957f607d` додав до `lib/d11-query-unique.lisp` повні похідні SENS-функції `підстави-однозначного-пошуку-ядро` та `підстави-однозначного-пошуку`. Жодної нової координати D11 не ратифіковано.

Результати: `(немає)` для нуля, `(єдиний значення)` для одного, `(кілька перший другий)` для мінімум двох збігів. Два свідки — самі вхідні значення, включно з допустимими D3:() і D1:ні; на відміну від `()` вони не використовуються як маркер лічильника. Протокол пояснення викликається окремо; короткі наявні запити не змінено. Попередній повний D3-preflight — до першого callback; після другого збігу callback не викликається. Нескінченний/неперевірений зовнішній світ не охоплюється доказом відсутності у скінченному списку.

## Зміни й свідки
`tests/semantic/d11-query-two-witness-law.lisp`: пять SENS законів (два значення з ()/ні; один ні; нуль; порожній з отруєним callback; коротке замикання після другого). `tests/semantic/d11-query-two-witness-mutant.lisp`: дві появи != одна. `tests/fixtures/d11-query-two-witness-{improper,preflight}-negative.lisp`: два справжні D3 Type. У наявному `scripts/prove-lisp-semantic-t5m.sh` чотири окремі SENS → Zig/T5M → paired → standalone Core4 маршрути й SHA256. Це структурно перевірені джерела; **нового native PASS до CI конкретного коміту ще немає**.

## Фактичні попередні CI
GitHub Actions `40167865589` для SHA `06b762488cf50f9c5a6d075ed5a2fa4b9b4d6ccf`: 528/529 існуючих SENS законів PASS, RED D9 F6 `d9-f6-package-key-canonicalization-positive` з D1:0. У тій же роботі всі чотири `d11-query-status-*` і всі чотири `d11-unique-query-*` були PASS у direct/paired/standalone. Колеги відтоді окремо виправляли D9 F6 canonical keys. Той старий RED не слід перепризначати новому SHA. F6 producer→consumer досі потребує канонічного remint фізичних `.sens` носіїв, а не Rust-оракула.

## Наступний рій
1. Перевірити 4 нових `d11-query-two-witness-*` на exact SHA, підтвердити і 8 попередніх D11 свідків; кожен RED має source/physical SHA, expected/actual.
2. F6: тільки чинний SENS/Zig codec може перевипустити `lib/lisp-fs.sens` та `tests/fixtures/wsm-fs-record-producer.sens`; перевірити READ/WRITE, відмову дубльованих/відсутніх полів та producer→consumer. Не відновлювати SID8.
3. Після F6 адресно атестувати D5 MEMBER, D6 UNION, D7–D10 точні викличні тотожності, D11 непокриті функції та D12+ signed widening.
4. Окремі субагенти тут не запускалися; не вигадувати паралельне тестування. Release — NO-GO.

**Deutsch:** Zwei überprüfbare SENS-Zeugen nur bei erklärender Anfrage. Native Bestätigung steht aus.
**English:** Two actual SENS values witness ambiguity; native execution pending.
