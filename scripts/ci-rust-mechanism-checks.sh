#!/usr/bin/env bash
# Run all mandatory Rust mechanism checks with explicit first-failure diagnostics.
set -euo pipefail
# Name each native mechanism test so the first failed command is explicit in CI.
if cargo test --locked -p sens --lib source_heads_preserve_exact_d6_identity_for_lisp_owned_definitions -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=1 target=-p sens --lib source_heads_preserve_exact_d6_identity_for_lisp_owned_definitions"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=1 status=$status command=cargo test --locked -p sens --lib source_heads_preserve_exact_d6_identity_for_lisp_owned_definitions -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens --test build_projection_transfer -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=2 target=-p sens --test build_projection_transfer"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=2 status=$status command=cargo test --locked -p sens --test build_projection_transfer -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens-cli --test utf8_physical_d1 -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=3 target=-p sens-cli --test utf8_physical_d1"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=3 status=$status command=cargo test --locked -p sens-cli --test utf8_physical_d1 -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens --lib utf8_partial_bootstrap_is_not_reported_as_complete -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=4 target=-p sens --lib utf8_partial_bootstrap_is_not_reported_as_complete"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=4 status=$status command=cargo test --locked -p sens --lib utf8_partial_bootstrap_is_not_reported_as_complete -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens --lib io::tests:: -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=5 target=-p sens --lib io::tests::"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=5 status=$status command=cargo test --locked -p sens --lib io::tests:: -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p swarm-node --test integration generic_emit_cannot_forge_fenced_task_facts -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=6 target=-p swarm-node --test integration generic_emit_cannot_forge_fenced_task_facts"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=6 status=$status command=cargo test --locked -p swarm-node --test integration generic_emit_cannot_forge_fenced_task_facts -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens --test d5_list_search_laws -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=7 target=-p sens --test d5_list_search_laws"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=7 status=$status command=cargo test --locked -p sens --test d5_list_search_laws -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens-host --test capability_scoping local_model_ -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=8 target=-p sens-host --test capability_scoping local_model_"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=8 status=$status command=cargo test --locked -p sens-host --test capability_scoping local_model_ -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens-lsp --lib transport::tests:: -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=9 target=-p sens-lsp --lib transport::tests::"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=9 status=$status command=cargo test --locked -p sens-lsp --lib transport::tests:: -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens-cli --bin sens t5m_quoted_ -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=10 target=-p sens-cli --bin sens t5m_quoted_"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=10 status=$status command=cargo test --locked -p sens-cli --bin sens t5m_quoted_ -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens-cli --bin sens-math-t5m -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=11 target=-p sens-cli --bin sens-math-t5m"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=11 status=$status command=cargo test --locked -p sens-cli --bin sens-math-t5m -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens-cli --bin sens tcp_repl_frame_ -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=12 target=-p sens-cli --bin sens tcp_repl_frame_"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=12 status=$status command=cargo test --locked -p sens-cli --bin sens tcp_repl_frame_ -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens-cli --bin wsm-fs-record-producer -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=13 target=-p sens-cli --bin wsm-fs-record-producer"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=13 status=$status command=cargo test --locked -p sens-cli --bin wsm-fs-record-producer -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens-cli --bin wsm-fs-record-consumer -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=14 target=-p sens-cli --bin wsm-fs-record-consumer"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=14 status=$status command=cargo test --locked -p sens-cli --bin wsm-fs-record-consumer -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens-cli --test wsm_fs_f6_pipeline -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=15 target=-p sens-cli --test wsm_fs_f6_pipeline"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=15 status=$status command=cargo test --locked -p sens-cli --test wsm_fs_f6_pipeline -- --nocapture"
  exit "$status"
fi
if cargo test --locked -p sens --example fn_table_bench -- --nocapture; then
  echo "SENS_RUST_CHECK_PASS id=16 target=-p sens --example fn_table_bench"
else
  status=$?
  echo "::error::SENS_RUST_CHECK_FAILED id=16 status=$status command=cargo test --locked -p sens --example fn_table_bench -- --nocapture"
  exit "$status"
fi
