; #150/#211/#4057 — executable one-way machine authority + anti-hybrid guard.
; Admitted authority direction remains semantic-to-machine; reverse authority is RED.
; Current semantic authority is Contract 11.8 + ratified exact-domain laws.
; Every bounded machine capability must name an independent exact-domain
; semantic witness. Native/host results may realize meaning but may never
; become their own answer key.

(визначити second (функція (x) (перше (решта x))))
(визначити third (функція (x) (перше (решта (решта x)))))

(визначити authority-edges
  (читати-всі (читати-файл "tests/machine-authority-edges.lisp")))

(визначити machine-capability-provenance
  (читати-всі (читати-файл "lib/machine/capability-provenance.lisp")))

(визначити machine-provenance-required-fields
  (як-є
    (name
     semantic-authority
     admitted-form
     lowering-owner
     machine-witness
     reverse-edge
     independent-semantic-witness)))

(визначити machine-provenance-field-from
  (функція (name fields)
    (за-умовою
      ((атом? fields) () (як-є missing))
      ((атом? fields) (1) (як-є missing))
      ((атом? fields) (0)
       (нехай ((field (перше fields)))
         (за-умовою
           ((атом? field) ()
            (machine-provenance-field-from name (решта fields)))
           ((атом? field) (1)
            (machine-provenance-field-from name (решта fields)))
           ((атом? field) (0)
            (за-умовою
              ((тотожне? (перше field) name) (1)
               (second field))
              ((тотожне? (перше field) name) (0)
               (machine-provenance-field-from name (решта fields)))))))))))

(визначити machine-provenance-field
  (функція (name row)
    (за-умовою
      ((атом? row) () (як-є missing))
      ((атом? row) (1) (як-є missing))
      ((атом? row) (0)
       (machine-provenance-field-from name (решта row))))))

(визначити machine-required-fields-state
  (функція (required row)
    (за-умовою
      ((атом? required) () (як-є complete))
      ((атом? required) (1) (як-є malformed))
      ((атом? required) (0)
       (нехай ((value (machine-provenance-field (перше required) row)))
         (за-умовою
           ((однакові? value (як-є missing)) (1)
            (як-є missing))
           ((однакові? value (як-є missing)) (0)
            (machine-required-fields-state (решта required) row))))))))

(визначити exact-domain-independent-witness-state
  (функція (witness)
    (за-умовою
      ((атом? witness) () (як-є rejected))
      ((атом? witness) (1) (як-є rejected))
      ((атом? witness) (0)
       (за-умовою
         ((тотожне? (перше witness) (як-є exact-domain-expression))
          (1)
          (як-є admitted))
         ((тотожне? (перше witness) (як-є exact-domain-expression))
          (0)
          (за-умовою
            ((тотожне? (перше witness) (як-є exact-domain-corpus))
             (1)
             (як-є admitted))
            ((тотожне? (перше witness) (як-є exact-domain-corpus))
             (0)
             (як-є rejected)))))))))

(визначити allowed-machine-edge-state
  (функція (row)
    (за-умовою
      ((атом? row) () (як-є denied))
      ((атом? row) (1) (як-є denied))
      ((атом? row) (0)
       (за-умовою
         ((тотожне? (перше row) (як-є authority-edge)) (1)
          (за-умовою
            ((тотожне? (second row) (як-є semantic)) (1)
             (за-умовою
               ((тотожне? (third row) (як-є machine)) (1)
                (як-є allowed))
               ((тотожне? (third row) (як-є machine)) (0)
                (як-є denied))))
            ((тотожне? (second row) (як-є semantic)) (0)
             (як-є denied))))
         ((тотожне? (перше row) (як-є authority-edge)) (0)
          (як-є denied)))))))

; Deliberately unbound diagnostic symbols make fail-closed violations visible
; even when stdout is buffered. CI requires the exact diagnostic name.
(визначити fail-machine-authority
  (функція (row)
    (machine-authority-boundary-violation row)))

(визначити fail-machine-hybrid
  (функція (row)
    (machine-semantic-hybrid-violation row)))

(визначити check-machine-edges
  (функція (rows)
    (за-умовою
      ((атом? rows) () (як-є machine-authority-ok))
      ((атом? rows) (1) (fail-machine-authority rows))
      ((атом? rows) (0)
       (нехай ((state (allowed-machine-edge-state (перше rows))))
         (за-умовою
           ((тотожне? state (як-є allowed)) (1)
            (check-machine-edges (решта rows)))
           ((тотожне? state (як-є allowed)) (0)
            (fail-machine-authority (перше rows)))))))))

(визначити machine-provenance-row-safe-state
  (функція (row)
    (за-умовою
      ((атом? row) () (як-є rejected))
      ((атом? row) (1) (як-є rejected))
      ((атом? row) (0)
       (за-умовою
         ((тотожне? (перше row) (як-є capability-provenance)) (1)
          (нехай ((required-state
                  (machine-required-fields-state
                    machine-provenance-required-fields
                    row)))
            (за-умовою
              ((тотожне? required-state (як-є complete)) (1)
               (нехай-послідовно ((semantic-authority
                        (machine-provenance-field
                          (як-є semantic-authority)
                          row))
                      (reverse-edge
                        (machine-provenance-field
                          (як-є reverse-edge)
                          row))
                      (machine-witness
                        (machine-provenance-field
                          (як-є machine-witness)
                          row))
                      (independent-witness
                        (machine-provenance-field
                          (як-є independent-semantic-witness)
                          row))
                      (independent-state
                        (exact-domain-independent-witness-state
                          independent-witness)))
                 (за-умовою
                   ((тотожне? semantic-authority (як-є language-contract.lisp+ratified-domain-laws))
                    (1)
                    (за-умовою
                      ((тотожне? reverse-edge (як-є forbidden))
                       (1)
                       (за-умовою
                         ((тотожне? independent-state (як-є admitted))
                          (1)
                          (за-умовою
                            ((однакові? independent-witness machine-witness)
                             (1)
                             (як-є rejected))
                            ((однакові? independent-witness machine-witness)
                             (0)
                             (як-є admitted))))
                         ((тотожне? independent-state (як-є admitted))
                          (0)
                          (як-є rejected))))
                      ((тотожне? reverse-edge (як-є forbidden))
                       (0)
                       (як-є rejected))))
                   ((тотожне? semantic-authority (як-є language-contract.lisp+ratified-domain-laws))
                    (0)
                    (як-є rejected)))))
              ((тотожне? required-state (як-є complete)) (0)
               (як-є rejected)))))
         ((тотожне? (перше row) (як-є capability-provenance)) (0)
          (як-є rejected)))))))

(визначити check-machine-capability-provenance
  (функція (rows)
    (за-умовою
      ((атом? rows) () (як-є machine-anti-hybrid-ok))
      ((атом? rows) (1) (fail-machine-hybrid rows))
      ((атом? rows) (0)
       (нехай ((state (machine-provenance-row-safe-state (перше rows))))
         (за-умовою
           ((тотожне? state (як-є admitted)) (1)
            (check-machine-capability-provenance (решта rows)))
           ((тотожне? state (як-є admitted)) (0)
            (fail-machine-hybrid (перше rows)))))))))

(check-machine-edges authority-edges)
(check-machine-capability-provenance machine-capability-provenance)
