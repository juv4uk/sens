# Pinned path manifest: executable vs declarative (#4460)

Мета: задовольнити приймання #4460 — *класифікувати виконувані vs Lisp-дані таблиці* і
зафіксувати path manifest, щоб декларативні файли **ніколи** не кодувались auto-T5 без
окремого контракту. Метод: прогнати канонічний мігратор по `lib/`, взяти head першої
форми кожного файлу; head, що є версіонованою схемою/документом (`name/N`) або відомим
документним head, — **декларативний**; решта — **виконавчі кандидати** (заблоковані з
інших причин, перелічені для беклогу наступників). Підсумок: **49 декларативних**,
**79 виконавчих кандидатів** (з 128 файлів `lib/`).

Purpose: satisfy #4460 acceptance — *classify executable vs Lisp-data tables* and pin a
path manifest, so declarative files are **never** auto-T5-encoded without a separate contract.

Method: run the canonical migrator over `lib/`, take each file's FIRST-form head; a head that
is a versioned schema/document (`name/N`) or a known document head is **declarative**; the rest
are **executable candidates** (still blocked for other reasons, listed for the successor backlog).

Totals: **49 declarative**, **79 executable-candidate** (of 128 `lib/` files).

## Declarative heads (must NOT be auto-encoded)

| head | files |
|---|---|
| `isa-catalogue/1` | 25 |
| `domain-table/1` | 9 |
| `schema` | 2 |
| `ft/2` | 1 |
| `uk-surface-audit/2` | 1 |
| `machine-authority-boundary/1` | 1 |
| `skylake-client-inventory/1` | 1 |
| `cpu-profile/1` | 1 |
| `machine-effect-boundary/1` | 1 |
| `x86-admission-iclass-projection/1` | 1 |
| `x86-admitted-iclass-index/2` | 1 |
| `x86-encoder-coverage/1` | 1 |
| `machine-profile/1` | 1 |
| `machine-domain-profile/2` | 1 |
| `xed-machine-evidence/1` | 1 |
| `xed-provenance/1` | 1 |

## Declarative files

- `lib/domains/d1.lisp`  — head `domain-table/1`
- `lib/domains/d2.lisp`  — head `domain-table/1`
- `lib/domains/d3.lisp`  — head `domain-table/1`
- `lib/domains/d4.lisp`  — head `domain-table/1`
- `lib/domains/d5.lisp`  — head `domain-table/1`
- `lib/domains/d6.lisp`  — head `domain-table/1`
- `lib/domains/d7.lisp`  — head `domain-table/1`
- `lib/domains/d8.lisp`  — head `domain-table/1`
- `lib/domains/d9.lisp`  — head `domain-table/1`
- `lib/function-table-mechanisms.lisp`  — head `schema`
- `lib/generated/function-table.lisp`  — head `ft/2`
- `lib/generated/uk-surface-audit.lisp`  — head `uk-surface-audit/2`
- `lib/island-math-evidence.lisp`  — head `schema`
- `lib/machine/authority-boundary.lisp`  — head `machine-authority-boundary/1`
- `lib/machine/cpu/intel-core-i5-6400-inventory.lisp`  — head `skylake-client-inventory/1`
- `lib/machine/cpu/intel-core-i5-6400.lisp`  — head `cpu-profile/1`
- `lib/machine/effect-boundary.lisp`  — head `machine-effect-boundary/1`
- `lib/machine/encoding/admission-iclass-projection.lisp`  — head `x86-admission-iclass-projection/1`
- `lib/machine/encoding/admitted-iclass-index.lisp`  — head `x86-admitted-iclass-index/2`
- `lib/machine/encoding/coverage.lisp`  — head `x86-encoder-coverage/1`
- `lib/machine/intel-core-i5-6400.lisp`  — head `machine-profile/1`
- `lib/machine/isa/adx.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/aes-ni.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/avx.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/avx2.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/bmi1.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/bmi2.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/clflushopt.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/f16c.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/fma3.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/mmx.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/mpx.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/pclmulqdq.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/rdrand.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/rdseed.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/sgx.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/sse.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/sse2.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/sse3.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/sse4.1.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/sse4.2.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/ssse3.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/x86-64.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/x86-base.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/x87.lisp`  — head `isa-catalogue/1`
- `lib/machine/isa/xsave.lisp`  — head `isa-catalogue/1`
- `lib/machine/profile/current-domain-x86-64.lisp`  — head `machine-domain-profile/2`
- `lib/machine/xed/generated/machine-evidence.lisp`  — head `xed-machine-evidence/1`
- `lib/machine/xed/provenance.lisp`  — head `xed-provenance/1`

