# Checkpoint — D11 SPAN/BREAK physical pair and RED triage
Date: 2026-10-24 (Europe/Kyiv)
Repository: https://github.com/juv4uk/sens
Branch: main

## Canonical SENS/Zig/T5M pair

The CI evidence artifact from run 40095322675 was retrieved and unpacked. The two sidecars below came from the actual SENS CLI + Zig/T5M mint outputs; they were not hand-generated.

- Source: lib/d11-srfi1-span-break.lisp (source includes the SENS_PAIR_REGEN comment marker used for this one-off regeneration).
- Physical bytes: lib/d11-srfi1-span-break.sens, 1,118 bytes, SHA-256 ab5b9369ae47d88c2b5f134a164b1b6cee96beb142c314177a75db0bf7bdd2b6, Git blob af93e845fffed74cec409441511d3444e88ff5a5.
- Binary view: lib/d11-srfi1-span-break, 5,588 ASCII bytes, SHA-256 a7b530ac7a845b4c8a3c2c307a6435de4ac2e15cc873633015e3f25889d50669, Git blob 01fa1cdb48eb88aa55977a053a349df1642fe22d.

Commit a9464fd79942b5bb915f0ba72288e61c39162eb6 stored the correct physical .sens bytes. A byte-for-byte comparison caught an incorrect view in that first commit. Commit 9765721bcc3610ad92075fa4e887b269213e42c6 replaced the view with the exact generator output. GitHub read-back confirmed both expected blob SHAs.

## Hosted proof status

CI run 40104162539 for commit 9765721bcc3610ad92075fa4e887b269213e42c6 was in_progress at the last read. Therefore the pair is byte-exact relative to the generator artifact, but physical execution/round-trip is still NOT_VERIFIED until that hosted run completes. Do not report PASS based on artifact matching alone.

## Known RED roots

Run 40095322675 ended failure after 176/180 laws passed. Four D11 list-equality type witnesses — d11-list-equality-improper-left-type, d11-list-equality-improper-right-type, d11-list-equality-invalid-singleton-type, d11-list-equality-invalid-third-type — returned unexpected-success from the direct SENS evaluator (exit 0), not merely a diagnostic-string mismatch. The intended SENS library validates each input list and then forces D3 CAR on an empty list to produce Type, but that error path did not execute for these four fixtures. Do not soften these tests or simply alter the expected error text: inspect the concrete value shapes and the SENS conditional/ATOM/false-predicate semantics, then fix the actual cause in the SENS definition or fixture.

A later completed run 40101733545 recorded six different RED cases: d5-reverse-onto-improper-tail, d5-reverse-improper-tail, d6-map-onto-improper-tail, d11-reason-index-law, d11-reason-index-improper-rules, d11-family-selection-reject-atom-type. Keep those separate from the four list-equality failures; use exact run/job receipts for diagnosis.

## Next agent work order

1. Read the newest CI result for 40104162539 and the subsequent run triggered by checkpoint creation. If pair/view drift remains, inspect exact logs and do not relax the gate.
2. Debug the four list-equality unexpected-success cases by comparing direct input fixtures, expected structures, SENS control flow and the real diagnostic. Add/update a paired positive+negative proof only after understanding the root cause.
3. Work through the six separate RED cases from run 40101733545 one by one. Do not claim D11 is closed from a subset of green witnesses.
4. Resume the broad D1–D11 resident/callability ledger and D12+ numeric-source/REPL audit. D12 is a numeric width domain, not a callable-function catalogue. Shared CLI/REPL remains D24-first. The D6 ledger last reported 60/64 residents without mechanical proof.

## Architectural status

D1–D4 are the truth/structure and core language mechanisms; D5–D10 domain residents must be distinguished from actual callability; D11 helpers remain SENS compositions/selectors, not new opcodes; D12+ remains the numeric domain ladder. Current work has closed the byte-copy error for SPAN/BREAK, not the full physical verification or all D1–D12+ functions. Release GO is NOT granted.
