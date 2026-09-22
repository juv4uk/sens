; #1131 — four-core profile authority contract.
;
; This is a Lisp-owned architecture document. It defines the four execution /
; compatibility profiles without splitting my-lisp into four semantic
; authorities.
;
; Canon, bare Sid8 identity, semantic-registry rows, language laws and answer
; domains remain single and unnumbered. A core profile may witness, project or
; execute that authority; it may not redefine it.
;
; The host may transport the profile identity mechanically. It must fail closed
; when a requested profile has no admitted implementation.
;
; Outer form:
;   (core-profile-contract/1 ENTRY ...)

(core-profile-contract/1
  ((identity . authority)
   (owner . my-lisp)
   (canon . single)
   (semantic-registry . single)
   (sid-domain . bare-sid-8)
   (language-laws . single)
   (profiles-may-redefine-meaning . forbidden)
   (profiles-may-renumber-sids . forbidden))

  ((identity . core1)
   (profile-number . 1)
   (role . bootstrap-self-hosting)
   (target-source . "lib/core1.lisp")
   (seed-compatibility . mccarthy-eval)
   (growth-track . wsm-my-lisp)
   (compiler-witness . cml)
   (unsupported-operation . fail-closed))

  ((identity . core2)
   (profile-number . 2)
   (role . legacy-my-lisp-compatibility)
   (target-source . "lib/core2.lisp")
   (historical-pin . required-before-activation)
   (compatibility-projection . explicit)
   (unsupported-operation . fail-closed))

  ((identity . core3)
   (profile-number . 3)
   (role . common-lisp-and-islands)
   (target-source . "lib/core3.lisp")
   (islands . (common-lisp prolog clips datalog))
   (selector-owner . my-lisp)
   (lowering-owner . my-lisp)
   (native-observation-preserved . yes)
   (unsupported-operation . fail-closed))

  ((identity . core4)
   (profile-number . 4)
   (role . current-research)
   (target-source . "lib/core4.lisp")
   (migration-source . "lib/core.lisp")
   (current-default-during-migration . yes)
   (unsupported-operation . fail-closed))

  ((identity . profile-selection)
   (kind . execution-mechanism-selection)
   (changes-sid-meaning . no)
   (changes-canon-law . no)
   (changes-surface-identity . no)
   (missing-profile-implementation . mechanism-unavailable))

  ((identity . bootstrap-lineage)
   (stages .
     (mccarthy-eval
      core1
      lisp-authored-compiler
      compiled-compiler
      self-compiled-compiler))
   (generation-provenance . required)
   (semantic-authority-transfer . forbidden))
)
