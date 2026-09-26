# SENS-REALITY-2 — current-main reality audit after #1477

**Issue:** #1433  
**Snapshot:** `main@bd271c92d74fdf7a0064b054a2696a92a1ca8e77`  
**Date:** 2026-09-26  
**Scope:** evidence/research only. No runtime changes.

This slice replaces stale structural claims from the 2026-09-25 benchmark era with facts that are true on current main. Timing claims are deliberately separated: the fresh `Language benchmark (instructions, base vs change)` run for #1477 is still queued on the self-hosted Guix runner, so this document does **not** invent current speed ratios.

## 1. Structural reality moved materially

| Metric | earlier #1433 snapshot | current main | status |
| --- | ---: | ---: | --- |
| named source call-head ratchet | 25,832 | **22,229** | improved |
| runtime non-SENS surface rows | 326 | **208** | improved |
| Rust named-builtin surface rows | >0 | **0** | eliminated by #1477 |
| exact-SENS Rust primitive slots | 13 | **46** | expanded |
| generated function-table rows | 255 | **256** | fixed by #1474 |
| authority registry rows | 256 | **256** | complete |

The numbers above come from current repository projections/tests, not from prose in old issues.

## 2. Claims from the original #1433 that are now superseded

### “English names are resolved on every call”

**Superseded as a universal claim.**

`crates/sens/src/eval/lower.rs` lowers immutable admitted heads once into:

`ExprKind::Call(Sens8, Rc<[Expr]>)`

so the evaluator does not repeat a human-name lookup for those calls. Shadowable heads intentionally remain lexical lists; that is a different case and needs a fresh benchmark rather than reusing the old 1.05–2.34× range.

### “Named Rust builtin and SENS code are two implementations”

**Superseded for current builtin installation.**

After #1477, `crates/sens/src/eval/builtins.rs` has no `environment.define(...)` builtin installation path. Current builtin mechanisms are admitted by exact SENS slots in `PRIMITIVE_TABLE`.

This does not mean every one of 256 functions is a Rust primitive. Language-defined closures/macros are deliberately separate mechanisms.

### “Generated function table has fewer identities than authority”

**Fixed.**

#1474 made the generated projection complete over all **256** exact SENS functions, including `00000000`, without aliasing it to `()`.

### “There is no benchmark CI”

**Fixed.**

`.github/workflows/sens-bench.yml` now runs deterministic Valgrind instruction-count comparison on the self-hosted Guix runner for 11 workloads × English/SENS forms, base versus change.

Current limitation: one self-hosted runner means evidence can queue behind functional CI; queued is not measured.

## 3. Current gaps that remain real

### 3.1 Named source debt

The baseline still contains **22,229** source call-heads written through admitted human surfaces instead of exact SENS. This is lower than the prior 25,832 but still large.

M1–M7 should be judged by this counter reaching the intended target without changing behavior.

### 3.2 Runtime surface rows

The runtime ratchet has **208** non-SENS surface rows:

- **185** Lisp-closure surface rows;
- **23** macro surface rows;
- **0** Rust named-builtin rows.

Interpretation matters: 208 is a count of admitted surface rows, not 208 distinct functions.

### 3.3 Exact macro reachability blocker is fixed

Merged #1468 added language-defined exact-code slots and pre-argument macro dispatch. Merged #1487 then bound the bootstrap `defmacro` Macro to its already-resolved exact slot `00001010`.

#1460 is now closed. Current black-box M0 evidence also exercises exact `or` and `let*` parity. The remaining macro-related migration risk is different: language macros can still construct quoted **surface** operator heads at expansion time; that is tracked separately by #1485.

### 3.4 Tail-call AST clone remains

Current evaluator code still returns tail calls with:

`expression: last.clone()`

for ordinary closure tail positions. This is a code-confirmed candidate cost, not yet a measured bottleneck on current main.

### 3.5 Representation remains allocation/reference-count heavy

Current `Value` / AST representation still uses `Rc`, `RefCell`, heap-backed lists/vectors/closures and arbitrary-precision rational components. Old byte-size numbers must be remeasured after representation changes; this audit does not reuse the old 64/80-byte figures as current fact.

## 4. Modern-tech audit: current classification

| Technique | current evidence |
| --- | --- |
| deterministic benchmark CI | **present** — `sens-bench.yml` |
| exact-SENS compact function identity | **present** — `Sens8` is 1 byte |
| one-time immutable-head lowering | **present** |
| tracing/generational GC | not found in current core; values use Rc/RefCell ownership |
| general JIT / Cranelift backend | not found in active evaluator |
| SIMD execution | machine metadata mentions AVX2 opportunities; broad executable SIMD coverage not established |
| core evaluator parallelism | not established; CLI/swarm/host code does use threads, so “repo has no threads” would be false |
| proptest / quickcheck / cargo-fuzz | no current code-search hits; negative search evidence only |

## 5. Next measurements — do not infer before they run

1. Fresh #1477 instruction-count artifact from `sens-bench`.
2. Current `size_of::<Value>() / ExprKind / Expr` witness.
3. Fresh cold-start instruction count after #1477.
4. Surface-vs-exact-SENS split into:
   - immutable heads already lowered once;
   - shadowable lexical heads.
5. Current `meta_eval_mutual` timing.
6. Current machine lowering inventory after M4: declared SENS rows versus executable transitions.
7. Re-run non-SENS inventory after each M1–M7 slice.

## 6. Current interpretation

The architecture is no longer honestly described by the strongest 25 September criticisms. In particular, named Rust builtin dispatch and the 255-row generated table are gone, and immutable surface lookup is no longer repeated universally.

The remaining performance/reality work is narrower and more measurable:

- remove the remaining source-name debt safely;
- finish the parser-aware source migration gate (M0 #1446/#1482) and macro-generated-head cleanup (#1485);
- measure allocation/clone/bootstrap costs on current code;
- prove how much of the machine/SIMD path is executable rather than descriptive;
- use fresh benchmark artifacts rather than carrying old ratios across major runtime rewrites.

This is a bounded evidence slice of #1433, not closure of the research issue.
