; #1256 — executable witness for the Core4 predicate-answer boundary.
;
; This script proves the narrow law only.  It does not change Sid8 evaluation,
; callable dispatch, or Canon identity.

(def pab-boundary-forms
  (read-all (read-file "contracts/core4-predicate-answer-boundary.lisp")))
(def pab-boundary-contract (car pab-boundary-forms))
(def pab-boundary-schema (car pab-boundary-contract))
(def pab-boundary-sections (cdr pab-boundary-contract))

(def pab-scale-forms
  (read-all (read-file "contracts/core4-predicate-answer-scale.lisp")))
(def pab-scale-contract (car pab-scale-forms))
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
             label
             expected
             actual)))))

(def pab-first-failure
  (lambda (checks)
    (cond
      ((atom checks) (structural-kind empty-list) (quote ()))
      ((atom (car checks)) (structural-kind empty-list)
       (pab-first-failure (cdr checks)))
      ((quote pab-failure) pab-failure (car checks)))))

(def pab-meta (car pab-boundary-sections))
(def pab-lower (second pab-boundary-sections))
(def pab-upper (third pab-boundary-sections))
(def pab-laws (fourth pab-boundary-sections))

; #1255 scale layout is intentionally small and fixed:
; meta, no, boundary, yes, algebra.
(def pab-scale-boundary (third pab-scale-sections))

(def pab-lower-sid (pab-field pab-lower (quote sid-anchor)))
(def pab-upper-sid (pab-field pab-upper (quote sid-anchor)))
(def pab-lower-projection (pab-field pab-lower (quote projection)))
(def pab-upper-projection (pab-field pab-upper (quote projection)))

(def pab-verdict
  (lambda ()
    (let ((failure
            (pab-first-failure
              (list
                (pab-check (quote schema)
                           pab-boundary-schema
                           (quote core4-predicate-answer-boundary/1))
                (pab-check (quote profile)
                           (pab-field pab-meta (quote profile))
                           (quote core4))
                (pab-check (quote sid-identity)
                           (pab-field pab-meta (quote sid-identity))
                           (quote preserved))
                (pab-check (quote bare-sid-evaluation)
                           (pab-field pab-meta (quote bare-sid-evaluation))
                           (quote unchanged))
                (pab-check (quote callable-dispatch)
                           (pab-field pab-meta (quote callable-dispatch))
                           (quote unchanged))
                (pab-check (quote fail-closed)
                           (pab-field pab-meta (quote unknown-callable-fail-closed))
                           (quote preserved))
                (pab-check (quote lower-last-answer)
                           (pab-field pab-lower (quote last-directed-answer-spelling))
                           "0000000")
                (pab-check (quote upper-last-answer)
                           (pab-field pab-upper (quote last-directed-answer-spelling))
                           "1111111")
                (pab-check (quote lower-sid)
                           pab-lower-sid
                           (quote 00000000))
                (pab-check (quote upper-sid)
                           pab-upper-sid
                           (quote 11111111))
                (pab-check (quote lower-projection)
                           pab-lower-projection
                           (quote ()))
                (pab-check (quote upper-projection)
                           pab-upper-projection
                           (quote ()))
                (pab-check (quote projections-equal)
                           (equal? pab-lower-projection pab-upper-projection)
                           (quote (structural-relation same)))
                (pab-check (quote sid-identities-distinct)
                           (equal? pab-lower-sid pab-upper-sid)
                           (quote (structural-relation distinct)))
                (pab-check (quote scale-lower-anchor)
                           (pab-field pab-scale-boundary (quote lower-sid-anchor))
                           pab-lower-sid)
                (pab-check (quote scale-upper-anchor)
                           (pab-field pab-scale-boundary (quote upper-sid-anchor))
                           pab-upper-sid)
                (pab-check (quote sid-alias-forbidden)
                           (pab-field pab-laws (quote sid-alias))
                           (quote forbidden))
                (pab-check (quote other-sid-projection-forbidden)
                           (pab-field pab-laws (quote other-sid-ground-projection))
                           (quote forbidden))
                (pab-check (quote older-core-impact)
                           (pab-field pab-laws (quote core1-core2-core3-impact))
                           (quote none))))))
      (cond
        ((atom failure) (structural-kind empty-list)
         (quote (core4-predicate-answer-boundary-ok)))
        ((quote pab-contract-failure) pab-contract-failure
         failure)))))

(pab-verdict)
