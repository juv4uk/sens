; #1140 — Core1 S3 compiler-prelude admission.
;
; Data only. This contract records why the prelude exists and the authority
; direction CML must preserve while compiling it.

(core1-s3-compiler-prelude/1
  ((profile . core1)
   (law-base-pin . "5a99136bf7a2e9ab5792bdc945ad53c3774802cd")
   (law-source . "lib/core1.lisp")
   (law-source-git-blob . "a2f184373428bc516a0b03491dfabfb3255d07ef")
   (identity-source . "contracts/core1-historical-sid-map.lisp")
   (identity-source-git-blob . "01c3f3ae49e294c47e65bebeb703954d25c4aa01")
   (semantic-authority . sens)
   (compiler-mechanism . cml))

  ((entry . not)
   (sid . 00100001)
   (core1-result-domain . historical-t-nil)
   (historical-mechanism . NOT)
   (prelude-source . "lib/core1-compiler-prelude.lisp")
   (prelude-git-blob . "a18e1c5fabd107f095be22b8d3f9265b062e55f1")
   (implementation-kind . replaceable-lisp-definition)
   (reason . s3a-concrete-unbound-variable-red))

  ((requirements)
   (explicit-input-before-compiler-source . yes)
   (historical-two-part-cond . admitted)
   (core4-result-records . forbidden)
   (cml-hidden-not-primitive . forbidden)
   ; "fallback" тут означає заборонений Sens8 -> surface -> evaluator lookup.
   ; Прямий language-defined Sens8 slot (#1455; формулювання з #1458) є
   ; механізмом того самого коду, а не запасним шляхом через ім'я.
   (semantic-evaluator-fallback . forbidden)
   (language-defined-sens-slot-dispatch . required)
   (additional-helper-without-concrete-red . forbidden)
   (prelude-provenance-required . yes))

  ((handoff)
   (next-source-repository . juv4uk/wsm-my-lisp)
   (next-source-path . "lib/compiler.lisp")
   (consumer-issue . "juv4uk/cml#190")
   (fixed-point-issue . "juv4uk/wsm-my-lisp#39")))
