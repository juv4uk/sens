#!/usr/bin/env bash
# Find exact changed executable SENS/Lisp sources and publish the native test manifest.
set -euo pipefail
raw="$RUNNER_TEMP/changed-lisp-raw.txt"
manifest="$RUNNER_TEMP/changed-t5m-lisp.txt"
base="$BEFORE_SHA"
if [[ "$GITHUB_EVENT_NAME" == pull_request ]]; then
  # Для PR GitHub перевіряє синтетичний merge-коміт.
  # Перший батько цього merge — точна база його файлів, без сусідніх push.
  if ! git cat-file -e "$GITHUB_SHA^1" 2>/dev/null; then
    timeout 60s git fetch --no-tags --deepen=2 origin "$GITHUB_REF"
  fi
  base="$(git rev-parse "$GITHUB_SHA^1")"
fi
if [[ -z "$base" || "$base" =~ ^0+$ ]]; then
  # Manual/atypical events may omit event.before. Never diff the whole
  # repository root: historical paths are not changed test inputs.
  if git cat-file -e "$GITHUB_SHA^1" 2>/dev/null; then
    base="$(git rev-parse "$GITHUB_SHA^1")"
  else
    echo "::error::T5M_CHANGED_BASE_UNAVAILABLE event=$GITHUB_EVENT_NAME sha=$GITHUB_SHA" >&2
    exit 2
  fi
fi
if ! git cat-file -e "$base^{commit}" 2>/dev/null; then
  timeout 60s git fetch --no-tags --depth=1 origin "$base"
fi
git -c core.quotePath=false diff --name-only -z --diff-filter=ACMRT "$base" "$GITHUB_SHA" -- '*.lisp' '*.sens' '*.rs' '*.zig' '.github/workflows/ci.yml' 'scripts/prove-lisp-semantic-t5m.sh' 'scripts/prove-lisp-language-laws.sh' 'scripts/execute_changed_lisp_t5m.sh' > "$raw"
printf '%s\n' "$base" > "$RUNNER_TEMP/native-semantic-base.sha"
python3 - "$raw" "$manifest" "$GITHUB_OUTPUT" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "scripts")
from report_ukr_projection_progress import tokenize_lisp, _contains_source_definitions

raw, manifest, output = map(Path, sys.argv[1:])
data_prefixes = ("lib/domains/", "lib/generated/", "knowledge/", "docs/",
                 "research/", "contracts/", "lib/machine/xed/generated/")
data_paths = {"language-contract.lisp"}
selected = []
has_lisp = False
has_rust = False
has_zig = False
workflow_changed = False
# Git -z зберігає справжні назви файлів. Далі маємо legacy
# рядковий manifest і GitHub Output: непридатні шляхи не пропускаємо.
def git_paths(blob: bytes) -> list[str]:
    if blob and not blob.endswith(bytes([0])):
        raise ValueError("Git path list must be NUL-terminated")
    paths = []
    for name in blob.decode("utf-8").split(chr(0)):
        if not name:
            continue
        if any(ch in name for ch in ("\n", "\r", "\t")) or name != name.strip():
            raise ValueError(f"line-manifest cannot represent path {name!r}")
        paths.append(name)
    return paths

# Негативний свідок самої механіки CI: раніше такий .lisp мовчки губився.
assert git_paths("lib/назва із пробілом.lisp".encode() + bytes([0])) == ["lib/назва із пробілом.lisp"]
for malformed in (b"lib/multiline\nsource.lisp\0", b"lib/tab\tname.lisp\0", b"lib/bad.lisp\n"):
    try:
        git_paths(malformed)
    except ValueError:
        pass
    else:
        raise AssertionError(f"T5M_CHANGED_GIT_PATH_SELFTEST_FAILED input={malformed!r}")
try:
    changed_paths = git_paths(raw.read_bytes())
except (ValueError, UnicodeError) as exc:
    raise SystemExit(f"::error::T5M_CHANGED_UNREPRESENTABLE_PATH {exc}") from exc
