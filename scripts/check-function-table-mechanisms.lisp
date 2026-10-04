; #1046 — fail-closed validation for transitional mechanism metadata.
; #3022: #d0/#d1 below are explicit transitional legacy predicate scalars.\n; #b... is now the canonical BinaryNumber source path and must not be used as a tooling boolean.\n; Semantic identity authority is ONLY lib/surface/semantic-registry.lisp.
; This checker proves mechanism metadata cannot invent a function beside that table.
; #1332/#1403: empty-list-ground is not a function mechanism.

(00001001 registry
  (00000101 (01001011 (10100110 "lib/surface/semantic-registry.lisp"))))

(00001001 metadata
  (00000101 (01001011 (10100110 "lib/function-table-mechanisms.lisp"))))

(00001001 registry-rows registry)

(00001001 find-section
  (00001000 (name sections)
    (00000111
      ((00000010 sections) () (00000001 ()))
      ((00000010 sections) (#d0)
       (00000111
         ((00000011 (00000101 (00000101 sections)) name) (#d1)
          (00000101 sections))
         ((00000011 (00000101 (00000101 sections)) name) (#d0)
          (find-section name (00000110 sections))))))))

(00001001 metadata-rows
  (00000110 (find-section (00000001 rows) metadata)))

(00001001 profile-rows
  (00000110 (find-section (00000001 profile-routes) metadata)))

(00001001 registry-has-sid?
  (00001000 (sid rows)
    (00000111
      ((00000010 rows) () (00000001 no))
      ((00000010 rows) (#d0)
       (00000111
         ((00000011 sid (00000101 (00000101 rows))) (#d1) (00000001 yes))
         ((00000011 sid (00000101 (00000101 rows))) (#d0)
          (registry-has-sid? sid (00000110 rows))))))))

(00001001 metadata-has-route?
  (00001000 (sid executor rows)
    (00000111
      ((00000010 rows) () (00000001 no))
      ((00000010 rows) (#d0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00000011 sid (00000101 row)) (#d1)
            (00000111
              ((00000011 executor (00101111 row)) (#d1) (00000001 yes))
              ((00000011 executor (00101111 row)) (#d0)
               (metadata-has-route? sid executor (00000110 rows)))))
           ((00000011 sid (00000101 row)) (#d0)
            (metadata-has-route? sid executor (00000110 rows)))))))))

(00001001 admitted-executor?
  (00001000 (executor)
    (00000111
      ((00000011 executor (00000001 evaluator)) (#d1) (00000001 yes))
      ((00000011 executor (00000001 common-lisp)) (#d1) (00000001 yes))
      ((00000011 executor (00000001 prolog)) (#d1) (00000001 yes))
      ((00000011 executor (00000001 clips)) (#d1) (00000001 yes))
      ((00000011 executor (00000001 datalog)) (#d1) (00000001 yes))
      (t (00000001 no)))))

(00001001 admitted-mechanism?
  (00001000 (mechanism)
    (00000111
      ((00000011 mechanism (00000001 quote-form)) (#d1) (00000001 yes))
      ((00000011 mechanism (00000001 atom-primitive)) (#d1) (00000001 yes))
      ((00000011 mechanism (00000001 eq-primitive)) (#d1) (00000001 yes))
      ((00000011 mechanism (00000001 cons-primitive)) (#d1) (00000001 yes))
      ((00000011 mechanism (00000001 car-primitive)) (#d1) (00000001 yes))
      ((00000011 mechanism (00000001 cdr-primitive)) (#d1) (00000001 yes))
      ((00000011 mechanism (00000001 cond-form)) (#d1) (00000001 yes))
      ((00000011 mechanism (00000001 lambda-form)) (#d1) (00000001 yes))
      ((00000011 mechanism (00000001 define-form)) (#d1) (00000001 yes))
      ((00000011 mechanism (00000001 bounded-exact-add)) (#d1) (00000001 yes))
      (t (00000001 no)))))

(00001001 admitted-profile?
  (00001000 (profile)
    (00000111
      ((00000011 profile (00000001 core3)) (#d1) (00000001 yes))
      (t (00000001 no)))))

(00001001 admitted-profile-mechanism?
  (00001000 (mechanism)
    (00000111
      ((00000011 mechanism (00000001 registered-host-mechanism))
       (#d1)
       (00000001 yes))
      (t (00000001 no)))))

(00001001 profile-has-route?
  (00001000 (profile sid rows)
    (00000111
      ((00000010 rows) () (00000001 no))
      ((00000010 rows) (#d0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00000011 profile (00000101 row)) (#d1)
            (00000111
              ((00000011 sid (00101111 row)) (#d1) (00000001 yes))
              ((00000011 sid (00101111 row)) (#d0)
               (profile-has-route? profile sid (00000110 rows)))))
           ((00000011 profile (00000101 row)) (#d0)
            (profile-has-route? profile sid (00000110 rows)))))))))

(00001001 validate-profile-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (function-table-mechanisms-ok)))
      ((00000010 rows) (#d0)
       (10011101 ((row (00000101 rows))
              (profile (00000101 row))
              (sid (00101111 row))
              (mechanism (00110000 row)))
         (00000111
           ((00000011 (admitted-profile? profile) (00000001 no))
            (#d1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-profile) profile sid))
           ((00000011 (registry-has-sid? sid registry-rows) (00000001 no))
            (#d1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 profile-function-not-in-canon-function-table) profile sid))
           ((00000011 (profile-has-route? profile sid (00000110 rows)) (00000001 yes))
            (#d1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 duplicate-profile-route) profile sid))
           ((00000011 (admitted-profile-mechanism? mechanism) (00000001 no))
            (#d1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-profile-mechanism) profile sid mechanism))
           (t (validate-profile-rows (00000110 rows)))))))))

(00001001 validate-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (function-table-mechanisms-ok)))
      ((00000010 rows) (#d0)
       (10011101 ((row (00000101 rows))
              (sid (00000101 row))
              (executor (00101111 row))
              (mechanism (00110000 row)))
         (00000111
           ((00000011 (admitted-executor? executor) (00000001 no))
            (#d1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-executor) sid executor))
           ((00000011 (registry-has-sid? sid registry-rows) (00000001 no))
            (#d1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 sid-not-in-canon-function-table) sid))
           ((00000011 (metadata-has-route? sid executor (00000110 rows)) (00000001 yes))
            (#d1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 duplicate-executor-route) sid executor))
           ((00000011 (admitted-mechanism? mechanism) (00000001 no))
            (#d1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-mechanism) sid mechanism))
           (t (validate-rows (00000110 rows)))))))))

(00001001 legacy-verdict (validate-rows metadata-rows))
(00001001 profile-verdict (validate-profile-rows profile-rows))

(00001001 verdict
  (00000111
    ((00100010 legacy-verdict (00000001 (function-table-mechanisms-ok)))
     (#d1)
     profile-verdict)
    (t legacy-verdict)))

(01001000 verdict)
