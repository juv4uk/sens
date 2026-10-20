; Повні українські первинні визначення D9/D10 згідно з ратифікованою драбинoю.
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

(визначити створити-доведений
  (функція (твердження результати)
    (список (як-є proved) твердження результати)))

(визначити створити-невідоме
  (функція (предмет)
    (список (як-є unknown) предмет)))

(визначити створити-частковий
  (функція (значення межа)
    (список (як-є partial) значення межа)))

(визначити створити-заблокований
  (функція (причина)
    (список (як-є blocked) причина)))

(визначити створити-спірний
  (функція (доказ)
    (список (як-є disputed) доказ)))

(визначити створити-некоректний
  (функція (причина вміст)
    (список (як-є invalid) причина вміст)))

(визначити результат-позначений?
  (функція (результат)
    (за-умовою
      ((атом? результат) ні)
      ((тотожне? (перше результат) (як-є proved)) так)
      ((тотожне? (перше результат) (як-є unknown)) так)
      ((тотожне? (перше результат) (як-є partial)) так)
      ((тотожне? (перше результат) (як-є blocked)) так)
      ((тотожне? (перше результат) (як-є disputed)) так)
      ((тотожне? (перше результат) (як-є invalid)) так)
      (так ні))))

(визначити результат-стан
  (функція (результат)
    (за-умовою
      ((результат-позначений? результат) (перше результат))
      (так (як-є ())))))

(визначити результат-вміст
  (функція (результат)
    (за-умовою
      ((результат-позначений? результат) (решта результат))
      (так (як-є ())))))

; Proper-list validation follows the same atom-first shape as
; knowledge-proper-list?: `eq` is an atom operation, so a pair must never be
; passed to it merely to ask whether that pair is `()`.
(визначити результат-є-правильним-списком?
  (функція (значення)
    (за-умовою
      ((атом? значення)
       (за-умовою
         ((тотожне? значення (як-є ())) так)
         (так ні)))
      (так
       (результат-є-правильним-списком? (решта значення))))))

; The reserved negation head: `not?` (predicate spelling since #1444) or the
; historical `not`.
(визначити результат-не-є-головою-правила?
  (функція (голова)
    (за-умовою
      ((тотожне? голова (як-є not?)) так)
      ((тотожне? голова (як-є not)) так)
      (так ні))))

; Minimal standalone goal validation for the observation adapter. Ordinary
; predicate goals require a symbol head and a proper list. The one reserved
; logical shape, `(not? goal)`, additionally requires exactly one recursively
; valid nested goal, so malformed `(not?)` / `(not? a b)` cannot be mislabeled as
; logical `unknown`.
; Arity check uses exact D3 ATOM/CDR + D4 selector; no W8 / D6 LENGTH.
(визначити результат-ціль?
  (функція (ціль)
    (за-умовою
      ((атом? ціль) ні)
      ((хибне? (результат-є-правильним-списком? ціль)) ні)
      ((хибне? (символ? (перше ціль))) ні)
      ((результат-не-є-головою-правила? (перше ціль))
       (за-умовою
         ((атом? (решта ціль))
          (за-умовою
            ((атом? (решта-решти ціль)) (результат-ціль? (друге ціль)))
            (так ні)))
         (так ні)))
      (так так))))

; `(not? goal)` is the explicit logical opposite used by the knowledge layer.
; A well-shaped top-level negative query asks about its positive counterpart;
; every other goal gets wrapped in `not?`.
(визначити результат-заперечений-ціль?
  (функція (ціль)
    (за-умовою
      ((хибне? (результат-ціль? ціль)) ні)
      ((результат-не-є-головою-правила? (перше ціль)) так)
      (так ні))))

(визначити результат-протилежний-ціль
  (функція (ціль)
    (за-умовою
      ((результат-заперечений-ціль? ціль) (друге ціль))
      (так (список (як-є not?) ціль)))))

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
(визначити міркувати-спостерігати
  (функція (ціль правила-або-індекс)
    (за-умовою
      ((хибне? (результат-ціль? ціль))
       (створити-некоректний (як-є invalid-goal) ціль))
      (так
       (нехай-послідовно ((протилежне (результат-протилежний-ціль ціль))
              (індекс (забезпечити-індекс-міркування правила-або-індекс))
              (позитивні-результати (міркувати ціль індекс))
              (протилежні-результати (міркувати протилежне індекс)))
         (за-умовою
           ((за-умовою
              ((хибне? (атом? позитивні-результати))
               (хибне? (атом? протилежні-результати)))
              (так ні))
            (створити-спірний
              (список
                (створити-доведений ціль позитивні-результати)
                (створити-доведений протилежне протилежні-результати))))
           ((хибне? (атом? позитивні-результати))
            (створити-доведений ціль позитивні-результати))
           ((хибне? (атом? протилежні-результати))
            (створити-доведений протилежне протилежні-результати))
           (так (як-є ()))))))))

; Knowledge-module adapter. Validation precedes lookup: malformed input is an
; `invalid` observation even when the named module does not exist. If a
; well-formed module name is absent after scanning the concrete append-only
; knowledge journal, that absence is already established: reasoning is blocked
; by a known missing precondition rather than epistemically `unknown`.
(визначити міркувати-у-спостерігати
  (функція (назва-модуля ціль)
    (за-умовою
      ((хибне? (символ? назва-модуля))
       (створити-некоректний (як-є invalid-module) назва-модуля))
      ((хибне? (результат-ціль? ціль))
       (створити-некоректний (як-є invalid-goal) ціль))
      ((модуль-відомий? назва-модуля)
       (міркувати-спостерігати ціль (модуль-клаузи-зараз назва-модуля)))
      (так
       (створити-заблокований
         (список (як-є module-not-found) назва-модуля))))))


; Англійські сумісні входи посилаються на ті самі замикання.
; Це мовні проєкції D9/D10, а не нові функції та не SID8/Sens8.
(визначити make-proved створити-доведений)
(визначити make-unknown створити-невідоме)
(визначити make-partial створити-частковий)
(визначити make-blocked створити-заблокований)
(визначити make-disputed створити-спірний)
(визначити make-invalid створити-некоректний)
(визначити result-tagged? результат-позначений?)
(визначити result-status результат-стан)
(визначити result-payload результат-вміст)
(визначити result-proper-list? результат-є-правильним-списком?)
(визначити result-not-head? результат-не-є-головою-правила?)
(визначити result-goal? результат-ціль?)
(визначити result-negated-goal? результат-заперечений-ціль?)
(визначити result-opposite-goal результат-протилежний-ціль)
(визначити reason-observe міркувати-спостерігати)
(визначити reason-in-observe міркувати-у-спостерігати)
