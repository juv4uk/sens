; Інвентар ролей предикатів і записів Core4 — #1259, контракт 9.
;
; Поле укр-проєкція містить повне поточне написання з колонки «укр»
; ратифікованої драбини доменів для однозначно зіставленого наступника.
; Це лише видима проєкція: вона не доводить тотожність старого запису,
; не надає права виклику та не змінює законів мови.
;
; Інвентар класифікує історичні ролі результатів, а не виконує функції.
; Ролі чинного формату:
;   predicate-question — запит із однобітною відповіддю;
;   classifier-observer — розширене описове спостереження;
;   control-consumer — споживач точного результату іншої операції.
;
; Ядра Core1–Core3 не входять до меж цієї інвентаризації.
; Історичні восьмибітні адреси не дублюються в активному Lisp-файлі.

(core4-predicate-record-inventory-3

  ((profile . core4)
   (status . inventory-only)
   (function-field . ukr-projection-only)
   (legacy-addresses . omitted)
   (named-function-ontology . forbidden)
   (callability . not-asserted)
   (semantic-change . forbidden)
   (mass-rewrite . forbidden)
   (performance-wrapper-audit . separate-axis-1277-1278)
   (host-capability-dispatch-gap . separate-axis-1276)
   (function-width-fpga-economics . separate-axis-1279-1280)
   (table-first-bootstrap-vision . out-of-scope-1281)
   (core1-core2-core3 . out-of-scope))

  ((укр-проєкція . атом?)
   (authority . tests/fixtures/semantic/atom-1bit-v1.lisp)
   (current-role . predicate-question)
   (current-result . exact-predicate-bit)
   (target-role . predicate-question)
   (migration . current-shared-foundation))

  ((укр-проєкція . тотожне?)
   (authority . tests/fixtures/semantic/eq-1bit-v1.lisp)
   (current-role . predicate-question)
   (current-result . exact-predicate-bit)
   (target-role . predicate-question)
   (migration . current-shared-foundation))

  ((укр-проєкція . однакові?)
   (authority . tests/fixtures/semantic/predicate-1bit-v1.lisp)
   (current-role . predicate-question)
   (current-result . exact-predicate-bit)
   (target-role . predicate-question)
   (migration . current-shared-foundation))

  ((укр-проєкція . символ?)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . bounded-later))

  ((укр-проєкція . рядок?)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . bounded-later))

  ((укр-проєкція . числовий-буфер?)
   (authority . contracts/structural-observation-contract.lisp)
   (current-role . predicate-question)
   (current-result . class-membership)
   (target-role . predicate-question)
   (migration . bounded-later))

  ((укр-проєкція . за-умовою)
   (authority . contracts/control-dispatch-contract.lisp)
   (current-role . control-consumer)
   (current-result . explicit-result-equality)
   (target-role . control-consumer)
   (migration . producer-laws-first)
   (compatibility-result . historical-truthiness)
   (compatibility-role . compatibility-only)))
