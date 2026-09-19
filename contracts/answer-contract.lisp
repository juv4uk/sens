; answer-contract.lisp — Lisp-owned answer/domain authority for #228/#244.
;
; This is deliberately a pure Lisp data document, not an executable library.
; It declares semantic authority without creating public API names or depending
; on the evaluator's historical T/NIL truth machinery merely to exist.
;
; Human spellings remain owned by lib/surface/semantic-registry.lisp.
; Canon 0 is the sole non-ID entry because the empty list itself has no lexical
; semantic-ID spelling.
;
; Governing non-interference rules from #214/#222/#227/#244:
;   * () is the empty list and the vertical unspecialized-result accumulator,
;     never FALSE and never an invented epistemic state.
;   * a stronger answer exists only after a domain has justified that
;     specialization; absence of specialization remains ().
;   * exact-Q binary decisions own only 0/1 and 1/1.
;   * non-binary mathematics remains mathematical result data.
;   * richer reasoning is non-mathematical and cannot redefine mathematics.
;   * arbitrary Value -> bool and host-bool truth authority are forbidden.
;   * lower domains may refine delegated territory; they may not redefine
;     upper domains.
;
; The outer form is:
;   (answer-contract/1 ENTRY ...)
; Consumers read it as data. #228/#244's Lisp-owned witness is the executable
; authority consumer. Runtime/backends may preserve this contract; they do not
; acquire authority to guess a specialization.

(answer-contract/1
  ((identity . canon-zero)
   (domain-owner . no-answer-boundary)
   (answer-role . unspecialized-accumulator)
   (indeterminacy . unresolved-specialization)
   (specialization-policy . justified-only)
   (cause-required . no)
   (reentry . allowed-at-query-boundaries)
   (input-domain . none)
   (result-form . empty-list)
   (no-answer . self)
   (allowed-coercions . ())
   (forbidden-coercions . (false-sentinel binary-collapse unknown-collapse
                           conflict-collapse timeout-collapse error-collapse
                           generic-value->bool host-bool)))

  ((identity . "00000001")
   (domain-owner . structure)
   (input-domain . syntax)
   (result-form . data)
   (no-answer . not-applicable)
   (allowed-coercions . ())
   (forbidden-coercions . (generic-value->bool host-bool)))

  ((identity . "00000100")
   (domain-owner . structure)
   (input-domain . (value value))
   (result-form . pair)
   (no-answer . not-applicable)
   (allowed-coercions . ())
   (forbidden-coercions . (generic-value->bool host-bool)))

  ((identity . "00000101")
   (domain-owner . structure)
   (input-domain . pair)
   (result-form . value)
   (no-answer . not-applicable)
   (allowed-coercions . ())
   (forbidden-coercions . (generic-value->bool host-bool)))

  ((identity . "00000110")
   (domain-owner . structure)
   (input-domain . pair)
   (result-form . value)
   (no-answer . not-applicable)
   (allowed-coercions . ())
   (forbidden-coercions . (generic-value->bool host-bool)))

  ; #218 has now selected explicit domain-owned result forms. PRIM_ATOM is a
  ; structural classifier over the actual value shape: Canon 0, pair, or other
  ; non-pair atom. It is not a universal proposition returning T/NIL.
  ((identity . "00000010")
   (domain-owner . structural-observation)
   (input-domain . value)
   (result-form . structural-kind)
   (result-values . ((structural-kind empty-list)
                     (structural-kind pair)
                     (structural-kind atom)))
   (no-answer . not-applicable)
   (allowed-coercions . ())
   (forbidden-coercions . (generic-value->bool host-bool mathematical-binary-collapse)))

  ; PRIM_EQ remains atom-only. Its two cases belong to the atomic-identity
  ; domain, not to mathematical 0/1 and not to universal truthiness.
  ((identity . "00000011")
   (domain-owner . structural-observation)
   (input-domain . (atom atom))
   (result-form . identity-relation)
   (result-values . ((identity-relation same)
                     (identity-relation distinct)))
   (outside-domain . type-error)
   (no-answer . not-applicable)
   (allowed-coercions . ())
   (forbidden-coercions . (generic-value->bool host-bool mathematical-binary-collapse)))

  ; < is the first exact-Q decision witness. outside-domain=delegate is
  ; essential: a non-Q question is not binary NO. A lower appropriate domain
  ; may answer it, or the concrete query may remain unspecialized as ().
  ((identity . "00011010")
   (domain-owner . exact-q-decision)
   (input-domain . exact-rational-sequence)
   (result-form . rational-binary-decision)
   (binary-values . ("0/1" "1/1"))
   (outside-domain . delegate)
   (unspecialized-result . ())
   (no-answer . ())
   (allowed-coercions . (exact-rational-normalization))
   (forbidden-coercions . (generic-value->bool host-bool truthy-collapse approximate-to-rational)))

  ; + witnesses the separate mathematical-result floor. A mathematical value
  ; does not become a truth status merely because it is non-binary or non-Q.
  ; If no justified mathematical specialization is produced, the answer may
  ; remain Canon 0 rather than being forced into another result algebra.
  ((identity . "00001100")
   (domain-owner . mathematical-result)
   (input-domain . mathematical-values)
   (result-form . mathematical-value)
   (unspecialized-result . ())
   (no-answer . ())
   (allowed-coercions . (domain-valid-mathematical-promotion))
   (forbidden-coercions . (truth-collapse many-valued-collapse generic-value->bool host-bool)))

  ; reason keeps its current public shape for now: a list of
  ; (substitution proof) answers, or () when no proof/result is produced.
  ; `unknown`, conflict, or any future richer state remain explicit reasoning
  ; values; they are never aliases for the unspecialized accumulator.
  ((identity . "10000101")
   (domain-owner . non-mathematical-reasoning)
   (input-domain . (goal rules-or-index))
   (result-form . reasoning-results)
   (unspecialized-result . ())
   (no-answer . ())
   (allowed-coercions . (reasoning-domain-refinement))
   (forbidden-coercions . (binary-collapse mathematical-collapse generic-value->bool host-bool)))

  ; cond consumes an explicit answer/result domain; it does not own universal
  ; truth. If no clause selects a branch, the control result remains ().
  ((identity . "00000111")
   (domain-owner . control-consumer)
   (input-domain . explicit-answer-result)
   (result-form . selected-branch-value)
   (unspecialized-result . ())
   (no-answer . ())
   (allowed-coercions . (domain-dispatch))
   (forbidden-coercions . (generic-value->bool host-bool truthy-collapse))
   (generic-value-coercion . forbidden)))
