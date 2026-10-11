; #150/#211/#4057 — executable one-way machine authority + anti-hybrid guard.
; Admitted authority direction remains semantic-to-machine; reverse authority is RED.
; Current semantic authority is Contract 11.8 + ratified exact-domain laws.
; Every bounded machine capability must name an independent exact-domain
; semantic witness. Native/host results may realize meaning but may never
; become their own answer key.

(0011 second (0010 (x) (100 (011 x))))
(0011 third (0010 (x) (100 (011 (011 x)))))

(0011 authority-edges
  (110101001 (110110111 "tests/machine-authority-edges.lisp")))

(0011 machine-capability-provenance
  (110101001 (110110111 "lib/machine/capability-provenance.lisp")))

(0011 machine-provenance-required-fields
  (001
    (name
     semantic-authority
     admitted-form
     lowering-owner
     machine-witness
     reverse-edge
     independent-semantic-witness)))

(0011 machine-provenance-field-from
  (0010 (name fields)
    (110
      ((010 fields) () (001 missing))
      ((010 fields) (1) (001 missing))
      ((010 fields) (0)
       (001000 ((field (100 fields)))
         (110
           ((010 field) ()
            (machine-provenance-field-from name (011 fields)))
           ((010 field) (1)
            (machine-provenance-field-from name (011 fields)))
           ((010 field) (0)
            (110
              ((101 (100 field) name) (1)
               (second field))
              ((101 (100 field) name) (0)
               (machine-provenance-field-from name (011 fields)))))))))))

(0011 machine-provenance-field
  (0010 (name row)
    (110
      ((010 row) () (001 missing))
      ((010 row) (1) (001 missing))
      ((010 row) (0)
       (machine-provenance-field-from name (011 row))))))

(0011 machine-required-fields-state
  (0010 (required row)
    (110
      ((010 required) () (001 complete))
      ((010 required) (1) (001 malformed))
      ((010 required) (0)
       (001000 ((value (machine-provenance-field (100 required) row)))
         (110
           ((11110111 value (001 missing)) (1)
            (001 missing))
           ((11110111 value (001 missing)) (0)
            (machine-required-fields-state (011 required) row))))))))

(0011 exact-domain-independent-witness-state
  (0010 (witness)
    (110
      ((010 witness) () (001 rejected))
      ((010 witness) (1) (001 rejected))
      ((010 witness) (0)
       (110
         ((101 (100 witness) (001 exact-domain-expression))
          (1)
          (001 admitted))
         ((101 (100 witness) (001 exact-domain-expression))
          (0)
          (110
            ((101 (100 witness) (001 exact-domain-corpus))
             (1)
             (001 admitted))
            ((101 (100 witness) (001 exact-domain-corpus))
             (0)
             (001 rejected)))))))))

(0011 allowed-machine-edge-state
  (0010 (row)
    (110
      ((010 row) () (001 denied))
      ((010 row) (1) (001 denied))
      ((010 row) (0)
       (110
         ((101 (100 row) (001 authority-edge)) (1)
          (110
            ((101 (second row) (001 semantic)) (1)
             (110
               ((101 (third row) (001 machine)) (1)
                (001 allowed))
               ((101 (third row) (001 machine)) (0)
                (001 denied))))
            ((101 (second row) (001 semantic)) (0)
             (001 denied))))
         ((101 (100 row) (001 authority-edge)) (0)
          (001 denied)))))))

; Deliberately unbound diagnostic symbols make fail-closed violations visible
; even when stdout is buffered. CI requires the exact diagnostic name.
(0011 fail-machine-authority
  (0010 (row)
    (machine-authority-boundary-violation row)))

(0011 fail-machine-hybrid
  (0010 (row)
    (machine-semantic-hybrid-violation row)))

(0011 check-machine-edges
  (0010 (rows)
    (110
      ((010 rows) () (001 machine-authority-ok))
      ((010 rows) (1) (fail-machine-authority rows))
      ((010 rows) (0)
       (001000 ((state (allowed-machine-edge-state (100 rows))))
         (110
           ((101 state (001 allowed)) (1)
            (check-machine-edges (011 rows)))
           ((101 state (001 allowed)) (0)
            (fail-machine-authority (100 rows)))))))))

(0011 machine-provenance-row-safe-state
  (0010 (row)
    (110
      ((010 row) () (001 rejected))
      ((010 row) (1) (001 rejected))
      ((010 row) (0)
       (110
         ((101 (100 row) (001 capability-provenance)) (1)
          (001000 ((required-state
                  (machine-required-fields-state
                    machine-provenance-required-fields
                    row)))
            (110
              ((101 required-state (001 complete)) (1)
               (001001 ((semantic-authority
                        (machine-provenance-field
                          (001 semantic-authority)
                          row))
                      (reverse-edge
                        (machine-provenance-field
                          (001 reverse-edge)
                          row))
                      (machine-witness
                        (machine-provenance-field
                          (001 machine-witness)
                          row))
                      (independent-witness
                        (machine-provenance-field
                          (001 independent-semantic-witness)
                          row))
                      (independent-state
                        (exact-domain-independent-witness-state
                          independent-witness)))
                 (110
                   ((101 semantic-authority (001 language-contract.lisp+ratified-domain-laws))
                    (1)
                    (110
                      ((101 reverse-edge (001 forbidden))
                       (1)
                       (110
                         ((101 independent-state (001 admitted))
                          (1)
                          (110
                            ((11110111 independent-witness machine-witness)
                             (1)
                             (001 rejected))
                            ((11110111 independent-witness machine-witness)
                             (0)
                             (001 admitted))))
                         ((101 independent-state (001 admitted))
                          (0)
                          (001 rejected))))
                      ((101 reverse-edge (001 forbidden))
                       (0)
                       (001 rejected))))
                   ((101 semantic-authority (001 language-contract.lisp+ratified-domain-laws))
                    (0)
                    (001 rejected)))))
              ((101 required-state (001 complete)) (0)
               (001 rejected)))))
         ((101 (100 row) (001 capability-provenance)) (0)
          (001 rejected)))))))

(0011 check-machine-capability-provenance
  (0010 (rows)
    (110
      ((010 rows) () (001 machine-anti-hybrid-ok))
      ((010 rows) (1) (fail-machine-hybrid rows))
      ((010 rows) (0)
       (001000 ((state (machine-provenance-row-safe-state (100 rows))))
         (110
           ((101 state (001 admitted)) (1)
            (check-machine-capability-provenance (011 rows)))
           ((101 state (001 admitted)) (0)
            (fail-machine-hybrid (100 rows)))))))))

(check-machine-edges authority-edges)
(check-machine-capability-provenance machine-capability-provenance)
