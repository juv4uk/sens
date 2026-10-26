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
mkdir -p "$tmp/tests/legacy" "$tmp/benchmarks/legacy" "$tmp/docs" "$tmp/scripts"
printf '#!/usr/bin/env sh\necho SENS runner\n' > "$tmp/scripts/execute_changed_lisp_t5m.sh"
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
positive="$(SENS_EVENT_NAME=pull_request SENS_PR_FIRST_FIELD='SENS_SOURCE=tests/legacy/test_old.sens' bash "$gate" --root "$tmp" 2>&1)"
if [[ "$positive" != *"ARCHIVE (поза мовним коридором): 2 артефактів — docs/language-policy-archive.md"* ]]; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL positive witness did not report one archived artifact"
  printf '%s\n' "$positive"
  exit 1
fi
# Push має власний native SENS test без PR-body; не вимагати
# довільного префікса коміт-повідомлення замість PR-контракту.
mkdir -p "$tmp/tests/new"
printf '(твердження)\n' > "$tmp/tests/new/push_native.lisp"
git -C "$tmp" add tests/new/push_native.lisp
git -C "$tmp" commit -qm "native SENS test on push"
if ! SENS_EVENT_NAME=push SENS_PR_FIRST_FIELD='' bash "$gate" --root "$tmp" > "$tmp/push-native.log" 2>&1; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL new SENS test on push was rejected without PR metadata"
  cat "$tmp/push-native.log"
  exit 1
fi
# Pull request with a new native test requires SENS_SOURCE first.
printf '(твердження)\n' > "$tmp/tests/new/pr_native.lisp"
git -C "$tmp" add tests/new/pr_native.lisp
git -C "$tmp" commit -qm "native SENS test in PR"
if SENS_EVENT_NAME=pull_request SENS_PR_FIRST_FIELD='' bash "$gate" --root "$tmp" > "$tmp/pr-native-negative.log" 2>&1; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL native PR test without SENS_SOURCE was accepted"
  cat "$tmp/pr-native-negative.log"
  exit 1
fi
if ! grep -q 'SENS_SOURCE_FIRST_FIELD_REQUIRED path=tests/new/pr_native.lisp' "$tmp/pr-native-negative.log"; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL native PR test failed for the wrong reason"
  cat "$tmp/pr-native-negative.log"
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
if SENS_EVENT_NAME=pull_request SENS_PR_FIRST_FIELD='' bash "$gate" --root "$tmp" > "$tmp/negative.log" 2>&1; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL negative witness was accepted"
  cat "$tmp/negative.log"
  exit 1
fi
if ! grep -q 'SENS_SOURCE_FIRST_FIELD_REQUIRED' "$tmp/negative.log" || ! grep -q 'unregistered_exclusion=tests/new/test_foreign.py' "$tmp/negative.log" || ! grep -q 'NEW_FOREIGN_TEST_ARCHIVE_FORBIDDEN' "$tmp/negative.log"; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL negative witness failed for the wrong reason"
  cat "$tmp/negative.log"
  exit 1
fi
# Test receipt-generation rejection in a clean tree. Earlier negative
# witnesses intentionally leave unregistered artifacts in $tmp, so reusing
# that tree can fail before the digest guard and misreport the cause.
hash_tmp="$(mktemp -d)"
trap 'rm -rf "$tmp" "$hash_tmp"' EXIT
git -C "$hash_tmp" init -q
git -C "$hash_tmp" config user.name "SENS digest gate self-test"
git -C "$hash_tmp" config user.email "sens-digest-gate@example.invalid"
mkdir -p "$hash_tmp/scripts" "$hash_tmp/tests/legacy" "$hash_tmp/benchmarks/legacy" "$hash_tmp/docs"
printf '#!/usr/bin/env sh\necho native carrier\n' > "$hash_tmp/scripts/execute_changed_lisp_t5m.sh"
printf 'historical fixture\n' > "$hash_tmp/tests/legacy/test_old.py"
printf '#!/usr/bin/env sh\necho legacy\n' > "$hash_tmp/benchmarks/legacy/old_runner.sh"
cat > "$hash_tmp/docs/language-policy-archive.md" <<EOF
Артефакт | Локація | Причина виключення з гейту | Статус
--- | --- | --- | ---
tests/legacy/test_old.py | tests/legacy/test_old.py | Archived artifact; https://github.com/juv4uk/sens/commit/$fake_sha | ARCHIVE
benchmarks/legacy/old_runner.sh | benchmarks/legacy/old_runner.sh | Archived runner; https://github.com/juv4uk/sens/commit/$fake_sha | ARCHIVE
EOF
git -C "$hash_tmp" add .
git -C "$hash_tmp" commit -qm "clean baseline for digest negative witness"
printf '#!/usr/bin/env sh\nsha256sum source > source.sha256\n' > "$hash_tmp/scripts/execute_changed_lisp_t5m.sh"
git -C "$hash_tmp" add scripts/execute_changed_lisp_t5m.sh
git -C "$hash_tmp" commit -qm "negative digest-generation witness"
if SENS_EVENT_NAME=push SENS_PR_FIRST_FIELD='' bash "$gate" --root "$hash_tmp" > "$hash_tmp/hash-negative.log" 2>&1; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL digest generation was accepted"
  cat "$hash_tmp/hash-negative.log"
  exit 1
fi
if ! grep -q 'digest_creation_forbidden path=scripts/execute_changed_lisp_t5m.sh' "$hash_tmp/hash-negative.log"; then
  echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=FAIL digest witness rejected for wrong reason"
  cat "$hash_tmp/hash-negative.log"
  exit 1
fi
echo "LANGUAGE_POLICY_ARCHIVE_SELFTEST=VALID positive=ARCHIVE_COUNTED negative=NEW_FOREIGN_TEST_RED"
