# D10: власні резиденти D9 не повинні потрапляти до D10 вдруге

Перевірено за чинним `knowledge/d1-d9-foundation.json` та `knowledge/d10-v1-semantic-inventory.json` (зріз selected=625, D10 ratified=0). Джерела Git blob: `lib/persistent-vector.lisp@80d071b3...` і `lib/unify.lisp@8dad35ae...`.

- `VEC-EMPTY`, `VEC-COUNT`, `VEC-NTH`, `VEC-CONJ`, `VEC->LIST`, `VEC-FROM-LIST` — уже D9. Для `VECTOR-NTH?` відмінність `()` проти `(())` має залишитися тестом D9, не ще одним D10 словом.
- `UNIFY` — уже D9 і викликає `unify-var`, який виконує occurs-check. Отже `UNIFY-TERMS-WITH-OCCURS-CHECK` — HOLD-D9-EQUIVALENCE, а не автоматично новий resident.
- Дійсно нові кандидати на окремий огляд: `APPLICABLE-METHODS`, `STANDARD-METHOD-COMBINATION`, `FIND-RESTART` із уже злитого research dossier #4800. Поки без координат, ратифікації й без дозволу на `.sens` execution. `CALL-NEXT-METHOD`, `SIGNAL-CONDITION`, `INVOKE-RESTART` залишаються HOLD-D2-CONTROL.
- Не плутати композитні операції й AVL-ротації із новою мовною семантикою. Цей пакет НЕ дописує канонічний інвентар D10 та не зменшує «399 remaining».

Перевірка на повному SENS checkout: `python3 scripts/check_d10_d9_donor_dedup.py --root .`; вона звіряє Git blob SHA та source line, D9 exact coordinate і не допускає фальшивої D10 ратифікації.

Для координації: [#4013](https://github.com/juv4uk/sens/issues/4013), [#4463](https://github.com/juv4uk/sens/issues/4463), [#4182](https://github.com/juv4uk/sens/issues/4182).
