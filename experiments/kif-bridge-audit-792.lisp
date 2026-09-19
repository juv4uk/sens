; #792 KIF-1 — explicit bridge admission audit.
;
; Research data only. KIF is treated as a historical interchange precedent,
; not as a required universal language for the archipelago.
;
; Core precedent:
; - KIF was designed for interchange of knowledge among heterogeneous systems.
; - Its semantics are declarative and logic-oriented.
; - Interchange works by mapping heterogeneous source knowledge into a shared
;   representation language.
;
; my-lisp adopts the discipline of explicit interchange contracts, but rejects
; the requirement that all island-native results be normalized into one
; universal knowledge representation.
;
; Decision vocabulary:
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
