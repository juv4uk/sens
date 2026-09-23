; #1145 executable witness for the yantraOS bridge contract.
;
; The witness proves the intended composition without network access:
; my-lisp constructs a typed action envelope, yantraOS is represented as
; the execution owner, and the returned execution observation remains data.
; No raw shell command is admitted to the envelope.

(def yo-proper-list?
  (lambda (value)
    (cond
      ((atom value)
       (structural-kind atom)
       (cond
         ((equal? value (quote ()))
          (structural-relation same)
          (quote yes))
         (t
          (quote always)
          (quote invalid))))
      (t
       (quote always)
       (yo-proper-list? (cdr value))))))

(def yo-field
  (lambda (name record)
    (let ((found (assoc name record)))
      (cond
        ((equal? found (quote ()))
         (structural-relation same)
         (quote ()))
        (t
         (quote always)
         (cdr found))))))

(def yo-has-field?
  (lambda (name record)
    (let ((found (assoc name record)))
      (cond
        ((equal? found (quote ()))
         (structural-relation same)
         (quote no))
        (t
         (quote always)
         (quote yes))))))

(def yo-no-raw-shell?
  (lambda (envelope)
    (cond
      ((equal?
         (yo-field (quote capability)
                   (yo-field (quote action) envelope))
         (quote shell))
       (structural-relation same)
       (quote no))
      (t
       (quote always)
       (quote yes)))))

(def yo-action-envelope
  (lambda (goal capability operation target parameters verification provenance approval)
    (list
      (cons (quote protocol) (quote (yantraos-bridge 1)))
      (cons (quote intent)
            (list
              (cons (quote goal) goal)
              (cons (quote requires) (quote ()))
              (cons (quote stop-on) (quote (verified)))
              (cons (quote produces) (quote (execution-observation)))))
      (cons (quote action)
            (list
              (cons (quote capability) capability)
              (cons (quote operation) operation)
              (cons (quote target) target)))
      (cons (quote parameters) parameters)
      (cons (quote verification) verification)
      (cons (quote provenance) provenance)
      (cons (quote approval) approval))))

(def yo-action-envelope?
  (lambda (value)
    (cond
      ((yo-proper-list? value)
       (quote yes)
       (cond
         ((yo-has-field? (quote protocol) value)
          (quote yes)
          (cond
            ((yo-has-field? (quote intent) value)
             (quote yes)
             (cond
               ((yo-has-field? (quote action) value)
                (quote yes)
                (cond
                  ((yo-has-field? (quote parameters) value)
                   (quote yes)
                   (cond
                     ((yo-has-field? (quote verification) value)
                      (quote yes)
                      (cond
                        ((yo-has-field? (quote provenance) value)
                         (quote yes)
                         (cond
                           ((yo-has-field? (quote approval) value)
                            (quote yes)
                            (yo-no-raw-shell? value))
                           (t
                            (quote always)
                            (quote no))))
                        (t
                         (quote always)
                         (quote no))))
                     (t
                      (quote always)
                      (quote no))))
                  (t
                   (quote always)
                   (quote no))))
               (t
                (quote always)
                (quote no))))
            (t
             (quote always)
             (quote no))))
         (t
          (quote always)
          (quote no))))
      (t
       (quote always)
       (quote no)))))

(def yo-execution-observation
  (lambda (result route evidence audit-ref provenance)
    (list
      (cons (quote protocol) (quote (yantraos-bridge 1)))
      (cons (quote result) result)
      (cons (quote route) route)
      (cons (quote evidence) evidence)
      (cons (quote audit-ref) audit-ref)
      (cons (quote provenance) provenance))))

(def yo-execution-observation?
  (lambda (value)
    (cond
      ((yo-proper-list? value)
       (quote yes)
       (cond
         ((yo-has-field? (quote protocol) value)
          (quote yes)
          (cond
            ((yo-has-field? (quote result) value)
             (quote yes)
             (cond
               ((yo-has-field? (quote route) value)
                (quote yes)
                (cond
                  ((yo-has-field? (quote evidence) value)
                   (quote yes)
                   (cond
                     ((yo-has-field? (quote audit-ref) value)
                      (quote yes)
                      (yo-has-field? (quote provenance) value))
                     (t
                      (quote always)
                      (quote no))))
                  (t
                   (quote always)
                   (quote no))))
               (t
                (quote always)
                (quote no))))
            (t
             (quote always)
             (quote no))))
         (t
          (quote always)
          (quote no))))
      (t
       (quote always)
       (quote no)))))
