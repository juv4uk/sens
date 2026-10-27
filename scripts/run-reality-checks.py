#!/usr/bin/env python3
"""Вбудовані перевірки реальності.

Кожен гейт тут — інформативний і ПРОЙШОВ на чинному main (перевірено локально
перед вбудовуванням). Раніше кожен лежав окремим ручним воркфлоу й ніколи не
біг; тепер біжить на кожен push. Механічний бюджет — семантику визначає
двійковий SENS, не цей Python.
"""
import hashlib
import os
import subprocess
import sys

CHECKS = [
    "scripts/check-cross-width-law-atlas.py",
    "scripts/check-d10-archived-donors.py",
    "scripts/check-d10-fill-v1-seed.py",
    "scripts/check-d10-owner-repo-donor-matrix-v2.py",
    "scripts/check-d4-cleanroom-full-candidate.py",
    "scripts/check-d5-internal-law-atlas.py",
    "scripts/check-d6-mechanism-census.py",
    "scripts/check-d6-v2-cleanroom-shadow.py",
    "scripts/check-d6-v2-law-first-ledger.py",
    "scripts/check-d8-fill-v2-seed.py",
    "scripts/check-d8-v2-semantic-inventory.py",
    "scripts/check-d9-fill-v1-seed.py",
    "scripts/check-domain-altitude-economy.py",
    "scripts/check-foundation-debt.py",
    "scripts/check-identity-witness-gate.py",
    "scripts/check-migrated-head-residency.py",
    "scripts/check-od005-od006-full-maps.py",
    "scripts/check-width-authority-boundary.py",
    "scripts/check_d10_allen_atms_research.py",
    "scripts/check_d10_binary_lyndon_factorization.py",
    "scripts/check_d10_brzozowski_ai_source.py",
    "scripts/check_d10_clhs_pathnames_census.py",
    "scripts/check_d10_clhs_streams_census.py",
    "scripts/check_d10_clos_lifecycle_history.py",
    "scripts/check_d10_clos_slot_state_history.py",
    "scripts/check_d10_cycle_witness_hobbies.py",
    "scripts/check_d10_cyclic_word_canon.py",
    "scripts/check_d10_d9_donor_dedup.py",
    "scripts/check_d10_debruijn_binary_cycle.py",
    "scripts/check_d10_finite_subsumes.py",
    "scripts/check_d10_finite_transducer_cross_hobby.py",
    "scripts/check_d10_flavors_restarts_research_v1.py",
    "scripts/check_d10_general_congruence_merge_hobbies.py",
    "scripts/check_d10_gps_means_ends_history.py",
    "scripts/check_d10_ground_congruence_research.py",
    "scripts/check_d10_historical_clos_interlisp_review.py",
    "scripts/check_d10_historical_gap_audit.py",
    "scripts/check_d10_lower_mechanical_word.py",
    "scripts/check_d10_maling_symbolic_differentiation.py",
    "scripts/check_d10_mop_reader_census.py",
    "scripts/check_d10_owner_whole_domain_ratification.py",
    "scripts/check_d10_placement_proof_crosswalk.py",
    "scripts/check_d10_r6rs_copy_mutable_oracle.py",
    "scripts/check_d10_r7rs_primary_slice.py",
    "scripts/check_d10_reason_alternate_define_donor_v1.py",
    "scripts/check_d10_state_distinguishing_suffix.py",
    "scripts/check_d10_stern_brocot_runs.py",
    "scripts/check_d10_strips_goal_regression.py",
    "scripts/check_d10_time_law_review_v2.py",
    "scripts/check_d10_v13_standards.py",
    "scripts/check_d10_v17_complete_research_gauge.py",
    "scripts/check_d10_v18_research_placement.py",
    "scripts/check_domain_source_delta_d3.py",
    "scripts/check_main_only_branch_history.py",
    "scripts/check_semantic_registry.py",]

def main() -> int:
    failures = []
    for rel in CHECKS:
        try:
            r = subprocess.run([sys.executable, rel], capture_output=True, text=True)
            rc = r.returncode
            blob = (r.stdout + r.stderr).encode("utf-8", "replace")
        except OSError as exc:
            rc, blob = 127, str(exc).encode()
        digest = hashlib.sha256(blob).hexdigest()
        tail = (blob.decode("utf-8", "replace").strip().splitlines() or [""])[-1][:200]
        if rc == 0:
            print(f"test_id={os.path.basename(rel)} layer=mechanical PASS", flush=True)
        else:
            print(
                f"test_id={os.path.basename(rel)} layer=mechanical FAIL rc={rc} "
                f"output_sha256={digest} tail={tail!r}",
                flush=True,
            )
            # The final JSON brace is never an actionable diagnosis.
            # Preserve actual output and the exact one-command replay.
            print(f"SENS_REALITY_FAILURE test_id={os.path.basename(rel)} "
                  f"commit={os.environ.get('GITHUB_SHA', 'LOCAL')} "
                  f"reproduce={sys.executable} {rel}", flush=True)
            print("SENS_REALITY_FAILURE_OUTPUT_BEGIN", flush=True)
            print(blob.decode("utf-8", "replace")[-12000:], flush=True)
            print("SENS_REALITY_FAILURE_OUTPUT_END", flush=True)
            failures.append(rel)
    if failures:
        print(f"REALITY-CHECKS-FAIL {len(failures)}/{len(CHECKS)}", flush=True)
        return 1
    print(f"REALITY-CHECKS-PASS {len(CHECKS)} gates", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
