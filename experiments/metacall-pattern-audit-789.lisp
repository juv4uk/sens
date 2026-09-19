; #789 METACALL-1 — evidence-backed runtime lifecycle audit.
;
; Research data only. This does not define my-lisp semantics.
;
; MetaCall precedent examined:
; - extensible/embeddable polyglot runtime
; - language loaders/plugins
; - load -> handle -> invoke -> unload lifecycle
; - dynamic-link handles and explicit unload
; - shared metacall_value foreign-value representation
;
; Decision vocabulary:
;   borrow-mechanism
;   adapt-explicitly
;   reject-ontology

(metacall-pattern-audit/1
  ((pattern . loader-plugin-boundary)
   (decision . borrow-mechanism)
   (metacall-evidence . per-language-loaders)
   (use-in-my-lisp . kernel-driver-registration)
   (reason . runtime-specific-loading-behind-one-mechanical-interface))

  ((pattern . explicit-load-handle-unload-lifecycle)
   (decision . borrow-mechanism)
   (metacall-evidence . dynlink-load-handle-unload)
   (use-in-my-lisp . kernel-lifecycle-handle)
   (reason . prevent-hidden-global-runtime-state))

  ((pattern . runtime-capability-discovery)
   (decision . adapt-explicitly)
   (metacall-evidence . extensible-loader-registry)
   (use-in-my-lisp . kernel-capability-observation)
   (reason . discover-execution-availability-without-changing-sid-meaning))

  ((pattern . named-runtime-failure)
   (decision . borrow-mechanism)
   (metacall-evidence . loader-and-dynlink-error-boundaries)
   (use-in-my-lisp . execution-unavailable-or-kernel-failure)
   (reason . failure-must-be-observable-before-semantic-projection))

  ((pattern . generic-function-lookup)
   (decision . adapt-explicitly)
   (metacall-evidence . polyglot-function-discovery)
   (use-in-my-lisp . explicit-invoke-target-selection)
   (reason . selection-is-mechanical-but-semantic-id-remains-lisp-owned))

  ((pattern . universal-metacall-value)
   (decision . reject-ontology)
   (metacall-evidence . shared-foreign-value-type-system)
   (use-in-my-lisp . none)
   (reason . native-result-domains-must-remain-producer-owned))

  ((pattern . automatic-cross-language-import)
   (decision . reject-ontology)
   (metacall-evidence . transparent-interlanguage-imports)
   (use-in-my-lisp . explicit-bridge-only)
   (reason . cross-island-projection-must-remain-explicit-and-partial))

  ((experiment . life-1-runtime-handle)
   (proposal .
     (kernel-handle
       (producer prolog)
       (availability observed)
       (lifecycle (load start invoke stop unload))
       (native-result-domain preserved)
       (semantic-authority my-lisp)))
   (acceptance .
     (runtime-handle-never-becomes-semantic-identity))
   (implementation-status . proposed))
)
