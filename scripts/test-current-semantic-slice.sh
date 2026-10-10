#!/usr/bin/env bash
set -euo pipefail

# #231 / #112-#114: the fast semantic lane executes current Lisp-owned
# expectations through host observers. It deliberately does not run legacy
# host-authored Canon truth assertions; deep/current-contract lanes retain
# broader mechanism and integration evidence.
# Rust verifies the physical domain ladder and exact-domain separation only.
# Semantic laws and application logic are owned by Lisp witnesses below.
cargo test -p sens \
  --test domain_ladder \
  --test domain_ladder_only_kernel \
  --test domain_width_authority_test \
  --test domain_ast_value_identity \
  --test d7_w7_pack


# Historical #1096 bare-SID witness remains preserved as compatibility evidence,
# but it is intentionally not executed by the current semantic slice. Contract
# 11.8 assigns W8 to exact D8 identity; Sens8/Sid8 remains migration/provenance only.
# #291: quantity semantics live in Lisp. The shell observes only the named
# pass envelope; expected scientific quantities and relations stay in the
# Lisp witness itself. No replacement Rust observer is introduced.
# #5408: насамперед випробувати саму послідовну лексичну область D6.
# Повний закон величин перевіряється лише після проходження цього SENS-свідка.
lambda_witness="witnesses/quantity-lambda-binding.lisp"
if lambda_status="$(cargo run --quiet -p sens-cli --bin sens -- "$lambda_witness" 2>&1)"; then
  if [[ "$lambda_status" != "7" ]]; then
    printf 'QUANTITY-LAMBDA-BLOCKED: очікувано точне SENS 7, одержано: %s\n' "$lambda_status" >&2
    exit 1
  fi
  printf 'QUANTITY-LAMBDA-PASS: D5 LAMBDA => 7\n'
else
  lambda_rc=$?
  printf 'QUANTITY-LAMBDA-BLOCKED: виконання D5 LAMBDA завершилося %s: %s\n' "$lambda_rc" "$lambda_status" >&2
  exit 1
fi

binding_witness="witnesses/quantity-sequential-binding.lisp"
if binding_status="$(cargo run --quiet -p sens-cli --bin sens -- "$binding_witness" 2>&1)"; then
  if [[ "$binding_status" != "7" ]]; then
    printf 'QUANTITY-BINDING-BLOCKED: очікувано SENS 7, одержано: %s\n' "$binding_status" >&2
    exit 1
  fi
  printf 'QUANTITY-BINDING-PASS: D6 нехай* => 7\n'
else
  binding_rc=$?
  printf 'QUANTITY-BINDING-BLOCKED: SENS-свідок завершився %s: %s\n' "$binding_rc" "$binding_status" >&2
  exit 1
fi

quantity_witness="tests/fixtures/exact-quantity-arithmetic-witness.lisp"
if quantity_status="$(cargo run --quiet -p sens-cli --bin sens -- "$quantity_witness" 2>&1)"; then
  if [[ "$quantity_status" != "(exact-quantity-arithmetic-witness (status pass))" ]]; then
    printf 'exact quantity Lisp witness returned a non-pass result: %s\n' "$quantity_status" >&2
    exit 1
  fi
else
  quantity_rc=$?
  printf 'exact quantity Lisp witness failed (exit %s):\n%s\n' "$quantity_rc" "$quantity_status" >&2

  # Diagnostic-only replay of the existing definitions. Read bindings and
  # calls separately so a non-callable value cannot masquerade as a law failure.
  # The source, expected quantities and failing gate stay unchanged.
  quantity_diag_dir="${RUNNER_TEMP:-$(mktemp -d)}"
  python3 - "$quantity_witness" "$quantity_diag_dir" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
tail = "\n(exact-quantity-arithmetic-witness)"
base = source.rstrip()
if not base.endswith(tail):
    raise SystemExit("QUANTITY-DIAGNOSTIC-BLOCKED: unexpected fixture terminator; refusing to rewrite")