## Executable candidates (blocked for successor/structure reasons)

- `lib/bridge/prolog-to-datalog.lisp`
- `lib/canon.lisp`
- `lib/clips-import.lisp`
- `lib/compiler-nucleus.lisp`
- `lib/content-store.lisp`
- `lib/core.lisp`
- `lib/core1-compiler-prelude.lisp`
- `lib/core1-compiler-sid-resolver.lisp`
- `lib/core1-sid8-bootstrap-overlay.lisp`
- `lib/core1.lisp`
- `lib/core2.lisp`
- `lib/core3.lisp`
- `lib/core4.lisp`
- `lib/epistemic.lisp`
- `lib/forward.lisp`
- `lib/fs.lisp`
- `lib/generated/meta-semantic-registry.lisp`
- `lib/guard.lisp`
- `lib/island-lowering.lisp`
- `lib/knowledge.lisp`
- `lib/life-1-scheduler.lisp`
- `lib/linter.lisp`
- `lib/lisp-fs.lisp`
- `lib/machine/admission/x86-64.lisp`
- `lib/machine/atoms/x86-64.lisp`
- `lib/machine/block.lisp`
- `lib/machine/capability-axis.lisp`
- `lib/machine/capability-provenance.lisp`
- `lib/machine/dispatch/native-first-coverage.lisp`
- `lib/machine/dispatch/native-first-execute.lisp`
- `lib/machine/dispatch/native-first-parity.lisp`
- `lib/machine/dispatch/native-first.lisp`
- `lib/machine/effects/u64.lisp`
- `lib/machine/encoding/x86-64.lisp`
- `lib/machine/layout/pair-x86-64.lisp`
- `lib/machine/lowering/semantic-effects.lisp`
- `lib/machine/lowering/semantic-x86-64.lisp`
- `lib/machine/operands/x86-64.lisp`
- `lib/machine/profile/minimal-runtime-x86-64.lisp`
- `lib/machine/projection/x86-64.lisp`
- `lib/macro.lisp`
- `lib/mechanism-selector.lisp`
- `lib/meta-eval-first-class.lisp`
- `lib/meta-eval-mutual.lisp`
- `lib/meta-eval.lisp`
- `lib/narrate.lisp`
- `lib/persistent-map.lisp`
- `lib/persistent-vector.lisp`
- `lib/process.lisp`
- `lib/quantity.lisp`
- `lib/reason.lisp`
- `lib/result-status.lisp`
- `lib/si-derived.lisp`
- `lib/si.lisp`
- `lib/surface/d5-definition-bindings.lisp`
- `lib/surface/function-signatures.lisp`
- `lib/surface/peer-identity-acceptance.lisp`
- `lib/surface/sa.lisp`
- `lib/surface/semantic-registry-api.lisp`
- `lib/surface/semantic-registry-experiment.lisp`
- `lib/surface/semantic-registry.lisp`
- `lib/surface/uk-acceptance.lisp`
- `lib/surface/uk-docs.lisp`
- `lib/surface/uk-inventory.lisp`
- `lib/surface/uk-name-audit.lisp`
- `lib/surface/uk-sa-coverage.lisp`
- `lib/surface/uk.lisp`
- `lib/surface/ukr-acceptance.lisp`
- `lib/surface/ukr.lisp`
- `lib/surface/український-профіль-джерела.lisp`
- `lib/tcp.lisp`
- `lib/time.lisp`
- `lib/translation.lisp`
- `lib/understand.lisp`
- `lib/unify-observe.lisp`
- `lib/unify.lisp`
- `lib/utf8.lisp`
- `lib/world.lisp`
- `lib/yantra.lisp`

## Boundary

This is computed from the migrator's own verdicts on the current tree; heads may change after the
alias-table fix. The manifest is a *classification*, not a ratification — the owner decides which
declarative files get a separate encode contract.
