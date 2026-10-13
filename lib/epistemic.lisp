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
; Migrated: bare host truthiness t → exact D1:1 form (010 (001 ())).
; False carriers use (001 ()). Two-field COND. Reuses existing CAR/CDR/
; EQ/ATOM discipline and project accessors. Width is identity.

; --- Constructors (Spec §6 exact arg order) ---------------------------

(0011 make-observation
  (0010 (source statement)
    (1110 (001 observation) (1110 (001 source) source) (1110 (001 statement) statement))))

(0011 make-claim
  (0010 (statement source review)
    (1110 (001 claim) (1110 (001 statement) statement) (1110 (001 source) source) (1110 (001 review) review))))

(0011 make-evidence
  (0010 (claim-ref method outcome source-ref)
    (1110 (001 evidence)
          (1110 (001 claim-ref) claim-ref)
          (1110 (001 method) method)
          (1110 (001 outcome) outcome)
          (1110 (001 source-ref) source-ref))))

(0011 make-intent
  (0010 (goal requirements stop-condition produces)
    (1110 (001 intent)
          (1110 (001 goal) goal)
          (1110 (001 requires) requirements)
          (1110 (001 stop-on) stop-condition)
          (1110 (001 produces) produces))))

; --- Shape predicates ---------------------------------------------------
; All return (010 (001 ())) for valid, (001 ()) for malformed — no new
; error/exception type, same idiom as lib/result-status.lisp.

(0011 source-ref?
  (0010 (value)
    (110
      ((010 value) (001 ()))
      ((010 (011 value)) (001 ()))
      ((101 (100 value) (001 digest)) (010 (001 ())))
      ((101 (100 value) (001 proof)) (010 (001 ())))
      ((101 (100 value) (001 test)) (010 (001 ())))
      ((101 (100 value) (001 observation)) (010 (001 ())))
      ((010 (001 ())) (001 ())))))

(0011 epistemic--claim-ref?
  (0010 (value)
    (110
      ((010 value) (001 ()))
      ((010 (011 value)) (001 ()))
      ((101 (100 value) (001 claim-ref)) (010 (001 ())))
      ((010 (001 ())) (001 ())))))

(0011 observation?
  (0010 (value)
    (110
      ((010 value) (001 ()))
      ((0100 (101 (100 value) (001 observation))) (001 ()))
      ((010 (011 value)) (001 ()))
      ((010 (1001 value)) (001 ()))
      ((0100 (101 (100 (1001 value)) (001 source))) (001 ()))
      ((010 (0111 value)) (001 ()))
      ((010 (100 (0111 value))) (001 ()))
      ((0100 (101 (100 (100 (0111 value))) (001 statement))) (001 ()))
      ((110111011 (010 (011 (0111 value)))) (001 ()))
      ((010 (001 ())) (010 (001 ()))))))

(0011 claim?
  (0010 (value)
    (110
      ((010 value) (001 ()))
      ((0100 (101 (100 value) (001 claim))) (001 ()))
      ((010 (011 value)) (001 ()))
      ((010 (1001 value)) (001 ()))
      ((0100 (101 (100 (1001 value)) (001 statement))) (001 ()))
      ((010 (0111 value)) (001 ()))
      ((010 (100 (0111 value))) (001 ()))
      ((0100 (101 (100 (100 (0111 value))) (001 source))) (001 ()))
      ((010 (011 (0111 value))) (001 ()))
      ((010 (100 (011 (0111 value)))) (001 ()))
      ((0100 (101 (100 (100 (011 (0111 value)))) (001 review))) (001 ()))
      ((0100 (11101 (1001 (100 (011 (0111 value)))) (001 (proposed reviewed rejected)))) (001 ()))
      ((110111011 (010 (011 (011 (0111 value))))) (001 ()))
      ((010 (001 ())) (010 (001 ()))))))

