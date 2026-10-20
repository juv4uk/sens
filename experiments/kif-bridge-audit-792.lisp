; #792 KIF-1 — аудит явного допуску моста.
;
; Лише дослідницькі дані. KIF розглядається як історичний прецедент обміну,
; а не як обов'язкова універсальна мова для архіпелагу.
;
; Основний прецедент:
; - KIF створювали для обміну знаннями між різнорідними системами.
; - Його семантика декларативна й орієнтована на логіку.
; - Обмін працює через відображення різнорідного вихідного знання в спільну
;   мову подання.
;
; my-lisp переймає дисципліну явних контрактів обміну, але відкидає
; вимогу, щоб усі рідні результати островів нормалізувалися в одне
; універсальне подання знань.
;
; Словник рішень:
;   borrow-mechanism
;   adapt-explicitly
;   reject-ontology

(kif-bridge-audit/1
  ((pattern . declarative-interchange-contract)
   (decision . borrow-mechanism)
   (kif-evidence . knowledge-interchange-between-heterogeneous-systems)
   (use-in-my-lisp . explicit-bridge-contract)
   (reason . bridge-meaning-must-be-auditable-before-execution))

  ((pattern . explicit-vocabulary-and-model-semantics)
   (decision . adapt-explicitly)
   (kif-evidence . formal-semantics-for-interchange-language)
   (use-in-my-lisp . source-target-domain-contract)
   (reason . state-what-source-data-means-before-projecting-it))

  ((pattern . shared-interlingua)
   (decision . reject-ontology)
   (kif-evidence . common-knowledge-representation-language)
   (use-in-my-lisp . none)
   (reason . native-result-domains-must-not-be-collapsed-into-one-language))

  ((pattern . implicit-semantic-equivalence)
   (decision . reject-ontology)
   (kif-evidence . translation-into-shared-logical-representation)
   (use-in-my-lisp . explicit-equivalence-claim-only)
   (reason . projection-may-be-lossy-partial-or-one-way))

  ((bridge-admission-checklist
     (source-native-domain . required)
     (target-native-domain . required)
     (source-producer . required)
     (target-producer . required)
     (semantic-id . required)
     (preserved-information . required)
     (discarded-information . required)
     (provenance-mapping . required)
     (round-trip . required)
     (equivalence-claim . required)
     (failure-mode . required)
     (missing-source-or-target . required)))

  ((bridge . prolog-substitutions-to-datalog-facts)
   (source-producer . prolog)
   (source-native-domain . substitution-list)
   (target-producer . datalog)
   (target-native-domain . extensional-facts)
   (preserved-information . bound-values-and-selected-variable-role)
   (discarded-information .
     (prolog-search-order
      choice-points
      proof-search-state
      continuation-state))
   (provenance-mapping . preserve-source-observation-ref)
   (round-trip . not-guaranteed)
   (equivalence-claim . partial-projection-only)
   (failure-mode . named-projection-failure)
   (missing-source-or-target . execution-unavailability))
)
