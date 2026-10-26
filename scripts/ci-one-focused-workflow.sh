#!/usr/bin/env bash
# Механічний бюджет GitHub Actions; семантичний оракул — лише SENS.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
cd "$root"
workflows=(.github/workflows/*.yml .github/workflows/*.yaml)
(("${#workflows[@]}" > 0)) || { echo "SENS_CI_BUDGET_FAIL no_workflows"; exit 1; }
errors=0
automatic_ci=0
for workflow in "${workflows[@]}"; do
  [[ -f "$workflow" ]] || continue
  events=""
  if grep -Eq '^on:[[:space:]]*\[' "$workflow"; then
    events="$(sed -nE 's/^on:[[:space:]]*\[([^]]*)\].*/\1/p' "$workflow" | tr ',' '\n' | sed -E "s/^[[:space:]'\" ]+|[[:space:]'\" ]+$//g")"
  elif grep -Eq '^on:[[:space:]]*[A-Za-z_-]' "$workflow"; then
    events="$(sed -nE 's/^on:[[:space:]]*([A-Za-z_-]+).*/\1/p' "$workflow" | head -n1)"
  else
    events="$(awk '
      /^on:[[:space:]]*$/ { inside=1; next }
      inside && /^[^[:space:]#]/ { exit }
      inside && /^  [A-Za-z0-9_-]+:[[:space:]]*$/ {
        event=$1; sub(/:$/, "", event); print event
      }' "$workflow")"
  fi
  if [[ -z "$events" ]]; then
    echo "SENS_CI_BUDGET_FAIL workflow=$workflow reason=missing_or_empty_events"
    errors=$((errors+1)); continue
  fi
  automatic="$(printf '%s\n' "$events" | grep -Ev '^(workflow_dispatch|workflow_call)$' || true)"
  if [[ "$workflow" == ".github/workflows/ci.yml" ]]; then
    automatic_ci=$((automatic_ci+1))
    got="$(printf '%s\n' "$automatic" | sort | tr '\n' ' ' | sed 's/[[:space:]]*$//')"
    if [[ "$got" != "pull_request push" ]]; then
      echo "SENS_CI_BUDGET_FAIL workflow=ci.yml expected='push pull_request' actual='$got'"
      errors=$((errors+1))
    fi
    grep -Eq '^  push:[[:space:]]*$' "$workflow" &&
    grep -Eq '^  pull_request:[[:space:]]*$' "$workflow" &&
    grep -Eq '^    branches:[[:space:]]*\[main\][[:space:]]*$' "$workflow" || {
      echo "SENS_CI_BUDGET_FAIL workflow=ci.yml reason=push_and_pr_must_target_main"; errors=$((errors+1));
    }
    awk '
      /^  push:[[:space:]]*$/ { block="push"; next }
      /^  pull_request:[[:space:]]*$/ { block="pull_request"; next }
      /^  [A-Za-z0-9_-]+:[[:space:]]*$/ { block="other"; next }
      block=="push" && /paths(-ignore)?:|tags(-ignore)?:|branches-ignore:/ { bad=1 }
      block=="pull_request" && /paths(-ignore)?:|branches-ignore:|types:/ { bad=1 }
      END { exit bad ? 1 : 0 }' "$workflow" || {
        echo "SENS_CI_BUDGET_FAIL workflow=ci.yml reason=trigger_filter_hides_required_checks"; errors=$((errors+1));
    }
  elif [[ -n "$automatic" ]]; then
    echo "SENS_CI_BUDGET_FAIL workflow=$workflow reason=additional_automatic_trigger events=$(printf '%s' "$automatic" | tr '\n' ' ')"
    errors=$((errors+1))
  fi
done
if [[ "$automatic_ci" -ne 1 ]]; then
  echo "SENS_CI_BUDGET_FAIL expected_one_central_ci actual=$automatic_ci"; errors=$((errors+1))
fi
promote=".github/workflows/contest-promote.yml"
if ! grep -Fq "if: \${{ github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main' }}" "$promote"; then
  echo "SENS_CI_BUDGET_FAIL id=contest-promote reason=job_not_pinned_to_main"; errors=$((errors+1))
fi
# Detect duplicate names and ids without a foreign-language runner or JSON output.
for field in name id; do
  if [[ "$field" == name ]]; then
    duplicates="$(grep -E '^      - name: ' .github/workflows/ci.yml | sed -E 's/^      - name: //' | sort | uniq -d || true)"
  else
    duplicates="$(grep -E '^        id: [A-Za-z][A-Za-z0-9_-]*$' .github/workflows/ci.yml | sed -E 's/^        id: //' | sort | uniq -d || true)"
  fi
  if [[ -n "$duplicates" ]]; then
    echo "SENS_CI_BUDGET_FAIL duplicate_$field: $duplicates"; errors=$((errors+1))
  fi
done
if grep -Eq 'python3?[^[:cntrl:]]*(test|bench|benchmark|trial|run\.py)|pytest([[:space:]]|$)|node[[:space:]]+--test|npm[[:space:]]+(test|run[[:space:]]+(test|bench|benchmark))|npx[[:space:]]+(jest|vitest|mocha)|bun[[:space:]]+test|deno[[:space:]]+test|go[[:space:]]+test([[:space:]]|$)' .github/workflows/*.yml .github/workflows/*.yaml; then
  echo "SENS_CI_BUDGET_FAIL foreign_test_or_benchmark_runner_in_active_workflow"; errors=$((errors+1))
fi
if (( errors != 0 )); then exit 1; fi
echo "SENS_CI_BUDGET_PASS workflows=${#workflows[@]} central_ci=ci.yml foreign_test_runners=0 json_output=false sha256_created=false"
