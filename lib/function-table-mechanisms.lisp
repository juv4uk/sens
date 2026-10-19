; #1046 — transitional executor metadata subordinate to Canon()/function table.
;
; Історичні SID8-біти є свідченням міграції, не чинним доменом D8.
; Історичний SID8:00001100 (PLUS) точно відповідає D5:01010, укр додати.
; Не переносити за рівністю байта: D8:00001100 означає зменшити-на-1.
; Цей файл описує механізми, а не ратифікує семантику чи виконуваність.
;
; Identity authority: lib/surface/semantic-registry.lisp
; Every exact function below must already exist in the canonical function table.
; Retirement: fold these mechanism descriptors into the unified function-table
; row model once #1046 completes.
;
; Reuses (2000+ surface):
;   semantic-registry authority, mechanism-selector consumers,
;   island-math-evidence / island-lowering for SID 00001100 routes.
;
; #1332/#1403: () is a structural value outside the 256-function space.
; Function 00000000 therefore has no empty-list-ground route here.
;
; Викличні голови нижче — чинні ратифіковані D3/D4/D5 поверхні `укр`.

(
  (schema function-table-mechanisms/1)
  (authority "lib/surface/semantic-registry.lisp")
  (lifecycle transitional)
  (retirement-issue 1046)
  (rows
    ; Форми evaluator: точні ратифіковані D3/D4 координати
    (як-є evaluator quote-form)
    (атом? evaluator atom-primitive)
    (тотожне? evaluator eq-primitive)
    (сполучити evaluator cons-primitive)
    (перше evaluator car-primitive)
    (решта evaluator cdr-primitive)
    (за-умовою evaluator cond-form)
    (функція evaluator lambda-form)
    (визначити evaluator define-form)
    ; SID8:00001001 і SID8:00001011 мали історичну позначку define-form.
    ; У сучасній D4:0011 — один закон і один маршрут визначити.
    ; Existing function + only. These rows admit executors; they do not define +.
    ; Evidence donors: #988/#1042; Datalog execution replay: #1052.
    ; Чотири острови виконують додавання (SID8:00001100 → D5:01010).
    (додати common-lisp bounded-exact-add)
    (додати prolog bounded-exact-add)
    (додати clips bounded-exact-add)
    (додати datalog bounded-exact-add))
  ; #1422 — profile selection precedes host mechanism lookup.
  ; Mechanical registered-host route for existing SENS function 10101000 under Core3.
  ; Defines no kernel syntax, surface spelling, result law, or host availability.
  (profile-routes))
