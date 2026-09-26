; result-status.lisp — canonical data-only reasoning outcome algebra.
; This module adds no exception mechanism and no new runtime Value variant.
; Ordinary `reason` / `reason-in` keep their historical return values for
; compatibility; `reason-observe` / `reason-in-observe` opt into explicit
; epistemic outcomes without discarding proof alternatives.
;
; Canonical shapes:
;   (proved statement results)
;   (unknown subject)
;   (partial value bound)
;   (blocked reason)
;   (disputed evidence)
;   (invalid reason payload)

(def make-proved
  (lambda (statement results)
    (list (quote proved) statement results)))

(def make-unknown
  (lambda (subject)
    (list (quote unknown) subject)))

(def make-partial
  (lambda (value bound)
    (list (quote partial) value bound)))

(def make-blocked
  (lambda (reason)
    (list (quote blocked) reason)))

(def make-disputed
  (lambda (evidence)
    (list (quote disputed) evidence)))

(def make-invalid
  (lambda (reason payload)
    (list (quote invalid) reason payload)))

(def result-tagged?
  (lambda (result)
    (cond
      ((atom? result) () (quote ()))
      ((atom? result) (1) (quote ()))
      ((eq? (car result) (quote proved)) t)
      ((eq? (car result) (quote unknown)) t)
      ((eq? (car result) (quote partial)) t)
      ((eq? (car result) (quote blocked)) t)
      ((eq? (car result) (quote disputed)) t)
      ((eq? (car result) (quote invalid)) t)
      (t (quote ())))))

(def result-status
  (lambda (result)
    (cond
      ((result-tagged? result) (car result))
      (t (quote ())))))

(def result-payload
  (lambda (result)
    (cond
      ((result-tagged? result) (cdr result))
      (t (quote ())))))

; Proper-list validation follows the same atom-first shape as
; knowledge-proper-list?: `eq` is an atom operation, so a pair must never be
; passed to it merely to ask whether that pair is `()`.
(def result-proper-list?
  (lambda (value)
    (cond
      ((atom? value) () (cond
         ((eq? value (quote ())) t)
         (t (quote ()))))
      ((atom? value) (1) (cond
         ((eq? value (quote ())) t)
         (t (quote ()))))
      (t (result-proper-list? (cdr value))))))

; Minimal standalone goal validation for the observation adapter. Ordinary
; predicate goals require a symbol head and a proper list. The one reserved
; logical shape, `(not goal)`, additionally requires exactly one recursively
; valid nested goal, so malformed `(not)` / `(not a b)` cannot be mislabeled as
; logical `unknown`.
(def result-goal?
  (lambda (goal)
    (cond
      ((atom? goal) () (quote ()))
      ((atom? goal) (1) (quote ()))
      ((not? (result-proper-list? goal)) (quote ()))
      ((not? (symbol? (car goal))) (quote ()))
      ((eq? (car goal) (quote not))
       (cond
         ((= (length goal) 2) 1 (result-goal? (second goal)))
         ((= (length goal) 2) 0 (quote ()))))
      (t t))))

; `(not goal)` is the explicit logical opposite used by the knowledge layer.
; A well-shaped top-level negative query asks about its positive counterpart;
; every other goal gets wrapped in `not`.
(def result-negated-goal?
  (lambda (goal)
    (cond
      ((not? (result-goal? goal)) (quote ()))
      ((eq? (car goal) (quote not)) t)
      (t (quote ())))))

(def result-opposite-goal
  (lambda (goal)
    (cond
      ((result-negated-goal? goal) (second goal))
      (t (list (quote not) goal)))))

; Observe one reasoning question without information collapse.
; - positive proof(s) => proved(goal, all-results)
; - only explicit opposite proof(s) => proved(opposite, all-results)
; - both => disputed(two proved observations)
; - neither => () unless a separate named contract positively establishes a
;              richer epistemic status such as unknown.
;
; `rules-or-index` may be the historical rule list or an explicitly prepared
; immutable `reason-index/1`. Positive and opposite observations share that one
; finite snapshot. Plain callers still build exactly one index per observation;
; repeated-query callers may retain the prepared index themselves. There is no
; hidden cache or invalidation policy: a retained index continues to represent
; the exact rules captured when it was built.
(def reason-observe
  (lambda (goal rules-or-index)
    (cond
      ((not? (result-goal? goal))
       (make-invalid (quote invalid-goal) goal))
      (t
       (let* ((opposite (result-opposite-goal goal))
              (index (reason-ensure-index rules-or-index))
              (positive-results
                (prove-goal
                  goal
                  (reason-index-candidates goal index)
                  (quote ())
                  index
                  0))
              (opposite-results
                (prove-goal
                  opposite
                  (reason-index-candidates opposite index)
                  (quote ())
                  index
                  0)))
         (cond
           ((and (10110001 (00000010 positive-results))
                 (10110001 (00000010 opposite-results)))
            (make-disputed
              (list
                (make-proved goal positive-results)
                (make-proved opposite opposite-results))))
           ((10110001 (00000010 positive-results))
            (make-proved goal positive-results))
           ((10110001 (00000010 opposite-results))
            (make-proved opposite opposite-results))
           (t (quote ()))))))))

; Knowledge-module adapter. Validation precedes lookup: malformed input is an
; `invalid` observation even when the named module does not exist. If a
; well-formed module name is absent after scanning the concrete append-only
; knowledge journal, that absence is already established: reasoning is blocked
; by a known missing precondition rather than epistemically `unknown`.
(def reason-in-observe
  (lambda (module-name goal)
    (cond
      ((not? (symbol? module-name))
       (make-invalid (quote invalid-module) module-name))
      ((not? (result-goal? goal))
       (make-invalid (quote invalid-goal) goal))
      ((module-known? module-name)
       (reason-observe goal (module-clauses-now module-name)))
      (t
       (make-blocked
         (list (quote module-not-found) module-name))))))
