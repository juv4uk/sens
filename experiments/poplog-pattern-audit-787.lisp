; #787 POPLOG-1 — evidence-backed pattern audit.
;
; This is research data, not language authority. It records what my-lisp may
; borrow/adapt/reject from Poplog before LIFE-1 grows more orchestration.
;
; Primary evidence consulted:
; - OpenPoplog HELP SUBSYSTEMS
; - OpenPoplog DOC SYSSPEC
; - OpenPoplog REF PROLOG
; - OpenPoplog DOC CONTINUATION
; - OpenPoplog REF EXTERNAL
;
; Decision vocabulary:
;   borrow-mechanism
;   adapt-explicitly
;   reject-architecture

(poplog-pattern-audit/1
  ((pattern . subsystem-descriptor)
   (decision . borrow-mechanism)
   (poplog-evidence . separate-language-subsystems)
   (use-in-my-lisp . kernel-capability-descriptor)
   (reason . explicit-producer-and-lifecycle-identity))

  ((pattern . is-subsystem-loaded)
   (decision . borrow-mechanism)
   (poplog-evidence . runtime-loaded-query)
   (use-in-my-lisp . kernel-availability-observation)
   (reason . execution-availability-without-semantic-mutation))

  ((pattern . compiler-dispatch-by-subsystem)
   (decision . adapt-explicitly)
   (poplog-evidence . subsystem-specific-compilers)
   (use-in-my-lisp . invoke-target-dispatch)
   (reason . route-by-producer-without-sharing-language-semantics))

  ((pattern . prolog-continuation-discipline)
   (decision . borrow-mechanism)
   (poplog-evidence . continuation-and-backtracking-preservation)
   (use-in-my-lisp . preserve-native-search-lifecycle)
   (reason . foreign-call-must-not-collapse-prolog-search))

  ((pattern . external-callback-boundary)
   (decision . adapt-explicitly)
   (poplog-evidence . pop-call-external-callback)
   (use-in-my-lisp . c-abi-kernel-callback-contract)
   (reason . explicit-lifecycle-and-memory-boundary))

  ((pattern . shared-poplog-virtual-machine)
   (decision . reject-architecture)
   (poplog-evidence . common-stack-oriented-vm)
   (use-in-my-lisp . none)
   (reason . islands-must-remain-autonomous-execution-witnesses))

  ((pattern . pop11-as-core-language)
   (decision . reject-architecture)
   (poplog-evidence . pop11-always-present-core)
   (use-in-my-lisp . none)
   (reason . my-lisp-must-not-become-runtime-substrate-for-all-islands))

  ((pattern . common-procedure-object-model)
   (decision . reject-architecture)
   (poplog-evidence . same-procedure-call-protocol)
   (use-in-my-lisp . native-result-and-call-domains-remain-producer-owned)
   (reason . avoid-universal-runtime-object-ontology))

  ((experiment . life-1-poplog-inspired-capability-probe)
   (source . poplog-is-subsystem-loaded)
   (proposal .
     (kernel-capability
       (producer prolog)
       (available observed)
       (started observed)
       (native-control search-backtracking)
       (semantic-authority my-lisp)))
   (acceptance .
     (missing-kernel-is-execution-unavailability-not-semantic-change))
   (implementation-status . proposed))
)
