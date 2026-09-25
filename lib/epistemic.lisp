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

(def make-observation
  (lambda (source statement)
    (list (quote observation) (list (quote source) source) (list (quote statement) statement))))

(def make-claim
  (lambda (statement source review)
    (list (quote claim) (list (quote statement) statement) (list (quote source) source) (list (quote review) review))))

(def make-evidence
  (lambda (claim-ref method outcome source-ref)
    (list (quote evidence)
          (list (quote claim-ref) claim-ref)
          (list (quote method) method)
          (list (quote outcome) outcome)
          (list (quote source-ref) source-ref))))

(def make-intent
  (lambda (goal requirements stop-condition produces)
    (list (quote intent)
          (list (quote goal) goal)
          (list (quote requires) requirements)
          (list (quote stop-on) stop-condition)
          (list (quote produces) produces))))

; --- Shape predicates ---------------------------------------------------
; All return t for valid, () for malformed — no new error/exception type,
; same idiom as lib/result-status.lisp's result-tagged? (no catchable
; exception mechanism exists at the my-lisp language level).

; source-ref? — structurally strict, semantically weak (Spec §3): tag
; must be one of the four v0 variants, payload must be a nonempty proper
; list. It does not, and must not, judge whether a digest is
; cryptographically real, a proof belongs to a World, or a test exists.
(def source-ref?
  (lambda (value)
    (cond
      ((atom? value) (quote ()))
      ((atom? (cdr value)) (quote ()))
      ((eq? (car value) (quote digest)) t)
      ((eq? (car value) (quote proof)) t)
      ((eq? (car value) (quote test)) t)
      ((eq? (car value) (quote observation)) t)
      (t (quote ())))))

; claim-ref shape check — no claim-ref? predicate is spec-mandated (and
; none is added as a public export), but supporting-evidence below needs
; a shape check somewhere. Applying the same "structurally strict,
; semantically weak" philosophy as source-ref?: car must be the symbol
; claim-ref, cdr nonempty. Architect-decision extension of the
; documented philosophy, not a literal spec requirement.
(def epistemic--claim-ref?
  (lambda (value)
    (cond
      ((atom? value) (quote ()))
      ((atom? (cdr value)) (quote ()))
      ((eq? (car value) (quote claim-ref)) t)
      (t (quote ())))))

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
(def observation?
  (lambda (value)
    (cond
      ((atom? value) (quote ()))
      ((not? (eq? (car value) (quote observation))) (quote ()))
      ((atom? (cdr value)) (quote ()))
      ((atom? (cadr value)) (quote ()))
      ((not? (eq? (car (cadr value)) (quote source))) (quote ()))
      ((atom? (cddr value)) (quote ()))
      ((atom? (car (cddr value))) (quote ()))
      ((not? (eq? (car (car (cddr value))) (quote statement))) (quote ()))
      ((not? (atom? (cdr (cddr value)))) (quote ()))
      (t t))))

; claim? — also validates `review` strictly against its finite enum
; {proposed, reviewed, rejected} via member?, unlike source-ref?'s
; deliberately unprovable "semantically weak" carve-out: a review tag is
; a fully decidable finite set, not an open-ended claim about the world
; (real-file digest, proof membership, test existence), so there is no
; reason to leave it unchecked. Architect decision, not silently assumed.
(def claim?
  (lambda (value)
    (cond
      ((atom? value) (quote ()))
      ((not? (eq? (car value) (quote claim))) (quote ()))
      ((atom? (cdr value)) (quote ()))
      ((atom? (cadr value)) (quote ()))
      ((not? (eq? (car (cadr value)) (quote statement))) (quote ()))
      ((atom? (cddr value)) (quote ()))
      ((atom? (car (cddr value))) (quote ()))
      ((not? (eq? (car (car (cddr value))) (quote source))) (quote ()))
      ((atom? (cdr (cddr value))) (quote ()))
      ((atom? (car (cdr (cddr value)))) (quote ()))
      ((not? (eq? (car (car (cdr (cddr value)))) (quote review))) (quote ()))
      ((not? (member? (cadr (car (cdr (cddr value)))) (quote (proposed reviewed rejected)))) (quote ()))
      ((not? (atom? (cdr (cdr (cddr value))))) (quote ()))
      (t t))))

