; #1046 — fail-closed validation for transitional mechanism metadata.
; #3022: #d0/#d1 below are explicit transitional legacy predicate scalars.\n; #b... is now the canonical BinaryNumber source path and must not be used as a tooling boolean.\n; Semantic identity authority is ONLY lib/surface/semantic-registry.lisp.
; This checker proves mechanism metadata cannot invent a function beside that table.
; #1332/#1403: empty-list-ground is not a function mechanism.

(визначити registry
  (перше (читати-всі (читати-файл "lib/surface/semantic-registry.lisp"))))

(визначити metadata
  (перше (читати-всі (читати-файл "lib/function-table-mechanisms.lisp"))))

(визначити registry-rows registry)

(визначити find-section
  (функція (name sections)
    (за-умовою
      ((атом? sections) () (як-є ()))
      ((атом? sections) (#d0)
       (за-умовою
         ((тотожне? (перше (перше sections)) name) (#d1)
          (перше sections))
         ((тотожне? (перше (перше sections)) name) (#d0)
          (find-section name (решта sections))))))))

(визначити metadata-rows
  (решта (find-section (як-є rows) metadata)))

(визначити profile-rows
  (решта (find-section (як-є profile-routes) metadata)))

(визначити registry-has-sid?
  (функція (sid rows)
    (за-умовою
      ((атом? rows) () (як-є no))
      ((атом? rows) (#d0)
       (за-умовою
         ((тотожне? sid (перше (перше rows))) (#d1) (як-є yes))
         ((тотожне? sid (перше (перше rows))) (#d0)
          (registry-has-sid? sid (решта rows))))))))

(визначити metadata-has-route?
  (функція (sid executor rows)
    (за-умовою
      ((атом? rows) () (як-є no))
      ((атом? rows) (#d0)
       (нехай ((row (перше rows)))
         (за-умовою
           ((тотожне? sid (перше row)) (#d1)
            (за-умовою
              ((тотожне? executor (друге row)) (#d1) (як-є yes))
              ((тотожне? executor (друге row)) (#d0)
               (metadata-has-route? sid executor (решта rows)))))
           ((тотожне? sid (перше row)) (#d0)
            (metadata-has-route? sid executor (решта rows)))))))))

(визначити admitted-executor?
  (функція (executor)
    (за-умовою
      ((тотожне? executor (як-є evaluator)) (#d1) (як-є yes))
      ((тотожне? executor (як-є common-lisp)) (#d1) (як-є yes))
      ((тотожне? executor (як-є prolog)) (#d1) (як-є yes))
      ((тотожне? executor (як-є clips)) (#d1) (як-є yes))
      ((тотожне? executor (як-є datalog)) (#d1) (як-є yes))
      (t (як-є no)))))

(визначити admitted-mechanism?
  (функція (mechanism)
    (за-умовою
      ((тотожне? mechanism (як-є quote-form)) (#d1) (як-є yes))
      ((тотожне? mechanism (як-є atom-primitive)) (#d1) (як-є yes))
      ((тотожне? mechanism (як-є eq-primitive)) (#d1) (як-є yes))
      ((тотожне? mechanism (як-є cons-primitive)) (#d1) (як-є yes))
      ((тотожне? mechanism (як-є car-primitive)) (#d1) (як-є yes))
      ((тотожне? mechanism (як-є cdr-primitive)) (#d1) (як-є yes))
      ((тотожне? mechanism (як-є cond-form)) (#d1) (як-є yes))
      ((тотожне? mechanism (як-є lambda-form)) (#d1) (як-є yes))
      ((тотожне? mechanism (як-є define-form)) (#d1) (як-є yes))
      ((тотожне? mechanism (як-є bounded-exact-add)) (#d1) (як-є yes))
      (t (як-є no)))))

(визначити admitted-profile?
  (функція (profile)
    (за-умовою
      ((тотожне? profile (як-є core3)) (#d1) (як-є yes))
      (t (як-є no)))))

(визначити admitted-profile-mechanism?
  (функція (mechanism)
    (за-умовою
      ((тотожне? mechanism (як-є registered-host-mechanism))
       (#d1)
       (як-є yes))
      (t (як-є no)))))

(визначити profile-has-route?
  (функція (profile sid rows)
    (за-умовою
      ((атом? rows) () (як-є no))
      ((атом? rows) (#d0)
       (нехай ((row (перше rows)))
         (за-умовою
           ((тотожне? profile (перше row)) (#d1)
            (за-умовою
              ((тотожне? sid (друге row)) (#d1) (як-є yes))
              ((тотожне? sid (друге row)) (#d0)
               (profile-has-route? profile sid (решта rows)))))
           ((тотожне? profile (перше row)) (#d0)
            (profile-has-route? profile sid (решта rows)))))))))

(визначити validate-profile-rows
  (функція (rows)
    (за-умовою
      ((атом? rows) ()
       (як-є (function-table-mechanisms-ok)))
      ((атом? rows) (#d0)
       (нехай-послідовно ((row (перше rows))
              (profile (перше row))
              (sid (друге row))
              (mechanism (третє row)))
         (за-умовою
           ((тотожне? (admitted-profile? profile) (як-є no))
            (#d1)
            (список (як-є function-table-mechanisms-violation)
                  (як-є unsupported-profile) profile sid))
           ((тотожне? (registry-has-sid? sid registry-rows) (як-є no))
            (#d1)
            (список (як-є function-table-mechanisms-violation)
                  (як-є profile-function-not-in-canon-function-table) profile sid))
           ((тотожне? (profile-has-route? profile sid (решта rows)) (як-є yes))
            (#d1)
            (список (як-є function-table-mechanisms-violation)
                  (як-є duplicate-profile-route) profile sid))
           ((тотожне? (admitted-profile-mechanism? mechanism) (як-є no))
            (#d1)
            (список (як-є function-table-mechanisms-violation)
                  (як-є unsupported-profile-mechanism) profile sid mechanism))
           (t (validate-profile-rows (решта rows)))))))))

(визначити validate-rows
  (функція (rows)
    (за-умовою
      ((атом? rows) ()
       (як-є (function-table-mechanisms-ok)))
      ((атом? rows) (#d0)
       (нехай-послідовно ((row (перше rows))
              (sid (перше row))
              (executor (друге row))
              (mechanism (третє row)))
         (за-умовою
           ((тотожне? (admitted-executor? executor) (як-є no))
            (#d1)
            (список (як-є function-table-mechanisms-violation)
                  (як-є unsupported-executor) sid executor))
           ((тотожне? (registry-has-sid? sid registry-rows) (як-є no))
            (#d1)
            (список (як-є function-table-mechanisms-violation)
                  (як-є sid-not-in-canon-function-table) sid))
           ((тотожне? (metadata-has-route? sid executor (решта rows)) (як-є yes))
            (#d1)
            (список (як-є function-table-mechanisms-violation)
                  (як-є duplicate-executor-route) sid executor))
           ((тотожне? (admitted-mechanism? mechanism) (як-є no))
            (#d1)
            (список (як-є function-table-mechanisms-violation)
                  (як-є unsupported-mechanism) sid mechanism))
           (t (validate-rows (решта rows)))))))))

(визначити legacy-verdict (validate-rows metadata-rows))
(визначити profile-verdict (validate-profile-rows profile-rows))

(визначити verdict
  (за-умовою
    ((однакові? legacy-verdict (як-є (function-table-mechanisms-ok)))
     (#d1)
     profile-verdict)
    (t legacy-verdict)))

(друкувати verdict)
