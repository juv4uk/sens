# D10 crossrepo Panini v1

**Статус:** research / unratified  
**Central sweep:** #4182  
**Donor task:** juv4uk/my-lisp-panini#52  
**Single-stream authority:** #4162

Перший executable Panini tranche бере лише загальні мовні операції з `my-lisp-panini`. Сутри, dhatu-ідентифікатори, таблиці звуків, hardcoded приклади та старі координати не стають residents.

## Результат

```text
new meanings          23
D10 selected         527/1024
law-forced placed    256
unplaced selected    271
remaining            497
ratified D10           0
```

## Сім'ї

```text
pratyahara           2
phonology/sandhi    10
verb derivation      4
paradigm             3
rule/scope checks    4
```

Pratyahara:
`RESOLVE-PRATYAHARA`, `PRATYAHARA-MEMBER?`.

Sandhi/phonology:
`APPLY-GUNA`, `APPLY-ECO-SANDHI`, four named sandhi rules, stop voice/devoice transforms, `APPLY-SANDHI`, `JOIN-WORDS-SANDHI`.

Derivation:
`DERIVE-VERB-LAKARA`, `DERIVE-VERB-OPTATIVE`, `DERIVE-VERB-ATMANEPADA`, `DERIVE-VERB-FUTURE`.

Paradigm:
`PARADIGM-PARASMAIPADA`, `PARADIGM-ATMANEPADA`, `PARADIGM-FULL`.

Rule/scope:
`ANUVRTTI-GRAPH-VALID?`, `IT-DELETABLE?`, `SAP-ELIGIBLE?`, `AMBIGUOUS-APAVADA?`.

## Що навмисно не вибрано

- D7 sound identities і готові pratyahara data;
- sutra/dhatu IDs;
- `in-AC?` / `in-HAL?` тощо як окремі slots, бо вони параметризуються pratyahara membership;
- hardcoded `derive-bhavati` / `derive-pacati` приклади;
- trace accessors: вони потребують окремої duplicate-перевірки проти чинних D10 witness/provenance/proof meanings;
- print helpers та внутрішні list helpers.

## Координатна межа

Усі 23 нові meanings:

```text
coordinate = null
coordinate_basis = UNPLACED
```

Жодна Paninian/UPC/старорепозиторна координата не переноситься в D10.

**Domain specificity дозволена; окремий Sanskrit10 namespace — ні.**
