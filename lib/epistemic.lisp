; epistemic.lisp — opt-in proof-of-expression / epistemic-status data layer:
; observation/claim/evidence/intent shapes, a tagged source-ref, and the
; narrow relations supporting-evidence and intent-capabilities-satisfied?.
; Design reconciled against the live codebase in an earlier design-only
; session (verdict: EXPRESSIBLE AS-IS — no kernel/evaluator change, no
; language-contract.lisp change); this file is that design's Phase 2
; implementation. Source docs (untracked drafts, read verbatim before
; writing this file):
;   docs/Контекст парадигми для  v0.md
;   docs/Brief для  v0.md
;   docs/_v0_ мінімальна специфікація proof-of-expression.md
; Not loaded by lib/core.lisp and not wired into reason.lisp/knowledge.lisp/
; world.lisp — same opt-in precedent as lib/result-status.lisp (see that
; file's header and docs/adr/unknown-result-semantics.md). Does not
; execute intent, touch network/process, write to World, admit a claim
; as fact, or change reason.lisp/forward.lisp return values.
;
; Точне D1:YES — #d1:1; без зайвого ATOM(QUOTE empty).
; False carriers use (001 ()). Two-field COND. Reuses existing CAR/CDR/
; EQ/ATOM discipline and project accessors. Width is identity.

; --- Constructors (Spec §6 exact arg order) ---------------------------
; Точні D10 українські SENS-функції визначено один раз у lib/core4.lisp.
; Ці історичні англійські поверхні — aliases, не повторні реалізації.
; D10 resident coordinate не означає допуск машинної інструкції.

(0011 make-observation створити-спостереження)

; D10:0001110110 — компактне ук та повне укр посилаються на той самий SENS closure.
(визначити створити-структуроване-твердження створити-твердження)
(визначити make-claim створити-структуроване-твердження)

(0011 make-evidence створити-доказ)

(0011 make-intent створити-намір)

; --- Shape predicates ---------------------------------------------------
; Exact D1 shape predicates: source-ref?, epistemic--claim-ref?, observation?,
; claim?, evidence?, intent?. Atomic tags are checked before D3:101 EQ.

(0011 source-ref?
  (0010 (value)
    (110
      ((010 value) #d1:0)
      ((010 (011 value)) #d1:0)
      ((0100 (010 (100 value))) #d1:0)
      ((101 (100 value) (001 digest)) #d1:1)
      ((101 (100 value) (001 proof)) #d1:1)
      ((101 (100 value) (001 test)) #d1:1)
      ((101 (100 value) (001 observation)) #d1:1)
      (#d1:1 #d1:0))))

; D10:0010011001 SOURCE-REF? — точна повна українська peer-назва.
(визначити це-належне-посилання-на-джерело? source-ref?)

(0011 epistemic--claim-ref?
  (0010 (value)
    (110
      ((010 value) #d1:0)
      ((010 (011 value)) #d1:0)
      ((0100 (010 (100 value))) #d1:0)
      ((101 (100 value) (001 claim-ref)) #d1:1)
      (#d1:1 #d1:0))))

(0011 observation? спостереження?)

(0011 claim? твердження?)

(0011 evidence? доказ?)

(0011 intent? намір?)

; --- Accessors ------------------------------------------------------------
; Reuse existing project selectors (1001 / 11100) already admitted in Core.

(0011 claim-statement (0010 (claim) (1001 (11100 (001 statement) (011 claim)))))
(0011 claim-review (0010 (claim) (1001 (11100 (001 review) (011 claim)))))
(0011 evidence-outcome (0010 (evidence) (1001 (11100 (001 outcome) (011 evidence)))))
(0011 evidence-source-ref (0010 (evidence) (1001 (11100 (001 source-ref) (011 evidence)))))
(0011 intent-goal (0010 (intent) (1001 (11100 (001 goal) (011 intent)))))

(0011 observation-source (0010 (observation) (1001 (11100 (001 source) (011 observation)))))
(визначити отримати-джерело-спостереження observation-source)
(0011 observation-statement (0010 (observation) (1001 (11100 (001 statement) (011 observation)))))
(0011 evidence-claim-ref (0010 (evidence) (1001 (11100 (001 claim-ref) (011 evidence)))))
(визначити отримати-посилання-доказу-на-твердження evidence-claim-ref)
(0011 evidence-method (0010 (evidence) (1001 (11100 (001 method) (011 evidence)))))
(0011 intent-requires (0010 (intent) (1001 (11100 (001 requires) (011 intent)))))
(визначити отримати-необхідні-можливості-наміру intent-requires)
(0011 intent-stop-on (0010 (intent) (1001 (11100 (001 stop-on) (011 intent)))))
(0011 intent-produces (0010 (intent) (1001 (11100 (001 produces) (011 intent)))))

; --- Narrow relations -------------------------------------------------
; Точна структурна рівність посилань — похідна Lisp-функція.
; EQ отримує лише атоми, CAR/CDR — лише пари, COND — тільки D1.

(0011 епістеміка--рівні-посилання?
  (0010 (a b)
    (110
      ((010 a)
       (110
         ((010 b) (101 a b))
         (#d1:1 #d1:0)))
      ((010 b) #d1:0)
      ((епістеміка--рівні-посилання? (100 a) (100 b))
       (епістеміка--рівні-посилання? (011 a) (011 b)))
      (#d1:1 #d1:0))))

; supporting-evidence returns () or the matching evidence record itself
; (retrieval, not a collapsed flag). Reuses evidence? / claim-ref helpers.
(0011 supporting-evidence
  (0010 (evidence claim-ref)
    (110
      ((хибне? (доказ? evidence)) (як-є ()))
      ((0100 (epistemic--claim-ref? claim-ref)) (001 ()))
      ((хибне? (тотожне? (доказ-підсумок evidence) (як-є supports))) (як-є ()))
      ((хибне? (епістеміка--рівні-посилання? (отримати-посилання-доказу-на-твердження evidence) claim-ref)) (як-є ()))
      (#d1:1 evidence))))

; D9:101100001 — той самий retrieval closure, без нової семантики.
(визначити підтверджувальний-доказ supporting-evidence)

(0011 epistemic--all-required-present?
  (0010 (requirements effective-capabilities)
    (110
      ((010 requirements) #d1:1)
      ((0100 (11101 (100 requirements) effective-capabilities)) #d1:0)
      (#d1:1
       (epistemic--all-required-present? (011 requirements) effective-capabilities)))))

(0011 intent-capabilities-satisfied?
  (0010 (intent effective-capabilities)
    (110
      ((хибне? (намір? intent)) ні)
      (#d1:1
       (epistemic--all-required-present? (отримати-необхідні-можливості-наміру intent) effective-capabilities)))))

; D10:0001111110 INTENT-CAPABILITIES-SATISFIED? — один мовний закон, дві peer-форми.
(визначити усі-необхідні-можливості-наміру-забезпечені? intent-capabilities-satisfied?)
