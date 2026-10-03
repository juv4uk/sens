; semantic-ownership.lisp — виконуваний інвентар ownership для issue #25.
; Це дані, не семантичний контракт. Вони вимірюють лише вже аудитовану власність.
; Один рядок = одна поведінка/відповідальність. Без LOC-claim і без "self-hosting %".
(schema semantic-ownership/1)
(as-of "2026-09-17")
(scope audited-primary-behaviors)

; ownership KEY SEMANTIC_ID CLASS LAYER STATUS POLICY_CANDIDATE
;           "BEHAVIOR" "IMPLEMENTATION_PATHS" "EVIDENCE_PATHS" PREVIOUS_OWNER MIGRATION_REF
(ownership canon-empty-list - canon-ground canon confirmed no "Canon 0: порожній список як ground object" "crates/sens/src/eval/canon.rs" "crates/sens/src/eval/canon.rs;crates/sens/tests/mccarthy.rs" - -)
(ownership canon-quote 00000001 canon-operation canon confirmed no "QUOTE: evaluator meaning і зарезервована surface resolution" "crates/sens/src/eval/canon.rs;crates/sens/src/eval/mod.rs" "crates/sens/src/eval/canon.rs;crates/sens/tests/mccarthy.rs" - -)
(ownership canon-atom 00000010 canon-operation canon confirmed no "ATOM: first-class канонічна операція" "crates/sens/src/eval/canon.rs" "crates/sens/src/eval/canon.rs;crates/sens/tests/mccarthy.rs" - -)
(ownership canon-eq 00000011 canon-operation canon confirmed no "EQ: канонічна операція тотожності" "crates/sens/src/eval/canon.rs" "crates/sens/src/eval/canon.rs;crates/sens/tests/mccarthy.rs" - -)
(ownership canon-cons 00000100 canon-operation canon confirmed no "CONS: канонічна операція побудови" "crates/sens/src/eval/canon.rs" "crates/sens/src/eval/canon.rs;crates/sens/tests/mccarthy.rs" - -)
(ownership canon-car 00000101 canon-operation canon confirmed no "CAR: канонічна операція проєкції першого елемента" "crates/sens/src/eval/canon.rs" "crates/sens/src/eval/canon.rs;crates/sens/tests/mccarthy.rs" - -)
(ownership canon-cdr 00000110 canon-operation canon confirmed no "CDR: канонічна операція структурного залишку" "crates/sens/src/eval/canon.rs" "crates/sens/src/eval/canon.rs;crates/sens/tests/mccarthy.rs" - -)
(ownership canon-cond 00000111 canon-operation canon confirmed no "COND: канонічна short-circuit syntax" "crates/sens/src/eval/canon.rs;crates/sens/src/eval/mod.rs" "crates/sens/src/eval/canon.rs;crates/sens/tests/mccarthy.rs" - -)

(ownership necessary-lambda 00001000 necessary-form bootstrap confirmed no "LAMBDA: evaluator-controlled побудова closure" "crates/sens/src/eval/necessary_forms.rs;crates/sens/src/eval/closures.rs" "crates/sens/tests/mccarthy.rs" - -)
(ownership necessary-define 00001001 necessary-form bootstrap confirmed no "DEFINE: evaluator-controlled immutable binding form" "crates/sens/src/eval/necessary_forms.rs;crates/sens/src/eval/mod.rs" "crates/sens/tests/mccarthy.rs" - -)
(ownership macro-definition 00001010 lisp-owned bootstrap confirmed no "Поведінка визначення макросів виведена у lib/macro.lisp поверх вузького make-macro substrate" "lib/macro.lisp;crates/sens/src/eval/macro_substrate.rs;crates/sens/src/lib.rs" "crates/sens/tests/macro_derivation.rs" host-mechanism 3fff9e9fbb7171a81ba128baedd68f093fc0c65b)

(ownership list-constructor - lisp-owned stdlib confirmed no "Варіадичний list-конструктор виведений із lambda/rest семантики самої мови" "lib/core.lisp" "crates/sens/tests/mccarthy.rs" host-mechanism efdd9252fd4ca4af4503b219ab3ae79130ef0e64)
(ownership gensym - lisp-owned stdlib confirmed no "Політика свіжого символу складена в Lisp зі string-операцій і monotonic observation" "lib/core.lisp" "tests/fixtures/conformance.lisp;crates/sens/tests/mccarthy.rs" - -)
(ownership meta-evaluator - lisp-owned self-hosting confirmed no "Lisp-owned metacircular evaluator witness; усі 34 required parity rows підтверджені machine evidence matrix" "lib/meta-eval.lisp;knowledge/meta-eval-evidence.lisp" "scripts/verify-repo.lisp;crates/sens/tests/witness_authority.rs;tests/fixtures/meta-semantic-registry-witness.lisp;crates/sens/tests/meta_eval_error_kind_parity.rs;crates/sens/tests/meta_eval_error_detail_boundary.rs" - -)

