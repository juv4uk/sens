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
      ((atom? fields) () (quote missing))
      ((atom? fields) (1) (quote missing))
      ((atom? fields) (0)
       (let ((field (car fields)))
         (cond
           ((atom? field) ()
            (machine-provenance-field-from name (cdr fields)))
           ((atom? field) (1)
            (machine-provenance-field-from name (cdr fields)))
           ((atom? field) (0)
            (cond
              ((eq? (car field) name) (1)
               (second field))
              ((eq? (car field) name) (0)
               (machine-provenance-field-from name (cdr fields)))))))))))

(def machine-provenance-field
  (lambda (name row)
    (cond
      ((atom? row) () (quote missing))
      ((atom? row) (1) (quote missing))
      ((atom? row) (0)
       (machine-provenance-field-from name (cdr row))))))

(def machine-required-fields-state
  (lambda (required row)
    (cond
      ((atom? required) () (quote complete))
      ((atom? required) (1) (quote malformed))
      ((atom? required) (0)
       (let ((value (machine-provenance-field (car required) row)))
         (cond
           ((equal? value (quote missing)) (1)
            (quote missing))
           ((equal? value (quote missing)) (0)
            (machine-required-fields-state (cdr required) row))))))))

(def lisp-owned-independent-witness-state
  (lambda (witness)
    (cond
      ((atom? witness) () (quote rejected))
      ((atom? witness) (1) (quote rejected))
      ((atom? witness) (0)
       (cond
         ((eq? (car witness) (quote lisp-owned-expression))
          (1)
          (quote admitted))
         ((eq? (car witness) (quote lisp-owned-expression))
          (0)
          (cond
            ((eq? (car witness) (quote lisp-owned-corpus))
             (1)
             (quote admitted))
            ((eq? (car witness) (quote lisp-owned-corpus))
             (0)
             (quote rejected)))))))))

(def allowed-machine-edge-state
  (lambda (row)
    (cond
      ((atom? row) () (quote denied))
      ((atom? row) (1) (quote denied))
      ((atom? row) (0)
       (cond
         ((eq? (car row) (quote authority-edge)) (1)
          (cond
            ((eq? (second row) (quote semantic)) (1)
             (cond
               ((eq? (third row) (quote machine)) (1)
                (quote allowed))
               ((eq? (third row) (quote machine)) (0)
                (quote denied))))
            ((eq? (second row) (quote semantic)) (0)
             (quote denied))))
         ((eq? (car row) (quote authority-edge)) (0)
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
      ((atom? rows) () (quote machine-authority-ok))
      ((atom? rows) (1) (fail-machine-authority rows))
      ((atom? rows) (0)
       (let ((state (allowed-machine-edge-state (car rows))))
         (cond
           ((eq? state (quote allowed)) (1)
            (check-machine-edges (cdr rows)))
           ((eq? state (quote allowed)) (0)
            (fail-machine-authority (car rows)))))))))

(def machine-provenance-row-safe-state
  (lambda (row)
    (cond
      ((atom? row) () (quote rejected))
      ((atom? row) (1) (quote rejected))
      ((atom? row) (0)
       (cond
         ((eq? (car row) (quote capability-provenance)) (1)
          (let ((required-state
                  (machine-required-fields-state
                    machine-provenance-required-fields
                    row)))
            (cond
              ((eq? required-state (quote complete)) (1)
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
                    (1)
                    (cond
                      ((eq? reverse-edge (quote forbidden))
                       (1)
                       (cond
                         ((eq? independent-state (quote admitted))
                          (1)
                          (cond
                            ((equal? independent-witness machine-witness)
                             (1)
                             (quote rejected))
                            ((equal? independent-witness machine-witness)
                             (0)
                             (quote admitted))))
                         ((eq? independent-state (quote admitted))
                          (0)
                          (quote rejected))))
                      ((eq? reverse-edge (quote forbidden))
                       (0)
                       (quote rejected))))
                   ((eq? semantic-authority (quote my-lisp))
                    (0)
                    (quote rejected)))))
              ((eq? required-state (quote complete)) (0)
               (quote rejected)))))
         ((eq? (car row) (quote capability-provenance)) (0)
          (quote rejected)))))))

(def check-machine-capability-provenance
  (lambda (rows)
    (cond
      ((atom? rows) () (quote machine-anti-hybrid-ok))
      ((atom? rows) (1) (fail-machine-hybrid rows))
      ((atom? rows) (0)
       (let ((state (machine-provenance-row-safe-state (car rows))))
         (cond
           ((eq? state (quote admitted)) (1)
            (check-machine-capability-provenance (cdr rows)))
           ((eq? state (quote admitted)) (0)
            (fail-machine-hybrid (car rows)))))))))

(check-machine-edges authority-edges)
(check-machine-capability-provenance machine-capability-provenance)
