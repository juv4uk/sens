# D8 v2 — перший щільний semantic inventory 256/256

**Статус:** research / candidate. **D8 ще не ратифікований.**

Цей inventory продовжує реальний метод D3→D6: спочатку вибираємо повний набір meanings, потім розв'язуємо геометрію.

## Склад 256

```text
64  selector-law
12  recovery
11  reopened prior work
15  structural/product
154 historical donor
---------------------
256 meanings
```

Це не sparse primitive core. Derived/generated residents дозволені так само, як у D4–D6.

## Що збережено обов'язково

- усі 64 selector candidates;
- усі 12 current recovery candidates;
- усі 11 rows, які раніше були помилково демотовані через derivability;
- усі 15 novel semantics із попередніх product/geometric D8 досліджень;
- 154 найсильніші historical donor meanings;
- усі 34 meanings, що не ввійшли в першу 256-ку, збережені в overflow ledger.

## Overflow ≠ видалення

`knowledge/d8-v2-overflow-ledger.json` містить 34 кандидати.

Вони не falsified і не стерті. Це лише перший компактний cut.

Основні причини holdout:

```text
lower-domain collision review
host/resource/tooling boundary
compiler/surface/meta facility
machine/carrier-specific operation
late specialized capability
```

Наприклад `APPLY`, `COMPOSE`, `REDUCE` поки не оголошені автоматично точними duplicate: вони винесені в collision review до окремої semantic перевірки.

## Важливі колізії назв

`OPEN` / `CLOSE` у D2 — структурні дужки, а historical D8 donor `OPEN` / `CLOSE` — stream operations. Однакове ім'я не означає однакову семантику.

`MAP` historical donor лишився в inventory, бо donor-опис охоплює mapping over up to several sequences; current D6 `MAP` треба порівнювати семантично, а не лише по назві.

## Координати

На цьому етапі final D8 coordinates **не призначаються**.

- selector law coordinates збережені як сильне structural evidence;
- product/fixed/gauge coordinates збережені як research evidence;
- recovery sequential coordinates збережені лише як provenance;
- historical #2934 coordinates мають статус `DONOR-COORDINATE-NONAUTHORITATIVE`.

Наступний етап — геометрія: law-forced placement → local family structure → explicit gauge → deterministic representative → owner ratification.

## Головний закон

```text
спочатку 256 meanings
потім 256 coordinates
```

Це той самий порядок, який стабілізував D5 і D6.
