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
; epistemic.lisp — опційний шар даних proof-of-expression / epistemic-
; status: форми observation/claim/evidence/intent, тегований source-ref
; і вузькі відношення supporting-evidence та
; intent-capabilities-satisfied?. Дизайн узгоджено з живим кодом в
; окремій, суто дизайнерській сесії (вердикт: EXPRESSIBLE AS-IS — без
; зміни kernel/evaluator, без зміни language-contract.lisp); цей файл —
; Phase 2, реалізація того дизайну. Джерельні документи (untracked
; чернетки, прочитані дослівно перед написанням цього файлу) названі
; вище. Не завантажується lib/core.lisp і не вбудовується в
; reason.lisp/knowledge.lisp/world.lisp — той самий опційний прецедент, що й
; lib/result-status.lisp. Не виконує intent, не звертається до
; network/process, не пише в World, не приймає claim як факт, не змінює
; return-значення reason.lisp/forward.lisp.

; --- Constructors (Spec §6 exact arg order) ---------------------------

(00001001 make-observation
  (00001000 (source statement)
    (00100111 (00000001 observation) (00100111 (00000001 source) source) (00100111 (00000001 statement) statement))))

(00001001 make-claim
  (00001000 (statement source review)
    (00100111 (00000001 claim) (00100111 (00000001 statement) statement) (00100111 (00000001 source) source) (00100111 (00000001 review) review))))

(00001001 make-evidence
  (00001000 (claim-ref method outcome source-ref)
    (00100111 (00000001 evidence)
          (00100111 (00000001 claim-ref) claim-ref)
          (00100111 (00000001 method) method)
          (00100111 (00000001 outcome) outcome)
          (00100111 (00000001 source-ref) source-ref))))

(00001001 make-intent
  (00001000 (goal requirements stop-condition produces)
    (00100111 (00000001 intent)
          (00100111 (00000001 goal) goal)
          (00100111 (00000001 requires) requirements)
          (00100111 (00000001 stop-on) stop-condition)
          (00100111 (00000001 produces) produces))))

; --- Shape predicates ---------------------------------------------------
; All return t for valid, () for malformed — no new error/exception type,
; same idiom as lib/result-status.lisp's result-tagged? (no catchable
; exception mechanism exists at the my-lisp language level).

; source-ref? — structurally strict, semantically weak (Spec §3): tag
; must be one of the four v0 variants, payload must be a nonempty proper
; list. It does not, and must not, judge whether a digest is
; cryptographically real, a proof belongs to a World, or a test exists.
(00001001 source-ref?
  (00001000 (value)
    (00000111
      
      ((00000010 value)  (00000001 ()))
      
      ((00000010 (00000110 value))  (00000001 ()))
      ((00000011 (00000101 value) (00000001 digest)) t)
      ((00000011 (00000101 value) (00000001 proof)) t)
      ((00000011 (00000101 value) (00000001 test)) t)
      ((00000011 (00000101 value) (00000001 observation)) t)
      (t (00000001 ())))))

; claim-ref shape check — no claim-ref? predicate is spec-mandated (and
; none is added as a public export), but supporting-evidence below needs
; a shape check somewhere. Applying the same "structurally strict,
; semantically weak" philosophy as source-ref?: car must be the symbol
; claim-ref, cdr nonempty. Architect-decision extension of the
; documented philosophy, not a literal spec requirement.
(00001001 epistemic--claim-ref?
  (00001000 (value)
    (00000111
      
      ((00000010 value)  (00000001 ()))
      
      ((00000010 (00000110 value))  (00000001 ()))
      ((00000011 (00000101 value) (00000001 claim-ref)) t)
      (t (00000001 ())))))

; observation? must NOT be tag-only: the `observation` tag is reused both
; for the full top-level record here and as one of source-ref's four
; light variants, e.g. (source (observation local-run)) — a 2-element
; list, tag + bare atom payload. A tag-only check would misclassify that
; bare source-ref variant as a full Observation record. Fix: after
; confirming the tag, additionally require the second element to be a
; (source ...)-tagged pair, not a bare atom — only then is it a real
; Observation record. Residual, deliberately unresolved edge case (not
; shown or disallowed in the docs, not this phase's problem to solve):
; if an observation-variant source-ref's payload were itself a full
; nested Observation record, this becomes structurally undecidable.
(00001001 observation?
  (00001000 (value)
    (00000111
      
      ((00000010 value)  (00000001 ()))
      ((00100001 (00000011 (00000101 value) (00000001 observation))) (00000001 ()))
      
      ((00000010 (00000110 value))  (00000001 ()))
      
      ((00000010 (00110100 value))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00110100 value)) (00000001 source))) (00000001 ()))
      
      ((00000010 (00110101 value))  (00000001 ()))
      
      ((00000010 (00000101 (00110101 value)))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00000101 (00110101 value))) (00000001 statement))) (00000001 ()))
      ((10110001 (00000010 (00000110 (00110101 value)))) (00000001 ()))
      (t t))))