prefix = base[:-len(tail)].rstrip()
root = Path(sys.argv[2])
probes = {
    "rows-binding": "\nexact-quantity-arithmetic-rows\n",
    "check-binding": "\nexact-quantity-arithmetic-check\n",
    "witness-binding": "\nexact-quantity-arithmetic-witness\n",
    "rows-call": "\n(exact-quantity-arithmetic-rows)\n",
    "check-call": "\n(exact-quantity-arithmetic-check (exact-quantity-arithmetic-rows))\n",
    "planck-record": "\n(scientific-constant-quantity si:defining-planck-constant)\n",
    "cesium-record": "\n(scientific-constant-quantity si:defining-cesium-frequency)\n",
    "quantity-product": "\n(quantity-product (scientific-constant-quantity si:defining-planck-constant) (scientific-constant-quantity si:defining-cesium-frequency))\n",
    "one-second": "\n(make-quantity 1 (make-unit (00100111 (make-dimension (00000001 second) 1))))\n",
    "speed-proper-list": "\n(science-proper-list? si:defining-speed-of-light)\n",
    "speed-constant-valid": "\n(scientific-constant? si:defining-speed-of-light)\n",
    "speed-source-valid": "\n(science-source? (scientific-constant-source si:defining-speed-of-light))\n",
    "speed-constant-clauses": "\n(scientific-constant->clauses si:defining-speed-of-light)\n",
    "distance-product": "\n(quantity-product (scientific-constant-quantity si:defining-speed-of-light) (make-quantity 1 (make-unit (00100111 (make-dimension (00000001 second) 1)))))\n",
    "speed-quotient": "\n(quantity-quotient (quantity-product (scientific-constant-quantity si:defining-speed-of-light) (make-quantity 1 (make-unit (00100111 (make-dimension (00000001 second) 1))))) (make-quantity 1 (make-unit (00100111 (make-dimension (00000001 second) 1)))))\n",
    "lambda-identity-probe": "\n((функція (x) x) 7)\n",
    "lambda-nested-probe": "\n((функція (x) ((функція (y) x) 8)) 7)\n",
    "list-two-probe": "\n(00100111 (00000001 a) (00000001 b))\n",
    "list-seven-probe": "\n(00100111 (00000001 a) (00000001 b) (00000001 c) (00000001 d) (00000001 e) (00000001 f) (00000001 g))\n",
    "rows-planck-cesium-prefix": "\n((функція (planck) ((функція (cesium) (00100111 planck cesium)) (scientific-constant-quantity si:defining-cesium-frequency))) (scientific-constant-quantity si:defining-planck-constant))\n",
    "rows-energy-prefix": "\n((функція (planck) ((функція (cesium) ((функція (energy) energy) (quantity-product planck cesium))) (scientific-constant-quantity si:defining-cesium-frequency))) (scientific-constant-quantity si:defining-planck-constant))\n",
    "rows-one-second-prefix": "\n((функція (one-second) one-second) (make-quantity 1 (make-unit (00100111 (make-dimension (00000001 second) 1)))))\n",
    "rows-speed-prefix": "\n((функція (speed) speed) (scientific-constant-quantity si:defining-speed-of-light))\n",
    "rows-distance-prefix": "\n((функція (speed) ((функція (one-second) (quantity-product speed one-second)) (make-quantity 1 (make-unit (00100111 (make-dimension (00000001 second) 1))))) (scientific-constant-quantity si:defining-speed-of-light))\n",
    "rows-recovered-prefix": "\n((функція (speed) ((функція (one-second) ((функція (distance) ((функція (recovered) recovered) (quantity-quotient distance one-second)) (quantity-product speed one-second))) (make-quantity 1 (make-unit (00100111 (make-dimension (00000001 second) 1))))) (scientific-constant-quantity si:defining-speed-of-light))\n",
    "planck-value": "\n(quantity-value (scientific-constant-quantity si:defining-planck-constant))\n",
    "planck-unit": "\n(quantity-unit (scientific-constant-quantity si:defining-planck-constant))\n",
    "numeric-product": "\n(00001110 (quantity-value (scientific-constant-quantity si:defining-planck-constant)) (quantity-value (scientific-constant-quantity si:defining-cesium-frequency)))\n",
    "product-units": "\n(unit-product (quantity-unit (scientific-constant-quantity si:defining-planck-constant)) (quantity-unit (scientific-constant-quantity si:defining-cesium-frequency)))\n",
    "merge-dimensions": "\n(science-merge-dimensions (unit-dimensions (quantity-unit (scientific-constant-quantity si:defining-planck-constant))) (unit-dimensions (quantity-unit (scientific-constant-quantity si:defining-cesium-frequency))))\n",
}
for stage, suffix in probes.items():
    (root / f"exact-quantity-{stage}-probe.lisp").write_text(
        prefix + suffix, encoding="utf-8"
    )
PY

  for stage in rows-binding check-binding witness-binding rows-call check-call planck-record cesium-record planck-value planck-unit numeric-product quantity-product one-second merge-dimensions product-units speed-proper-list speed-constant-valid speed-source-valid speed-constant-clauses distance-product speed-quotient lambda-identity-probe lambda-nested-probe list-two-probe list-seven-probe rows-planck-cesium-prefix rows-energy-prefix rows-one-second-prefix rows-speed-prefix rows-distance-prefix rows-recovered-prefix; do
    probe="$quantity_diag_dir/exact-quantity-$stage-probe.lisp"
    log="$quantity_diag_dir/exact-quantity-$stage-probe.log"
    if cargo run --quiet -p sens-cli --bin sens -- "$probe" >"$log" 2>&1; then
      printf 'QUANTITY-DIAGNOSTIC %s=PASS\n' "$stage"
      cat "$log"
    else
      probe_rc=$?
      printf 'QUANTITY-DIAGNOSTIC %s=FAIL exit=%s\n' "$stage" "$probe_rc" >&2
      cat "$log" >&2
    fi
  done
  exit 1
