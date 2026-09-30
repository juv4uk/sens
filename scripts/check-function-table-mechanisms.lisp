; #1046 — fail-closed validation for transitional mechanism metadata.
; Semantic identity authority is ONLY lib/surface/semantic-registry.lisp.
; This checker proves mechanism metadata cannot invent a function beside that table.
; #1332/#1403: empty-list-ground is not a function mechanism.

(00001001 registry
  (00000101 (01001011 (10100110 "lib/surface/semantic-registry.lisp"))))

(00001001 metadata
  (00000101 (01001011 (10100110 "lib/function-table-mechanisms.lisp"))))

(00001001 registry-rows registry)

; Structural helpers keep list-shape checks exact under PredicateBit control.
(00001001 mechanism-predicate-yes
  (00001000 ()
    (00000010 (00000001 ()))))

(00001001 mechanism-predicate-no
  (00001000 ()
    (00000010 (00000001 (00000000)))))

(00001001 mechanism-empty-list?
  (00001000 (value)
    (00100010 value (00000001 ()))))

(00001001 mechanism-pair?
  (00001000 (value)
    (00000111
      ((00000010 value)
       (mechanism-predicate-no))
      ((mechanism-predicate-yes)
       (mechanism-predicate-yes)))))

(00001001 find-section
  (00001000 (name sections)
    (00000111
      ((mechanism-empty-list? sections)
       (00000001 ()))
      ((mechanism-pair? sections)
       (00000111
         ((00000011 (00000101 (00000101 sections)) name)
          (00000101 sections))
         ((mechanism-predicate-yes)
          (find-section name (00000110 sections))))))))

(00001001 metadata-rows
  (00000110 (find-section (00000001 rows) metadata)))

(00001001 profile-rows
  (00000110 (find-section (00000001 profile-routes) metadata)))

(00001001 registry-has-sid?
  (00001000 (sid rows)
    (00000111
      ((mechanism-empty-list? rows)
       (00000001 no))
      ((mechanism-pair? rows)
       (00000111
         ((00000011 sid (00000101 (00000101 rows)))
          (00000001 yes))
         ((mechanism-predicate-yes)
          (registry-has-sid? sid (00000110 rows))))))))

(00001001 metadata-has-route?
  (00001000 (sid executor rows)
    (00000111
      ((mechanism-empty-list? rows)
       (00000001 no))
      ((mechanism-pair? rows)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00000011 sid (00000101 row))
            (00000111
              ((00000011 executor (00101111 row))
               (00000001 yes))
              ((mechanism-predicate-yes)
               (metadata-has-route? sid executor (00000110 rows)))))
           ((mechanism-predicate-yes)
            (metadata-has-route? sid executor (00000110 rows)))))))))

(00001001 admitted-executor?
  (00001000 (executor)
    (00000111
      ((00000011 executor (00000001 evaluator)) (00000001 yes))
      ((00000011 executor (00000001 common-lisp)) (00000001 yes))
      ((00000011 executor (00000001 prolog)) (00000001 yes))
      ((00000011 executor (00000001 clips)) (00000001 yes))
      ((00000011 executor (00000001 datalog)) (00000001 yes))
      ((mechanism-predicate-yes) (00000001 no)))))

(00001001 admitted-mechanism?
  (00001000 (mechanism)
    (00000111
      ((00000011 mechanism (00000001 quote-form)) (00000001 yes))
      ((00000011 mechanism (00000001 atom-primitive)) (00000001 yes))
      ((00000011 mechanism (00000001 eq-primitive)) (00000001 yes))
      ((00000011 mechanism (00000001 cons-primitive)) (00000001 yes))
      ((00000011 mechanism (00000001 car-primitive)) (00000001 yes))
      ((00000011 mechanism (00000001 cdr-primitive)) (00000001 yes))
      ((00000011 mechanism (00000001 cond-form)) (00000001 yes))
      ((00000011 mechanism (00000001 lambda-form)) (00000001 yes))
      ((00000011 mechanism (00000001 define-form)) (00000001 yes))
      ((00000011 mechanism (00000001 bounded-exact-add)) (00000001 yes))
      ((mechanism-predicate-yes) (00000001 no)))))


(00001001 admitted-profile?
  (00001000 (profile)
    (00000111
      ((00000011 profile (00000001 core3)) (00000001 yes))
      ((mechanism-predicate-yes) (00000001 no)))))

(00001001 admitted-profile-mechanism?
  (00001000 (mechanism)
    (00000111
      ((00000011 mechanism (00000001 registered-host-mechanism))
       (00000001 yes))
      ((mechanism-predicate-yes) (00000001 no)))))

(00001001 profile-has-route?
  (00001000 (profile sid rows)
    (00000111
      ((mechanism-empty-list? rows)
       (00000001 no))
      ((mechanism-pair? rows)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00000011 profile (00000101 row))
            (00000111
              ((00000011 sid (00101111 row))
               (00000001 yes))
              ((mechanism-predicate-yes)
               (profile-has-route? profile sid (00000110 rows)))))
           ((mechanism-predicate-yes)
            (profile-has-route? profile sid (00000110 rows)))))))))

(00001001 validate-profile-rows
  (00001000 (rows)
    (00000111
      ((mechanism-empty-list? rows)
       (00000001 (function-table-mechanisms-ok)))
      ((mechanism-pair? rows)
       (10011101 ((row (00000101 rows))
              (profile (00000101 row))
              (sid (00101111 row))
              (mechanism (00110000 row)))
         (00000111
           ((00000011 (admitted-profile? profile) (00000001 no))
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-profile) profile sid))
           ((00000011 (registry-has-sid? sid registry-rows) (00000001 no))
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 profile-function-not-in-canon-function-table) profile sid))
           ((00000011 (profile-has-route? profile sid (00000110 rows)) (00000001 yes))
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 duplicate-profile-route) profile sid))
           ((00000011 (admitted-profile-mechanism? mechanism) (00000001 no))
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-profile-mechanism) profile sid mechanism))
           ((mechanism-predicate-yes)
            (validate-profile-rows (00000110 rows)))))))))

(00001001 validate-rows
  (00001000 (rows)
    (00000111
      ((mechanism-empty-list? rows)
       (00000001 (function-table-mechanisms-ok)))
      ((mechanism-pair? rows)
       (10011101 ((row (00000101 rows))
              (sid (00000101 row))
              (executor (00101111 row))
              (mechanism (00110000 row)))
         (00000111
           ((00000011 (admitted-executor? executor) (00000001 no))
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-executor) sid executor))
           ((00000011 (registry-has-sid? sid registry-rows) (00000001 no))
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 sid-not-in-canon-function-table) sid))
           ((00000011 (metadata-has-route? sid executor (00000110 rows)) (00000001 yes))
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 duplicate-executor-route) sid executor))
           ((00000011 (admitted-mechanism? mechanism) (00000001 no))
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-mechanism) sid mechanism))
           ((mechanism-predicate-yes)
            (validate-rows (00000110 rows)))))))))

(00001001 legacy-verdict (validate-rows metadata-rows))
(00001001 profile-verdict (validate-profile-rows profile-rows))

(00001001 verdict
  (00000111
    ((00100010 legacy-verdict (00000001 (function-table-mechanisms-ok)))
     profile-verdict)
    ((mechanism-predicate-yes)
     legacy-verdict)))

(01001000 verdict)
