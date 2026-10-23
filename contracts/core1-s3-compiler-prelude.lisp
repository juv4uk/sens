; #1140 — Допуск підготовчої бібліотеки компілятора першого ядра, етап S3.
;
; Файл містить тільки дані. Контракт пояснює призначення підготовчої
; бібліотеки та напрямок семантичних повноважень, який компілятор CML
; зобов'язаний зберігати під час компіляції.

(core1-s3-compiler-prelude-2
  ((profile . core1)
   (law-base-pin . "5a99136bf7a2e9ab5792bdc945ad53c3774802cd")
   (law-source . "lib/core1.lisp")
   (law-source-git-blob . "a2f184373428bc516a0b03491dfabfb3255d07ef")
   (current-identity-source . "lib/domains/d4.lisp")
   (current-identity-source-git-blob . "643a6325a566444f1a7151ca2ff157562a72a1cf")
   (historical-identity-source . "contracts/core1-historical-sid-map.lisp")
   (historical-identity-source-git-blob . "01c3f3ae49e294c47e65bebeb703954d25c4aa01")
   (semantic-authority . sens)
   (compiler-mechanism . cml))

  ((entry . хибне?)
   (current-domain . D4)
   (current-bits . "0100")
   (current-ukr . хибне?)
   (historical-entry-name . "not?")
   (historical-core1-result-domain . historical-t-nil)
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
   ; Виклик використовує точну identity доменної драбини та її повну проєкцію «укр».
   ; Історичний SID8 не диспетчеризує сучасні функції й не переозначає D8.
   (semantic-evaluator-fallback . forbidden)
   (legacy-sid8-slot-dispatch . forbidden)
   (exact-domain-qualified-dispatch . required)
   (ukr-projection-from-ratified-domain-table . required)
   (call-admission-separate-from-identity . required)
   (no-w8-to-d8-byte-substitution . required)
   (additional-helper-without-concrete-red . forbidden)
   (prelude-provenance-required . yes))

  ((handoff)
   (next-source-repository . juv4uk/wsm-my-lisp)
   (next-source-path . "lib/compiler.lisp")
   (consumer-issue . "juv4uk/cml#190")
   (fixed-point-issue . "juv4uk/wsm-my-lisp#39")))