; claim? — also validates `review` strictly against its finite enum
; {proposed, reviewed, rejected} via member?, unlike source-ref?'s
; deliberately unprovable "semantically weak" carve-out: a review tag is
; a fully decidable finite set, not an open-ended claim about the world
; (real-file digest, proof membership, test existence), so there is no
; reason to leave it unchecked. Architect decision, not silently assumed.
(00001001 claim?
  (00001000 (value)
    (00000111
      
      ((00000010 value)  (00000001 ()))
      ((00100001 (00000011 (00000101 value) (00000001 claim))) (00000001 ()))
      
      ((00000010 (00000110 value))  (00000001 ()))
      
      ((00000010 (00110100 value))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00110100 value)) (00000001 statement))) (00000001 ()))
      
      ((00000010 (00110101 value))  (00000001 ()))
      
      ((00000010 (00000101 (00110101 value)))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00000101 (00110101 value))) (00000001 source))) (00000001 ()))
      
      ((00000010 (00000110 (00110101 value)))  (00000001 ()))
      
      ((00000010 (00000101 (00000110 (00110101 value))))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00000101 (00000110 (00110101 value)))) (00000001 review))) (00000001 ()))
      ((00100001 (00101100 (00110100 (00000101 (00000110 (00110101 value)))) (00000001 (proposed reviewed rejected)))) (00000001 ()))
      ((10110001 (00000010 (00000110 (00000110 (00110101 value))))) (00000001 ()))
      (t t))))

; evidence? — same reasoning as claim? for the finite outcome enum
; {supports, contradicts, inconclusive}.
(00001001 evidence?
  (00001000 (value)
    (00000111
      
      ((00000010 value)  (00000001 ()))
      ((00100001 (00000011 (00000101 value) (00000001 evidence))) (00000001 ()))
      
      ((00000010 (00000110 value))  (00000001 ()))
      
      ((00000010 (00110100 value))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00110100 value)) (00000001 claim-ref))) (00000001 ()))
      
      ((00000010 (00110101 value))  (00000001 ()))
      
      ((00000010 (00000101 (00110101 value)))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00000101 (00110101 value))) (00000001 method))) (00000001 ()))
      
      ((00000010 (00000110 (00110101 value)))  (00000001 ()))
      
      ((00000010 (00000101 (00000110 (00110101 value))))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00000101 (00000110 (00110101 value)))) (00000001 outcome))) (00000001 ()))
      ((00100001 (00101100 (00110100 (00000101 (00000110 (00110101 value)))) (00000001 (supports contradicts inconclusive)))) (00000001 ()))
      
      ((00000010 (00000110 (00000110 (00110101 value))))  (00000001 ()))
      
      ((00000010 (00000101 (00000110 (00000110 (00110101 value)))))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00000101 (00000110 (00000110 (00110101 value))))) (00000001 source-ref))) (00000001 ()))
      ((10110001 (00000010 (00000110 (00000110 (00000110 (00110101 value)))))) (00000001 ()))
      (t t))))

(00001001 intent?
  (00001000 (value)
    (00000111
      
      ((00000010 value)  (00000001 ()))
      ((00100001 (00000011 (00000101 value) (00000001 intent))) (00000001 ()))
      
      ((00000010 (00000110 value))  (00000001 ()))
      
      ((00000010 (00110100 value))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00110100 value)) (00000001 goal))) (00000001 ()))
      
      ((00000010 (00110101 value))  (00000001 ()))
      
      ((00000010 (00000101 (00110101 value)))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00000101 (00110101 value))) (00000001 requires))) (00000001 ()))
      
      ((00000010 (00000110 (00110101 value)))  (00000001 ()))
      
      ((00000010 (00000101 (00000110 (00110101 value))))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00000101 (00000110 (00110101 value)))) (00000001 stop-on))) (00000001 ()))
      
      ((00000010 (00000110 (00000110 (00110101 value))))  (00000001 ()))
      
      ((00000010 (00000101 (00000110 (00000110 (00110101 value)))))  (00000001 ()))
      ((00100001 (00000011 (00000101 (00000101 (00000110 (00000110 (00110101 value))))) (00000001 produces))) (00000001 ()))
      ((10110001 (00000010 (00000110 (00000110 (00000110 (00110101 value)))))) (00000001 ()))
      (t t))))

