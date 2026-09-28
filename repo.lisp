; repo.my — Swarm Contract v0.1 scope declaration for my-lisp.
; See docs/swarm-mesh-v2.md for the full spec. Format confirmed by
; example against fpga-lisp/repo.lisp, shiva-sutras/repo.lisp and
; tauricode/repo.lisp (MYLISP-SWARM-CONTRACT-01).
;
; A declaration of scope, not an authorization grant — authorities/
; non-authorities state what this repo is and is not the source of
; truth for, so other repos' agents don't have to re-derive it.

(repository
  (id my-lisp)
  (role language-core)
  (exports language-contract conformance-fixtures core-libs
    semantic-oracle machine-lowering-boundary swarm-node)
  (imports swarm-contract)
  (capabilities lisp rust testing docs debugging swarm-coordination)
  (authorities language-semantics runtime-core standard-library
    swarm-protocol-implementation)
  (non-authorities cml-compilation fpga-hardware sanskrit-canon
    paninian-ontology agent-workstation-ui registry-data))
