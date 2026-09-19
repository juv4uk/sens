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

# #305: persistent-vector AVL balance is witnessed by Lisp before retiring the
# stale Rust `== "t"` assertion. The shell observes only the named pass envelope.
vector_balance_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/persistent-vector-balance-witness.lisp)"
if [[ "$vector_balance_status" != "(persistent-vector-balance-witness (status pass))" ]]; then
  printf 'persistent vector balance Lisp witness failed: %s\n' "$vector_balance_status" >&2
  exit 1
fi

# #305: reason-index parity and snapshot meaning are Lisp-owned. The shell
# observes only the named pass envelope before stale Rust `t` oracles retire.
reason_index_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/reason-index-authority-witness.lisp)"
if [[ "$reason_index_status" != "(reason-index-authority-witness (status pass) (laws indexed-linear-parity immutable-prepared-snapshot recursion-negation-parity))" ]]; then
  printf 'reason-index Lisp witness failed: %s\n' "$reason_index_status" >&2
  exit 1
fi

# #408 / #305: a well-formed explicit negative is a valid reasoning goal, and
# no evidence for either side remains Canon 0 unless a named completeness
# contract establishes a richer epistemic status. The shell observes only the
# Lisp witness's pass envelope before the stale Rust `unknown` oracle retires.
explicit_negative_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/explicit-negative-reason-observe-witness.lisp)"
if [[ "$explicit_negative_status" != "(explicit-negative-reason-observe-witness (status pass))" ]]; then
  printf 'explicit-negative reasoning Lisp witness failed: %s\n' "$explicit_negative_status" >&2
  exit 1
fi

# #176: admitted x86-64 instructions (LEA, JMP rel32, Jcc rel32) encode
# deterministically and enforce admission bounds in Lisp. The shell observes
# only the named pass envelope.
x86_instruction_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/x86-64-instruction-set-witness.lisp)"
if [[ "$x86_instruction_status" != "(x86-64-instruction-set-witness (status pass))" ]]; then
  printf 'x86-64 instruction set Lisp witness failed: %s\n' "$x86_instruction_status" >&2
  exit 1
fi


# #491: encoder aliases may share register codes, but typed machine operands
# must preserve byte-vs-64-bit width discipline.
machine_register_width_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/machine-register-width-witness.lisp)"
if [[ "$machine_register_width_status" != "(machine-register-width-witness (status pass))" ]]; then
  printf 'machine register-width witness failed: %s\n' "$machine_register_width_status" >&2
  exit 1
fi


# #178: typed machine atoms cover current admitted GPR/XMM composition and
# execute representative integer/SSE2 paths on the physical CPU.
machine_gpr_atoms_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/machine-current-gpr-atoms-witness.lisp)"
if [[ "$machine_gpr_atoms_status" != "(machine-current-gpr-atoms-witness (status pass))" ]]; then
  printf 'current machine-atoms Lisp witness failed: %s\n' "$machine_gpr_atoms_status" >&2
  exit 1
fi


# #626: native-first classification is total over pair-headed application data.
# Unsupported pair-headed forms must fall back unchanged instead of reaching atom-only eq.
native_first_totality_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/native-first-totality-witness.lisp)"
if [[ "$native_first_totality_status" != "(pass pass)" ]]; then
  printf 'native-first totality witness failed: %s\n' "$native_first_totality_status" >&2
  exit 1
fi


# #506: native-first execution bridge must expose route provenance, execute
# admitted plans on the CPU, fall back before admission only, and never mask
# a chosen native-plan rejection by re-running through the evaluator.
native_first_execution_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/native-first-execution-witness.lisp)"
if [[ "$native_first_execution_status" != "(pass pass pass pass pass)" ]]; then
  printf 'native-first execution bridge witness failed: %s\n' "$native_first_execution_status" >&2
  exit 1
fi


# #509: every admitted native-first island must agree with independent
# Lisp-owned expected evidence AND the reference evaluator, while proving the
# observed execution route is really native rather than a hidden fallback.
native_first_parity_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/native-first-parity-witness.lisp)"
if [[ "$native_first_parity_status" != "(native-first-parity-witness (status pass) (cases 4))" ]]; then
  printf 'native/evaluator differential parity witness failed: %s\n' "$native_first_parity_status" >&2
  exit 1
fi


# #508: the native coverage ledger is diagnostic only. Native-supported rows
# must be independently backed by classifier + CPU route + #509 parity, while
# fallback/blocked rows must remain explicit evaluator fallbacks with reasons.
native_coverage_ledger_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/native-first-coverage-ledger-witness.lisp)"
if [[ "$native_coverage_ledger_status" != "(native-first-coverage-ledger-witness (status pass) (rows 6) (native 1) (fallback 2) (blocked 3))" ]]; then
  printf 'native-first coverage ledger witness failed: %s\n' "$native_coverage_ledger_status" >&2
  exit 1
fi

# #305: scientific-constant knowledge projection remains a pure Lisp-owned
# operation. The shell observes only the named pass envelope; clause count,
# admission and journal-preservation expectations live in the Lisp witness.
science_projection_status="$(cargo run --quiet -p my-lisp-cli --bin my-lisp -- tests/fixtures/scientific-constant-knowledge-projection-witness.lisp)"
if [[ "$science_projection_status" != "(scientific-constant-knowledge-projection-witness (status pass))" ]]; then
  printf 'scientific constant knowledge-projection witness failed: %s\n' "$science_projection_status" >&2
  exit 1
fi