; evidence? — same reasoning as claim? for the finite outcome enum
; {supports, contradicts, inconclusive}.
(def evidence?
  (lambda (value)
    (cond
      ((atom? value) (quote ()))
      ((not? (eq? (car value) (quote evidence))) (quote ()))
      ((atom? (cdr value)) (quote ()))
      ((atom? (cadr value)) (quote ()))
      ((not? (eq? (car (cadr value)) (quote claim-ref))) (quote ()))
      ((atom? (cddr value)) (quote ()))
      ((atom? (car (cddr value))) (quote ()))
      ((not? (eq? (car (car (cddr value))) (quote method))) (quote ()))
      ((atom? (cdr (cddr value))) (quote ()))
      ((atom? (car (cdr (cddr value)))) (quote ()))
      ((not? (eq? (car (car (cdr (cddr value)))) (quote outcome))) (quote ()))
      ((not? (member? (cadr (car (cdr (cddr value)))) (quote (supports contradicts inconclusive)))) (quote ()))
      ((atom? (cdr (cdr (cddr value)))) (quote ()))
      ((atom? (car (cdr (cdr (cddr value))))) (quote ()))
      ((not? (eq? (car (car (cdr (cdr (cddr value))))) (quote source-ref))) (quote ()))
      ((not? (atom? (cdr (cdr (cdr (cddr value)))))) (quote ()))
      (t t))))

(def intent?
  (lambda (value)
    (cond
      ((atom? value) (quote ()))
      ((not? (eq? (car value) (quote intent))) (quote ()))
      ((atom? (cdr value)) (quote ()))
      ((atom? (cadr value)) (quote ()))
      ((not? (eq? (car (cadr value)) (quote goal))) (quote ()))
      ((atom? (cddr value)) (quote ()))
      ((atom? (car (cddr value))) (quote ()))
      ((not? (eq? (car (car (cddr value))) (quote requires))) (quote ()))
      ((atom? (cdr (cddr value))) (quote ()))
      ((atom? (car (cdr (cddr value)))) (quote ()))
      ((not? (eq? (car (car (cdr (cddr value)))) (quote stop-on))) (quote ()))
      ((atom? (cdr (cdr (cddr value)))) (quote ()))
      ((atom? (car (cdr (cdr (cddr value))))) (quote ()))
      ((not? (eq? (car (car (cdr (cdr (cddr value))))) (quote produces))) (quote ()))
      ((not? (atom? (cdr (cdr (cdr (cddr value)))))) (quote ()))
      (t t))))

; --- Accessors ------------------------------------------------------------
; lib/core.lisp's assoc (line 311) returns the whole matched (field value)
; sub-form, not the bare value — it's written for dotted-pair alists
; elsewhere in the codebase. Every accessor here is therefore
; (cadr (assoc 'field (cdr record))), not (cdr (assoc ...)).

; Spec-literal (Spec §6 names these explicitly):
(def claim-statement (lambda (claim) (cadr (assoc (quote statement) (cdr claim)))))
(def claim-review (lambda (claim) (cadr (assoc (quote review) (cdr claim)))))
(def evidence-outcome (lambda (evidence) (cadr (assoc (quote outcome) (cdr evidence)))))
(def evidence-source-ref (lambda (evidence) (cadr (assoc (quote source-ref) (cdr evidence)))))
(def intent-goal (lambda (intent) (cadr (assoc (quote goal) (cdr intent)))))

; Architect-completed by symmetry — the spec names accessors for claim's
; statement/review, evidence's outcome/source-ref, and intent's goal, but
; not for observation's fields, evidence's claim-ref/method, or intent's
; requires/stop-on/produces. Added here for API completeness, not
; spec-literal:
(def observation-source (lambda (observation) (cadr (assoc (quote source) (cdr observation)))))
(def observation-statement (lambda (observation) (cadr (assoc (quote statement) (cdr observation)))))
(def evidence-claim-ref (lambda (evidence) (cadr (assoc (quote claim-ref) (cdr evidence)))))
(def evidence-method (lambda (evidence) (cadr (assoc (quote method) (cdr evidence)))))
(def intent-requires (lambda (intent) (cadr (assoc (quote requires) (cdr intent)))))
(def intent-stop-on (lambda (intent) (cadr (assoc (quote stop-on) (cdr intent)))))
(def intent-produces (lambda (intent) (cadr (assoc (quote produces) (cdr intent)))))

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
(def supporting-evidence
  (lambda (evidence claim-ref)
    (cond
      ((not? (evidence? evidence)) (quote ()))
      ((not? (epistemic--claim-ref? claim-ref)) (quote ()))
      ((not? (eq? (evidence-outcome evidence) (quote supports))) (quote ()))
      ((not? (equal? (evidence-claim-ref evidence) claim-ref)) (quote ()))
      (t evidence))))

; local helper for intent-capabilities-satisfied? — no every?/all? helper
; exists in lib/core.lisp (confirmed directly, not assumed), so this small
; recursive walk lives here instead of being added to core.lisp.
(def epistemic--all-required-present?
  (lambda (requirements effective-capabilities)
    (cond
      ((atom? requirements) t)
      ((not? (member? (car requirements) effective-capabilities)) (quote ()))
      (t (epistemic--all-required-present? (cdr requirements) effective-capabilities)))))

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
(def intent-capabilities-satisfied?
  (lambda (intent effective-capabilities)
    (cond
      ((not? (intent? intent)) (quote ()))
      (t (epistemic--all-required-present? (intent-requires intent) effective-capabilities)))))
