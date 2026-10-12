#!/usr/bin/env bash
set -euo pipefail

# #231 / #112-#114: the fast semantic lane executes current Lisp-owned
# expectations through host observers. It deliberately does not run legacy
# host-authored Canon truth assertions; deep/current-contract lanes retain
# broader mechanism and integration evidence.
cargo test -p my-lisp \
  --test witness_authority \
  --test structural_query_inventory \
  --test structural_observation_contract \
  --test deep_structural_relation_contract \
  --test exact_q_binary_contract \
  --test mathematical_result_taxonomy \
  --test control_dispatch_contract \
  --test canon_laws_v2_contract \
  --test reason_honesty_contract \
  --test unification_outcome_contract \
  --test knowledge_clause_kind_contract \
  --test content_store_authority \
  --test decimal_comma_authority \
  --test authority_guard_contract \
  --test semantic_ref_fail_closed

# #291: quantity semantics live in Lisp. The shell observes only the named
# pass envelope; expected scientific quantities and relations stay in the
# Lisp witness itself. No replacement Rust observer is introduced.
quantity_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/exact-quantity-arithmetic-witness.lisp)"
if [[ "$quantity_status" != "(exact-quantity-arithmetic-witness (status pass))" ]]; then
  printf 'exact quantity Lisp witness failed: %s\n' "$quantity_status" >&2
  exit 1
fi

# #305 / TASK-001: empty meta-program semantics are owned by Lisp. The shell
# observes only the named pass envelope; environment/result meaning stays in
# the witness and no replacement Rust semantic assertion is introduced.
meta_empty_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/meta-eval-empty-program-witness.lisp)"
if [[ "$meta_empty_status" != "(meta-eval-empty-program-witness (status pass))" ]]; then
  printf 'empty meta-program Lisp witness failed: %s\n' "$meta_empty_status" >&2
  exit 1
fi

# #305: registry projection, peer-surface parity, and necessary-form routing
# are now witnessed by Lisp itself. The shell observes only the named pass
# envelope and does not encode any semantic expected values.
meta_registry_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/meta-semantic-registry-witness.lisp)"
if [[ "$meta_registry_status" != "(meta-semantic-registry-witness (status pass))" ]]; then
  printf 'meta semantic-registry Lisp witness failed: %s\n' "$meta_registry_status" >&2
  exit 1
fi

# #305: `unknown` presentation is meaningful only for an explicitly
# established unknown outcome. No-evidence honesty remains a separate Lisp law
# and returns Canon 0; the shell observes only this witness's named envelope.
narrate_outcome_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/narrate-outcome-authority-witness.lisp)"
if [[ "$narrate_outcome_status" != "(narrate-outcome-authority-witness (status pass))" ]]; then
  printf 'narrate outcome Lisp witness failed: %s\n' "$narrate_outcome_status" >&2
  exit 1
fi

# #305: buffer-specific EQ behavior is semantic data owned in Lisp before the
# historical Rust t/() assertions are retired. The shell observes only the
# named envelope; the identity-relation expectations stay in the Lisp witness.
numeric_buffer_identity_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/numeric-buffer-identity-witness.lisp)"
if [[ "$numeric_buffer_identity_status" != "(numeric-buffer-identity-witness (status pass))" ]]; then
  printf 'numeric-buffer identity Lisp witness failed: %s\n' "$numeric_buffer_identity_status" >&2
  exit 1
fi

# #305: persistent-vector AVL balance is witnessed by Lisp before retiring the
# stale Rust `== "t"` assertion. The shell observes only the named pass envelope.
vector_balance_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/persistent-vector-balance-witness.lisp)"
if [[ "$vector_balance_status" != "(persistent-vector-balance-witness (status pass))" ]]; then
  printf 'persistent vector balance Lisp witness failed: %s\n' "$vector_balance_status" >&2
  exit 1
fi

# #362: UTF-8 acceptance, scalar decoding, rejection classes, and failure
# precedence are Lisp-owned. The shell observes only the named pass envelope.
utf8_fused_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/utf8-fused-decode-witness.lisp)"
if [[ "$utf8_fused_status" != "(utf8-fused-decode-witness (status pass))" ]]; then
  printf 'fused UTF-8 Lisp witness failed: %s\n' "$utf8_fused_status" >&2
  exit 1
fi