(0011 evidence?
  (0010 (value)
    (110
      ((010 value) (001 ()))
      ((0100 (101 (100 value) (001 evidence))) (001 ()))
      ((010 (011 value)) (001 ()))
      ((010 (1001 value)) (001 ()))
      ((0100 (101 (100 (1001 value)) (001 claim-ref))) (001 ()))
      ((010 (0111 value)) (001 ()))
      ((010 (100 (0111 value))) (001 ()))
      ((0100 (101 (100 (100 (0111 value))) (001 method))) (001 ()))
      ((010 (011 (0111 value))) (001 ()))
      ((010 (100 (011 (0111 value)))) (001 ()))
      ((0100 (101 (100 (100 (011 (0111 value)))) (001 outcome))) (001 ()))
      ((0100 (11101 (1001 (100 (011 (0111 value)))) (001 (supports contradicts inconclusive)))) (001 ()))
      ((010 (011 (011 (0111 value)))) (001 ()))
      ((010 (100 (011 (011 (0111 value))))) (001 ()))
      ((0100 (101 (100 (100 (011 (011 (0111 value))))) (001 source-ref))) (001 ()))
      ((110111011 (010 (011 (011 (011 (0111 value)))))) (001 ()))
      ((010 (001 ())) (010 (001 ()))))))

(0011 intent?
  (0010 (value)
    (110
      ((010 value) (001 ()))
      ((0100 (101 (100 value) (001 intent))) (001 ()))
      ((010 (011 value)) (001 ()))
      ((010 (1001 value)) (001 ()))
      ((0100 (101 (100 (1001 value)) (001 goal))) (001 ()))
      ((010 (0111 value)) (001 ()))
      ((010 (100 (0111 value))) (001 ()))
      ((0100 (101 (100 (100 (0111 value))) (001 requires))) (001 ()))
      ((010 (011 (0111 value))) (001 ()))
      ((010 (100 (011 (0111 value)))) (001 ()))
      ((0100 (101 (100 (100 (011 (0111 value)))) (001 stop-on))) (001 ()))
      ((010 (011 (011 (0111 value)))) (001 ()))
      ((010 (100 (011 (011 (0111 value))))) (001 ()))
      ((0100 (101 (100 (100 (011 (011 (0111 value))))) (001 produces))) (001 ()))
      ((110111011 (010 (011 (011 (011 (0111 value)))))) (001 ()))
      ((010 (001 ())) (010 (001 ()))))))

; --- Accessors ------------------------------------------------------------
; Reuse existing project selectors (1001 / 11100) already admitted in Core.

(0011 claim-statement (0010 (claim) (1001 (11100 (001 statement) (011 claim)))))
(0011 claim-review (0010 (claim) (1001 (11100 (001 review) (011 claim)))))
(0011 evidence-outcome (0010 (evidence) (1001 (11100 (001 outcome) (011 evidence)))))
(0011 evidence-source-ref (0010 (evidence) (1001 (11100 (001 source-ref) (011 evidence)))))
(0011 intent-goal (0010 (intent) (1001 (11100 (001 goal) (011 intent)))))

(0011 observation-source (0010 (observation) (1001 (11100 (001 source) (011 observation)))))
(0011 observation-statement (0010 (observation) (1001 (11100 (001 statement) (011 observation)))))
(0011 evidence-claim-ref (0010 (evidence) (1001 (11100 (001 claim-ref) (011 evidence)))))
(0011 evidence-method (0010 (evidence) (1001 (11100 (001 method) (011 evidence)))))
(0011 intent-requires (0010 (intent) (1001 (11100 (001 requires) (011 intent)))))
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
         ((010 (001 ())) (001 ()))))
      ((010 b) (001 ()))
      ((епістеміка--рівні-посилання? (100 a) (100 b))
       (епістеміка--рівні-посилання? (011 a) (011 b)))
      ((010 (001 ())) (001 ())))))

; supporting-evidence returns () or the matching evidence record itself
; (retrieval, not a collapsed flag). Reuses evidence? / claim-ref helpers.
(0011 supporting-evidence
  (0010 (evidence claim-ref)
    (110
      ((0100 (evidence? evidence)) (001 ()))
      ((0100 (epistemic--claim-ref? claim-ref)) (001 ()))
      ((0100 (101 (evidence-outcome evidence) (001 supports))) (001 ()))
      ((0100 (епістеміка--рівні-посилання? (evidence-claim-ref evidence) claim-ref)) (001 ()))
      ((010 (001 ())) evidence))))

(0011 epistemic--all-required-present?
  (0010 (requirements effective-capabilities)
    (110
      ((010 requirements) (010 (001 ())))
      ((0100 (11101 (100 requirements) effective-capabilities)) (001 ()))
      ((010 (001 ()))
       (epistemic--all-required-present? (011 requirements) effective-capabilities)))))

(0011 intent-capabilities-satisfied?
  (0010 (intent effective-capabilities)
    (110
      ((0100 (intent? intent)) (001 ()))
      ((010 (001 ()))
       (epistemic--all-required-present? (intent-requires intent) effective-capabilities)))))