fi

# #305 / TASK-001: empty meta-program semantics are owned by Lisp. The shell
# observes only the named pass envelope; environment/result meaning stays in
# the witness and no replacement Rust semantic assertion is introduced.
meta_empty_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/meta-eval-empty-program-witness.lisp)"
if [[ "$meta_empty_status" != "(meta-eval-empty-program-witness (status pass))" ]]; then
  printf 'empty meta-program Lisp witness failed: %s\n' "$meta_empty_status" >&2
  exit 1
fi

# #305: registry projection, peer-surface parity, and necessary-form routing
# are now witnessed by Lisp itself. The shell observes only the named pass
# envelope and does not encode any semantic expected values.
meta_registry_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/meta-semantic-registry-witness.lisp)"
if [[ "$meta_registry_status" != "(meta-semantic-registry-witness (status pass))" ]]; then
  printf 'meta semantic-registry Lisp witness failed: %s\n' "$meta_registry_status" >&2
  exit 1
fi
 
# #771: current compact-SID post-core process declaration must load cleanly
# and preserve one runtime identity across the English/Ukrainian stable peer.
process_load_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/process-load-witness.lisp)"
if [[ "$process_load_status" != "(process-load-witness (status pass))" ]]; then
  printf 'process-load Lisp witness failed: %s\n' "$process_load_status" >&2
  exit 1
fi


# #305: `unknown` presentation is meaningful only for an explicitly
# established unknown outcome. No-evidence honesty remains a separate Lisp law
# and returns Canon 0; the shell observes only this witness's named envelope.
narrate_outcome_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/narrate-outcome-authority-witness.lisp)"
if [[ "$narrate_outcome_status" != "(narrate-outcome-authority-witness (status pass))" ]]; then
  printf 'narrate outcome Lisp witness failed: %s\n' "$narrate_outcome_status" >&2
  exit 1
fi

# #305: persistent-vector AVL balance is witnessed by Lisp before retiring the
# stale Rust `== "t"` assertion. The shell observes only the named pass envelope.
vector_balance_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/persistent-vector-balance-witness.lisp)"
if [[ "$vector_balance_status" != "(persistent-vector-balance-witness (status pass))" ]]; then
  printf 'persistent vector balance Lisp witness failed: %s\n' "$vector_balance_status" >&2
  exit 1
fi

# #305: reason-index parity and snapshot meaning are Lisp-owned. The shell
# observes only the named pass envelope before stale Rust `t` oracles retire.
reason_index_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/reason-index-authority-witness.lisp)"
if [[ "$reason_index_status" != "(reason-index-authority-witness (status pass) (laws indexed-linear-parity immutable-prepared-snapshot recursion-negation-parity))" ]]; then
  printf 'reason-index Lisp witness failed: %s\n' "$reason_index_status" >&2
  exit 1
fi

# #408 / #305: a well-formed explicit negative is a valid reasoning goal, and
# no evidence for either side remains Canon 0 unless a named completeness
# contract establishes a richer epistemic status. The shell observes only the
# Lisp witness's pass envelope before the stale Rust `unknown` oracle retires.
explicit_negative_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/explicit-negative-reason-observe-witness.lisp)"
if [[ "$explicit_negative_status" != "(explicit-negative-reason-observe-witness (status pass))" ]]; then
  printf 'explicit-negative reasoning Lisp witness failed: %s\n' "$explicit_negative_status" >&2
  exit 1
fi

# #176: admitted x86-64 instructions (LEA, JMP rel32, Jcc rel32) encode
# deterministically and enforce admission bounds in Lisp. The shell observes
# only the named pass envelope.
x86_instruction_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/x86-64-instruction-set-witness.lisp)"
if [[ "$x86_instruction_status" != "(x86-64-instruction-set-witness (status pass))" ]]; then
  printf 'x86-64 instruction set Lisp witness failed: %s\n' "$x86_instruction_status" >&2
  exit 1
fi


# #491: encoder aliases may share register codes, but typed machine operands
# must preserve byte-vs-64-bit width discipline.
machine_register_width_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/machine-register-width-witness.lisp)"
if [[ "$machine_register_width_status" != "(machine-register-width-witness (status pass))" ]]; then
  printf 'machine register-width witness failed: %s\n' "$machine_register_width_status" >&2
  exit 1
fi


