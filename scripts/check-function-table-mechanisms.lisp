; #1046 — fail-closed validation for transitional mechanism metadata.
; #3022: #d0/#d1 below are explicit transitional legacy predicate scalars.\n; #b... is now the canonical BinaryNumber source path and must not be used as a tooling boolean.\n; Semantic identity authority is ONLY lib/surface/semantic-registry.lisp.
; This checker proves mechanism metadata cannot invent a function beside that table.
; #1332/#1403: empty-list-ground is not a function mechanism.

(0011 registry
  (100 (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))

(0011 metadata
  (100 (110101001 (110110111 "lib/function-table-mechanisms.lisp"))))

(0011 registry-rows registry)

(0011 find-section
  (0010 (name sections)
    (110
      ((010 sections) () (001 ()))
      ((010 sections) (#d0)
       (110
         ((101 (100 (100 sections)) name) (#d1)
          (100 sections))
         ((101 (100 (100 sections)) name) (#d0)
          (find-section name (011 sections))))))))

(0011 metadata-rows
  (011 (find-section (001 rows) metadata)))

(0011 profile-rows
  (011 (find-section (001 profile-routes) metadata)))

(0011 registry-has-sid?
  (0010 (sid rows)
    (110
      ((010 rows) () (001 no))
      ((010 rows) (#d0)
       (110
         ((101 sid (100 (100 rows))) (#d1) (001 yes))
         ((101 sid (100 (100 rows))) (#d0)
          (registry-has-sid? sid (011 rows))))))))

(0011 metadata-has-route?
  (0010 (sid executor rows)
    (110
      ((010 rows) () (001 no))
      ((010 rows) (#d0)
       (001000 ((row (100 rows)))
         (110
           ((101 sid (100 row)) (#d1)
            (110
              ((101 executor (1001 row)) (#d1) (001 yes))
              ((101 executor (1001 row)) (#d0)
               (metadata-has-route? sid executor (011 rows)))))
           ((101 sid (100 row)) (#d0)
            (metadata-has-route? sid executor (011 rows)))))))))

(0011 admitted-executor?
  (0010 (executor)
    (110
      ((101 executor (001 evaluator)) (#d1) (001 yes))
      ((101 executor (001 common-lisp)) (#d1) (001 yes))
      ((101 executor (001 prolog)) (#d1) (001 yes))
      ((101 executor (001 clips)) (#d1) (001 yes))
      ((101 executor (001 datalog)) (#d1) (001 yes))
      (t (001 no)))))

(0011 admitted-mechanism?
  (0010 (mechanism)
    (110
      ((101 mechanism (001 quote-form)) (#d1) (001 yes))
      ((101 mechanism (001 atom-primitive)) (#d1) (001 yes))
      ((101 mechanism (001 eq-primitive)) (#d1) (001 yes))
      ((101 mechanism (001 cons-primitive)) (#d1) (001 yes))
      ((101 mechanism (001 car-primitive)) (#d1) (001 yes))
      ((101 mechanism (001 cdr-primitive)) (#d1) (001 yes))
      ((101 mechanism (001 cond-form)) (#d1) (001 yes))
      ((101 mechanism (001 lambda-form)) (#d1) (001 yes))
      ((101 mechanism (001 define-form)) (#d1) (001 yes))
      ((101 mechanism (001 bounded-exact-add)) (#d1) (001 yes))
      (t (001 no)))))

(0011 admitted-profile?
  (0010 (profile)
    (110
      ((101 profile (001 core3)) (#d1) (001 yes))
      (t (001 no)))))

(0011 admitted-profile-mechanism?
  (0010 (mechanism)
    (110
      ((101 mechanism (001 registered-host-mechanism))
       (#d1)
       (001 yes))
      (t (001 no)))))

(0011 profile-has-route?
  (0010 (profile sid rows)
    (110
      ((010 rows) () (001 no))
      ((010 rows) (#d0)
       (001000 ((row (100 rows)))
         (110
           ((101 profile (100 row)) (#d1)
            (110
              ((101 sid (1001 row)) (#d1) (001 yes))
              ((101 sid (1001 row)) (#d0)
               (profile-has-route? profile sid (011 rows)))))
           ((101 profile (100 row)) (#d0)
            (profile-has-route? profile sid (011 rows)))))))))

(0011 validate-profile-rows
  (0010 (rows)
    (110
      ((010 rows) ()
       (001 (function-table-mechanisms-ok)))
      ((010 rows) (#d0)
       (001001 ((row (100 rows))
              (profile (100 row))
              (sid (1001 row))
              (mechanism (10011 row)))
         (110
           ((101 (admitted-profile? profile) (001 no))
            (#d1)
            (1110 (001 function-table-mechanisms-violation)
                  (001 unsupported-profile) profile sid))
           ((101 (registry-has-sid? sid registry-rows) (001 no))
            (#d1)
            (1110 (001 function-table-mechanisms-violation)
                  (001 profile-function-not-in-canon-function-table) profile sid))
           ((101 (profile-has-route? profile sid (011 rows)) (001 yes))
            (#d1)
            (1110 (001 function-table-mechanisms-violation)
                  (001 duplicate-profile-route) profile sid))
           ((101 (admitted-profile-mechanism? mechanism) (001 no))
            (#d1)
            (1110 (001 function-table-mechanisms-violation)
                  (001 unsupported-profile-mechanism) profile sid mechanism))
           (t (validate-profile-rows (011 rows)))))))))

(0011 validate-rows
  (0010 (rows)
    (110
      ((010 rows) ()
       (001 (function-table-mechanisms-ok)))
      ((010 rows) (#d0)
       (001001 ((row (100 rows))
              (sid (100 row))
              (executor (1001 row))
              (mechanism (10011 row)))
         (110
           ((101 (admitted-executor? executor) (001 no))
            (#d1)
            (1110 (001 function-table-mechanisms-violation)
                  (001 unsupported-executor) sid executor))
           ((101 (registry-has-sid? sid registry-rows) (001 no))
            (#d1)
            (1110 (001 function-table-mechanisms-violation)
                  (001 sid-not-in-canon-function-table) sid))
           ((101 (metadata-has-route? sid executor (011 rows)) (001 yes))
            (#d1)
            (1110 (001 function-table-mechanisms-violation)
                  (001 duplicate-executor-route) sid executor))
           ((101 (admitted-mechanism? mechanism) (001 no))
            (#d1)
            (1110 (001 function-table-mechanisms-violation)
                  (001 unsupported-mechanism) sid mechanism))
           (t (validate-rows (011 rows)))))))))

(0011 legacy-verdict (validate-rows metadata-rows))
(0011 profile-verdict (validate-profile-rows profile-rows))

(0011 verdict
  (110
    ((11110111 legacy-verdict (001 (function-table-mechanisms-ok)))
     (#d1)
     profile-verdict)
    (t legacy-verdict)))

(11011011 verdict)
