# SENS code migration tools

These scripts migrate source toward current exact-width SENS codes without hard-coding semantic coordinates.

Authority is verified against the complete ratified D1–D9 ladder and the Number width law:

- `knowledge/d1-d9-foundation.json` — all D1–D9 coordinates checked against `lib/domains/d1.lisp` … `d9.lisp`;
- `knowledge/number-width-ratified.json` — D24/D48/D96/D192 exact widths; width ratification does **not** define a numeric literal bit-layout.

The D3–D6 resident set remains the historically proved **executable migration subset**. D7 is text; D8/D9 residency does not authorize executing arbitrary calls. D10 remains unratified. Unproven legacy DIVIDE → D5 QUOTIENT must fail closed: D8 DIVIDE is distinct.

The generated report records the foundation authority and SHA-256, so outputs can be regenerated if domain geometry changes.

## 1. Audit one repository

```bash
python3 scripts/migrate-to-sens-codes.py ../wsm-my-lisp \
  --foundation knowledge/d1-d9-foundation.json
```

Default mode is dry-run. Exit code 1 means rewritable symbolic call heads were found. Exit code 2 means a file was blocked because of an obvious semantic ambiguity such as redefining a canonical SENS surface name.

## 2. Generate a converted mirror

```bash
python3 scripts/migrate-to-sens-codes.py ../wsm-my-lisp \
  --foundation knowledge/d1-d9-foundation.json \
  --mirror ../sens-migrated/wsm-my-lisp
```

Only executable S-expression list heads are rewritten. Strings, comments, quoted data, package-qualified names and non-head symbols are preserved.

## 3. Rewrite an already-SENS source tree in place

```bash
python3 scripts/migrate-to-sens-codes.py ./examples \
  --foundation knowledge/d1-d9-foundation.json \
  --apply
```

Use in-place mode only where exact-width SENS words are valid source. Do not use it on Rust, C, C++, Java, shell or workflow syntax.

## 4. Audit symbolic-name debt in host code

```bash
python3 scripts/audit-sens-name-debt.py ../cml \
  --foundation knowledge/d1-d9-foundation.json \
  --report /tmp/cml-sens-name-debt.json
```

This script does not rewrite host-language identifiers. It reports where human surface names are still coupled to semantic identity so those boundaries can be replaced deliberately.

## 5. Run across the ecosystem

```bash
python3 scripts/migrate-sens-ecosystem.py \
  ../cml ../wsm-my-lisp ../wsm-graalvm ../sens-futhark \
  --foundation knowledge/d1-d9-foundation.json \
  --mirror-root ../sens-migrated
```

The orchestrator writes one report per repository plus an aggregate summary.

## Design rule

Migration is a derived projection, not a new semantic authority.

```text
current ratified foundation
        ↓
manifest-driven migration
        ↓
generated exact-width source
```

If the ratified geometry changes later, regenerate from the new foundation instead of preserving stale coordinates by hand.


## Current application-library witness: `lib/si-derived.lisp`

Run both existing scripts against a real library, without manual substitution or extra file-envelope tools, using the dedicated hosted CI workflow `.github/workflows/si-derived-migrator-probe.yml` in PR #4437.

- `migrate-three-pass.py` recognizes historical functions, **but** output can retain unresolved names/numbers, so it is **not** yet canonical binary. In particular, historical `00001111` DIVIDE must NOT silently become D5 QUOTIENT; it is a migration blocker pending proven D8 call admission.
- `migrate-to-sens-codes.py --binary-mirror` correctly refuses Number literal `2` until an owner-proven 24-bit numeric value codec exists. D24 width alone cannot justify an invented signedness, endianness or integer layout.
- D10 research missing-functions notes go to #4013 and #4301; a missing migration implementation is **not** itself a new D10 semantic resident.
- Never publish partially translated extensionless programs into `master` just because their filename has no suffix. Preserve source until all identities and round-trip witnesses are valid.
