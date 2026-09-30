# P1 — sens-wire як транспорт агентного контракту

**Issue:** #1845  
**Дані:** `report.md` цього ж каталогу (SHA `86e836be`, N=1000)  
**Не новий valgrind-прогін** — розклад уже зібраних колонок decode / execute / size.

## Payload-only (без старту процесу)

Harness уже віднімає `base`. На повідомлення в живій сесії:

| форма | size (B) | decode | execute | decode+execute |
|-------|---------:|-------:|--------:|---------------:|
| **sens-wire** | **34.3** | 12 036 | 43 812 | **55 848** |
| sens-fasl | 154.1 | 10 173 | 43 265 | 53 438 |
| py-json | 48.4 | 24 801 | 45 522 | 70 324 |
| py-src | 46.4 | 196 851 | 5 451 | 202 302 |
| py-marshal | 195.9 | 8 979 | 5 024 | 14 003 |

Висновок payload-only:
- **wire vs json:** менше байт (**×0.71**), дешевше decode (**×0.49**), трохи дешевше execute, разом **×0.79**.
- **wire vs fasl:** розмір **×0.22**, decode трохи дорожчий, execute майже той самий — fasl платить за header/hash/f64/u32, не за Function8.
- **wire vs marshal:** wire виграє розмір (**×0.18**), програє execute (~×8.7) — marshal = bytecode VM, не portable agent format.

## Wire vs JSON як *транспорт контракту*

Порівнюємо не «мови програмування», а **envelope для маленької програми**:

| критерій | sens-wire | py-json (AST) |
|----------|-----------|---------------|
| байт на повідомлення | **34** | 48 |
| decode I-refs | **12k** | 25k |
| execute I-refs | ~44k | ~46k |
| ідентичність функції | Function8 (1 byte) | текстовий op `"+"` у JSON |
| portability між runtime | wire/fasl SENS | залежить від Python AST-інтерпретатора |
| human-readable | ні (binary) | так |

Для agent bus, де важливі **розмір + дешевий decode + стабільна identity**, wire виграє JSON на виміряних числах.  
Для **максимального warm execute** у вже піднятому CPython — marshal сильніший; це інша ніша (і не portable).

## Absolute-binary гіпотеза (не доведена цим файлом)

Після Control2 + Function8 + Number + Text7 + Predicate1 (#1694):

- wire/fasl мають стати **канонічним повідомленням**, а не «ще одним codec поруч із JSON»;
- JSON/en/text — human/debug projection до lower;
- agent bus обмінюється бітами контракту, не рядками імен.

Цей звіт **не** стверджує, що absolute-binary вже завершено. Він фіксує: *навіть до повної онтології* поточний wire уже вимірювано вигідний як compact transport vs JSON.

## Що не робити

- Не писати «SENS швидший за Python» без cold / warm / size.
- Не ставити wire проти marshal як чесний portable agent format.
- Не міняти `lower.rs` / semantic contract заради чисел.

## Acceptance P1 (цей документ)

- [x] payload-only таблиця з існуючих колонок
- [x] wire vs JSON як transport (size + decode + execute)
- [x] absolute-binary гіпотеза сформульована окремо від виміру
