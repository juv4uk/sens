; #383 — machine-readable classification of knowledge artifacts.
; Directory placement never creates semantic authority.
; This registry classifies artifact role, scope, provenance, lifecycle, and
; consumers. It does not redefine language semantics.

(about
  (schema knowledge-authority-inventory/1)
  (issue 383)
  (scope knowledge-artifact-governance)
  (authority-rule provenance-and-scope-not-directory)
  (language-semantics-authority (repo-path "docs/semantic-authority-map.md")))

(artifact
  (path "knowledge/astronomy.lisp")
  (class operational-reference)
  (scope reasoning-demo-knowledge)
  (authority-source (synthetic-fixture reasoning-demo))
  (lifecycle active)
  (consumers ("crates/my-lisp/tests/knowledge.rs")))

(artifact
  (path "knowledge/examples/astronomy-package.lisp")
  (class operational-reference)
  (scope knowledge-package-format-example)
  (authority-source (synthetic-fixture knowledge-package-format))
  (lifecycle active)
  (consumers ("crates/my-lisp/tests/knowledge.rs")))

(artifact
  (path "knowledge/family.lisp")
  (class operational-reference)
  (scope recursive-reasoning-demo)
  (authority-source (synthetic-fixture reasoning-demo))
  (lifecycle active)
  (consumers ("crates/my-lisp/tests/knowledge.rs")))

(artifact
  (path "knowledge/guard-fact-policy.lisp")
  (class executable-policy)
  (scope guard-runtime-fact-classification)
  (authority-source (repo-path "docs/guard-oracle-node-plan.md"))
  (lifecycle active)
  (consumers ("crates/wsm-guard-facts/src/main.rs")))

(artifact
  (path "knowledge/guard-reference-inbox.mylog")
  (class evidence-ledger)
  (scope guard-reference-candidate-history)
  (authority-source (embedded-record-provenance))
  (lifecycle active)
  (consumers ("crates/my-lisp-host/tests/windows_native_exec_abi.rs")))

(artifact
  (path "knowledge/guard-reference.lisp")
  (class operational-reference)
  (scope guard-navigation)
  (authority-source (embedded-topic-authorities))
  (lifecycle active)
  (consumers
    ("AGENTS.md"
     "lib/guard.lisp"
     "crates/my-lisp-cli/src/swarm.rs"
     "crates/my-lisp-lsp/src/guard_knowledge.rs")))

(artifact
  (path "knowledge/guard-runtime-policy.lisp")
  (class executable-policy)
  (scope guard-runtime-request-classification)
  (authority-source (repo-path "docs/guard-oracle-node-plan.md"))
  (lifecycle active)
  (consumers ("crates/wsm-guard-slice/src/main.rs")))

(artifact
  (path "knowledge/language-detection-probe.lisp")
  (class historical-record)
  (scope github-language-detection-observation)
  (authority-source (observed-behavior github-code-search "2026-09-08"))
  (lifecycle legacy)
  (consumers ()))

(artifact
  (path "knowledge/language-policy.lisp")
  (class executable-policy)
  (scope owner-authored-human-communication)
  (authority-source (owner-directive "2026-09-07"))
  (lifecycle active)
  (consumers
    ("AGENTS.md"
     "README.md"
     "scripts/check-bilingual-docs"
     "knowledge/guard-reference.lisp")))

(artifact
  (path "knowledge/meta-eval-evidence.lisp")
  (class evidence-ledger)
  (scope meta-evaluator-parity-claims)
  (authority-source (issue 26))
  (lifecycle active)
  (consumers
    ("scripts/generate-meta-eval-evidence.py"
     "scripts/check-meta-eval-evidence.py"
     "scripts/semantic-ownership.py"
     "docs/meta-eval-evidence.md")))

(artifact
  (path "knowledge/physics.lisp")
  (class operational-reference)
  (scope reasoning-demo-knowledge)
  (authority-source (synthetic-fixture reasoning-demo))
  (lifecycle active)
  (consumers ("crates/my-lisp/tests/knowledge.rs")))

(artifact
  (path "knowledge/repo-tooling-inventory.lisp")
  (class operational-reference)
  (scope repo-tooling-governance)
  (authority-source (issue 382))
  (lifecycle active)
  (consumers ("scripts/check-repo-tooling-inventory.lisp")))

(artifact
  (path "knowledge/sanskrit-cyrillic-audit.lisp")
  (class evidence-ledger)
  (scope sanskrit-cyrillic-cross-reference)
  (authority-source (embedded-provenance))
  (lifecycle transitional)
  (consumers
    ("knowledge/sanskrit-cyrillic-phoneme-map.lisp"
     "knowledge/sanskrit-cyrillic-keyboard.lisp")))

(artifact
  (path "knowledge/sanskrit-cyrillic-keyboard.lisp")
  (class derived-reference)
  (scope sanskrit-cyrillic-input-gesture-spec)
  (authority-source (repo-path "knowledge/sanskrit-cyrillic-phoneme-map.lisp"))
  (lifecycle transitional)
  (consumers ("knowledge/sanskrit-keyboard.ahk")))

(artifact
  (path "knowledge/sanskrit-cyrillic-phoneme-map.lisp")
  (class derived-reference)
  (scope sanskrit-cyrillic-sound-id-candidates)
  (authority-source (repo-path "knowledge/sanskrit-cyrillic-audit.lisp"))
  (lifecycle transitional)
  (consumers ("knowledge/sanskrit-cyrillic-keyboard.lisp")))

(artifact
  (path "knowledge/sanskrit-keyboard.ahk")
  (class derived-reference)
  (scope windows-sanskrit-cyrillic-input-implementation)
  (authority-source (repo-path "knowledge/sanskrit-cyrillic-keyboard.lisp"))
  (lifecycle transitional)
  (consumers ()))

(artifact
  (path "knowledge/semantic-ownership.lisp")
  (class evidence-ledger)
  (scope audited-semantic-ownership)
  (authority-source (issue 25))
  (lifecycle active)
  (consumers
    ("scripts/semantic-ownership.py"
     "docs/semantic-ownership-report.md")))

(artifact
  (path "knowledge/swarm-legacy-deprecation.lisp")
  (class coordination-marker)
  (scope retired-9999-coordination-surface)
  (authority-source (repo-path "docs/swarm-mesh-v2.md"))
  (lifecycle active)
  (consumers
    ("AGENTS.md"
     "crates/xtask/src/checks.rs"
     "crates/my-lisp/tests/swarm_deprecation.rs"
     "knowledge/swarm-no-live-callers-audit.lisp")))

(artifact
  (path "knowledge/swarm-no-live-callers-audit.lisp")
  (class evidence-ledger)
  (scope swarm-legacy-removal-audit)
  (authority-source (repo-path "knowledge/swarm-legacy-deprecation.lisp"))
  (lifecycle active)
  (consumers ("crates/my-lisp/tests/swarm_deprecation.rs")))

(artifact
  (path "knowledge/knowledge-authority-inventory.lisp")
  (class operational-reference)
  (scope knowledge-artifact-governance)
  (authority-source (issue 383))
  (lifecycle active)
  (consumers ("scripts/check-knowledge-authority.lisp")))
