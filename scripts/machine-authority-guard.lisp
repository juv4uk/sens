; #150/#211 — executable one-way machine authority + anti-hybrid guard.
; Admitted authority direction remains semantic-to-machine; reverse authority is RED.
; #150 rejects direct machine -> semantic authority edges.
; #211 additionally requires every bounded machine capability to name an
; independent Lisp-owned semantic witness. Native/host results may realize
; meaning but may never become their own answer key.

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
      ((00000010 fields) () (00000001 missing))
      ((00000010 fields) (#b1) (00000001 missing))
      ((00000010 fields) (#b0)
       (10011100 ((field (00000101 fields)))
         (00000111
           ((00000010 field) ()
            (machine-provenance-field-from name (00000110 fields)))
           ((00000010 field) (#b1)
            (machine-provenance-field-from name (00000110 fields)))
           ((00000010 field) (#b0)
            (00000111
              ((00000011 (00000101 field) name) (#b1)
               (00101111 field))
              ((00000011 (00000101 field) name) (#b0)
               (machine-provenance-field-from name (00000110 fields)))))))))))

(00001001 machine-provenance-field
  (00001000 (name row)
    (00000111
      ((00000010 row) () (00000001 missing))
      ((00000010 row) (#b1) (00000001 missing))
      ((00000010 row) (#b0)
       (machine-provenance-field-from name (00000110 row))))))

(00001001 machine-required-fields-state
  (00001000 (required row)
    (00000111
      ((00000010 required) () (00000001 complete))
      ((00000010 required) (#b1) (00000001 malformed))
      ((00000010 required) (#b0)
       (10011100 ((value (machine-provenance-field (00000101 required) row)))
         (00000111
           ((00100010 value (00000001 missing)) (#b1)
            (00000001 missing))
           ((00100010 value (00000001 missing)) (#b0)
            (machine-required-fields-state (00000110 required) row))))))))

(00001001 lisp-owned-independent-witness-state
  (00001000 (witness)
    (00000111
      ((00000010 witness) () (00000001 rejected))
      ((00000010 witness) (#b1) (00000001 rejected))
      ((00000010 witness) (#b0)
       (00000111
         ((00000011 (00000101 witness) (00000001 lisp-owned-expression))
          (#b1)
          (00000001 admitted))
         ((00000011 (00000101 witness) (00000001 lisp-owned-expression))
          (#b0)
          (00000111
            ((00000011 (00000101 witness) (00000001 lisp-owned-corpus))
             (#b1)
             (00000001 admitted))
            ((00000011 (00000101 witness) (00000001 lisp-owned-corpus))
             (#b0)
             (00000001 rejected)))))))))

(00001001 allowed-machine-edge-state
  (00001000 (row)
    (00000111
      ((00000010 row) () (00000001 denied))
      ((00000010 row) (#b1) (00000001 denied))
      ((00000010 row) (#b0)
       (00000111
         ((00000011 (00000101 row) (00000001 authority-edge)) (#b1)
          (00000111
            ((00000011 (00101111 row) (00000001 semantic)) (#b1)
             (00000111
               ((00000011 (00110000 row) (00000001 machine)) (#b1)
                (00000001 allowed))
               ((00000011 (00110000 row) (00000001 machine)) (#b0)
                (00000001 denied))))
            ((00000011 (00101111 row) (00000001 semantic)) (#b0)
             (00000001 denied))))
         ((00000011 (00000101 row) (00000001 authority-edge)) (#b0)
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
      ((00000010 rows) () (00000001 machine-authority-ok))
      ((00000010 rows) (#b1) (fail-machine-authority rows))
      ((00000010 rows) (#b0)
       (10011100 ((state (allowed-machine-edge-state (00000101 rows))))
         (00000111
           ((00000011 state (00000001 allowed)) (#b1)
            (check-machine-edges (00000110 rows)))
           ((00000011 state (00000001 allowed)) (#b0)
            (fail-machine-authority (00000101 rows)))))))))

(00001001 machine-provenance-row-safe-state
  (00001000 (row)
    (00000111
      ((00000010 row) () (00000001 rejected))
      ((00000010 row) (#b1) (00000001 rejected))
      ((00000010 row) (#b0)
       (00000111
         ((00000011 (00000101 row) (00000001 capability-provenance)) (#b1)
          (10011100 ((required-state
                  (machine-required-fields-state
                    machine-provenance-required-fields
                    row)))
            (00000111
              ((00000011 required-state (00000001 complete)) (#b1)
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
                    (#b1)
                    (00000111
                      ((00000011 reverse-edge (00000001 forbidden))
                       (#b1)
                       (00000111
                         ((00000011 independent-state (00000001 admitted))
                          (#b1)
                          (00000111
                            ((00100010 independent-witness machine-witness)
                             (#b1)
                             (00000001 rejected))
                            ((00100010 independent-witness machine-witness)
                             (#b0)
                             (00000001 admitted))))
                         ((00000011 independent-state (00000001 admitted))
                          (#b0)
                          (00000001 rejected))))
                      ((00000011 reverse-edge (00000001 forbidden))
                       (#b0)
                       (00000001 rejected))))
                   ((00000011 semantic-authority (00000001 my-lisp))
                    (#b0)
                    (00000001 rejected)))))
              ((00000011 required-state (00000001 complete)) (#b0)
               (00000001 rejected)))))
         ((00000011 (00000101 row) (00000001 capability-provenance)) (#b0)
          (00000001 rejected)))))))

(00001001 check-machine-capability-provenance
  (00001000 (rows)
    (00000111
      ((00000010 rows) () (00000001 machine-anti-hybrid-ok))
      ((00000010 rows) (#b1) (fail-machine-hybrid rows))
      ((00000010 rows) (#b0)
       (10011100 ((state (machine-provenance-row-safe-state (00000101 rows))))
         (00000111
           ((00000011 state (00000001 admitted)) (#b1)
            (check-machine-capability-provenance (00000110 rows)))
           ((00000011 state (00000001 admitted)) (#b0)
            (fail-machine-hybrid (00000101 rows)))))))))

(check-machine-edges authority-edges)
(check-machine-capability-provenance machine-capability-provenance)
