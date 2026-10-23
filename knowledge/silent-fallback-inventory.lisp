;; Інвентар тихих відкатів (#2134).
;; Базис для scripts/check-silent-fallback-classes.py: відомий сайт проходить,
;; НОВИЙ неіменований сайт не проходить. Перегенерувати з --emit-inventory.
;; Classes: total-serializer-fallback | implicit-default-flag |
;;          fail-fast-hides-suites | silent-regeneration.
;; 2026-10-23: старі silent-regeneration рядки прибрано після аудиту живого дерева.
;; Нині scripts/generate*.lisp та lib/generated/*.lisp не містять активних W8/трьохпольових COND-шаблонів.
(silent-fallback-inventory
  (site (class "fail-fast-hides-suites") (file ".github/workflows/ci.yml") (key "fail-fast-hides-suites|.github/workflows/ci.yml|cargo test --workspace") (line "278"))
  (site (class "fail-fast-hides-suites") (file ".github/workflows/full-nightly.yml") (key "fail-fast-hides-suites|.github/workflows/full-nightly.yml|run: cargo test --workspace") (line "34"))
  (site (class "implicit-default-flag") (file "crates/sens/src/environment.rs") (key "implicit-default-flag|crates/sens/src/environment.rs|pub fn is_tcp_connect_allowed(&self, host: &str, port: u16) -> bool {") (line "174"))
  (site (class "implicit-default-flag") (file "crates/sens/src/environment.rs") (key "implicit-default-flag|crates/sens/src/environment.rs|pub fn is_tcp_listen_allowed(&self, address: &str, port: u16) -> bool {") (line "183"))
  (site (class "implicit-default-flag") (file "crates/sens/tests/semantic_authority.rs") (key "implicit-default-flag|crates/sens/tests/semantic_authority.rs|fn alist_flag(entries: &[Expr], key: &str) -> bool {") (line "103"))
  (site (class "implicit-default-flag") (file "crates/sens/tests/witness_authority.rs") (key "implicit-default-flag|crates/sens/tests/witness_authority.rs|fn alist_flag(entries: &[Expr], key: &str) -> bool {") (line "58"))
  (site (class "total-serializer-fallback") (file "crates/sens/src/value.rs") (key "total-serializer-fallback|crates/sens/src/value.rs|_ => render(value, true),") (line "852"))
  (site (class "total-serializer-fallback") (file "crates/sens/src/presentation.rs") (key "total-serializer-fallback|crates/sens/src/presentation.rs|_ => format!(\"#<host-об'єкт {kind}>\"),") (line "53"))
  (site (class "total-serializer-fallback") (file "crates/sens/src/value.rs") (key "total-serializer-fallback|crates/sens/src/value.rs|_ => format!(\"#<host-handle {kind}>\"),") (line "780"))
)
