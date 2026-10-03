; #150/#211 — executable one-way machine authority + anti-hybrid guard.
; Admitted authority direction remains semantic-to-machine; reverse authority is RED.
; #150 rejects direct machine -> semantic authority edges.
; #211 additionally requires every bounded machine capability to name an
; independent Lisp-owned semantic witness. Native/host results may realize
; meaning but may never become their own answer key.

(00001001 second (00001000 (x) (00000101 (00000110 x))))
(00001001 third (00001000 (x) (00000101 (00000110 (00000110 x)))))

; Local structural predicates preserve the retired three-state ATOM
; classification while machine authority control uses exact PredicateBit.
(00001001 machine-authority-predicate-yes
  (00001000 ()
    (00000010 (00000001 ()))))

(00001001 machine-authority-predicate-no
  (00001000 ()
    (00000010 (00000001 (00000000)))))

(00001001 machine-authority-predicate-no?
  (00001000 (value)
    (00000011 value (machine-authority-predicate-no))))

(00001001 machine-authority-empty-list?
  (00001000 (value)
    (00100010 value (00000001 ()))))

(00001001 machine-authority-nonempty-atom?
  (00001000 (value)
    (00000111
      ((00000010 value)
       (machine-authority-predicate-no? (machine-authority-empty-list? value)))
      ((machine-authority-predicate-yes)
       (machine-authority-predicate-no)))))

(00001001 machine-authority-pair?
  (00001000 (value)
    (00000111
      ((00000010 value)
       (machine-authority-predicate-no))
      ((machine-authority-predicate-yes)
       (machine-authority-predicate-yes)))))

(00001001 authority-edges
  (01001011 (10100110 "tests/machine-authority-edges.lisp")))

(00001001 machine-capability-provenance
  (01001011 (10100110 "lib/machine/capability-provenance.lisp")))

(00001001 machine-provenance-required-fields
  (00000001
    (name
     semantic-authority
     admitted-form
     lowering-owner
     machine-witness
     reverse-edge
     independent-semantic-witness)))

(00001001 machine-provenance-field-from
  (00001000 (name fields)
    (00000111
      ((machine-authority-empty-list? fields) (00000001 missing))
      ((machine-authority-nonempty-atom? fields) (00000001 missing))
      ((machine-authority-pair? fields)
       (10011100 ((field (00000101 fields)))
         (00000111
           ((machine-authority-empty-list? field)
            (machine-provenance-field-from name (00000110 fields)))
           ((machine-authority-nonempty-atom? field)
            (machine-provenance-field-from name (00000110 fields)))
           ((machine-authority-pair? field)
            (00000111
              ((00000011 (00000101 field) name)
               (second field))
              ((machine-authority-predicate-no? (00000011 (00000101 field) name))
               (machine-provenance-field-from name (00000110 fields)))))))))))

(00001001 machine-provenance-field
  (00001000 (name row)
    (00000111
      ((machine-authority-empty-list? row) (00000001 missing))
      ((machine-authority-nonempty-atom? row) (00000001 missing))
      ((machine-authority-pair? row)
       (machine-provenance-field-from name (00000110 row))))))

(00001001 machine-required-fields-state
  (00001000 (required row)
    (00000111
      ((machine-authority-empty-list? required) (00000001 complete))
      ((machine-authority-nonempty-atom? required) (00000001 malformed))
      ((machine-authority-pair? required)
       (10011100 ((value (machine-provenance-field (00000101 required) row)))
         (00000111
           ((00100010 value (00000001 missing))
            (00000001 missing))
           ((machine-authority-predicate-no? (00100010 value (00000001 missing)))
            (machine-required-fields-state (00000110 required) row))))))))

(00001001 lisp-owned-independent-witness-state
  (00001000 (witness)
    (00000111
      ((machine-authority-empty-list? witness) (00000001 rejected))
      ((machine-authority-nonempty-atom? witness) (00000001 rejected))
      ((machine-authority-pair? witness)
       (00000111
         ((00000011 (00000101 witness) (00000001 lisp-owned-expression))
          (00000001 admitted))
         ((machine-authority-predicate-no? (00000011 (00000101 witness) (00000001 lisp-owned-expression)))
          (00000111
            ((00000011 (00000101 witness) (00000001 lisp-owned-corpus))
             (00000001 admitted))
            ((machine-authority-predicate-no? (00000011 (00000101 witness) (00000001 lisp-owned-corpus)))
             (00000001 rejected)))))))))

