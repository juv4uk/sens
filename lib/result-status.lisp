; SOURCE UKR: лише ратифіковані D1/D3–D6 і підтверджені D9 peer-виклики.
; Три D9 без доказу викличного укр closure збережені як точні бітові голови:
; 101001110 (reason), 101010010 (module-known?), 110000011 (module-clauses-now).
; Код висновків, теги цитованих даних і історичні публічні назви незмінні.

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

(визначити make-proved
  (функція (statement results)
    (список (як-є proved) statement results)))

(визначити make-unknown
  (функція (subject)
    (список (як-є unknown) subject)))

(визначити make-partial
  (функція (value bound)
    (список (як-є partial) value bound)))

(визначити make-blocked
  (функція (reason)
    (список (як-є blocked) reason)))

(визначити make-disputed
  (функція (evidence)
    (список (як-є disputed) evidence)))

(визначити make-invalid
  (функція (reason payload)
    (список (як-є invalid) reason payload)))

(визначити result-tagged?
  (функція (result)
    (за-умовою
      ((атом? result) ні)
      ((тотожне? (перше result) (як-є proved)) так)
      ((тотожне? (перше result) (як-є unknown)) так)
      ((тотожне? (перше result) (як-є partial)) так)
      ((тотожне? (перше result) (як-є blocked)) так)
      ((тотожне? (перше result) (як-є disputed)) так)
      ((тотожне? (перше result) (як-є invalid)) так)
      (так ні))))

(визначити result-status
  (функція (result)
    (за-умовою
      ((результат-позначений? result) (перше result))
      (так (як-є ())))))

(визначити result-payload
  (функція (result)
    (за-умовою
      ((результат-позначений? result) (решта result))
      (так (як-є ())))))

; Proper-list validation follows the same atom-first shape as
; knowledge-proper-list?: `eq` is an atom operation, so a pair must never be
; passed to it merely to ask whether that pair is `()`.
(визначити result-proper-list?
  (функція (value)
    (за-умовою
      ((атом? value)
       (за-умовою
         ((тотожне? value (як-є ())) так)
         (так ні)))
      (так
       (результат-є-правильним-списком? (решта value))))))

; The reserved negation head: `not?` (predicate spelling since #1444) or the
; historical `not`.
(визначити result-not-head?
  (функція (head)
    (за-умовою
      ((тотожне? head (як-є not?)) так)
      ((тотожне? head (як-є not)) так)
      (так ні))))

; Minimal standalone goal validation for the observation adapter. Ordinary
; predicate goals require a symbol head and a proper list. The one reserved
; logical shape, `(not? goal)`, additionally requires exactly one recursively
; valid nested goal, so malformed `(not?)` / `(not? a b)` cannot be mislabeled as
; logical `unknown`.
; Arity check uses exact D3 ATOM/CDR + D4 selector; no W8 / D6 LENGTH.
(визначити result-goal?
  (функція (goal)
    (за-умовою
      ((атом? goal) ні)
      ((хибне? (результат-є-правильним-списком? goal)) ні)
      ((хибне? (символ? (перше goal))) ні)
      ((результат-не-є-головою-правила? (перше goal))
       (за-умовою
         ((атом? (решта goal))
          (за-умовою
            ((атом? (решта-решти goal)) (результат-ціль? (друге goal)))
            (так ні)))
         (так ні)))
      (так так))))

; `(not? goal)` is the explicit logical opposite used by the knowledge layer.
; A well-shaped top-level negative query asks about its positive counterpart;
; every other goal gets wrapped in `not?`.
(визначити result-negated-goal?
  (функція (goal)
    (за-умовою
      ((хибне? (результат-ціль? goal)) ні)
      ((результат-не-є-головою-правила? (перше goal)) так)
      (так ні))))

(визначити result-opposite-goal
  (функція (goal)
    (за-умовою
      ((результат-заперечений-ціль? goal) (друге goal))
      (так (список (як-є not?) goal)))))

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
(визначити reason-observe
  (функція (goal rules-or-index)
    (за-умовою
      ((хибне? (результат-ціль? goal))
       (створити-некоректний (як-є invalid-goal) goal))
      (так
       (нехай-послідовно ((opposite (результат-протилежний-ціль goal))
              (index (reason-ensure-index rules-or-index))
              (positive-results (101001110 goal index))
              (opposite-results (101001110 opposite index)))
         (за-умовою
           ((за-умовою
              ((хибне? (атом? positive-results))
               (хибне? (атом? opposite-results)))
              (так ні))
            (створити-спірний
              (список
                (створити-доведений goal positive-results)
                (створити-доведений opposite opposite-results))))
           ((хибне? (атом? positive-results))
            (створити-доведений goal positive-results))
           ((хибне? (атом? opposite-results))
            (створити-доведений opposite opposite-results))
           (так (як-є ()))))))))

; Knowledge-module adapter. Validation precedes lookup: malformed input is an
; `invalid` observation even when the named module does not exist. If a
; well-formed module name is absent after scanning the concrete append-only
; knowledge journal, that absence is already established: reasoning is blocked
; by a known missing precondition rather than epistemically `unknown`.
(визначити reason-in-observe
  (функція (module-name goal)
    (за-умовою
      ((хибне? (символ? module-name))
       (створити-некоректний (як-є invalid-module) module-name))
      ((хибне? (результат-ціль? goal))
       (створити-некоректний (як-є invalid-goal) goal))
      ((101010010 module-name)
       (міркувати-спостерігати goal (110000011 module-name)))
      (так
       (створити-заблокований
         (список (як-є module-not-found) module-name))))))

; D9:000010000 REASON-OBSERVE and D9:000110100 REASON-IN-OBSERVE.
; Ukrainian SENS bindings to the existing source-owned reasoning laws.
; No direct D9 machine admission.
(визначити міркувати-спостерігати reason-observe)
(визначити міркувати-у-спостерігати reason-in-observe)
