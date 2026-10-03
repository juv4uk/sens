# #2628 — мінімізація кореня shared-location

Фаза: **SENS-DERIVATION**  
Фактор: `shared-location-update`  
Width: **UNKNOWN**  
Coordinate: **UNPLACED**

## Результат

```text
GLOBAL-D4-COMPILABLE = так
DERIVED-D4-LOCAL     = ні
ROOT-STATUS          = CARRIER-PREMISE
ROOT-PROMOTED        = ні
```

Це уточнює, а не скасовує старий результат #2442.

Explicit-state модель D4 представляє frames, location IDs та immutable store як
звичайні дані. Вона відтворює nearest-existing lookup, update, aliases,
shadowing і fail-on-miss.

Але observer у цій моделі має протокол:

```text
observer(store)
```

тоді як вихідне спостереження — уже створений:

```text
observer()
```

який після update з іншого scope бачить нове значення тієї самої shared
location.

Для immutable persistent data побудова `new_store` не може заднім числом
змінити store, замкнений у старому zero-argument closure. Старий observer
продовжує бачити OLD. NEW з'являється лише якщо:

1. явно передати новий store;
2. мутувати захоплену location/store;
3. читати неявний current/global store;
4. переписати або замінити observer.

Перший і четвертий варіанти — whole-program protocol rewrite. Другий і третій
вносять саме той ambient/shared-location carrier, який ми перевіряємо.

За законом derivation #2468 це не local D4 derivation. Але й update-алгоритм не
треба оголошувати новим root: коли carrier явний, усе обчислюється звичайними
D3/D4 перетвореннями даних.

Консервативна bounded-класифікація:

```text
CARRIER-PREMISE = ambient-current-store/shared-location
```

### Фальсифікатор

Context-preserving D1-D4 replacement, який не змінює старі zero-argument
observers/callers, але дає їм побачити NEW у nearest existing location без
ambient/mutable store-location channel, спростовує цей результат.

Жодного D5/D6 residency з цього не випливає.
