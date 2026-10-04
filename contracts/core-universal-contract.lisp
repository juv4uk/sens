; #1664 — Core1–4 shared ATOM/EQ/COND binary foundation.
;
; One executable foundation contract shared by Core1, Core2, Core3 and Core4.
; The shared foundation is deliberately small and stable; experimental Core4
; logic must not redefine it. Core profiles may grow outward; they do not fork
; the predicate/control foundation.
;
; Odna vykonuvana kontrakt-osnova dlia Core1–4. Spilna osnova navmysne mala
; i stabilna; eksperymentalna lohika Core4 yii ne perevyznachaie. Profili
; rostut nazovni, ale ne rozshchepliuiut osnovu predykativ/kontroliu.
;
; The law below is observable law, never human surface spelling. The corpus
; that proves it lives in `tests/fixtures/semantic/` (#1709) and is consumed
; here, not duplicated.

(core-universal-contract/1

  ((scope . core1-core4-universal-foundation)
   (governs . "#1664")
   (corpus . "tests/fixtures/semantic")
   (principle . "Core profiles may grow outward; they do not fork the predicate/control foundation."))

  ((predicate-answer . one-bit)
   (yes . 1)
   (no . 0)
   (graded-answers . forbidden)
   (partial-predicate-no-witness . ())
   (empty-no-witness-equals-no . forbidden)
   (host-boolean-defines-semantics . forbidden)
   (governs . "#1699")
   (ratified-extension . "#3161"))

  (("010" . ((compat-function8 . "00000010")
             (empty-structure . 1)
             (non-pair . 1)
             (pair-structure . 0)))
   (governs . "#1704"))

  (("111" . ((compat-function8 . "00000011")
             (same-admitted-atom . 1)
             (distinct-admitted-atom . 0)
             (pair-operand . named-error)))
   (governs . "#1705"))

  (("011" . ((compat-function8 . "00000111")
             (clause-shape . two-part)
             (test-1 . select)
             (test-0 . skip)
             (test-empty . skip-no-witness)
             (zero-equals-empty . forbidden)
             (other-test-value . named-type-error)
             (unselected-expression . not-evaluated)
             (exhaustion . ())
             (three-part-clause . rejected)))
   (governs . "#1713"))

  ((reader . ((malformed-source . rejected-not-repaired)))
   (governs . "#1709"))

  ((shared-identities . ("00000001" "00000010" "00000011" "00000100"
                         "00000101" "00000110" "00000111"))
   (identity-scope . observable-law-not-spelling))

  ((negative-laws . (graded-predicate-answer
                     empty-equals-predicate-no
                     untyped-empty-as-truth
                     structural-kind-substitution
                     host-truth-substitution))
   (host-truth-defines-semantics . forbidden))

  ((profile-coverage . ((native . proven)
                        (core3 . proven)
                        (core2 . measured-blocked)
                        (core1 . not-yet-exercisable)
                        (core4 . not-yet-exercisable)))
   (divergence-is-a-defect . t)
   (note . "Coverage is measured, not assumed: core2 is a pinned blocker and core1/core4 have no corpus loader yet.")))