(ownership unification - lisp-owned reasoning confirmed no "Уніфікація логічних змінних з occurs-check" "lib/unify.lisp" "tests/fixtures/conformance.lisp" - -)
(ownership backward-reasoning - lisp-owned reasoning confirmed no "Backward-chaining пошук доказу й побудова provenance" "lib/reason.lisp" "crates/sens/tests/reason_stack.rs;crates/sens/tests/reason_index.rs" - -)
(ownership reason-index - lisp-owned reasoning confirmed no "Скінченний immutable predicate index із точним linear fallback" "lib/reason.lisp" "crates/sens/tests/reason_index.rs;crates/sens/tests/reason_advice_scale.rs" - -)
(ownership reasoning-outcomes - lisp-owned reasoning confirmed no "Data-only outcome algebra: proved/unknown/partial/blocked/disputed/invalid" "lib/result-status.lisp" "crates/sens/tests/result_status.rs" - -)
(ownership knowledge-journal - lisp-owned knowledge confirmed no "Append-only журнал знань і guarded knowledge admission" "lib/knowledge.lisp" "crates/sens/tests/knowledge.rs" - -)
(ownership immutable-worlds - lisp-owned knowledge confirmed no "Immutable world snapshots і явні переходи стану світу" "lib/world.lisp" "crates/sens/tests/world.rs" - -)
(ownership translation-review - lisp-owned knowledge confirmed no "Валідація зовнішніх translation candidates і admission review" "lib/translation.lisp" "crates/sens/tests/translation_boundary.rs" - -)
(ownership outcome-narration - lisp-owned reasoning confirmed no "Людське пояснення поверх структурованих reasoning outcomes" "lib/narrate.lisp" "crates/sens/tests/narrate_outcomes.rs" - -)

(ownership time-semantics - lisp-owned stdlib confirmed no "UTC/calendar/deadline meaning виводиться в Lisp із raw clock observations" "lib/time.lisp;crates/sens/src/lib.rs" "crates/sens/tests/time_host_surface.rs;crates/sens/tests/clock.rs" - -)
(ownership utf8-interpretation - lisp-owned stdlib confirmed no "Валідація та інтерпретація UTF-8 bytes → text" "lib/utf8.lisp" "crates/sens-host/tests/process_text.rs" - -)
(ownership process-public-result - lisp-owned stdlib confirmed no "Публічна інтерпретація process-run result поверх process-run-raw" "lib/process.lisp;crates/sens/src/lib.rs" "crates/sens-host/tests/process_surface.rs;crates/sens-host/tests/process_text.rs" - -)
(ownership tcp-text-semantics - lisp-owned stdlib confirmed no "Публічне декодування TCP text поверх raw socket bytes" "lib/tcp.lisp;crates/sens/src/lib.rs" "crates/sens-host/tests/portable_substrate.rs" - -)

(ownership monotonic-clock - host-observation host-capability confirmed no "Monotonic nanosecond observation без calendar policy" "crates/sens/src/eval/builtins.rs" "crates/sens/tests/clock.rs" - -)
(ownership process-run-raw - host-mechanism host-capability confirmed no "OS process execution і захоплення raw bytes" "crates/sens-host/src/process_raw.rs;crates/sens-host/src/lib.rs" "crates/sens-host/tests/process_raw.rs;crates/sens-host/tests/process_surface.rs" - -)
(ownership filesystem-authorization - host-authorization host-capability confirmed no "Per-session filesystem read/write scope і host canonicalization enforcement" "crates/sens/src/environment.rs;crates/sens-host/src/lib.rs" "crates/sens-host/tests/capability_scoping.rs" - -)
(ownership process-authorization - host-authorization host-capability confirmed no "Per-session process allowlist, який Lisp-код не може видати собі сам" "crates/sens/src/environment.rs;crates/sens-host/src/process_raw.rs" "crates/sens-host/tests/process_raw.rs;crates/sens-host/tests/capability_scoping.rs" - -)
(ownership tcp-authorization - host-authorization host-capability confirmed no "Per-session connect/listen allowlists, перевірені до OS-операції" "crates/sens/src/environment.rs;crates/sens-host/src/lib.rs" "crates/sens-host/tests/capability_scoping.rs" - -)
(ownership tcp-resource-representation - host-mechanism host-capability confirmed no "Concrete TcpStream/TcpListener storage is confined to core Value; semantics and OS operations remain host-only; opaque Rc<dyn Any> experiment proves representation can be erased when a real portability trigger appears" "crates/sens/src/value.rs;crates/sens-host/src/lib.rs" "crates/sens/tests/host_resource_boundary.rs;crates/sens-host/tests/tcp_handle_semantics.rs;crates/sens-host/tests/tcp.rs" - -)