(00001001 allowed-machine-edge-state
  (00001000 (row)
    (00000111
      ((machine-authority-empty-list? row) (00000001 denied))
      ((machine-authority-nonempty-atom? row) (00000001 denied))
      ((machine-authority-pair? row)
       (00000111
         ((00000011 (00000101 row) (00000001 authority-edge))
          (00000111
            ((00000011 (second row) (00000001 semantic))
             (00000111
               ((00000011 (third row) (00000001 machine))
                (00000001 allowed))
               ((machine-authority-predicate-no? (00000011 (third row) (00000001 machine)))
                (00000001 denied))))
            ((machine-authority-predicate-no? (00000011 (second row) (00000001 semantic)))
             (00000001 denied))))
         ((machine-authority-predicate-no? (00000011 (00000101 row) (00000001 authority-edge)))
          (00000001 denied)))))))

; Deliberately unbound diagnostic symbols make fail-closed violations visible
; even when stdout is buffered. CI requires the exact diagnostic name.
(00001001 fail-machine-authority
  (00001000 (row)
    (machine-authority-boundary-violation row)))

(00001001 fail-machine-hybrid
  (00001000 (row)
    (machine-semantic-hybrid-violation row)))

(00001001 check-machine-edges
  (00001000 (rows)
    (00000111
      ((machine-authority-empty-list? rows) (00000001 machine-authority-ok))
      ((machine-authority-nonempty-atom? rows) (fail-machine-authority rows))
      ((machine-authority-pair? rows)
       (10011100 ((state (allowed-machine-edge-state (00000101 rows))))
         (00000111
           ((00000011 state (00000001 allowed))
            (check-machine-edges (00000110 rows)))
           ((machine-authority-predicate-no? (00000011 state (00000001 allowed)))
            (fail-machine-authority (00000101 rows)))))))))

(00001001 machine-provenance-row-safe-state
  (00001000 (row)
    (00000111
      ((machine-authority-empty-list? row) (00000001 rejected))
      ((machine-authority-nonempty-atom? row) (00000001 rejected))
      ((machine-authority-pair? row)
       (00000111
         ((00000011 (00000101 row) (00000001 capability-provenance))
          (10011100 ((required-state
                  (machine-required-fields-state
                    machine-provenance-required-fields
                    row)))
            (00000111
              ((00000011 required-state (00000001 complete))
               (10011101 ((semantic-authority
                        (machine-provenance-field
                          (00000001 semantic-authority)
                          row))
                      (reverse-edge
                        (machine-provenance-field
                          (00000001 reverse-edge)
                          row))
                      (machine-witness
                        (machine-provenance-field
                          (00000001 machine-witness)
                          row))
                      (independent-witness
                        (machine-provenance-field
                          (00000001 independent-semantic-witness)
                          row))
                      (independent-state
                        (lisp-owned-independent-witness-state
                          independent-witness)))
                 (00000111
                   ((00000011 semantic-authority (00000001 my-lisp))
                    (00000111
                      ((00000011 reverse-edge (00000001 forbidden))
                       (00000111
                         ((00000011 independent-state (00000001 admitted))
                          (00000111
                            ((00100010 independent-witness machine-witness)
                             (00000001 rejected))
                            ((machine-authority-predicate-no? (00100010 independent-witness machine-witness))
                             (00000001 admitted))))
                         ((machine-authority-predicate-no? (00000011 independent-state (00000001 admitted)))
                          (00000001 rejected))))
                      ((machine-authority-predicate-no? (00000011 reverse-edge (00000001 forbidden)))
                       (00000001 rejected))))
                   ((machine-authority-predicate-no? (00000011 semantic-authority (00000001 my-lisp)))
                    (00000001 rejected)))))
              ((machine-authority-predicate-no? (00000011 required-state (00000001 complete)))
               (00000001 rejected)))))
         ((machine-authority-predicate-no? (00000011 (00000101 row) (00000001 capability-provenance)))
          (00000001 rejected)))))))

(00001001 check-machine-capability-provenance
  (00001000 (rows)
    (00000111
      ((machine-authority-empty-list? rows) (00000001 machine-anti-hybrid-ok))
      ((machine-authority-nonempty-atom? rows) (fail-machine-hybrid rows))
      ((machine-authority-pair? rows)
       (10011100 ((state (machine-provenance-row-safe-state (00000101 rows))))
         (00000111
           ((00000011 state (00000001 admitted))
            (check-machine-capability-provenance (00000110 rows)))
           ((machine-authority-predicate-no? (00000011 state (00000001 admitted)))
            (fail-machine-hybrid (00000101 rows)))))))))

(check-machine-edges authority-edges)
(check-machine-capability-provenance machine-capability-provenance)
