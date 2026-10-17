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
; PredicateBit comes from exact D3:010 ATOM and D4:0100 NOT, not from
; synthetic EQ of quoted digit lists. TRUE = exact D1:1; FALSE = exact D1:0.
; No derived predicate constructor is required to represent one-bit truth.
; The D3:000 empty is data, never numeric zero.
; Two-field COND throughout.
; У exact-domain reader безумовний guard — канонічний однобітний D1:1.
; Width is identity; every bit of the domain address is valued.
; Current migration rule: every executable call whose ratified resident is in
; D9 uses that exact 9-bit identity below. Helpers not yet admitted to a
; callable D9-or-lower resident stay named and fail closed rather than being
; guessed into D7/D10 or a historical W8 slot.

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
      ((010 result) 0)
      ((101 (100 result) (001 proved)) 1)
      ((101 (100 result) (001 unknown)) 1)
      ((101 (100 result) (001 partial)) 1)
      ((101 (100 result) (001 blocked)) 1)
      ((101 (100 result) (001 disputed)) 1)
      ((101 (100 result) (001 invalid)) 1)
      (1 0))))

(0011 result-status
  (0010 (result)
    (110
      ((000000100 result) (100 result))
      (1 (001 ())))))

(0011 result-payload
  (0010 (result)
    (110
      ((000000100 result) (011 result))
      (1 (001 ())))))

; Proper-list validation follows the same atom-first shape as
; knowledge-proper-list?: `eq` is an atom operation, so a pair must never be
; passed to it merely to ask whether that pair is `()`.
(0011 result-proper-list?
  (0010 (value)
    (110
      ((010 value)
       (110
         ((101 value (001 ())) 1)
         (1 0)))
      (1
       (результат-є-правильним-списком? (решта value))))))

; The reserved negation head: `not?` (predicate spelling since #1444) or the
; historical `not`.
(0011 result-not-head?
  (0010 (head)
    (110
      ((101 head (001 not?)) 1)
      ((101 head (001 not)) 1)
      (1 0))))

; Minimal standalone goal validation for the observation adapter. Ordinary
; predicate goals require a symbol head and a proper list. The one reserved
; logical shape, `(not? goal)`, additionally requires exactly one recursively
; valid nested goal, so malformed `(not?)` / `(not? a b)` cannot be mislabeled as
; logical `unknown`.
; Arity check uses exact D3 ATOM/CDR + D4 selector; no W8 / D6 LENGTH.
(0011 result-goal?
  (0010 (goal)
    (110
      ((010 goal) 0)
      ((хибне? (результат-є-правильним-списком? goal)) 0)
      ((0100 (110101100 (100 goal))) 0)
      ((результат-не-є-головою-правила? (перше goal))
       (110
         ((010 (011 goal))
          (110
            ((010 (0111 goal)) (000011101 (1001 goal)))
            (1 0)))
         (1 0)))
      (1 1))))

; `(not? goal)` is the explicit logical opposite used by the knowledge layer.
; A well-shaped top-level negative query asks about its positive counterpart;
; every other goal gets wrapped in `not?`.
(0011 result-negated-goal?
  (0010 (goal)
    (110
      ((0100 (000011101 goal)) 0)
      ((результат-не-є-головою-правила? (перше goal)) 1)
      (1 0))))

(0011 result-opposite-goal
  (0010 (goal)
    (110
      ((000111010 goal) (1001 goal))
      (1 (1110 (001 not?) goal)))))

; Both positive and opposite queries use the already-ratified exact D9:101001110
; REASON entry, sharing one immutable reason-index. This removes two legacy
; unqualified depth=0 intermediates and a duplicated proof-engine call.
; Depth initialization remains owned by lib/reason.lisp and must be migrated
; separately under D24+ numeric law; do not rebrand host 0 as D1:NO.
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
      ((0100 (000011101 goal))
       (000001101 (001 invalid-goal) goal))
      (1
       (001001 ((opposite (000111110 goal))
              (index (reason-ensure-index rules-or-index))
              (positive-results (101001110 goal index))
              (opposite-results (101001110 opposite index)))
         (110
           ((110
              ((0100 (010 positive-results))
               (0100 (010 opposite-results)))
              (1 0))
            (000000111
              (1110
                (000111101 goal positive-results)
                (000111101 opposite opposite-results))))
           ((0100 (010 positive-results))
            (000111101 goal positive-results))
           ((0100 (010 opposite-results))
            (000111101 opposite opposite-results))
           (1 (001 ()))))))))

; Knowledge-module adapter. Validation precedes lookup: malformed input is an
; `invalid` observation even when the named module does not exist. If a
; well-formed module name is absent after scanning the concrete append-only
; knowledge journal, that absence is already established: reasoning is blocked
; by a known missing precondition rather than epistemically `unknown`.
(0011 reason-in-observe
  (0010 (module-name goal)
    (110
      ((0100 (110101100 module-name))
       (000001101 (001 invalid-module) module-name))
      ((0100 (000011101 goal))
       (000001101 (001 invalid-goal) goal))
      ((101010010 module-name)
       (000010000 goal (110000011 module-name)))
      (1
       (000100111
         (1110 (001 module-not-found) module-name))))))

; D9:000010000 REASON-OBSERVE and D9:000110100 REASON-IN-OBSERVE.
; Ukrainian SENS bindings to the existing source-owned reasoning laws.
; No direct D9 machine admission.
(0011 міркувати-спостерігати reason-observe)
(0011 міркувати-у-спостерігати reason-in-observe)