; --- Accessors ------------------------------------------------------------
; lib/core.lisp's assoc (line 311) returns the whole matched (field value)
; sub-form, not the bare value — it's written for dotted-pair alists
; elsewhere in the codebase. Every accessor here is therefore
; (cadr (assoc 'field (cdr record))), not (cdr (assoc ...)).

; Spec-literal (Spec §6 names these explicitly):
(00001001 claim-statement (00001000 (claim) (00110100 (00101101 (00000001 statement) (00000110 claim)))))
(00001001 claim-review (00001000 (claim) (00110100 (00101101 (00000001 review) (00000110 claim)))))
(00001001 evidence-outcome (00001000 (evidence) (00110100 (00101101 (00000001 outcome) (00000110 evidence)))))
(00001001 evidence-source-ref (00001000 (evidence) (00110100 (00101101 (00000001 source-ref) (00000110 evidence)))))
(00001001 intent-goal (00001000 (intent) (00110100 (00101101 (00000001 goal) (00000110 intent)))))

; Architect-completed by symmetry — the spec names accessors for claim's
; statement/review, evidence's outcome/source-ref, and intent's goal, but
; not for observation's fields, evidence's claim-ref/method, or intent's
; requires/stop-on/produces. Added here for API completeness, not
; spec-literal:
(00001001 observation-source (00001000 (observation) (00110100 (00101101 (00000001 source) (00000110 observation)))))
(00001001 observation-statement (00001000 (observation) (00110100 (00101101 (00000001 statement) (00000110 observation)))))
(00001001 evidence-claim-ref (00001000 (evidence) (00110100 (00101101 (00000001 claim-ref) (00000110 evidence)))))
(00001001 evidence-method (00001000 (evidence) (00110100 (00101101 (00000001 method) (00000110 evidence)))))
(00001001 intent-requires (00001000 (intent) (00110100 (00101101 (00000001 requires) (00000110 intent)))))
(00001001 intent-stop-on (00001000 (intent) (00110100 (00101101 (00000001 stop-on) (00000110 intent)))))
(00001001 intent-produces (00001000 (intent) (00110100 (00101101 (00000001 produces) (00000110 intent)))))

; --- Narrow relations -------------------------------------------------

; supporting-evidence — the spec leaves it open whether "supports" means
; only the outcome tag or also a specific claim match. Resolved here
; (architect decision, not spec-literal) as: both the outcome tag must
; be `supports` AND the evidence's own claim-ref must structurally equal
; the claim-ref argument (equal?, not eq, since claim-ref values can be
; compound structural references) — a piece of evidence "supports" a
; *specific* claim, not just any supports-tagged evidence floating
; around unattached to the claim in question.
;
; Retrieval, not a predicate (owner-directed audit, 2026-09-02): once
; every check has passed, the function is already holding the matched
; `evidence` -- returning bare `t` there would be exactly the
; information collapse the audit was looking for (a search/retrieval
; function that finds something concrete and then throws it away in
; favor of a flag). Returns `()` (no support found) or the matching
; `evidence` record itself. `cond`/`if` need no change: `()` stays
; falsy, any non-Nil value -- including this evidence record -- stays
; truthy, so `(cond ((supporting-evidence e c) ...))` still works
; exactly like the old evidence-supports? did; callers who want the
; evidence itself, not just the fact of its existence, now have it for
; free instead of re-deriving it.
(00001001 supporting-evidence
  (00001000 (evidence claim-ref)
    (00000111
      ((00100001 (10010000 evidence)) (00000001 ()))
      ((00100001 (epistemic--claim-ref? claim-ref)) (00000001 ()))
      ((00100001 (00000011 (10010010 evidence) (00000001 supports))) (00000001 ()))
      ((00100001 (00100010 (evidence-claim-ref evidence) claim-ref)) (00000001 ()))
      (t evidence))))

; local helper for intent-capabilities-satisfied? — no every?/all? helper
; exists in lib/core.lisp (confirmed directly, not assumed), so this small
; recursive walk lives here instead of being added to core.lisp.
(00001001 epistemic--all-required-present?
  (00001000 (requirements effective-capabilities)
    (00000111
      
      ((00000010 requirements)  t)
      ((00100001 (00101100 (00000101 requirements) effective-capabilities)) (00000001 ()))
      (t (epistemic--all-required-present? (00000110 requirements) effective-capabilities)))))

; intent-capabilities-satisfied? checks ONLY the requires-subset
; membership relation: every symbol in the intent's `requires` list must
; appear in the caller-supplied effective-capabilities snapshot. This is
; explicitly NOT authorization, plan validation, evidence validation, or
; a scheduler decision — both source docs are near-identical and
; explicit on this point:
;   "Він не означає authorization, plan validity, input/revision
;   validity, evidence sufficiency або guaranteed execution."
;   (_v0_ мінімальна специфікація proof-of-expression.md, §6)
;   "It is not authorization, plan validation, evidence validation,
;   input/revision validation, a scheduler decision or a guarantee that
;   intent can execute." (Brief для  v0.md)
; `effective-capabilities` is taken here as a plain list of capability
; symbols (matching the `requires` shape) to check membership against —
; the same plain-list convention `requires` itself uses.
(00001001 intent-capabilities-satisfied?
  (00001000 (intent effective-capabilities)
    (00000111
      ((00100001 (10010101 intent)) (00000001 ()))
      (t (epistemic--all-required-present? (intent-requires intent) effective-capabilities)))))