for original in changed_paths:
    if original in {".github/workflows/ci.yml", "scripts/prove-lisp-semantic-t5m.sh", "scripts/prove-lisp-language-laws.sh", "scripts/execute_changed_lisp_t5m.sh"}:
        workflow_changed = True
        continue
    if original.endswith(".lisp"):
        has_lisp = True
    if original.endswith(".rs"):
        has_rust = True
        continue
    if original.endswith(".zig"):
        has_zig = True
        continue
    name = original[:-5] + ".lisp" if original.endswith(".sens") else original
    if not name.endswith(".lisp") or name.startswith(data_prefixes) or name in data_paths:
        continue
    path = Path(name)
    if not path.is_file() or path.is_symlink():
        raise SystemExit(f"T5M_CHANGED_SOURCE_INVALID path={name}")
    # Core4 parts are byte-range fragments, often beginning within
    # an open SENS form. They are NOT standalone source programs:
    # testing each with T5M mint reports a false parser regression.
    # Always test the whole generated Core4 SENS program instead.
    # Keep committed pair/view drift RED until native Zig/T5M remint.
    if name.startswith("lib/core4-parts/"):
        full_source = Path("lib/core4.lisp")
        if not full_source.is_file() or full_source.is_symlink():
            raise SystemExit(
                f"::error::T5M_CORE4_AGGREGATE_MISSING fragment={name}"
            )
        if "lib/core4.lisp" not in selected:
            selected.append("lib/core4.lisp")
        print(
            f"T5M_CORE4_FRAGMENT_IN_AGGREGATE fragment={name} "
            "source=lib/core4.lisp standalone=NOT_APPLICABLE"
        )
        continue
    if name.startswith("lib/surface/") and not _contains_source_definitions(path):
        print(f"T5M_NONPROGRAM_SURFACE path={name}")
        continue
    try:
        if not tokenize_lisp(path.read_text(encoding="utf-8")):
            continue
    except (OSError, UnicodeError, ValueError):
        pass  # malformed Lisp must reach the real SENS reader and fail closed
    # Ці law/mutant є залежними фікстурами, не автономними програмами.
    if name in {
        # Ці свідки потребують фізичного UTF-8 bootstrap; їх виконує
        # обов'язковий utf8_physical_d1 нижче разом із точністю пар.
        "tests/semantic/utf8-direct-d1-law.lisp",
        "tests/semantic/utf8-direct-d1-mutant.lisp",
        "tests/semantic/meta-eval-graph-d1-law.lisp",
        "tests/semantic/meta-eval-graph-d1-mutant.lisp",
        "tests/semantic/meta-eval-predicates-d1-law.lisp",
        "tests/semantic/meta-eval-predicates-d1-mutant.lisp",
        "tests/semantic/meta-eval-lexical-shadow-d1-physical-law.lisp",
        "tests/semantic/meta-eval-lexical-shadow-d1-physical-mutant.lisp",
        "tests/semantic/meta-fc-predicates-d1-mutant.lisp",
        "tests/semantic/unification-occurs-check-law.lisp",
        "tests/semantic/unification-occurs-check-mutant.lisp",
        # D11 scan/fold: залежні SENS-свідки з бібліотечними DEFINE.
        # D9 MAP: тести потребують lib/persistent-map.lisp.
        # Їх уже виконує обов'язковий SENS → Zig/T5M native law runner
        # разом із DEFINE; автономний changed-Lisp дав би UnknownSymbol.
        "tests/semantic/d9-map-hidden-tail-positive.lisp",
        "tests/semantic/d9-map-hidden-tail-get-negative.lisp",
        "tests/semantic/d9-map-hidden-tail-insert-negative.lisp",
        "tests/semantic/d11-scan-fold-d3-tail-law.lisp",
        "tests/semantic/d11-scan-fold-d3-tail-mutant.lisp",
        "tests/semantic/d11-scan-fold-d3-tail-scan-improper-negative.lisp",
        "tests/semantic/d11-scan-fold-d3-tail-left-improper-negative.lisp",
        "tests/semantic/d11-scan-fold-d3-tail-right-improper-negative.lisp",
        "tests/semantic/d11-srfi1-list-equality-law.lisp",
        # Д11: залежні свідки вилучення асоціацій з SENS-бібліотекою.
        # Без DEFINE standalone відхиляється; виконує лише law runner.
        "tests/semantic/d11-assoc-delete-proper-law.lisp",
        "tests/semantic/d11-assoc-delete-order-mutant.lisp",
        "tests/semantic/d11-assoc-delete-improper-tail-negative.lisp",
        "tests/semantic/d11-assoc-delete-invalid-record-negative.lisp",
        # D11 list=: залежні позитиви, справжні визначення lib/ перед ними.
        "tests/semantic/d11-srfi1-list-equality-structure-law.lisp",
        "tests/semantic/d11-srfi1-list-equality-pairs-law.lisp",
        "tests/semantic/d11-srfi1-list-equality-directed-pairs-law.lisp",
        "tests/semantic/d11-srfi1-list-equality-directed-adjacent-law.lisp",
        "tests/semantic/d11-srfi1-list-equality-directed-mutant.lisp",
        "tests/semantic/d11-srfi1-list-equality-directed-law.lisp",
        "tests/semantic/d11-srfi1-list-equality-directed-pairs-mutant.lisp",
        "tests/semantic/d11-srfi1-list-equality-directed-adjacent-mutant.lisp",
        "tests/semantic/d11-srfi1-list-equality-nullary-law.lisp",
        "tests/semantic/d11-srfi1-list-equality-mutant.lisp",
        # F11-PROOF-TRACE запускається в єдиному нативному law runner із DEFINE lib/reason.lisp.
        "tests/semantic/d11-reason-proof-trace-law.lisp",
        "tests/semantic/d11-reason-proof-results-law.lisp",
        "tests/semantic/d11-reason-proof-results-mutant.lisp",
        "tests/semantic/d11-reason-proof-results-improper-accum-negative.lisp",
        "tests/semantic/d11-reason-proof-results-improper-scan-negative.lisp",
        "tests/semantic/d11-reason-proof-results-improper-map-negative.lisp",
        "tests/semantic/d11-reason-proof-results-improper-attach-negative.lisp",
        "tests/semantic/d11-reason-index-law.lisp",
        "tests/semantic/d11-reason-index-mutant.lisp",
        "tests/semantic/d11-reason-index-improper-reverse-negative.lisp",
        "tests/semantic/d11-reason-index-improper-buckets-negative.lisp",
        "tests/semantic/d11-reason-index-improper-rules-negative.lisp",
        "tests/semantic/d11-reason-proof-trace-mutant.lisp",
        "tests/semantic/d11-reason-proof-trace-improper-provenance-negative.lisp",
        "tests/semantic/d11-reason-proof-trace-improper-count-negative.lisp",
        # D11 FIND-TAIL requires its canonical Lisp DEFINE from lib/.
        # It is executed in the native bundled law step and in the
        # physical law runner; never misclassify it as standalone.
        "tests/semantic/d11-srfi1-find-tail-laws.lisp",
        # Обидва juxt-свідки потребують реального DEFINE з lib/d11-clojure-juxt.lisp.
        # Їх виконує повний нативний закон Lisp → Zig/T5M → SENS нижче.
        "tests/semantic/d11-clojure-juxt-laws.lisp",
        "tests/semantic/d11-clojure-juxt-mutant.lisp",
        # Негативний D11 juxt залежить від DEFINE і очікує Type.
        # Його запускає run_type_rejection у фізичному law bundle.
        "tests/semantic/d11-clojure-juxt-improper-d1-tail-negative.lisp",
        # D11 частоти: обидва негативні свідки потребують бібліотечного DEFINE.
        # Д11 unary frequencies: dependent positive law and mutant are
        # evaluated with the canonical library inside native T5M suite.
        "tests/semantic/d11-clojure-frequencies-unary-law.lisp",
        "tests/semantic/d11-clojure-frequencies-unary-mutant.lisp",
        "tests/semantic/d11-clojure-frequencies-improper-count-negative.lisp",
        "tests/semantic/d11-clojure-frequencies-improper-groups-negative.lisp",
        "tests/semantic/unification-variable-shape-law.lisp",
        "tests/semantic/unification-variable-shape-positive.lisp",
        "tests/semantic/unification-variable-shape-negative.lisp",
        "tests/semantic/unification-variable-shape-mutant.lisp",
        # Конструктор і предикат потребують DEFINE lib/unify.lisp.
        "tests/semantic/unification-constructor-law.lisp",
        "tests/semantic/unification-constructor-mutant.lisp",
        "tests/semantic/unification-occurs-predicate-law.lisp",
        "tests/semantic/unification-occurs-predicate-mutant.lisp",
        "tests/semantic/core-d3-car-cdr-cons-mutant.lisp",
        # UTF-8 laws require the admitted library and are bundled by the native SENS witness runner.
        "tests/semantic/utf8-boundary-laws.lisp",
        "tests/semantic/utf8-boundary-mutant.lisp",
        "tests/semantic/utf8-quotient-laws.lisp",
        "tests/semantic/utf8-quotient-mutant.lisp",
        "tests/semantic/result-status-laws.lisp",
        "tests/semantic/d11-srfi1-span-break-laws.lisp",
        # Залежні SPAN/BREAK негативні SENS-свідки запускаються з lib/ в Zig/T5M.
        "tests/semantic/d11-srfi1-span-improper-suffix-negative.lisp",
        "tests/semantic/d11-srfi1-break-improper-suffix-negative.lisp",
        # D7/D8 епістемічні закони залежать від Lisp-бібліотеки.
        # Вони завжди запускаються через реальний T5M law bundle нижче.
        "tests/semantic/d7-epistemic-structural-tag-law.lisp",
        "tests/semantic/d7-epistemic-structural-tag-mutant.lisp",
        "tests/semantic/language-law-epistemic-records.lisp",
        "tests/semantic/language-mutant-epistemic-records.lisp",
        # D6 quantifier files must be evaluated only inside the exact-Core4 bundle.
        "tests/semantic/усі-за-предикатом-law.lisp",
        "tests/semantic/усі-за-предикатом-mutant.lisp",
        "tests/semantic/існує-за-предикатом-law.lisp",
        "tests/semantic/існує-за-предикатом-mutant.lisp",
        # D6 ZIP dependent library-backed witnesses in native law suite.
        "tests/semantic/d6-zip-proper-law.lisp",
        "tests/semantic/d6-zip-proper-mutant.lisp",
        "tests/semantic/d6-zip-improper-tail-negative.lisp",
        "tests/semantic/d6-zip-improper-root-negative.lisp",
        # Core4 D6 FILTER fixture: execute with exact Core4 profile in the semantic bundle below.
        "tests/semantic/d6-filter-improper-tail-negative.lisp",
        "tests/semantic/ukr-lists-d24-language-law.lisp",
        "tests/semantic/d24-polynomial-language-law.lisp",
        "tests/semantic/d24-polynomial-language-mutant.lisp",
        "tests/semantic/d24-ackermann-language-law.lisp",
        "tests/semantic/d24-ackermann-language-mutant.lisp",
        "tests/semantic/d24-fibonacci-language-law.lisp",
        "tests/semantic/d24-fibonacci-language-mutant.lisp",
        "tests/semantic/d24-reader-fraction-language-law.lisp",
        "tests/semantic/d24-reader-fraction-language-mutant.lisp",
        "tests/semantic/d24-reader-zero-denominator-negative.lisp",
        "tests/semantic/d4-recursion-benchmark-law.lisp",
        "tests/semantic/d4-recursion-benchmark-mutant.lisp",
        # Ці D3 свідки залежать від DEFINE в benchmarks/d3-proper-tail-hot.lisp.
        # Тільки bundle проходить Lisp → Zig/T5M → SENS, не самотній .lisp.
        "tests/semantic/d3-proper-tail-hot-law.lisp",
        "tests/semantic/d3-proper-tail-hot-mutant.lisp",
        # Ці фікстури потребують DEFINE обійти із benchmarks/recursion.lisp.
        # Повний бандл law/mutant запускається через SENS/Zig/T5M нижче;
        # окремий змінений-файл без бібліотеки помилково дає UnknownSymbol.
        "tests/semantic/d4-recursion-atom-result-law.lisp",
        "tests/semantic/d4-recursion-atom-result-mutant.lisp",
        "tests/fixtures/conformance-transition-witness.lisp",
        # Ці дві допоміжні Lisp-бібліотеки виконуються лише в бандлі мовного свідка.
        "tests/fixtures/witness-runner.lisp",
        "tests/fixtures/epistemic-authority-witness.lisp",
        "tests/fixtures/d11-list-equality-improper-left-must-error.lisp",
        "tests/fixtures/d11-list-equality-improper-right-must-error.lisp",
        "tests/fixtures/d11-list-equality-invalid-singleton-must-error.lisp",
        "tests/fixtures/d11-list-equality-invalid-third-must-error.lisp",
        # DWIM D11: ці SENS-свідки вимагають попередні DEFINE,
        # тому запускаються тільки як фізичні пакети law-runner.
        "tests/fixtures/d11-dwim-exact-context-positive.lisp",
        "tests/fixtures/d11-dwim-extra-field-negative.lisp",
        "tests/fixtures/d11-dwim-unrelated-extra-field-negative.lisp",
        "tests/fixtures/d11-dwim-dotted-record-negative.lisp",
        # D11 UNFOLD terminal tail: виконувати тільки з canonical DEFINE через фізичний law-runner.
        "tests/fixtures/d11-unfold-terminal-left-atom-must-error.lisp",
        "tests/fixtures/d11-unfold-terminal-left-dotted-must-error.lisp",
        "tests/fixtures/d11-unfold-terminal-right-atom-must-error.lisp",
        "tests/fixtures/d11-unfold-terminal-right-dotted-must-error.lisp",
        # Д5/D24+: залежні SENS-свідки із DEFINE чинної числової бібліотеки.
        # Працюють тільки як зібрані SENS-програми law-runner.
        "tests/semantic/d5-exact-numbers-filter-law.lisp",
        "tests/semantic/d5-exact-numbers-filter-mutant.lisp",
        "tests/semantic/d5-exact-numbers-filter-improper-tail-negative.lisp",
        # Д6 ANY/ALL: негативні Type-свідки навмисне відхиляються;
        # виконуються тільки повним SENS law-runner із Core4.
        "tests/semantic/d6-any-improper-tail-negative.lisp",
        "tests/semantic/d6-all-improper-tail-negative.lisp",
        # Д3/Д4 ZIP laws depend on lib/list-zip-general.lisp and are run
        # by the canonical SENS law runner with that library prepended.
        # Do not execute these witnesses as isolated changed-file programs.
        "tests/semantic/d4-zip-equal-length-law.lisp",
        "tests/semantic/d4-zip-equal-length-mutant.lisp",
        "tests/semantic/d4-zip-extra-left-negative.lisp",
        "tests/semantic/d4-zip-extra-right-negative.lisp",
        "tests/semantic/d4-zip-improper-right-negative.lisp",
        # D9/F6 package-key laws need persistent-map/world/content-store/lisp-fs.
        # The dedicated native law runner assembles that dependency stack; do not
        # execute these leaf witnesses alone in the generic changed-file runner.
        "tests/semantic/d9-f6-package-key-canonicalization-law.lisp",
        "tests/semantic/d9-f6-package-key-canonicalization-mutant.lisp",
        # Д9/F6: два SENS-свідки форми bindings потребують DEFINE.
        "tests/semantic/d9-f6-bindings-shape-law.lisp",
        "tests/semantic/d9-f6-bindings-shape-mutant.lisp",
        # П’ять D9/F6 свідків потребують DEFINE lib/lisp-fs.lisp.
        # Їх виконує чинний фізичний Zig/T5M law-runner;
        # standalone без бібліотеки не є перевіркою мовного закону.
        "tests/semantic/d9-f6-object-addresses-law.lisp",
        "tests/semantic/d9-f6-object-addresses-mutant.lisp",
        "tests/semantic/d9-f6-object-addresses-d1-root-negative.lisp",
        "tests/semantic/d9-f6-object-addresses-d1-tail-negative.lisp",
        "tests/semantic/d9-f6-object-addresses-empty-address-negative.lisp",
        # D5 PAIRLIS: залежні від чинного SENS DEFINE у Core4.
        # Усі п'ять уже зареєстровані в native Zig/T5M law-runner.
        "tests/semantic/d5-pairlis-total-list-law.lisp",
        "tests/semantic/d5-pairlis-total-list-mutant.lisp",
        "tests/semantic/d5-pairlis-improper-key-tail-negative.lisp",
        "tests/semantic/d5-pairlis-improper-value-tail-negative.lisp",
        "tests/semantic/d5-pairlis-extra-value-negative.lisp",
        # Вхід F6 producer для Rust producer→consumer інтеграційного тесту,
        # не окремий мовний закон для самостійного виконання.
        "tests/fixtures/wsm-fs-record-producer.lisp",
    }:
        print(f"T5M_DEPENDENT_FIXTURE path={name} status=NOT_STANDALONE")
        continue
    if name not in selected:
        selected.append(name)
