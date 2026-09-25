; #150/#211 — executable one-way machine authority + anti-hybrid guard.
; Admitted authority direction remains semantic-to-machine; reverse authority is RED.
; #150 rejects direct machine -> semantic authority edges.
; #211 additionally requires every bounded machine capability to name an
; independent Lisp-owned semantic witness. Native/host results may realize
; meaning but may never become their own answer key.

(def second (lambda (x) (car (cdr x))))
(def third (lambda (x) (car (cdr (cdr x)))))

(def authority-edges
  (read-all (read-file "tests/machine-authority-edges.lisp")))

(def machine-capability-provenance
  (read-all (read-file "lib/machine/capability-provenance.lisp")))

(def machine-provenance-required-fields
  (quote
    (name
     semantic-authority
     admitted-form
     lowering-owner
     machine-witness
     reverse-edge
     independent-semantic-witness)))

(def machine-provenance-field-from
  (lambda (name fields)
    (cond
      ((atom? fields) (structural-kind empty-list) (quote missing))
      ((atom? fields) (structural-kind atom) (quote missing))
      ((atom? fields) (structural-kind pair)
       (let ((field (car fields)))
         (cond
           ((atom? field) (structural-kind empty-list)
            (machine-provenance-field-from name (cdr fields)))
           ((atom? field) (structural-kind atom)
            (machine-provenance-field-from name (cdr fields)))
           ((atom? field) (structural-kind pair)
            (cond
              ((eq? (car field) name) (identity-relation same)
               (second field))
              ((eq? (car field) name) (identity-relation distinct)
               (machine-provenance-field-from name (cdr fields)))))))))))

(def machine-provenance-field
  (lambda (name row)
    (cond
      ((atom? row) (structural-kind empty-list) (quote missing))
      ((atom? row) (structural-kind atom) (quote missing))
      ((atom? row) (structural-kind pair)
       (machine-provenance-field-from name (cdr row))))))

(def machine-required-fields-state
  (lambda (required row)
    (cond
      ((atom? required) (structural-kind empty-list) (quote complete))
      ((atom? required) (structural-kind atom) (quote malformed))
      ((atom? required) (structural-kind pair)
       (let ((value (machine-provenance-field (car required) row)))
         (cond
           ((equal? value (quote missing)) (structural-relation same)
            (quote missing))
           ((equal? value (quote missing)) (structural-relation distinct)
            (machine-required-fields-state (cdr required) row))))))))

(def lisp-owned-independent-witness-state
  (lambda (witness)
    (cond
      ((atom? witness) (structural-kind empty-list) (quote rejected))
      ((atom? witness) (structural-kind atom) (quote rejected))
      ((atom? witness) (structural-kind pair)
       (cond
         ((eq? (car witness) (quote lisp-owned-expression))
          (identity-relation same)
          (quote admitted))
         ((eq? (car witness) (quote lisp-owned-expression))
          (identity-relation distinct)
          (cond
            ((eq? (car witness) (quote lisp-owned-corpus))
             (identity-relation same)
             (quote admitted))
            ((eq? (car witness) (quote lisp-owned-corpus))
             (identity-relation distinct)
             (quote rejected)))))))))

(def allowed-machine-edge-state
  (lambda (row)
    (cond
      ((atom? row) (structural-kind empty-list) (quote denied))
      ((atom? row) (structural-kind atom) (quote denied))
      ((atom? row) (structural-kind pair)
       (cond
         ((eq? (car row) (quote authority-edge)) (identity-relation same)
          (cond
            ((eq? (second row) (quote semantic)) (identity-relation same)
             (cond
               ((eq? (third row) (quote machine)) (identity-relation same)
                (quote allowed))
               ((eq? (third row) (quote machine)) (identity-relation distinct)
                (quote denied))))
            ((eq? (second row) (quote semantic)) (identity-relation distinct)
             (quote denied))))
         ((eq? (car row) (quote authority-edge)) (identity-relation distinct)
          (quote denied)))))))

; Deliberately unbound diagnostic symbols make fail-closed violations visible
; even when stdout is buffered. CI requires the exact diagnostic name.
(def fail-machine-authority
  (lambda (row)
    (machine-authority-boundary-violation row)))

(def fail-machine-hybrid
  (lambda (row)
    (machine-semantic-hybrid-violation row)))

(def check-machine-edges
  (lambda (rows)
    (cond
      ((atom? rows) (structural-kind empty-list) (quote machine-authority-ok))
      ((atom? rows) (structural-kind atom) (fail-machine-authority rows))
      ((atom? rows) (structural-kind pair)
       (let ((state (allowed-machine-edge-state (car rows))))
         (cond
           ((eq? state (quote allowed)) (identity-relation same)
            (check-machine-edges (cdr rows)))
           ((eq? state (quote allowed)) (identity-relation distinct)
            (fail-machine-authority (car rows)))))))))

(def machine-provenance-row-safe-state
  (lambda (row)
    (cond
      ((atom? row) (structural-kind empty-list) (quote rejected))
      ((atom? row) (structural-kind atom) (quote rejected))
      ((atom? row) (structural-kind pair)
       (cond
         ((eq? (car row) (quote capability-provenance)) (identity-relation same)
          (let ((required-state
                  (machine-required-fields-state
                    machine-provenance-required-fields
                    row)))
            (cond
              ((eq? required-state (quote complete)) (identity-relation same)
               (let* ((semantic-authority
                        (machine-provenance-field
                          (quote semantic-authority)
                          row))
                      (reverse-edge
                        (machine-provenance-field
                          (quote reverse-edge)
                          row))
                      (machine-witness
                        (machine-provenance-field
                          (quote machine-witness)
                          row))
                      (independent-witness
                        (machine-provenance-field
                          (quote independent-semantic-witness)
                          row))
                      (independent-state
                        (lisp-owned-independent-witness-state
                          independent-witness)))
                 (cond
                   ((eq? semantic-authority (quote my-lisp))
                    (identity-relation same)
                    (cond
                      ((eq? reverse-edge (quote forbidden))
                       (identity-relation same)
                       (cond
                         ((eq? independent-state (quote admitted))
                          (identity-relation same)
                          (cond
                            ((equal? independent-witness machine-witness)
                             (structural-relation same)
                             (quote rejected))
                            ((equal? independent-witness machine-witness)
                             (structural-relation distinct)
                             (quote admitted))))
                         ((eq? independent-state (quote admitted))
                          (identity-relation distinct)
                          (quote rejected))))
                      ((eq? reverse-edge (quote forbidden))
                       (identity-relation distinct)
                       (quote rejected))))
                   ((eq? semantic-authority (quote my-lisp))
                    (identity-relation distinct)
                    (quote rejected)))))
              ((eq? required-state (quote complete)) (identity-relation distinct)
               (quote rejected)))))
         ((eq? (car row) (quote capability-provenance)) (identity-relation distinct)
          (quote rejected)))))))

(def check-machine-capability-provenance
  (lambda (rows)
    (cond
      ((atom? rows) (structural-kind empty-list) (quote machine-anti-hybrid-ok))
      ((atom? rows) (structural-kind atom) (fail-machine-hybrid rows))
      ((atom? rows) (structural-kind pair)
       (let ((state (machine-provenance-row-safe-state (car rows))))
         (cond
           ((eq? state (quote admitted)) (identity-relation same)
            (check-machine-capability-provenance (cdr rows)))
           ((eq? state (quote admitted)) (identity-relation distinct)
            (fail-machine-hybrid (car rows)))))))))

(check-machine-edges authority-edges)
(check-machine-capability-provenance machine-capability-provenance)
