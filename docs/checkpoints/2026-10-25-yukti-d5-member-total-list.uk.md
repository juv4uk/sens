# Yukti (युक्ति) — D5:11101 MEMBER / sambaddha — 2026-10-25

## Першопричина
Попередній SENS MEMBER у `lib/core4-parts/core4-d6.lisp` та `lib/core4.lisp` повертав D1:так одразу після першого збігу й не помічав пошкодженого подальшого D3-хвоста. Порушення Contract 12.0: доказ існування збігу не може підмінити передумову правильного списку.

## Виконана зміна
Обидва вихідні SENS-файли синхронізовано: `значення-у-списку?-ядро` продовжує один хвостовий обхід після збігу, зберігаючи D1 прапорець. `значення-у-списку?` є чинною публічною Д5:11101; санскритська поверхня `sambaddha`. D3:() є кінцем, інший атомний хвіст спричиняє D3 ПЕРШЕ Type; D1:ні не є D3:(). Жодних нових кодів, жодної семантики в Rust. Складність за кількістю вузлів O(n), runtime stack ще не виміряний.

Чотири прямі нативні SENS→Zig/T5M→paired→standalone Core4 свідки: `d5-member-total-list-positive`, `d5-member-total-list-mutant`, `d5-member-hidden-tail`, `d5-member-nonlist-root`. Двійковий виклик Д5:11101 перевіряється поряд з українським. Ізольований D6 UNION proof bundle тепер витягає спочатку MEMBER-ядро, потім MEMBER. Негативи повинні дати `car expects a non-empty list`.

## Підтверджене раніше, не для цього SHA
CI #40170843658, SHA `d19a193bbeacf231ec58ec0e55c39ac8bf5d2d0a`, підтвердив чотири D11 two-witness свідки у прямому, парному й автономному виконанні. Загальний CI залишався RED через F6 producer→consumer і проблеми фізичних пар. Жоден раніше успішний тест не підтверджує нове D5-визначення.

## Чекпоінт наступному агенту
1. Для точного нового SHA: чотири D5-свідки, регресійні D6 UNION, D5 проєкції. Записати source/physical/view SHA та expected/actual.
2. Перевипустити канонічний фізичний Core4 через SENS/Zig T5M, не вручну. Текстові `.lisp` ще не є runtime доказом.
3. Д5:11100 ASSOC `знайти-за-ключем` перевірити на ранній збіг і пізній неправильний хвіст, не маскувати Type.
4. F6 producer→consumer: незалежно remint `lib/lisp-fs.sens` та `tests/fixtures/wsm-fs-record-producer.sens`; відрізнити `invalid-format` від відсутніх, дубльованих полів.
5. D1–D11 резиденти та точна числова драбина D12→D24→D48 залишаються атестаційно неповними. Відсутній дозвіл власника на реліз GO. Додаткові субагенти в цьому ході не запускалися.

`D5_MEMBER=SOURCE_COMPLETE_NATIVE_PENDING`
`RELEASE=NO-GO`
**Deutsch:** D5 MEMBER überprüft den vollständigen D3-Listenrest.
**English:** D5 MEMBER checks the entire proper-list spine.
