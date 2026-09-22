; #1140 — Core1 S3 compiler-prelude admission.
;
; Data only. This contract records why the prelude exists and the authority
; direction CML must preserve while compiling it.

(core1-s3-compiler-prelude/1
  ((profile . core1)
   (law-base-pin . "5a99136bf7a2e9ab5792bdc945ad53c3774802cd")
   (law-source . "lib/core1.lisp")
   (identity-source . "contracts/core1-historical-sid-map.lisp")
   (semantic-authority . my-lisp)
   (compiler-mechanism . cml))

  ((entry . not)
   (sid . 00100001)
   (core1-result-domain . historical-t-nil)
   (historical-mechanism . NOT)
   (prelude-source . "lib/core1-compiler-prelude.lisp")
   (implementation-kind . replaceable-lisp-definition)
   (reason . s3a-concrete-unbound-variable-red))

  ((requirements)
   (explicit-input-before-compiler-source . yes)
   (historical-two-part-cond . admitted)
   (core4-result-records . forbidden)
   (cml-hidden-not-primitive . forbidden)
   (semantic-evaluator-fallback . forbidden)
   (additional-helper-without-concrete-red . forbidden)
   (prelude-provenance-required . yes))

  ((handoff)
   (next-source-repository . juv4uk/wsm-my-lisp)
   (next-source-path . "lib/compiler.lisp")
   (consumer-issue . "juv4uk/cml#190")
   (fixed-point-issue . "juv4uk/wsm-my-lisp#39")))
