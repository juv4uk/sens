#!/usr/bin/env bash
# Самоперевірка гейту: позитивний запис ARCHIVE та негативний новий foreign test.
set -euo pipefail
repo="$(git rev-parse --show-toplevel)"
gate="$repo/scripts/check-language-policy-archive.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
git -C "$tmp" init -q
git -C "$tmp" config user.name "SENS gate self-test"
git -C "$tmp" config user.email "sens-gate-self-test@example.invalid"
mkdir -p "$tmp/tests/legacy" "$tmp/benchmarks/legacy" "$tmp/docs"
printf 'print("historical artifact")\n' > "$tmp/tests/legacy/test_old.py"
printf '#!/usr/bin/env sh\necho historical benchmark\n' > "$tmp/benchmarks/legacy/old_runner.sh"
fake_sha=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
cat > "$tmp/docs/language-policy-archive.md" <<EOF
Артефакт | Локація | Причина виключення з гейту | Статус
--- | --- | --- | ---
tests/legacy/test_old.py | tests/legacy/test_old.py | Legacy archive fixture; https://github.com/juv4uk/sens/commit/$fake_sha | ARCHIVE
benchmarks/legacy/old_runner.sh | benchmarks/legacy/old_runner.sh | Legacy archived runner fixture; https://github.com/juv4uk/sens/commit/$fake_sha | ARCHIVE
EOF
git -C "$tmp" add .
git -C "$tmp" commit -qm "baseline archive fixture"
printf 'self-test positive witness\n' > "$tmp/docs/note.md"
git -C "$tmp" add docs/note.md
git -C "$tmp" commit -qm "positive archive witness"
positive="$(SENS_PR_FIRST_FIELD='SENS_SOURCE=tests/legacy/test_old.sens' bash "$gate" --root "$tmp" 2>&1)"
if [[ "$positive" != *"ARCHIVE (поза мовним коридором): 2 артефактів — docs/language-policy-archive.md"* ]]; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL positive witness did not report one archived artifact"
  printf '%s\n' "$positive"
  exit 1
fi
# Existing shell benchmark without an archive row must be rejected too.
printf '#!/usr/bin/env sh\necho unregistered historical runner\n' > "$tmp/benchmarks/legacy/unregistered_runner.sh"
git -C "$tmp" add benchmarks/legacy/unregistered_runner.sh
git -C "$tmp" commit -qm "negative unregistered shell archive witness"
if SENS_PR_FIRST_FIELD='SENS_SOURCE=tests/legacy/test_old.sens' bash "$gate" --root "$tmp" > "$tmp/shell-negative.log" 2>&1; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL unregistered historical shell runner was accepted"
  cat "$tmp/shell-negative.log"
  exit 1
fi
if ! grep -q 'unregistered_exclusion=benchmarks/legacy/unregistered_runner.sh' "$tmp/shell-negative.log"; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL shell archive escaped complete extension scan"
  cat "$tmp/shell-negative.log"
  exit 1
fi
# Required new foreign-test negative witness.
mkdir -p "$tmp/tests/new"
printf 'print("new foreign test")\n' > "$tmp/tests/new/test_foreign.py"
git -C "$tmp" add tests/new/test_foreign.py
git -C "$tmp" commit -qm "negative foreign test witness"
if SENS_PR_FIRST_FIELD='' bash "$gate" --root "$tmp" > "$tmp/negative.log" 2>&1; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL negative witness was accepted"
  cat "$tmp/negative.log"
  exit 1
fi
if ! grep -q 'SENS_SOURCE_FIRST_FIELD_REQUIRED' "$tmp/negative.log" || ! grep -q 'unregistered_exclusion=tests/new/test_foreign.py' "$tmp/negative.log" || ! grep -q 'NEW_FOREIGN_TEST_ARCHIVE_FORBIDDEN' "$tmp/negative.log"; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL negative witness failed for the wrong reason"
  cat "$tmp/negative.log"
  exit 1
fi
echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=VALID positive=ARCHIVE_COUNTED negative=NEW_FOREIGN_TEST_RED"
