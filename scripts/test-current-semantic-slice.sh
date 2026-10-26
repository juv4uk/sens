#!/usr/bin/env bash
set -euo pipefail

# Основний семантичний контроль виконується САМОЮ двійковою мовою SENS.
# Rust/Python тут не визначають логіку; лише зібрані binary SENS-програми.
run_native_binary_semantics() {
  local bindir="${CARGO_TARGET_DIR:-target}/debug"
  if [[ "${SENS_BINARY_BUILT:-0}" != "1" ]]; then
    cargo build --locked -p sens-cli --bin sens --bin sens-trit
  fi
  local file output peer
  for case_name in atom-empty atom-pair eq-reflexive eq-distinct car-cons cdr-cons cond-short-circuit nested-cons-atom; do
    file="tests/semantic/native-t5/${case_name}.sens"
    if ! output="$("$bindir/sens" "$file")"; then
      printf 'SENS-NATIVE-SEMANTICS: BLOCKED execution %s\n' "$file" >&2
      return 1
    fi
    # The SENS program performs all logic and returns its own exact D1 verdict.
    if [[ "$output" != "1" ]]; then
      printf 'SENS-NATIVE-SEMANTICS: BLOCKED D1 verdict %s=%s\n' "$file" "$output" >&2
      return 1
    fi
    if ! peer="$("$bindir/sens-trit" eval "$file")"; then
      printf 'SENS-NATIVE-SEMANTICS: BLOCKED independent entrypoint %s\n' "$file" >&2
      return 1
    fi
    if [[ "$peer" != "$output" ]]; then
      printf 'SENS-NATIVE-SEMANTICS: BLOCKED oracle/entrypoint mismatch %s\n' "$file" >&2
      return 1
    fi
  done
  for case_name in reject-cond-three-fields reject-cond-non-d1 reject-eq-pair; do
    file="tests/semantic/native-t5/${case_name}.sens"
    if "$bindir/sens" "$file" >/dev/null 2>&1; then
      printf 'SENS-NATIVE-SEMANTICS: BLOCKED invalid binary program admitted %s\n' "$file" >&2
      return 1
    fi
  done
  # Native SENS itself judges the D4/D5 index-field selector law.
  # D6:100111 is quoted data here; no unadmitted invocation.
  local selector_law="tests/semantic/reason-index-width-selectors-law.sens"
  local selector_mutant="tests/semantic/reason-index-width-selectors-mutant.sens"
  local selector_result selector_peer
  if ! selector_result="$("$bindir/sens" "$selector_law")"; then
    printf 'REGRESSION id=reason-index-width-selectors layer=eval fixture=%s expected=D1:1 actual=execution-error\n' "$selector_law" >&2
    return 1
  fi
  if [[ "$selector_result" != "1" ]]; then
    printf 'REGRESSION id=reason-index-width-selectors layer=eval fixture=%s expected=D1:1 actual=%s\n' "$selector_law" "$selector_result" >&2
    return 1
  fi
  if ! selector_peer="$("$bindir/sens-trit" eval "$selector_law")" || [[ "$selector_peer" != "$selector_result" ]]; then
    printf 'REGRESSION id=reason-index-width-selectors-peer layer=eval fixture=%s expected=D1:1 actual=%s\n' "$selector_law" "$selector_peer" >&2
    return 1
  fi
  # Не перетворювати будь-який nonzero exit (reader crash / T5 decode error)
  # на нібито успішний семантичний негативний свідок. Рішення — native SENS.
  local selector_mutant_diagnostic
  if selector_mutant_diagnostic="$("$bindir/sens" "$selector_mutant" 2>&1)"; then
    printf 'REGRESSION id=reason-index-width-selectors-mutant layer=eval fixture=%s expected=D1-noncallable actual=accepted reproduce=%q\n' \
      "$selector_mutant" "$bindir/sens $selector_mutant" >&2
    return 1
  fi
  if [[ "$selector_mutant_diagnostic" != *"domain identity is not callable under its ratified law: D1"* ]]; then
    printf 'UNINFORMATIVE-NEGATIVE id=reason-index-width-selectors-mutant layer=eval fixture=%s expected=D1-noncallable actual=unrelated-error first_diff=unknown reproduce=%q\n' \
      "$selector_mutant" "$bindir/sens $selector_mutant" >&2
    printf '%s\n' "$selector_mutant_diagnostic" >&2
    return 1
  fi
  printf 'SENS_NATIVE_NEGATIVE id=reason-index-width-selectors-mutant outcome=D1-noncallable input=%s\n' "$selector_mutant"
  # One SENS-authored binary program checks three facts together:
  # D4:0011 = D4:0011; D4:0011 != D8:00001010; final predicate D1:1.
  # Old SID8 DEFMACRO and current D8 REPEAT must NEVER alias.
  local migration_fixture="tests/semantic/native-t5/core-d4-vs-d8-width-law.sens"
  local migration_projection="tests/semantic/native-t5/core-d4-vs-d8-width-law.bits"
  local migration_tmp
  migration_tmp="$(mktemp -d)"
  printf '1\n' > "$migration_tmp/expected"
  printf 'SENS_NATIVE_WIDTH_PROOF id=core-d4-vs-d8-width-law executor=%s version=%s reproduce=%q\n' \
    "$bindir/sens" "$("$bindir/sens" --version)" "$migration_fixture"
  if ! "$bindir/sens" "$migration_fixture" > "$migration_tmp/actual" 2> "$migration_tmp/stderr"; then
    printf 'REGRESSION id=core-d4-vs-d8-width-law layer=eval executor=%s fixture=%s expected=D1:1 actual=execution-error\n' \
      "$bindir/sens" "$migration_fixture" >&2
    cat "$migration_tmp/stderr" >&2
    rm -rf "$migration_tmp"
    return 1
  fi
  printf 'SENS_NATIVE_WIDTH_DIGESTS id=core-d4-vs-d8-width-law expected='
  printf 'SENS_NATIVE_WIDTH_DIGESTS id=core-d4-vs-d8-width-law actual='
  if ! cmp -s "$migration_tmp/expected" "$migration_tmp/actual"; then
    printf 'REGRESSION id=core-d4-vs-d8-width-law layer=eval expected=D1:1 actual=' >&2
    cat "$migration_tmp/actual" >&2
    rm -rf "$migration_tmp"
    return 1
  fi
  local migration_peer
  if ! migration_peer="$("$bindir/sens-trit" eval "$migration_fixture")" || [[ "$migration_peer" != "1" ]]; then
    printf 'REGRESSION id=core-d4-vs-d8-width-law layer=eval authority=sens secondary=sens-trit result=%s\n' "$migration_peer" >&2
    rm -rf "$migration_tmp"
    return 1
  fi
  rm -rf "$migration_tmp"
  printf 'SENS_NATIVE_WIDTH_PASS id=core-d4-vs-d8-width-law exact_domains=D4:0011,D8:00001010 verdict=D1:1\n'
  printf 'SENS_NATIVE_D4_D5_SELECTOR: PASS law=1 mutant=blocked\n'
  printf 'SENS-NATIVE-SEMANTICS: PASS 10 SENS-owned positive verdicts, 4 fail-closed negatives\n'
}

