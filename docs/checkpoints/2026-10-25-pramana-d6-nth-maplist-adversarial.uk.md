# Pramāṇa (प्रमाण) · D6 NTH/MAPLIST · 25.10.2026

## Передача від Kārya
Дякуємо Kārya за реальні мовні SENS-визначення D6:000100
`елемент-списку-за-індексом` і D6:000101 `відобразити-залишки`
(коміт `68de0a00f5b9`). Ці вже наявні DEFINE не переписувалися.
Ратифіковані доменні координати залишилися незмінними.

## Шість нових SENS-свідків
1. NTH неправильний вибір на D24+ індексі один: очікуваний D1:ні.
2. NTH від'ємний D24+ індекс: нормативна D3 CAR Type відмова.
3. NTH атомний D1:ні корінь: відмова до повернення елемента.
4. MAPLIST тотожний callback: усі три суфікси збережені по черзі.
5. MAPLIST мутант зі зворотним порядком: очікуваний D1:ні.
6. MAPLIST атомний D1:ні корінь з отруйним CDR callback:
   структурна D3 CAR Type має пріоритет.

Файли `tests/semantic/d6-nth-*.lisp` і
`tests/semantic/d6-maplist-*.lisp` підключено в чинний
`scripts/prove-lisp-semantic-t5m.sh` з профілем `core4`.
SHA256 квитанцію входів розширено. Shell виконує лише механізм тесту,
фізичні байти кодує Zig/T5M, D1/D3/D5/D12+ семантику виконує SENS.

## Доказова межа
Виконання CI на commit SHA має самостійно показати:
direct → Zig/T5M mint/open/verify → paired → standalone.
У цьому ході нативні SENS/Zig не запускалися; не називати створення
тесту підтвердженням закону. Core4 source/view/carrier parity ще
потребує канонічного remint. `l0.42.0` лишається NO-GO.

## Наступний агент
На точному SHA виконати всі шість нових законів і попередні чотири,
звірити D1 вердикти й точну D3 Type діагностику. Якщо будь-який
негатив відхиляється з іншої причини, визначити першопричину в
SENS, не пом'якшувати класифікацію без доказу. Далі звірити
D6:000110 MACROEXPAND-1, D6:000111 MACROEXPAND, D6:001000 LET,
D6:001001 LET* та D11/D12+ механізми з ратифікованими таблицями.

**Deutsch:** Sechs echte SENS-Zeugen für NTH/MAPLIST, native
Laufzeit- und Codec-Prüfung noch offen.
**English:** Six SENS witnesses for index bounds, root structure,
suffix order and callback priority; native verification pending.
