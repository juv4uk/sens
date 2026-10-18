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

(визначити make-observation створити-спостереження)

; D10:0001110110 — компактне ук та повне укр посилаються на той самий SENS closure.
(визначити створити-структуроване-твердження створити-твердження)
(визначити make-claim створити-структуроване-твердження)

(визначити make-evidence створити-доказ)

(визначити make-intent створити-намір)

; --- Shape predicates ---------------------------------------------------
; Exact D1 shape predicates: source-ref?, epistemic--claim-ref?, observation?,
; claim?, evidence?, intent?. Atomic tags are checked before D3:101 EQ.

(визначити source-ref?
  (функція (value)
    (за-умовою
      ((атом? value) #d1:0)
      ((атом? (решта value)) #d1:0)
      ((хибне? (атом? (перше value))) #d1:0)
      ((тотожне? (перше value) (001 digest)) #d1:1)
      ((тотожне? (перше value) (001 proof)) #d1:1)
      ((тотожне? (перше value) (001 test)) #d1:1)
      ((тотожне? (перше value) (001 observation)) #d1:1)
      (#d1:1 #d1:0))))

; D10:0010011001 SOURCE-REF? — точна повна українська peer-назва.
(визначити це-належне-посилання-на-джерело? source-ref?)

(визначити epistemic--claim-ref?
  (функція (value)
    (за-умовою
      ((атом? value) #d1:0)
      ((атом? (решта value)) #d1:0)
      ((хибне? (атом? (перше value))) #d1:0)
      ((тотожне? (перше value) (001 claim-ref)) #d1:1)
      (#d1:1 #d1:0))))

(визначити observation? спостереження?)

(визначити claim? твердження?)

(визначити evidence? доказ?)

(визначити intent? намір?)

; --- Accessors ------------------------------------------------------------
; Reuse existing project selectors (1001 / 11100) already admitted in Core.

(визначити claim-statement (функція (claim) (друге (11100 (001 statement) (решта claim)))))
(визначити claim-review (функція (claim) (друге (11100 (001 review) (решта claim)))))
(визначити evidence-outcome (функція (evidence) (друге (11100 (001 outcome) (решта evidence)))))
(визначити evidence-source-ref (функція (evidence) (друге (11100 (001 source-ref) (решта evidence)))))
(визначити intent-goal (функція (intent) (друге (11100 (001 goal) (решта intent)))))

(визначити observation-source (функція (observation) (друге (11100 (001 source) (решта observation)))))
(визначити отримати-джерело-спостереження observation-source)
(визначити observation-statement (функція (observation) (друге (11100 (001 statement) (решта observation)))))
(визначити evidence-claim-ref (функція (evidence) (друге (11100 (001 claim-ref) (решта evidence)))))
(визначити отримати-посилання-доказу-на-твердження evidence-claim-ref)
(визначити evidence-method (функція (evidence) (друге (11100 (001 method) (решта evidence)))))
(визначити intent-requires (функція (intent) (друге (11100 (001 requires) (решта intent)))))
(визначити отримати-необхідні-можливості-наміру intent-requires)
(визначити intent-stop-on (функція (intent) (друге (11100 (001 stop-on) (решта intent)))))
(визначити intent-produces (функція (intent) (друге (11100 (001 produces) (решта intent)))))

; --- Narrow relations -------------------------------------------------
; Точна структурна рівність посилань — похідна Lisp-функція.
; EQ отримує лише атоми, CAR/CDR — лише пари, COND — тільки D1.

(визначити епістеміка--рівні-посилання?
  (функція (a b)
    (за-умовою
      ((атом? a)
       (за-умовою
         ((атом? b) (тотожне? a b))
         (#d1:1 #d1:0)))
      ((атом? b) #d1:0)
      ((епістеміка--рівні-посилання? (перше a) (перше b))
       (епістеміка--рівні-посилання? (решта a) (решта b)))
      (#d1:1 #d1:0))))

; supporting-evidence returns () or the matching evidence record itself
; (retrieval, not a collapsed flag). Reuses evidence? / claim-ref helpers.
(визначити supporting-evidence
  (функція (evidence claim-ref)
    (за-умовою
      ((хибне? (доказ? evidence)) (як-є ()))
      ((хибне? (epistemic--claim-ref? claim-ref)) (001 ()))
      ((хибне? (тотожне? (доказ-підсумок evidence) (як-є supports))) (як-є ()))
      ((хибне? (епістеміка--рівні-посилання? (отримати-посилання-доказу-на-твердження evidence) claim-ref)) (як-є ()))
      (#d1:1 evidence))))

; D9:101100001 — той самий retrieval closure, без нової семантики.
(визначити підтверджувальний-доказ supporting-evidence)

(визначити epistemic--all-required-present?
  (функція (requirements effective-capabilities)
    (за-умовою
      ((атом? requirements) #d1:1)
      ((хибне? (11101 (перше requirements) effective-capabilities)) #d1:0)
      (#d1:1
       (epistemic--all-required-present? (решта requirements) effective-capabilities)))))

(визначити intent-capabilities-satisfied?
  (функція (intent effective-capabilities)
    (за-умовою
      ((хибне? (намір? intent)) ні)
      (#d1:1
       (epistemic--all-required-present? (отримати-необхідні-можливості-наміру intent) effective-capabilities)))))

; D10:0001111110 INTENT-CAPABILITIES-SATISFIED? — один мовний закон, дві peer-форми.
(визначити усі-необхідні-можливості-наміру-забезпечені? intent-capabilities-satisfied?)