# #178: typed machine atoms cover current admitted GPR/XMM composition and
# execute representative integer/SSE2 paths on the physical CPU.
machine_gpr_atoms_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/machine-current-gpr-atoms-witness.lisp)"
if [[ "$machine_gpr_atoms_status" != "(machine-current-gpr-atoms-witness (status pass))" ]]; then
  printf 'current machine-atoms Lisp witness failed: %s\n' "$machine_gpr_atoms_status" >&2
  exit 1
fi


# #626: native-first classification is total over pair-headed application data.
# Unsupported pair-headed forms must fall back unchanged instead of reaching atom-only eq.
native_first_totality_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/native-first-totality-witness.lisp)"
if [[ "$native_first_totality_status" != "(pass pass)" ]]; then
  printf 'native-first totality witness failed: %s\n' "$native_first_totality_status" >&2
  exit 1
fi


# #506: native-first execution bridge must expose route provenance, execute
# admitted plans on the CPU, fall back before admission only, and never mask
# a chosen native-plan rejection by re-running through the evaluator.
native_first_execution_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/native-first-execution-witness.lisp)"
if [[ "$native_first_execution_status" != "(pass pass pass pass pass)" ]]; then
  printf 'native-first execution bridge witness failed: %s\n' "$native_first_execution_status" >&2
  exit 1
fi


# #509: every admitted native-first island must agree with independent
# Lisp-owned expected evidence AND the reference evaluator, while proving the
# observed execution route is really native rather than a hidden fallback.
native_first_parity_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/native-first-parity-witness.lisp)"
if [[ "$native_first_parity_status" != "(native-first-parity-witness (status pass) (cases 4))" ]]; then
  printf 'native/evaluator differential parity witness failed: %s\n' "$native_first_parity_status" >&2
  exit 1
fi


# #508: the native coverage ledger is diagnostic only. Native-supported rows
# must be independently backed by classifier + CPU route + #509 parity, while
# fallback/blocked rows must remain explicit evaluator fallbacks with reasons.
native_coverage_ledger_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/native-first-coverage-ledger-witness.lisp)"
if [[ "$native_coverage_ledger_status" != "(native-first-coverage-ledger-witness (status pass) (rows 6) (native 1) (fallback 2) (blocked 3))" ]]; then
  printf 'native-first coverage ledger witness failed: %s\n' "$native_coverage_ledger_status" >&2
  exit 1
fi

# #305: scientific-constant knowledge projection remains a pure Lisp-owned
# operation. The shell observes only the named pass envelope; clause count,
# admission and journal-preservation expectations live in the Lisp witness.
science_projection_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/scientific-constant-knowledge-projection-witness.lisp)"
if [[ "$science_projection_status" != "(scientific-constant-knowledge-projection-witness (status pass))" ]]; then
  printf 'scientific constant knowledge-projection witness failed: %s\n' "$science_projection_status" >&2
  exit 1
fi

# #1047: mechanism selection occurs only after surface->SID resolution and may
# choose only executor routes already admitted by Canon/function-table metadata.
mechanism_selector_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/mechanism-selector-1047-witness.lisp)"
if [[ "$mechanism_selector_status" != "(mechanism-selector-1047 (status pass))" ]]; then
  printf 'mechanism selector Lisp witness failed: %s\n' "$mechanism_selector_status" >&2
  exit 1
fi

# #1048/#1169: lowering consumes only Lisp-selected mechanisms. All admitted
# bounded-add transports carry arguments only; operation identity remains SID8.
island_lowering_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/island-lowering-1048-witness.lisp)"
if [[ "$island_lowering_status" != "(island-lowering-1048 (status pass) (executable-payloads 4) (clips admitted-direct-sid8))" ]]; then
  printf 'island lowering Lisp witness failed: %s\n' "$island_lowering_status" >&2
  exit 1
fi

# #369: external translation boundary semantics are Lisp-owned. The shell
# observes only the named pass envelope; invalid-module/refusal classification
# stays in the Lisp witness rather than becoming a new Rust oracle.
translation_symbol_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/translation-symbol-boundary-witness.lisp)"
if [[ "$translation_symbol_status" != "(translation-symbol-boundary-witness (status pass))" ]]; then
  printf 'translation symbol-boundary Lisp witness failed: %s\n' "$translation_symbol_status" >&2
  exit 1
fi


# #536: preserve comparison-peer topology after retiring stale Rust t-oracles.
# The current Lisp-owned witness is observed only through its pass envelope.
runtime_peer_topology_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/runtime-peer-comparison-topology-witness.lisp)"
if [[ "$runtime_peer_topology_status" != "(runtime-peer-comparison-topology-witness (status pass))" ]]; then
  printf 'runtime comparison peer topology witness failed: %s\n' "$runtime_peer_topology_status" >&2
  exit 1
fi