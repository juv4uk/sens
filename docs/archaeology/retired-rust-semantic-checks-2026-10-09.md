# Retired Rust semantic suites — archaeology record (2026-10-09)

## Authority and scope

Owner-ratified policy: [#5140](https://github.com/juv4uk/sens/issues/5140). Coordination and merge rule: [#5041](https://github.com/juv4uk/sens/issues/5041).

Commit [a6f611ca9d58246d48d7aaad32f353778af2daf8](https://github.com/juv4uk/sens/commit/a6f611ca9d58246d48d7aaad32f353778af2daf8), titled **test(rust): retire Lisp-owned semantic oracles outside the domain ladder**, removed the following active Rust integration-test files. The exact pre-deletion source revision was [1eb99907658959dd0592e1cf295966d90648e348](https://github.com/juv4uk/sens/commit/1eb99907658959dd0592e1cf295966d90648e348), its direct parent. The original file blobs remain recoverable from Git history; this register prevents silent loss of source provenance. No archived source is reintroduced into Cargo test discovery.

## Source manifest

| Removed path | Original blob SHA | Original `#[test]` annotations | Removal |
|---|---|---:|---|
| `crates/sens/tests/advice.rs` | `8f30b0695320452368b30177365509b011b58811` | 2 | `a6f611ca9d58246d48d7aaad32f353778af2daf8` |
| `crates/sens/tests/forward.rs` | `2480d63e1b7aa264c4d1283879f042703f753757` | 41 | `a6f611ca9d58246d48d7aaad32f353778af2daf8` |
| `crates/sens/tests/knowledge.rs` | `0ea8f423079aff6c195099fd822b495e8450d405` | 42 | `a6f611ca9d58246c4d1283879f042703f753757` |
| `crates/sens/tests/mccarthy.rs` | `bcb657fdf4fb7365d207611e23588af9f9cac6e3` | 34 | `a6f611ca9d58246d48d7aaad32f353778af2daf8` |
| `crates/sens/tests/meta_eval.rs` | `78aa04ca605ed9c8c09b250b735bdbbd96fb236d` | 13 | `a6f611ca9d58246d48d7aaad32f353778af2daf8` |
| `crates/sens/tests/narrate.rs` | `cda96edac6844cb51a1133dda63f7981ef3a71fe` | 6 | `a6f611ca9d58246d48d7aaad32f353778af2daf8` |
| `crates/sens/tests/reason.rs` | `af22147df2b07517611481d832962fca11fc7ec9` | 11 | `a6f611ca9d58246d48d7aaad32f353778af2daf8` |
| `crates/sens/tests/understand.rs` | `a66f750485cc7b9cb47f60ad7635084939dc260b` | 9 | `a6f611ca9d58246d48d7aaad32f353778af2daf8` |
| `crates/sens/tests/unify.rs` | `e608fa8322432e6dd1c7b7778100b1bc9b2e8b86` | 11 | `a6f611ca9d58246d48d7aaad32f353778af2daf8` |
| `crates/sens/tests/world.rs` | `c88f2c0a45843ad6c0f5f8bdaf3aecf9714b1e89` | 21 | `a6f611ca9d58246d48d7aaad32f353778af2daf8` |

Totals: **10 files, 190 original test annotations**.

## Classification caveat

This record pins each removed source blob and its deletion reason/provenance. It does **not** claim that every old assertion already has a replacement Lisp witness or that every assertion was independently adjudicated. Remaining coverage gaps must be tracked as migration work rather than treated as proven semantic equivalence. Neutral Rust substrate/domain-carrier checks remain separate from Lisp-owned language-law witnesses.

## Verification

This is an archaeology-only addition: no runtime source, domain coordinate, Lisp source, canonical fixture, or active test target is changed. CI status is not inferred from this record; the current-head hosted checks remain the merge gate.
