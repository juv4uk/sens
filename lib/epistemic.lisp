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
; All return t for valid, () for malformed — no new error/exception type,
; same idiom as lib/result-status.lisp's result-tagged? (no catchable
; exception mechanism exists at the my-lisp language level).

; source-ref? — structurally strict, semantically weak (Spec §3): tag
; must be one of the four v0 variants, payload must be a nonempty proper
; list. It does not, and must not, judge whether a digest is
; cryptographically real, a proof belongs to a World, or a test exists.
(0011 source-ref?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      
      ((010 (011 value))  (001 ()))
      ((101 (100 value) (001 digest)) t)
      ((101 (100 value) (001 proof)) t)
      ((101 (100 value) (001 test)) t)
      ((101 (100 value) (001 observation)) t)
      )))

; claim-ref shape check — no claim-ref? predicate is spec-mandated (and
; none is added as a public export), but supporting-evidence below needs
; a shape check somewhere. Applying the same "structurally strict,
; semantically weak" philosophy as source-ref?: car must be the symbol
; claim-ref, cdr nonempty. Architect-decision extension of the
; documented philosophy, not a literal spec requirement.
(0011 epistemic--claim-ref?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      
      ((010 (011 value))  (001 ()))
      ((101 (100 value) (001 claim-ref)) t)
      )))

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
(0011 observation?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      ((0100 (101 (100 value) (001 observation))) (001 ()))
      
      ((010 (011 value))  (001 ()))
      
      ((010 (1001 value))  (001 ()))
      ((0100 (101 (100 (1001 value)) (001 source))) (001 ()))
      
      ((010 (0111 value))  (001 ()))
      
      ((010 (100 (0111 value)))  (001 ()))
      ((0100 (101 (100 (100 (0111 value))) (001 statement))) (001 ()))
      ((110111011 (010 (011 (0111 value)))) (001 ()))
      ((010 ()) t))))

; claim? — also validates `review` strictly against its finite enum
; {proposed, reviewed, rejected} via member?, unlike source-ref?'s
; deliberately unprovable "semantically weak" carve-out: a review tag is
; a fully decidable finite set, not an open-ended claim about the world
; (real-file digest, proof membership, test existence), so there is no
; reason to leave it unchecked. Architect decision, not silently assumed.
(0011 claim?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      ((0100 (101 (100 value) (001 claim))) (001 ()))
      
      ((010 (011 value))  (001 ()))
      
      ((010 (1001 value))  (001 ()))
      ((0100 (101 (100 (1001 value)) (001 statement))) (001 ()))
      
      ((010 (0111 value))  (001 ()))
      
      ((010 (100 (0111 value)))  (001 ()))
      ((0100 (101 (100 (100 (0111 value))) (001 source))) (001 ()))
      
      ((010 (011 (0111 value)))  (001 ()))
      
      ((010 (100 (011 (0111 value))))  (001 ()))
      ((0100 (101 (100 (100 (011 (0111 value)))) (001 review))) (001 ()))
      ((0100 (11101 (1001 (100 (011 (0111 value)))) (001 (proposed reviewed rejected)))) (001 ()))
      ((110111011 (010 (011 (011 (0111 value))))) (001 ()))
      ((010 ()) t))))

; evidence? — same reasoning as claim? for the finite outcome enum
; {supports, contradicts, inconclusive}.
(0011 evidence?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      ((0100 (101 (100 value) (001 evidence))) (001 ()))
      
      ((010 (011 value))  (001 ()))
      
      ((010 (1001 value))  (001 ()))
      ((0100 (101 (100 (1001 value)) (001 claim-ref))) (001 ()))
      
      ((010 (0111 value))  (001 ()))
      
      ((010 (100 (0111 value)))  (001 ()))
      ((0100 (101 (100 (100 (0111 value))) (001 method))) (001 ()))
      
      ((010 (011 (0111 value)))  (001 ()))
      
      ((010 (100 (011 (0111 value))))  (001 ()))
      ((0100 (101 (100 (100 (011 (0111 value)))) (001 outcome))) (001 ()))
      ((0100 (11101 (1001 (100 (011 (0111 value)))) (001 (supports contradicts inconclusive)))) (001 ()))
      
      ((010 (011 (011 (0111 value))))  (001 ()))
      
      ((010 (100 (011 (011 (0111 value)))))  (001 ()))
      ((0100 (101 (100 (100 (011 (011 (0111 value))))) (001 source-ref))) (001 ()))
      ((110111011 (010 (011 (011 (011 (0111 value)))))) (001 ()))
      ((010 ()) t))))

