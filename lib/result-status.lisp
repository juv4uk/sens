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
;
; Migrated predicate law: true = exact D1:1 (010 (001 ())); false = exact
; D1:0 (101 (001 (0)) (001 (1))). `()` is data only, never predicate false.
; Two-field COND throughout.
; Width is identity; every bit of the domain address is valued.

(0011 make-proved
  (0010 (statement results)
    (1110 (001 proved) statement results)))

(0011 make-unknown
  (0010 (subject)
    (1110 (001 unknown) subject)))

(0011 make-partial
  (0010 (value bound)
    (1110 (001 partial) value bound)))

(0011 make-blocked
  (0010 (reason)
    (1110 (001 blocked) reason)))

(0011 make-disputed
  (0010 (evidence)
    (1110 (001 disputed) evidence)))

(0011 make-invalid
  (0010 (reason payload)
    (1110 (001 invalid) reason payload)))

(0011 result-tagged?
  (0010 (result)
    (110
      ((010 result) (101 (001 (0)) (001 (1))))
      ((101 (100 result) (001 proved)) (010 (001 ())))
      ((101 (100 result) (001 unknown)) (010 (001 ())))
      ((101 (100 result) (001 partial)) (010 (001 ())))
      ((101 (100 result) (001 blocked)) (010 (001 ())))
      ((101 (100 result) (001 disputed)) (010 (001 ())))
      ((101 (100 result) (001 invalid)) (010 (001 ())))
      ((010 (001 ())) (101 (001 (0)) (001 (1)))))))

(0011 result-status
  (0010 (result)
    (110
      ((result-tagged? result) (100 result))
      ((010 (001 ())) (001 ())))))

(0011 result-payload
  (0010 (result)
    (110
      ((result-tagged? result) (011 result))
      ((010 (001 ())) (001 ())))))

; Proper-list validation follows the same atom-first shape as
; knowledge-proper-list?: `eq` is an atom operation, so a pair must never be
; passed to it merely to ask whether that pair is `()`.
(0011 result-proper-list?
  (0010 (value)
    (110
      ((010 value)
       (110
         ((101 value (001 ())) (010 (001 ())))
         ((010 (001 ())) (101 (001 (0)) (001 (1))))))
      ((010 (001 ()))
       (result-proper-list? (011 value))))))

; The reserved negation head: `not?` (predicate spelling since #1444) or the
; historical `not`.
(0011 result-not-head?
  (0010 (head)
    (110
      ((101 head (001 not?)) (010 (001 ())))
      ((101 head (001 not)) (010 (001 ())))
      ((010 (001 ())) (101 (001 (0)) (001 (1)))))))

; Minimal standalone goal validation for the observation adapter. Ordinary
; predicate goals require a symbol head and a proper list. The one reserved
; logical shape, `(not? goal)`, additionally requires exactly one recursively
; valid nested goal, so malformed `(not?)` / `(not? a b)` cannot be mislabeled as
; logical `unknown`.
; Arity check uses exact D3 ATOM/CDR + D4 selector; no W8 / D6 LENGTH.
(0011 result-goal?
  (0010 (goal)
    (110
      ((010 goal) (101 (001 (0)) (001 (1))))
      ((0100 (result-proper-list? goal)) (101 (001 (0)) (001 (1))))
      ((0100 (110101100 (100 goal))) (101 (001 (0)) (001 (1))))
      ((result-not-head? (100 goal))
       (110
         ((010 (011 goal))
          (110
            ((010 (011 (011 goal))) (result-goal? (1001 goal)))
            ((010 (001 ())) (101 (001 (0)) (001 (1))))))
         ((010 (001 ())) (101 (001 (0)) (001 (1))))))
      ((010 (001 ())) (010 (001 ()))))))

; `(not? goal)` is the explicit logical opposite used by the knowledge layer.
; A well-shaped top-level negative query asks about its positive counterpart;
; every other goal gets wrapped in `not?`.
(0011 result-negated-goal?
  (0010 (goal)
    (110
      ((0100 (result-goal? goal)) (101 (001 (0)) (001 (1))))
      ((result-not-head? (100 goal)) (010 (001 ())))
      ((010 (001 ())) (101 (001 (0)) (001 (1)))))))

(0011 result-opposite-goal
  (0010 (goal)
    (110
      ((result-negated-goal? goal) (1001 goal))
      ((010 (001 ())) (1110 (001 not?) goal)))))

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
(0011 reason-observe
  (0010 (goal rules-or-index)
    (110
      ((0100 (result-goal? goal))
       (make-invalid (001 invalid-goal) goal))
      ((010 (001 ()))
       (001001 ((opposite (result-opposite-goal goal))
              (index (reason-ensure-index rules-or-index))
              (positive-results
                (101011011
                  goal
                  (reason-index-candidates goal index)
                  (001 ())
                  index
                  0))
              (opposite-results
                (101011011
                  opposite
                  (reason-index-candidates opposite index)
                  (001 ())
                  index
                  0)))
         (110
           ((110
              ((110111011 (010 positive-results))
               (110111011 (010 opposite-results)))
              ((010 (001 ())) (101 (001 (0)) (001 (1)))))
            (make-disputed
              (1110
                (make-proved goal positive-results)
                (make-proved opposite opposite-results))))
           ((110111011 (010 positive-results))
            (make-proved goal positive-results))
           ((110111011 (010 opposite-results))
            (make-proved opposite opposite-results))
           ((010 (001 ())) (001 ())))))))))

; Knowledge-module adapter. Validation precedes lookup: malformed input is an
; `invalid` observation even when the named module does not exist. If a
; well-formed module name is absent after scanning the concrete append-only
; knowledge journal, that absence is already established: reasoning is blocked
; by a known missing precondition rather than epistemically `unknown`.
(0011 reason-in-observe
  (0010 (module-name goal)
    (110
      ((0100 (110101100 module-name))
       (make-invalid (001 invalid-module) module-name))
      ((0100 (result-goal? goal))
       (make-invalid (001 invalid-goal) goal))
      ((101010010 module-name)
       (reason-observe goal (110000011 module-name)))
      ((010 (001 ()))
       (make-blocked
         (1110 (001 module-not-found) module-name))))))
