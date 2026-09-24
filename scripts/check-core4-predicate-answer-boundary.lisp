; #1336 — executable witness for Core4 directed function-SID endpoints.
;
; Proves:
;   NO  -> 00000000
;   YES -> 11111111
; while () remains a distinct structural empty value outside function-SID space.

(def pab-boundary-contract
  (car (read-all (read-file "contracts/core4-predicate-answer-boundary.lisp"))))
(def pab-schema (car pab-boundary-contract))
(def pab-sections (cdr pab-boundary-contract))

(def pab-scale-contract
  (car (read-all (read-file "contracts/core4-predicate-answer-scale.lisp"))))
(def pab-scale-sections (cdr pab-scale-contract))

(def pab-field-from
  (lambda (name fields)
    (cond
      ((atom fields) (structural-kind empty-list) (quote missing))
      ((atom fields) (structural-kind pair)
       (let ((field (car fields)))
         (cond
           ((atom field) (structural-kind pair)
            (cond
              ((eq (car field) name) (identity-relation same) (cdr field))
              ((eq (car field) name) (identity-relation distinct)
               (pab-field-from name (cdr fields)))))
           ((quote pab-next) pab-next
            (pab-field-from name (cdr fields)))))))))

(def pab-field
  (lambda (section name)
    (pab-field-from name section)))

(def pab-check
  (lambda (label actual expected)
    (cond
      ((equal? actual expected) (structural-relation same) (quote ()))
      ((quote pab-fail) pab-fail
       (list (quote predicate-answer-boundary-mismatch)
             label expected actual)))))

(def pab-first-failure
  (lambda (checks)
    (cond
      ((atom checks) (structural-kind empty-list) (quote ()))
      ((atom (car checks)) (structural-kind empty-list)
       (pab-first-failure (cdr checks)))
      ((quote pab-failure) pab-failure (car checks)))))

(def pab-meta (car pab-sections))
(def pab-no (second pab-sections))
(def pab-yes (third pab-sections))
(def pab-undirected (fourth pab-sections))
(def pab-laws (fifth pab-sections))

(def pab-scale-boundary (third pab-scale-sections))

(def pab-no-sid (pab-field pab-no (quote sid-endpoint)))
(def pab-yes-sid (pab-field pab-yes (quote sid-endpoint)))

(def pab-verdict
  (lambda ()
    (let ((failure
            (pab-first-failure
              (list
                (pab-check (quote schema)
                           pab-schema
                           (quote core4-predicate-answer-boundary/2))
                (pab-check (quote profile)
                           (pab-field pab-meta (quote profile))
                           (quote core4))
                (pab-check (quote sid-space)
                           (pab-field pab-meta (quote sid-space))
                           (quote function-only))
                (pab-check (quote empty-list-space)
                           (pab-field pab-meta (quote empty-list-space))
                           (quote structural-value))
                (pab-check (quote no-direction)
                           (pab-field pab-no (quote direction))
                           (quote no))
                (pab-check (quote no-last-short-answer)
                           (pab-field pab-no (quote last-directed-answer-spelling))
                           "0000000")
                (pab-check (quote no-endpoint)
                           pab-no-sid
                           (quote 00000000))
                (pab-check (quote no-endpoint-kind)
                           (pab-field pab-no (quote endpoint-kind))
                           (quote function-sid))
                (pab-check (quote yes-direction)
                           (pab-field pab-yes (quote direction))
                           (quote yes))
                (pab-check (quote yes-last-short-answer)
                           (pab-field pab-yes (quote last-directed-answer-spelling))
                           "1111111")
                (pab-check (quote yes-endpoint)
                           pab-yes-sid
                           (quote 11111111))
                (pab-check (quote yes-endpoint-kind)
                           (pab-field pab-yes (quote endpoint-kind))
                           (quote function-sid))
                (pab-check (quote undirected-answer)
                           (pab-field pab-undirected (quote undirected-answer))
                           (quote ()))
                (pab-check (quote undirected-kind)
                           (pab-field pab-undirected (quote kind))
                           (quote structural-empty-value))
                (pab-check (quote endpoint-sids-distinct)
                           (equal? pab-no-sid pab-yes-sid)
                           (quote (structural-relation distinct)))
                (pab-check (quote no-sid-not-empty-list)
                           (equal? pab-no-sid (quote ()))
                           (quote (structural-relation distinct)))
                (pab-check (quote yes-sid-not-empty-list)
                           (equal? pab-yes-sid (quote ()))
                           (quote (structural-relation distinct)))
                (pab-check (quote endpoint-projection-forbidden)
                           (pab-field pab-laws (quote endpoint-to-empty-list-projection))
                           (quote forbidden))
                (pab-check (quote eighth-step)
                           (pab-field pab-laws (quote eighth-directed-step))
                           (quote reaches-function-sid-endpoint))
                (pab-check (quote scale-no-endpoint)
                           (pab-field pab-scale-boundary (quote no-sid-endpoint))
                           pab-no-sid)
                (pab-check (quote scale-yes-endpoint)
                           (pab-field pab-scale-boundary (quote yes-sid-endpoint))
                           pab-yes-sid)
                (pab-check (quote scale-empty-list-alias)
                           (pab-field pab-scale-boundary (quote empty-list-alias))
                           (quote forbidden))
                (pab-check (quote older-core-impact)
                           (pab-field pab-laws (quote core1-core2-core3-impact))
                           (quote none)))))))
      (cond
        ((atom failure) (structural-kind empty-list)
         (quote (core4-predicate-answer-boundary-ok)))
        ((quote pab-contract-failure) pab-contract-failure
         failure)))))

(pab-verdict)
