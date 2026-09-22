; #1132 — Core1 bootstrap contract.
;
; Core1 is the minimal Lisp-on-Lisp bootstrap profile. my-lisp owns this
; contract; mccarthy-eval is only the Stage-0 execution seed.
;
; Important boundary:
; historical S0 spellings/mechanisms are NOT automatically aliases for current
; my-lisp SID laws. They are a bootstrap substrate used to execute lib/core1.lisp.
; Any bridge to a current semantic identity requires an explicit witness.
;
; This file is data, not executable semantics.

(core1-bootstrap-contract/1
  ((identity . authority)
   (owner . my-lisp)
   (profile . core1)
   (semantic-authority-transfer . forbidden)
   (seed-may-mint-sid . forbidden)
   (seed-may-redefine-current-sid . forbidden))

  ((identity . stage-lineage)
   (stages .
     (s0-mccarthy-eval
      s1-core1-lisp
      s2-lisp-authored-compiler
      s3-compiled-compiler
      s4-self-compiled-compiler
      s5-fixed-point-comparison))
   (generation-provenance . required)
   (same-source-fixed-point . required))

  ((identity . s0-substrate)
   (repository . juv4uk/mccarthy-eval)
   (pinned-commit . "1ae9745b66a1439c1929b0d9038c680567118a58")
   (surface-case . exact-uppercase)
   (historical-forms .
     (QUOTE ATOM EQ COND CAR CDR CONS LABEL LAMBDA DEFINE FUNCTION FUNARG))
   (historical-control-values . (T NIL))
   (first-class-closures . explicit-function-funarg)
   (naked-lambda-as-value . historically-unavailable)
   (closure-gap-policy . consume-lisp15-function-funarg)
   (unsupported-form-policy . fail-closed))

  ((identity . s0-surface-boundary)
   (kind . sid-owned-historical-mechanism-projection)
   (semantic-alias-claim . forbidden-without-witness)
   (sid-mechanism-map . "contracts/core1-historical-sid-map.lisp")
   (identity-source . semantic-registry-sid)
   (historical-name-authority . no)
   (projection-must-be-explicit . yes)
   (seed-only-mechanisms . (LABEL apply appq evcon evlis FUNCTION FUNARG T)))

  ((identity . historical-root)
   (mccarthy-1960-mechanisms-consumed .
     (apply appq eval evcon evlis assoc pair append
      QUOTE ATOM EQ COND CAR CDR CONS LABEL LAMBDA))
   (lisp15-mechanisms-consumed . (FUNCTION FUNARG))
   (closure-provenance . lisp15-appendix-b)
   (closure-representation . (FUNARG fn captured-environment))
   (semantic-authority . my-lisp)
   (mechanism-provenance . mccarthy-eval))

  ((identity . s1-source)
   (path . "lib/core1.lisp")
   (source-surface . historical-uppercase-s0)
   (host-arithmetic-required . no)
   (host-first-class-functions-required . historical-function-funarg)
   (host-mutation-required . no)
   (host-strings-required . no))

  ((identity . s1-owned-mechanisms)
   (implemented-in-lisp .
     (lookup
      lexical-binding
      argument-evaluation
      application
      explicit-top-level-frame
      function-funarg-adapter
      program-evaluation
      named-bootstrap-error-data))
   (closure-representation . historical-FUNARG)
   (world-representation . (C1-WORLD last-value global-frame))
   (error-representation . (C1-ERROR kind detail)))

  ((identity . s1-language-shapes)
   (special-forms . (QUOTE COND LAMBDA DEFINE))
   (callable-bootstrap-operations . (ATOM EQ CONS CAR CDR LIST NOT))
   (derived-not-seed-primitives . (LIST NOT))
   (compiler-surface-projection . lazy-lisp-owned-dispatch)
   (compiler-surface-source . lowercase-wsm-my-lisp)
   (projection-preserves-quoted-payload . yes)
   (projection-allocation . zero-copy)
   (whole-ast-copy . forbidden)
   (recursive-definition-mechanism . explicit-global-frame)
   (conditional-policy . historical-two-part-truthiness)
   (predicate-result-domain . historical-t-nil)
   (eq-result-domain . historical-t-nil)
   (atom-result-domain . historical-t-nil)
   (core4-identity-relation . out-of-profile)
   (core4-structural-kind . out-of-profile)
   (exhausted-cond . named-bootstrap-error)
   (modern-core4-structural-results . forbidden))

  ((identity . bootstrap-minimality)
   (admission-question . "Is this required for Lisp to build the next Lisp/compiler generation?")
   (arithmetic . excluded-until-real-witness)
   (strings . excluded-until-real-witness)
   (io . excluded-until-real-witness)
   (macros . excluded-until-real-witness)
   (reasoning . excluded)
   (external-kernels . excluded)
   (machine-opcodes-as-language-semantics . forbidden))

  ((identity . current-known-consumer)
   (repository . juv4uk/wsm-my-lisp)
   (pinned-commit . "a6bd9747196f2d676ab6883cbb4b84c7fcfc6947")
   (compiler-source . "lib/compiler.lisp")
   (requires-at-bootstrap-runtime .
     (QUOTE ATOM EQ CONS CAR CDR COND LAMBDA DEFINE LIST NOT recursion))
   (mentions-but-does-not-require-to-run-compiler .
     (+ -))
   (fixed-point-owner . wsm-my-lisp-issue-39)
   (compiler-mechanism-owner . cml-issue-190))

  ((identity . acceptance)
   (s0-loads-core1-source . required)
   (historical-function-funarg-witness . required)
   (core1-lambda-produces-funarg . required)
   (closure-witness-runs-through-historical-funarg . required)
   (recursive-definition-witness . required)
   (compiler-source-load-witness . required)
   (unsupported-modern-operation-fails-closed . required)
   (s0-source-sha . required)
   (s1-source-sha . required)
   (artifact-hashes . required)))