(0011 intent?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      ((0100 (101 (100 value) (001 intent))) (001 ()))
      
      ((010 (011 value))  (001 ()))
      
      ((010 (1001 value))  (001 ()))
      ((0100 (101 (100 (1001 value)) (001 goal))) (001 ()))
      
      ((010 (0111 value))  (001 ()))
      
      ((010 (100 (0111 value)))  (001 ()))
      ((0100 (101 (100 (100 (0111 value))) (001 requires))) (001 ()))
      
      ((010 (011 (0111 value)))  (001 ()))
      
      ((010 (100 (011 (0111 value))))  (001 ()))
      ((0100 (101 (100 (100 (011 (0111 value)))) (001 stop-on))) (001 ()))
      
      ((010 (011 (011 (0111 value))))  (001 ()))
      
      ((010 (100 (011 (011 (0111 value)))))  (001 ()))
      ((0100 (101 (100 (100 (011 (011 (0111 value))))) (001 produces))) (001 ()))
      ((110111011 (010 (011 (011 (011 (0111 value)))))) (001 ()))
      ((010 ()) t))))

; --- Accessors ------------------------------------------------------------
; lib/core.lisp's assoc (line 311) returns the whole matched (field value)
; sub-form, not the bare value — it's written for dotted-pair alists
; elsewhere in the codebase. Every accessor here is therefore
; (cadr (assoc 'field (cdr record))), not (cdr (assoc ...)).

; Spec-literal (Spec §6 names these explicitly):
(0011 claim-statement (0010 (claim) (1001 (11100 (001 statement) (011 claim)))))
(0011 claim-review (0010 (claim) (1001 (11100 (001 review) (011 claim)))))
(0011 evidence-outcome (0010 (evidence) (1001 (11100 (001 outcome) (011 evidence)))))
(0011 evidence-source-ref (0010 (evidence) (1001 (11100 (001 source-ref) (011 evidence)))))
(0011 intent-goal (0010 (intent) (1001 (11100 (001 goal) (011 intent)))))

; Architect-completed by symmetry — the spec names accessors for claim's
; statement/review, evidence's outcome/source-ref, and intent's goal, but
; not for observation's fields, evidence's claim-ref/method, or intent's
; requires/stop-on/produces. Added here for API completeness, not
; spec-literal:
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
; Тут немає припущення, що історичний W8:11110111 є чинним D8 EQUAL.
(0011 епістеміка--рівні-посилання?
  (0010 (a b)
    (110
      ((010 a)
       (110
         ((010 b) (101 a b))
         ((010 ()) (010 (001 (0))))))
      ((010 b) (010 (001 (0))))
      ((епістеміка--рівні-посилання? (100 a) (100 b))
       (епістеміка--рівні-посилання? (011 a) (011 b)))
      ((010 ()) (010 (001 (0)))))))

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
(0011 supporting-evidence
  (0010 (evidence claim-ref)
    (110
      ((0100 (101010110 evidence)) (001 ()))
      ((0100 (epistemic--claim-ref? claim-ref)) (001 ()))
      ((0100 (101 (101111111 evidence) (001 supports))) (001 ()))
      ((0100 (епістеміка--рівні-посилання? (evidence-claim-ref evidence) claim-ref)) (001 ()))
      ((010 ()) evidence))))

; local helper for intent-capabilities-satisfied? — no every?/all? helper
; exists in lib/core.lisp (confirmed directly, not assumed), so this small
; recursive walk lives here instead of being added to core.lisp.
(0011 epistemic--all-required-present?
  (0010 (requirements effective-capabilities)
    (110
      
      ((010 requirements)  t)
      ((0100 (11101 (100 requirements) effective-capabilities)) (001 ()))
      ((010 ()) (epistemic--all-required-present? (011 requirements) effective-capabilities)))))

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
(0011 intent-capabilities-satisfied?
  (0010 (intent effective-capabilities)
    (110
      ((0100 (101101100 intent)) (001 ()))
      ((010 ()) (epistemic--all-required-present? (intent-requires intent) effective-capabilities)))))
