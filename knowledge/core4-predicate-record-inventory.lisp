; Інвентар ролей предикатів і записів Core4 — #1259, контракт 9.
;
; Історичні точні восьмибітні значення в цьому інвентарі є
; даними відповідного знімка, а не дозволом викликати їх через
; нинішню доменну драбину. Назви людських проєкцій не визначають
; тотожності функцій.
;
; Інвентар лише класифікує ролі результатів: він не змінює
; виконання й не встановлює семантику предикатів.
; Ролі чинного формату:
;   predicate-question — запит із однобітною відповіддю;
;   classifier-observer — розширене описове спостереження;
;   control-consumer — споживач точного результату іншої операції.
;
; Ядра Core1–Core3 не входять до меж цієї інвентаризації.
; Протокольні ключі та бітові рядки збережено буквально.
;
(core4-predicate-record-inventory/2

  ((profile . core4)
   (status . inventory-only)
   (function-identity . exact-8-bits-only)
   (named-function-ontology . forbidden)
   (semantic-change . forbidden)
   (mass-rewrite . forbidden)
   (performance-wrapper-audit . separate-axis-1277-1278)
   (host-capability-dispatch-gap . separate-axis-1276)
   (function-width-fpga-economics . separate-axis-1279-1280)
   (table-first-bootstrap-vision . out-of-scope-1281)
   (core1-core2-core3 . out-of-scope))

  ((function . 00000010)
   (authority . tests/fixtures/semantic/atom-1bit-v1.lisp)
   (current-role . predicate-question)
   (current-result . exact-predicate-bit)
   (target-role . predicate-question)
   (migration . current-shared-foundation))

  ((function . 00000011)
   (authority . tests/fixtures/semantic/eq-1bit-v1.lisp)
   (current-role . predicate-question)
   (current-result . exact-predicate-bit)
   (target-role . predicate-question)
   (migration . current-shared-foundation))

  ((function . 00100010)
   (authority . tests/fixtures/semantic/predicate-1bit-v1.lisp)
   (current-role . predicate-question)
   (current-result . exact-predicate-bit)
   (target-role . predicate-question)
   (migration . current-shared-foundation))

  ((function . 00100011)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . bounded-later))

  ((function . 00100100)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . bounded-later))

  ((function . 00100110)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . bounded-later))

  ((function . 00000111)
   (authority . contracts/control-dispatch-contract.lisp)
   (current-role . control-consumer)
   (current-result . explicit-result-equality)
   (target-role . control-consumer)
   (migration . producer-laws-first)
   (compatibility-result . historical-truthiness)
   (compatibility-role . compatibility-only)))