case "${1:-}" in
  --native-binary-only)
    [[ $# -eq 1 ]] || { echo "SENS-NATIVE-SEMANTICS: unexpected arguments" >&2; exit 2; }
    run_native_binary_semantics
    exit $?
    ;;
  "")
    [[ $# -eq 0 ]] || exit 2
    run_native_binary_semantics
    ;;
  *)
    echo "SENS-NATIVE-SEMANTICS: use --native-binary-only" >&2
    exit 2
    ;;
esac


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

# Rust is the observer/harness; Lisp's witness-runner owns the semantic verdict.
cargo test -p sens --test witness_authority exact_d3_predicate_boundaries_are_judged_by_lisp_owned_witness_logic



# Historical #1096 bare-SID witness remains preserved as compatibility evidence,
# but it is intentionally not executed by the current semantic slice. Contract
# 11.8 assigns W8 to exact D8 identity; Sens8/Sid8 remains migration/provenance only.
# #291: quantity semantics live in Lisp. The shell observes only the named
# pass envelope; expected scientific quantities and relations stay in the
# Lisp witness itself. No replacement Rust observer is introduced.
# #5408: насамперед випробувати саму послідовну лексичну область D6.
# Повний закон величин перевіряється лише після проходження цього SENS-свідка.
lambda_witness="witnesses/quantity-lambda-binding.lisp"
lambda_expected="(quantity-lambda-binding (status pass) (authority lisp))"
if lambda_status="$(cargo run --quiet -p sens-cli --bin sens -- "$lambda_witness" 2>&1)"; then
  if [[ "$lambda_status" != "$lambda_expected" ]]; then
    printf 'QUANTITY-LAMBDA-BLOCKED: Lisp-вердикт не підтверджено, очікувано %s, одержано: %s\n' "$lambda_expected" "$lambda_status" >&2
    exit 1
  fi
  printf 'QUANTITY-LAMBDA-PASS: D5 LAMBDA; authority=Lisp self-verdict\n'
else
  lambda_rc=$?
  printf 'QUANTITY-LAMBDA-BLOCKED: виконання Lisp-свідка завершилося %s: %s\n' "$lambda_rc" "$lambda_status" >&2
  exit 1
fi

binding_witness="witnesses/quantity-sequential-binding.lisp"
binding_expected="(quantity-sequential-binding (status pass) (authority lisp))"
if binding_status="$(cargo run --quiet -p sens-cli --bin sens -- "$binding_witness" 2>&1)"; then
  if [[ "$binding_status" != "$binding_expected" ]]; then
    printf 'QUANTITY-BINDING-BLOCKED: Lisp-вердикт не підтверджено, очікувано %s, одержано: %s\n' "$binding_expected" "$binding_status" >&2
    exit 1
  fi
  printf 'QUANTITY-BINDING-PASS: D6 нехай-послідовно; authority=Lisp self-verdict\n'
else
  binding_rc=$?
  printf 'QUANTITY-BINDING-BLOCKED: виконання Lisp-свідка завершилося %s: %s\n' "$binding_rc" "$binding_status" >&2
  exit 1
fi

# Сучасний SENS-свідок сам доводить закони точних Д24+ чисел.
# Жодних історичних бітових викличних голів, Python-генераторів,
# сторонніх JSON-оракулів чи старої назви неіснуючої функції.
quantity_witness="tests/fixtures/exact-quantity-arithmetic-witness.lisp"
if ! quantity_status="$(cargo run --quiet -p sens-cli --bin sens -- "$quantity_witness" 2>&1)"; then
  printf 'QUANTITY-NATIVE-RED source=%s expected=quantity-arithmetic-pass actual=execution-error diagnostic=%s\n' "$quantity_witness" "$quantity_status" >&2
  exit 1
fi
if [[ "$quantity_status" != "(quantity-arithmetic (status pass))" ]]; then
  printf 'QUANTITY-NATIVE-RED source=%s expected=%s actual=%s\n' "$quantity_witness" "(quantity-arithmetic (status pass))" "$quantity_status" >&2
  exit 1
fi
printf 'QUANTITY-NATIVE-PASS source=%s authority=SENS domain=D24+\n' "$quantity_witness"

# Мовна семантика й логіка перевіряються виконуваним українським Lisp-свідком.
# Тут немає Rust-очікувань для CAR/CDR/CONS/ATOM/EQ/COND: shell лише
# перевіряє підсумок, який сформувала сама програма SENS.
language_laws_witness="tests/fixtures/domain-ladder-language-laws-witness.lisp"
if ! language_laws_status="$(cargo run --quiet -p sens-cli --bin sens -- "$language_laws_witness" 2>&1)"; then
  printf 'LANGUAGE-LAWS-RED source=%s actual=execution-error diagnostic=%s\n' "$language_laws_witness" "$language_laws_status" >&2
  exit 1
fi
if [[ "$language_laws_status" != "(закон-драбини-мови (стан пройдено))" ]]; then
  printf 'LANGUAGE-LAWS-RED source=%s expected=%s actual=%s\n' "$language_laws_witness" "(закон-драбини-мови (стан пройдено))" "$language_laws_status" >&2
  exit 1
fi
printf 'LANGUAGE-LAWS-PASS source=%s authority=ukr-lisp laws=ATOM/EQ/CONS/CAR/CDR/COND\n' "$language_laws_witness"

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
if [[ "$meta_registry_status" != "(semantic-registry (status pass))" ]]; then
  printf 'meta semantic-registry Lisp witness failed: %s\n' "$meta_registry_status" >&2
  exit 1
fi
 
# #771: SENS повертає фактичні три значення: порожній код -> -1,
# нуль -> 0, ненульовий -> 1. Перевіряємо результат, а не старий status-marker.
process_load_status="$(cargo run --quiet -p sens-cli --bin sens -- tests/fixtures/process-load-witness.lisp)"
if [[ "$process_load_status" != "(-1 0 1)" ]]; then
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
if [[ "$x86_instruction_status" != "(machine-commands (status pass))" ]]; then
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
if [[ "$native_first_parity_status" != "(нативний-паритет-свідок (status pass) (cases 4))" ]]; then
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

# #1047: тільки точна ратифікована драбина, без колишнього плоского SID.
# Вибір механізму перевіряє SENS із нинішніми українськими DEFINE.
# Фізичний T5M переносить Zig; paired є реальним SENS-виконанням.
mechanism_selector_status="$(
  set -euo pipefail
  native_scratch="$(mktemp -d)"
  trap 'rm -rf -- "$native_scratch"' EXIT
  cargo run --quiet -p sens-cli --bin sens -- \
    --t5m-mint-pair tests/fixtures/mechanism-selector-1047-witness.lisp \
    "$native_scratch/mechanism.sens" \
    --binding-source lib/mechanism-selector.lisp >/dev/null
  cargo run --quiet -p sens-cli --bin sens -- \
    --t5m-pair tests/fixtures/mechanism-selector-1047-witness.lisp \
    "$native_scratch/mechanism.sens" \
    --binding-source lib/mechanism-selector.lisp
)"
if [[ "$mechanism_selector_status" != "(mechanism-selector-1047 (status pass))" ]]; then
  printf 'mechanism selector native SENS witness failed: %s\n' "$mechanism_selector_status" >&2
  exit 1
fi

# #1048/#1169: the current SENS selector chooses admitted mechanisms.
# Four exact D24+ operand pairs cross Zig/T5M; no old flat SID8, no host LOAD,
# no unsupported string literal and no Python/JSON execution oracle.
island_lowering_status="$(
  set -euo pipefail
  native_scratch="$(mktemp -d)"
  trap 'rm -rf -- "$native_scratch"' EXIT
  cargo run --quiet -p sens-cli --bin sens --     --t5m-mint-pair tests/fixtures/island-lowering-1048-witness.lisp     "$native_scratch/island.sens"     --binding-source lib/mechanism-selector.lisp     --binding-source lib/island-lowering.lisp >/dev/null
  cargo run --quiet -p sens-cli --bin sens --     --t5m-pair tests/fixtures/island-lowering-1048-witness.lisp     "$native_scratch/island.sens"     --binding-source lib/mechanism-selector.lisp     --binding-source lib/island-lowering.lisp
)"
if [[ "$island_lowering_status" != "(island-lowering-1048 (status pass) (executable-payloads 4) (clips admitted-direct))" ]]; then
  printf 'island lowering native SENS witness failed: %s\n' "$island_lowering_status" >&2
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
if [[ "$runtime_peer_topology_status" != "(peer-topology (status pass))" ]]; then
  printf 'runtime comparison peer topology witness failed: %s\n' "$runtime_peer_topology_status" >&2
  exit 1
fi