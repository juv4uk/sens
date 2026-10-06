# CML Lowering → SENS Migration Analysis

## File: cml/src/lower.rs (1034 lines)

### Dependencies to remove (Sid8-based)
- Line 58-73: SID-keyed definition lookup (uses Sid8)
- Line 117-118: MATH_SIDS constant (classification by Sid8)
- Line 246: sid_keyed_defs HashSet<Sens8>
- Line 322: "exact Sens8" comment & logic
- Line 365: lower_sid_head(sid: Sid8, ...)
- Line 444: "dispatches by its Sens8 call key"
- Line 537: lower_sid_call(sid: Sid8, ...)
- Line 748: "SID-keyed define"
- Line 889: "dispatches by its typed Sens8"

### Functions to keep (DomainIdentity-compatible)
- lower_program() → lower_program_with_domain_identity()
- lower_expr() → needs rewrite for DomainIdentity
- lower_call() → dispatch on DomainIdentity
- lower_quote() → stays mostly same
- lower_cond() → stays same
- lower_lambda() → stays same
- lower_let() → stays same

### What changes
- Expr::Sid → Expr::DomainIdentity
- MATH_SIDS table → query SENS semantic classifier
- lower_sid_head/call → generic lower_domain_call with DomainIdentity dispatch
- Environment tracking: keep, adapt to DomainIdentity keys

### What SENS provides
- DomainIdentity carrier & width tracking ✓
- D3 operation semantics (law #3202) ✓
- D4 operation semantics (contract #3272) ✓
- Callable role projection (compiler_language.rs) ✓
- No legacy Sid8 anywhere ✓

## Next: Start Phase 1 commit
