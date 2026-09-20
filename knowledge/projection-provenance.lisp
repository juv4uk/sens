; GENERATED — DO NOT EDIT BY HAND.
; Authority: lib/surface/semantic-registry.lisp
; Generator: scripts/generate-projection-provenance.lisp
; This manifest is provenance/evidence only; it cannot mint SID meaning.

(binary 8)

(projection-provenance/1
  (authority "lib/surface/semantic-registry.lisp")
  (source-digest "sha256:7f532c203be8a271f3f0a2a2b33dd12da92e3bd83fd414ea00e4842052a98208")
  (bounded-source-sids (00001100))
  (rows
    (projection
      (target "crates/my-lisp/src/semantic_registry_generated.rs")
      (target-digest "sha256:5a71c2f3a00dde6370069527c01c93ac96d300fe2b4aac22b36081d171f75f96")
      (source "lib/surface/semantic-registry.lisp")
      (source-digest "sha256:7f532c203be8a271f3f0a2a2b33dd12da92e3bd83fd414ea00e4842052a98208")
      (source-sids (00001100))
      (producer "scripts/generate-rust-semantic-registry.lisp")
      (generator-version projection-provenance/1)
      (purpose runtime-surface-sid)
      (input-api internal-runtime-readonly))
    (projection
      (target "lib/generated/function-table.lisp")
      (target-digest "sha256:7e0365aa526d08bd0f88a0c06aa2ea08a4299e136a50d86083cb8c44d52e52a3")
      (source "lib/surface/semantic-registry.lisp")
      (source-digest "sha256:7f532c203be8a271f3f0a2a2b33dd12da92e3bd83fd414ea00e4842052a98208")
      (source-sids (00001100))
      (producer "scripts/generate-function-table.lisp")
      (generator-version projection-provenance/1)
      (purpose function-table-review)
      (input-api forbidden))
    (projection
      (target "docs/generated/function-table.md")
      (target-digest "sha256:1a2619e35e06adf7ec417b74b6fb6d513b51ebb24d04717c9c784a9dc528a9b6")
      (source "lib/surface/semantic-registry.lisp")
      (source-digest "sha256:7f532c203be8a271f3f0a2a2b33dd12da92e3bd83fd414ea00e4842052a98208")
      (source-sids (00001100))
      (producer "scripts/generate-function-table.lisp")
      (generator-version projection-provenance/1)
      (purpose human-documentation)
      (input-api forbidden))
    (projection
      (target "lib/generated/meta-semantic-registry.lisp")
      (target-digest "sha256:5a1cb884f2ca8ecff5d55be0f23a0f756277c68d5aefbdebe7e73153fe20d44f")
      (source "lib/surface/semantic-registry.lisp")
      (source-digest "sha256:7f532c203be8a271f3f0a2a2b33dd12da92e3bd83fd414ea00e4842052a98208")
      (source-sids (00001100))
      (producer "scripts/generate-meta-semantic-registry.lisp")
      (generator-version projection-provenance/1)
      (purpose meta-evaluator-surface-projection)
      (input-api check-only))
    (projection
      (target "lib/generated/uk-surface-audit.lisp")
      (target-digest "sha256:e20524f4d130b3f220503f340e9968dc4f588dc4e989edd2250b0c413ecf88a2")
      (source "lib/surface/semantic-registry.lisp")
      (source-digest "sha256:7f532c203be8a271f3f0a2a2b33dd12da92e3bd83fd414ea00e4842052a98208")
      (source-sids (00001100))
      (producer "scripts/generate-uk-surface-audit.lisp")
      (generator-version projection-provenance/1)
      (purpose ukrainian-surface-review)
      (input-api review-only))))
