#!/usr/bin/env python3
"""Fail-closed preparation gate: migration scripts ↔ Zig physical codec.

Does NOT invent semantics. Does NOT admit programs. Does NOT write .lisp/.sens.

Runs the already-contracted mechanical checks the swarm needs before a
migration batch, in fixed order:

  0. zig-pin                 — .zig-version == 0.16.0 and install-zig default
  1. ci_zig_purity           — no W8/Sens8/SID-8 contamination in *.zig
  2. check_sterile_zig_corridor — default Rust↔SENS uses the Zig ABI
  3. check_rust_sens_zig_corridor — R1–R5 host-neutral C↔Zig physical ABI
  4. check_rust_sens_corridor_coverage — no invisible Rust-host bypass
  5. check_corridor_axiom_binding — guard rules trace to SENS axioms
  5b. report_rust_zig_sens_boundary — publish Rust↔Zig↔SENS map (file+SHA; report mode)
  6. check-domain-ladder-identity — width=identity on canonical surfaces
  7. migrate-exact-domain authority load — D3/D4 tables + owner ratification
  8. test_zig_codec_bridge   — REQUIRED physical T5 round-trip; --self-test is NOT a full gate

Chronology / ratification history is documented, not re-derived here:
  docs/migration/semantic-chronology-handoff-2026-10-14.uk.md
  docs/migration/chronology-authority-handoff-2026-10-14.uk.md
  docs/zig-migration-scripts-handoff-2026-10-14.uk.md

Axiom reminder (language-core / owner):
  width of the binary key IS the domain address;
  Zig is a turnstile (physical transport), never the registry of meaning;
  historical W8 is provenance archive, not current identity.

Full gate PASS requires every required step. --self-test returns SELF_TEST_ONLY
(no transport evidence); incomplete full gate exits 2.
"""
# SEE_REPO_FOR_FULL_BODY
raise SystemExit('MIGRATION_ZIG_GATE_PLACEHOLDER_RESTORE_PENDING')