# Виконувані мовні закони: весь вердикт формулюється у Lisp/SENS.
if has_lisp or workflow_changed:
    for witness in (
        "tests/semantic/ukr-d3-structural-selftest.lisp",
        "tests/semantic/language-law-d1-d4-ukr.lisp",
        "tests/semantic/language-law-d4-closure-shadow-ukr.lisp",
        "tests/semantic/language-mutant-d4-closure-shadow-ukr.lisp",
        "tests/semantic/language-law-d3-cond-demand.lisp",
        "tests/semantic/language-mutant-d3-cond-demand.lisp",
        "tests/semantic/language-law-d4-parameter-shadowing.lisp",
        "tests/semantic/language-mutant-d4-parameter-shadowing.lisp",
        "tests/semantic/language-law-quote-inertness.lisp",
        "tests/semantic/language-mutant-quote-inertness.lisp",
        "tests/semantic/lisp-d4-lexical-closure-laws.lisp",
        "tests/semantic/lisp-d4-recursive-list-laws.lisp",
        "tests/semantic/lisp-d4-recursive-list-mutant.lisp",
        "tests/semantic/lisp-d3-atom-cond-laws.lisp",
        "tests/semantic/lisp-d3-cons-selectors-laws.lisp",
        "tests/semantic/lisp-d3-eq-branches-laws.lisp",
        "tests/semantic/language-law-d3-eq-symmetry-ukr.lisp",
        "tests/semantic/language-mutant-d3-eq-symmetry-ukr.lisp",
        "tests/semantic/lisp-d3-d4-list-self-verdict.lisp",
        "tests/semantic/d3-structural-native-t5m-law.lisp",
        "tests/semantic/d3-structural-native-t5m-mutant.lisp",
        # TRANSITIONAL #5854: D6 LENGTH ратифікований, але невикличний у T5M.
    ):
        if witness not in selected:
            selected.append(witness)
        print(f"SENS_LISP_SEMANTIC_LAW source={witness} authority=SENS")
manifest.write_text("".join(name + "\n" for name in selected), encoding="utf-8")
with output.open("a", encoding="utf-8") as out:
    out.write(f"has_lisp={'true' if has_lisp or workflow_changed else 'false'}\n")
    out.write(f"has_files={'true' if selected else 'false'}\n")
    out.write(f"has_rust={'true' if has_rust else 'false'}\n")
    out.write(f"has_zig={'true' if has_zig else 'false'}\n")
    # Передати точні шляхи цього запуску в нативний remint-job;
    # це інвентар вхідних джерел, не мовний вердикт.
    out.write("lisp_files<<SENS_LISP_FILES\n")
    lisp_files = manifest.read_text(encoding="utf-8")
    out.write(lisp_files)
    if lisp_files and not lisp_files.endswith("\n"):
        out.write("\n")
    out.write("SENS_LISP_FILES\n")
print(f"T5M_CHANGED_EXECUTABLE_LISP count={len(selected)}")
for name in selected:
    print(f"T5M_CHANGED_FILE {name}")
PY

      - uses: dtolnay/rust-toolchain@1.99.0
        if: ${{ always() }}
