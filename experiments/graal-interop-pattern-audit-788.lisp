; #788 GRAAL-INTEROP-1 — capability/message interop audit.
;
; Research data only. GraalVM/Truffle is treated as a precedent for
; capability-based foreign-object interaction, not as a universal value
; ontology for the archipelago.
;
; Evidence consulted:
; - Truffle interoperability protocol uses standardized messages
; - foreign values expose capabilities such as array/member/executable traits
; - consumers probe capabilities before performing operations
; - unsupported access/conversion is an explicit failure mode
; - Polyglot APIs may eagerly convert/re-type foreign values
;
; Decisions:
;   borrow-mechanism
;   adapt-explicitly
;   reject-ontology

(graal-interop-pattern-audit/1
  ((pattern . capability-probe-before-operation)
   (decision . borrow-mechanism)
   (graal-evidence . has-array-elements-is-executable-has-members-style-probes)
   (use-in-my-lisp . native-observation-capability-probe)
   (reason . ask-what-a-native-result-supports-before-bridging-or-inspecting))

  ((pattern . operation-specific-messages)
   (decision . borrow-mechanism)
   (graal-evidence . read-member-read-array-element-execute-style-messages)
   (use-in-my-lisp . explicit-observation-operations)
   (reason . operations-should-be-narrow-and-auditable-not-generic-coercions))

  ((pattern . unsupported-operation-failure)
   (decision . borrow-mechanism)
   (graal-evidence . unsupported-or-invalid-interop-operation)
   (use-in-my-lisp . named-capability-failure)
   (reason . missing-capability-is-not-false-and-not-empty-list))

  ((pattern . language-neutral-dispatch-protocol)
   (decision . adapt-explicitly)
   (graal-evidence . any-truffle-language-can-speak-the-same-message-protocol)
   (use-in-my-lisp . producer-neutral-mechanical-observation-interface)
   (reason . host-can-dispatch-without-knowing-island-semantics))

  ((pattern . foreign-value-kind-taxonomy)
   (decision . reject-ontology)
   (graal-evidence . shared-kinds-like-null-boolean-number-array-string)
   (use-in-my-lisp . none)
   (reason . native-result-domain-must-remain-producer-owned))

  ((pattern . eager-or-implicit-value-conversion)
   (decision . reject-ontology)
   (graal-evidence . polyglot-cast-and-implicit-interop)
   (use-in-my-lisp . explicit-bridge-only)
   (reason . no-automatic-cross-island-semantic-coercion))

  ((pattern . same-memory-space-interoperability)
   (decision . reject-ontology)
   (graal-evidence . direct-foreign-values-in-shared-runtime)
   (use-in-my-lisp . opaque-result-ref-and-explicit-projection)
   (reason . autonomous-islands-must-not-require-one-shared-runtime))

  ((experiment . native-observation-capabilities)
   (proposal .
     (observation-capabilities
       (producer prolog)
       (supports
         (enumerate-substitutions
          count-results
          preserve-native-payload))
       (unsupported
         (treat-as-datalog-relation-directly
          coerce-to-truth))))
   (implementation-status . proposed))
)
