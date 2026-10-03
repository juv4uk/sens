# #2527 — D6 non-prefix/product/quotient falsifier

Статус: лише research.  
Фаза: **STRUCTURAL-DISCOVERY**.

## Binary-domain record

```text
DOMAIN        Core D6
BINARY OBJECT чотиристановий binding-policy product; resident не admitted
LAW           дві незалежні комутативні refinement-осі утворюють semantic product
WITNESS       #2511 product square + #2523 local-width lower bound
FALSIFIER     non-prefix / factor / quotient / explicit-residue models
STATUS        theorem-scope attack
RELATION      Core-only
```

## Питання

Локальна теорема каже: за законом D4-parent + незалежні спостережувані
binary-refinements shared-location policy потребує двох локальних відмінностей.
Чи може інше канонічне представлення зберегти ту саму семантику з меншою
кількістю семантичної структури?

Перевіряються:

1. ordered local path;
2. direct two-factor coordinate;
3. quotient двох комутативних derivation paths;
4. explicit residue/root;
5. arbitrary non-prefix D6 numbering;
6. навмисно оманливий 2-bit external table index.

## Результат

Жодна перевірена модель не зменшує число семантичних відмінностей нижче двох
доведених осей, якщо треба зберегти повну чотиристанову алгебру без прихованої
табличної authority.

```text
4 observable states
=> 2 independent semantic axes
=> minimum 2 local binary distinctions without external table/context
```

Direct factor coordinate може друкувати лише два локальні factor bits, але не
прибирає жодного factor. Це компактна coordinate-проекція того самого product.

Quotient прибирає дубльовані **proof paths**:

```text
scope ; miss
miss  ; scope
```

використовуючи вже доведений закон комутації. Жодна observable axis при цьому
не зникає.

Explicit residue може довільним токеном назвати лише фінальний endpoint, але
тоді вже не представляє весь чотиристановий product, який є предметом теореми.

Arbitrary non-prefix table може закодувати всі чотири стани, але існує 24
однаково допустимі перестановки. Отже інтерпретація живе в table authority, а
не у виведеному coordinate law.

## Semantic / coordinate / accidental classification

Свідомо повторюємо дисципліну #2494:

```text
two-axis product structure                    semantic-law
parent-prefix + two factor bits               coordinate-law
which semantic axis is printed as 01 vs 10    coordinate-law
arbitrary non-prefix enumeration              accidental-representation
short external table index                    accidental-representation
```

Семантичний інваріант — endpoint, де застосовані обидві refinement-осі. При
перестановці осей два проміжні corners міняються місцями, а both-axes endpoint
лишається тим самим. Це не робить конкретну фізичну polarity bit семантичним
законом.

## Постійний guard #2508

Однакові raw bits можуть існувати в іншому домені. Q-group-factor `11` не є
binding-policy `11`. Executable witness відхиляє cross-domain application
навіть при однаковому raw bit string.

Тому:

> semantic law identity never follows from the bit transform alone.

## Не-висновки

Цей witness **не**:

- ратифікує `001111`;
- не додає `001100/01/10/11` у D6 map;
- не вибирає axis polarity;
- не закриває historical ingest;
- не імпортує Core-Math authority у Core.

Консервативна D6 map залишається під authority #2422.

## Phase-report line

```text
semantic product law = preserved
coordinate orientation = non-unique under axis swap
non-prefix/table encodings = representation alternatives, not semantic lower-bound falsifiers
```
