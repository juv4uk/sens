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
  (функція (значення)
    (за-умовою
      ((атом? значення) ні)
      ((атом? (решта значення)) ні)
      ((хибне? (атом? (перше значення))) ні)
      ((тотожне? (перше значення) (як-є digest)) так)
      ((тотожне? (перше значення) (як-є proof)) так)
      ((тотожне? (перше значення) (як-є test)) так)
      ((тотожне? (перше значення) (як-є observation)) так)
      (так ні))))

; D10:0010011001 SOURCE-REF? — точна повна українська peer-назва.
(визначити це-належне-посилання-на-джерело? source-ref?)

(визначити epistemic--claim-ref?
  (функція (значення)
    (за-умовою
      ((атом? значення) ні)
      ((атом? (решта значення)) ні)
      ((хибне? (атом? (перше значення))) ні)
      ((тотожне? (перше значення) (як-є claim-ref)) так)
      (так ні))))

(визначити observation? спостереження?)

(визначити claim? твердження?)

(визначити evidence? доказ?)

(визначити intent? намір?)

; --- Accessors ------------------------------------------------------------
; Reuse existing project selectors (1001 / 11100) already admitted in Core.

(визначити claim-statement (функція (твердження) (друге (знайти-за-ключем (як-є statement) (решта твердження)))))
(визначити claim-review (функція (твердження) (друге (знайти-за-ключем (як-є review) (решта твердження)))))
(визначити evidence-outcome (функція (доказ) (друге (знайти-за-ключем (як-є outcome) (решта доказ)))))
(визначити evidence-source-ref (функція (доказ) (друге (знайти-за-ключем (як-є source-ref) (решта доказ)))))
(визначити intent-goal (функція (намір) (друге (знайти-за-ключем (як-є goal) (решта намір)))))

(визначити observation-source (функція (спостереження) (друге (знайти-за-ключем (як-є source) (решта спостереження)))))
(визначити отримати-джерело-спостереження observation-source)
(визначити observation-statement (функція (спостереження) (друге (знайти-за-ключем (як-є statement) (решта спостереження)))))
(визначити evidence-claim-ref (функція (доказ) (друге (знайти-за-ключем (як-є claim-ref) (решта доказ)))))
(визначити отримати-посилання-доказу-на-твердження evidence-claim-ref)
(визначити evidence-method (функція (доказ) (друге (знайти-за-ключем (як-є method) (решта доказ)))))
(визначити intent-requires (функція (намір) (друге (знайти-за-ключем (як-є requires) (решта намір)))))
(визначити отримати-необхідні-можливості-наміру intent-requires)
(визначити intent-stop-on (функція (намір) (друге (знайти-за-ключем (як-є stop-on) (решта намір)))))
(визначити intent-produces (функція (намір) (друге (знайти-за-ключем (як-є produces) (решта намір)))))

; --- Narrow relations -------------------------------------------------
; Точна структурна рівність посилань — похідна Lisp-функція.
; EQ отримує лише атоми, CAR/CDR — лише пари, COND — тільки D1.

(визначити епістеміка--рівні-посилання?
  (функція (лівий правий)
    (за-умовою
      ((атом? лівий)
       (за-умовою
         ((атом? правий) (тотожне? лівий правий))
         (так ні)))
      ((атом? правий) ні)
      ((епістеміка--рівні-посилання? (перше лівий) (перше правий))
       (епістеміка--рівні-посилання? (решта лівий) (решта правий)))
      (так ні))))

; supporting-evidence returns () or the matching evidence record itself
; (retrieval, not a collapsed flag). Reuses evidence? / claim-ref helpers.
(визначити supporting-evidence
  (функція (доказ посилання-на-твердження)
    (за-умовою
      ((хибне? (доказ? доказ)) (як-є ()))
      ((хибне? (epistemic--claim-ref? посилання-на-твердження)) (як-є ()))
      ((хибне? (тотожне? (доказ-підсумок доказ) (як-є supports))) (як-є ()))
      ((хибне? (епістеміка--рівні-посилання? (отримати-посилання-доказу-на-твердження доказ) посилання-на-твердження)) (як-є ()))
      (так доказ))))

; D9:101100001 — той самий retrieval closure, без нової семантики.
(визначити підтверджувальний-доказ supporting-evidence)

(визначити epistemic--all-required-present?
  (функція (вимоги доступні-можливості)
    (за-умовою
      ((атом? вимоги) так)
      ((хибне? (значення-у-списку? (перше вимоги) доступні-можливості)) ні)
      (так
       (epistemic--all-required-present? (решта вимоги) доступні-можливості)))))

(визначити intent-capabilities-satisfied?
  (функція (намір доступні-можливості)
    (за-умовою
      ((хибне? (намір? намір)) ні)
      (так
       (epistemic--all-required-present? (отримати-необхідні-можливості-наміру намір) доступні-можливості)))))

; D10:0001111110 INTENT-CAPABILITIES-SATISFIED? — один мовний закон, дві peer-форми.
(визначити усі-необхідні-можливості-наміру-забезпечені? intent-capabilities-satisfied?)
