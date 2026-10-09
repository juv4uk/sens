# SENS code migration tools

Ці скрипти мігрують код до поточних точних SENS-кодів без хардкоду семантичних
координат. Authority завжди завантажується з `knowledge/d1-d7-foundation.json`;
згенерований звіт фіксує authority та SHA-256, тож результати можна відтворити
після зміни геометрії домену. Типово — dry-run; exit code 1 означає переписувані
символьні call-heads, exit code 2 — заблокований файл через однозначну семантичну
неоднозначність (напр. перевизначення канонічного імені поверхні SENS).
Переписуються лише executable S-expression list heads; рядки, коментарі, quoted
дані, пакетно-кваліфіковані імена та не-head-символи зберігаються.

These scripts migrate source toward current exact-width SENS codes without hard-coding semantic coordinates.

Authority is always loaded from:

`knowledge/d1-d7-foundation.json`

The generated report records the foundation authority and SHA-256, so outputs can be regenerated if domain geometry changes.

## 1. Audit one repository

```bash
python3 scripts/migrate-to-sens-codes.py ../wsm-my-lisp \
  --foundation knowledge/d1-d7-foundation.json
```

Default mode is dry-run. Exit code 1 means rewritable symbolic call heads were found. Exit code 2 means a file was blocked because of an obvious semantic ambiguity such as redefining a canonical SENS surface name.

## 2. Generate a converted mirror

```bash
python3 scripts/migrate-to-sens-codes.py ../wsm-my-lisp \
  --foundation knowledge/d1-d7-foundation.json \
  --mirror ../sens-migrated/wsm-my-lisp
```

Only executable S-expression list heads are rewritten. Strings, comments, quoted data, package-qualified names and non-head symbols are preserved.

## 3. Rewrite an already-SENS source tree in place

```bash
python3 scripts/migrate-to-sens-codes.py ./examples \
  --foundation knowledge/d1-d7-foundation.json \
  --apply
```

Use in-place mode only where exact-width SENS words are valid source. Do not use it on Rust, C, C++, Java, shell or workflow syntax.

## 4. Audit symbolic-name debt in host code

```bash
python3 scripts/audit-sens-name-debt.py ../cml \
  --foundation knowledge/d1-d7-foundation.json \
  --report /tmp/cml-sens-name-debt.json
```

This script does not rewrite host-language identifiers. It reports where human surface names are still coupled to semantic identity so those boundaries can be replaced deliberately.

## 5. Run across the ecosystem

```bash
python3 scripts/migrate-sens-ecosystem.py \
  ../cml ../wsm-my-lisp ../wsm-graalvm ../sens-futhark \
  --foundation knowledge/d1-d7-foundation.json \
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
