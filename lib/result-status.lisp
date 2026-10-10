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

(00001001 make-proved
  (00001000 (statement results)
    (00100111 (00000001 proved) statement results)))

(00001001 make-unknown
  (00001000 (subject)
    (00100111 (00000001 unknown) subject)))

(00001001 make-partial
  (00001000 (value bound)
    (00100111 (00000001 partial) value bound)))

(00001001 make-blocked
  (00001000 (reason)
    (00100111 (00000001 blocked) reason)))

(00001001 make-disputed
  (00001000 (evidence)
    (00100111 (00000001 disputed) evidence)))

(00001001 make-invalid
  (00001000 (reason payload)
    (00100111 (00000001 invalid) reason payload)))

; Contract 11.8 incremental migration (#5029): the shape/classifier layer below
; returns exact D1 PredicateBit for predicates (1 YES, 0 NO); a bare () is
; structural data, never a predicate or truthiness fallback. D3 ATOM/CONS/EQ
; are used as exact-D1 producers at the historical mechanism boundary.
; Remaining higher-level reasoning clauses are held for independent migration.

(00001001 result-tagged?
  (00001000 (result)
    (00000111
      ((00000010 result) (00000010 (00000100 (00000001 ()) (00000001 ()))))
      ((00000011 (00000101 result) (00000001 proved)) (00000010 (00000001 ())))
      ((00000011 (00000101 result) (00000001 unknown)) (00000010 (00000001 ())))
      ((00000011 (00000101 result) (00000001 partial)) (00000010 (00000001 ())))
      ((00000011 (00000101 result) (00000001 blocked)) (00000010 (00000001 ())))
      ((00000011 (00000101 result) (00000001 disputed)) (00000010 (00000001 ())))
      ((00000011 (00000101 result) (00000001 invalid)) (00000010 (00000001 ())))
      ((00000010 (00000001 ())) (00000010 (00000100 (00000001 ()) (00000001 ())))))))

(00001001 result-status
  (00001000 (result)
    (00000111
      ((result-tagged? result) (00000101 result))
      ((00000010 (00000001 ())) (00000001 ())))))

(00001001 result-payload
  (00001000 (result)
    (00000111
      ((result-tagged? result) (00000110 result))
      ((00000010 (00000001 ())) (00000001 ())))))

; Proper-list validation follows the same atom-first shape as
; knowledge-proper-list?: `eq` is an atom operation, so a pair must never be
; passed to it merely to ask whether that pair is `()`.
(00001001 result-proper-list?
  (00001000 (value)
    (00000111
      ((00000010 value) (00000011 value (00000001 ())))
      ((00000010 (00000001 ())) (result-proper-list? (00000110 value))))))

; The reserved negation head: `not?` (predicate spelling since #1444) or the
; historical `not`.
(00001001 result-not-head?
  (00001000 (head)
    (00000111
      ((00000011 head (00000001 not?)) (00000010 (00000001 ())))
      ((00000011 head (00000001 not)) (00000010 (00000001 ())))
      ((00000010 (00000001 ())) (00000010 (00000100 (00000001 ()) (00000001 ())))))))

; Minimal standalone goal validation for the observation adapter. Ordinary
; predicate goals require a symbol head and a proper list. The one reserved
; logical shape, `(not? goal)`, additionally requires exactly one recursively
; valid nested goal, so malformed `(not?)` / `(not? a b)` cannot be mislabeled as
; logical `unknown`.
(00001001 result-goal?
  (00001000 (goal)
    (00000111
      ((00000010 goal) () (00000001 ()))
      ((00000010 goal) (1) (00000001 ()))
      ((00100001 (result-proper-list? goal)) (00000001 ()))
      ((00100001 (00100011 (00000101 goal))) (00000001 ()))
      ((result-not-head? (00000101 goal))
       (00000111
         ((00011100 (00101000 goal) 2) 1 (result-goal? (00101111 goal)))
         ((00011100 (00101000 goal) 2) 0 (00000001 ()))))
      (t t))))

; `(not? goal)` is the explicit logical opposite used by the knowledge layer.
; A well-shaped top-level negative query asks about its positive counterpart;
; every other goal gets wrapped in `not?`.
(00001001 result-negated-goal?
  (00001000 (goal)
    (00000111
      ((00100001 (result-goal? goal)) (00000001 ()))
      ((result-not-head? (00000101 goal)) t)
      (t (00000001 ())))))

(00001001 result-opposite-goal
  (00001000 (goal)
    (00000111
      ((result-negated-goal? goal) (00101111 goal))
      (t (00100111 (00000001 not?) goal)))))

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
(00001001 reason-observe
  (00001000 (goal rules-or-index)
    (00000111
      ((00100001 (result-goal? goal))
       (make-invalid (00000001 invalid-goal) goal))
      (t
       (10011101 ((opposite (result-opposite-goal goal))
              (index (reason-ensure-index rules-or-index))
              (positive-results
                (10000000
                  goal
                  (reason-index-candidates goal index)
                  (00000001 ())
                  index
                  0))
              (opposite-results
                (10000000
                  opposite
                  (reason-index-candidates opposite index)
                  (00000001 ())
                  index
                  0)))
         (00000111
           ((10011010 (10110001 (00000010 positive-results))
                 (10110001 (00000010 opposite-results)))
            (make-disputed
              (00100111
                (make-proved goal positive-results)
                (make-proved opposite opposite-results))))
           ((10110001 (00000010 positive-results))
            (make-proved goal positive-results))
           ((10110001 (00000010 opposite-results))
            (make-proved opposite opposite-results))
           (t (00000001 ()))))))))

; Knowledge-module adapter. Validation precedes lookup: malformed input is an
; `invalid` observation even when the named module does not exist. If a
; well-formed module name is absent after scanning the concrete append-only
; knowledge journal, that absence is already established: reasoning is blocked
; by a known missing precondition rather than epistemically `unknown`.
(00001001 reason-in-observe
  (00001000 (module-name goal)
    (00000111
      ((00100001 (00100011 module-name))
       (make-invalid (00000001 invalid-module) module-name))
      ((00100001 (result-goal? goal))
       (make-invalid (00000001 invalid-goal) goal))
      ((01111110 module-name)
       (reason-observe goal (01111111 module-name)))
      (t
       (make-blocked
         (00100111 (00000001 module-not-found) module-name))))))
