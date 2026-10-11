# Історичний Lisp → українська поверхня + точні двійкові слова

Сім джерел міграції (усі оригінали незмінні):

- `historic-atom` ← `tests/fixtures/migration-atom-cohort/atom-empty.lisp`
- `historic-eq-legacy` ← `tests/fixtures/migration-eq-cohort/eq-legacy-sid.lisp`
- `historic-eq-lisp15` ← `tests/fixtures/migration-eq-cohort/eq-lisp15.lisp`
- `historic-cons-legacy` ← `tests/fixtures/migration-pair-cohort/pair-cons.lisp`
- `historic-quote-legacy` ← `tests/fixtures/migration-quote-cohort/quote-legacy.lisp`
- `historic-quote-lisp15` ← `tests/fixtures/migration-quote-cohort/quote-lisp15.lisp`
- `historic-quote-mylisp` ← `tests/fixtures/migration-quote-cohort/quote-mylisp.lisp`

Для кожного stem є лише два **нові** файли: `name.lisp` (чинна українська `ук` поверхня) і `name` (точні бінарні слова D1–D3). Нових `.sens` немає. Старі T5-артефакти в каталогах provenance не змінювалися.

Незалежна від фізичного кодека перевірка (вихідне джерело → історичний трипрохідний переклад слів → `ук` → ті самі слова): `python3 -m unittest discover -s tests -p 'test_migrated_historical_two_projections.py' -v`.

Це механічна логічна міграція джерел з фіксованого корпусу, а не сертифікат виконання, не сім різних семантичних операцій і не релізне допущення. Кодування `name.sens` збережено для наступного етапу Frame3.