(ownership surface-registry-projection - host-mechanism tooling confirmed no "Rust projection/index mechanism читає numeric surface authority, не володіючи людськими spelling" "crates/sens/src/semantic_registry.rs;lib/surface/semantic-registry.lisp" "crates/sens/src/semantic_registry.rs;crates/sens/tests/runtime_peer_operators.rs" host-hardcoded 668794caf6f3e2e1d0d6c8e740f218cc6ef04db9)
(ownership tooling-syntax-discovery - derived-tooling tooling confirmed no "Tooling metadata ключується semantic identity, а spelling отримує з registry" "crates/sens/src/language_items.rs;crates/sens/src/semantic_registry.rs" "crates/sens/src/language_items.rs;crates/sens/tests/uk_surface_inventory.rs" human-spelling-tooling e8f60f659199686205376ca4fd1c570034c05de6)

; migration KEY FROM_OWNER TO_OWNER STATUS COMMIT "BEHAVIOR" "CURRENT_EVIDENCE_PATHS"
(migration list-rust-to-lisp host-mechanism lisp-owned confirmed efdd9252fd4ca4af4503b219ab3ae79130ef0e64 "Rust special form list видалено; list визначено в lib/core.lisp" "lib/core.lisp;crates/sens/tests/mccarthy.rs")
(migration defmacro-fallback-to-lisp host-mechanism lisp-owned confirmed 3fff9e9fbb7171a81ba128baedd68f093fc0c65b "Rust defmacro evaluator fallback видалено; поведінкою володіє language macro path" "lib/macro.lisp;crates/sens/tests/macro_derivation.rs")
(migration necessary-form-surface-authority host-hardcoded registry-data confirmed 3fa2ae1f5e5786cd5c0b41489648a23bb1f405f5 "LAMBDA/DEFINE stable surface routing перенесено з Rust spelling tables у numeric registry projection" "crates/sens/src/eval/necessary_forms.rs;crates/sens/src/semantic_registry.rs")
(migration canon-surface-authority host-hardcoded registry-data confirmed 668794caf6f3e2e1d0d6c8e740f218cc6ef04db9 "Canon stable surface routing перенесено у shared numeric semantic registry projection" "crates/sens/src/eval/canon.rs;crates/sens/src/semantic_registry.rs")
(migration peer-builtin-surface-authority host-hardcoded registry-data confirmed dd4d9ae7d7bccbe465a0ae8ceb1b2f17f5f80f4e "Arithmetic/comparison peer names перенесено з Rust arrays у registry-derived bindings" "crates/sens/src/eval/builtins.rs;crates/sens/tests/runtime_peer_operators.rs")
(migration macro-peer-surface-authority host-hardcoded registry-data confirmed baa03b7acf0793bec3184a48099c484231922bea "00001010 stable і compatibility peer names перенесено з loader literals у registry admission" "crates/sens/src/lib.rs;crates/sens/tests/macro_derivation.rs")
(migration tooling-human-key-to-semantic-id human-spelling-tooling semantic-id-tooling confirmed e8f60f659199686205376ca4fd1c570034c05de6 "Tooling syntax discovery перенесено з human spelling keys на semantic identities" "crates/sens/src/language_items.rs;crates/sens/tests/uk_surface_inventory.rs")
(migration core-host-capability-split core-os-code host-adapter confirmed f565f6692c36a97f80afe0233f0bdb8dca506b81 "OS-touching filesystem/process/TCP операції перенесено з my-lisp core у my-lisp-host" "crates/sens/src/eval/capabilities.rs;crates/sens-host/src/lib.rs;crates/sens-host/tests/portable_substrate.rs")
