; semantic-ownership.lisp — виконуваний інвентар ownership для issue #25.
; Це дані, не семантичний контракт. Вони вимірюють лише вже аудитовану власність.
; Один рядок = одна поведінка/відповідальність. Без LOC-claim і без "self-hosting %".
(schema semantic-ownership/1)
(as-of "2026-09-17")
(scope audited-primary-behaviors)

; ownership KEY SEMANTIC_ID CLASS LAYER STATUS POLICY_CANDIDATE
;           "BEHAVIOR" "IMPLEMENTATION_PATHS" "EVIDENCE_PATHS" PREVIOUS_OWNER MIGRATION_REF
(ownership canon-empty-list - canon-ground canon confirmed no "Canon 0: порожній список як ground object" "crates/my-lisp/src/eval/canon.rs" "crates/my-lisp/src/eval/canon.rs;crates/my-lisp/tests/mccarthy.rs" - -)
(ownership canon-quote "00000001" canon-operation canon confirmed no "QUOTE: evaluator meaning і зарезервована surface resolution" "crates/my-lisp/src/eval/canon.rs;crates/my-lisp/src/eval/mod.rs" "crates/my-lisp/src/eval/canon.rs;crates/my-lisp/tests/mccarthy.rs" - -)
(ownership canon-atom "00000010" canon-operation canon confirmed no "ATOM: first-class канонічна операція" "crates/my-lisp/src/eval/canon.rs" "crates/my-lisp/src/eval/canon.rs;crates/my-lisp/tests/mccarthy.rs" - -)
(ownership canon-eq "00000011" canon-operation canon confirmed no "EQ: канонічна операція тотожності" "crates/my-lisp/src/eval/canon.rs" "crates/my-lisp/src/eval/canon.rs;crates/my-lisp/tests/mccarthy.rs" - -)
(ownership canon-cons "00000100" canon-operation canon confirmed no "CONS: канонічна операція побудови" "crates/my-lisp/src/eval/canon.rs" "crates/my-lisp/src/eval/canon.rs;crates/my-lisp/tests/mccarthy.rs" - -)
(ownership canon-car "00000101" canon-operation canon confirmed no "CAR: канонічна операція проєкції першого елемента" "crates/my-lisp/src/eval/canon.rs" "crates/my-lisp/src/eval/canon.rs;crates/my-lisp/tests/mccarthy.rs" - -)
(ownership canon-cdr "00000110" canon-operation canon confirmed no "CDR: канонічна операція структурного залишку" "crates/my-lisp/src/eval/canon.rs" "crates/my-lisp/src/eval/canon.rs;crates/my-lisp/tests/mccarthy.rs" - -)
(ownership canon-cond "00000111" canon-operation canon confirmed no "COND: канонічна short-circuit syntax" "crates/my-lisp/src/eval/canon.rs;crates/my-lisp/src/eval/mod.rs" "crates/my-lisp/src/eval/canon.rs;crates/my-lisp/tests/mccarthy.rs" - -)

(ownership necessary-lambda "00001000" necessary-form bootstrap confirmed no "LAMBDA: evaluator-controlled побудова closure" "crates/my-lisp/src/eval/necessary_forms.rs;crates/my-lisp/src/eval/closures.rs" "crates/my-lisp/tests/mccarthy.rs" - -)
(ownership necessary-define "00001001" necessary-form bootstrap confirmed no "DEFINE: evaluator-controlled immutable binding form" "crates/my-lisp/src/eval/necessary_forms.rs;crates/my-lisp/src/eval/mod.rs" "crates/my-lisp/tests/mccarthy.rs" - -)
(ownership macro-definition "00001010" lisp-owned bootstrap confirmed no "Поведінка визначення макросів виведена у lib/macro.lisp поверх вузького make-macro substrate" "lib/macro.lisp;crates/my-lisp/src/eval/macro_substrate.rs;crates/my-lisp/src/lib.rs" "crates/my-lisp/tests/macro_derivation.rs" host-mechanism 3fff9e9fbb7171a81ba128baedd68f093fc0c65b)

(ownership list-constructor - lisp-owned stdlib confirmed no "Варіадичний list-конструктор виведений із lambda/rest семантики самої мови" "lib/core.lisp" "crates/my-lisp/tests/mccarthy.rs" host-mechanism efdd9252fd4ca4af4503b219ab3ae79130ef0e64)
(ownership gensym - lisp-owned stdlib confirmed no "Політика свіжого символу складена в Lisp зі string-операцій і monotonic observation" "lib/core.lisp" "tests/fixtures/conformance.lisp;crates/my-lisp/tests/mccarthy.rs" - -)
(ownership meta-evaluator - lisp-owned self-hosting confirmed no "Lisp-owned metacircular evaluator witness; усі 34 required parity rows підтверджені machine evidence matrix" "lib/meta-eval.lisp;knowledge/meta-eval-evidence.lisp" "crates/xtask/src/checks.rs;crates/my-lisp/tests/witness_authority.rs;tests/fixtures/meta-semantic-registry-witness.lisp;crates/my-lisp/tests/meta_eval_error_kind_parity.rs;crates/my-lisp/tests/meta_eval_error_detail_boundary.rs" - -)

(ownership unification - lisp-owned reasoning confirmed no "Уніфікація логічних змінних з occurs-check" "lib/unify.lisp" "tests/fixtures/conformance.lisp" - -)
(ownership backward-reasoning - lisp-owned reasoning confirmed no "Backward-chaining пошук доказу й побудова provenance" "lib/reason.lisp" "crates/my-lisp/tests/reason_stack.rs;crates/my-lisp/tests/reason_index.rs" - -)
(ownership reason-index - lisp-owned reasoning confirmed no "Скінченний immutable predicate index із точним linear fallback" "lib/reason.lisp" "crates/my-lisp/tests/reason_index.rs;crates/my-lisp/tests/reason_advice_scale.rs" - -)
(ownership reasoning-outcomes - lisp-owned reasoning confirmed no "Data-only outcome algebra: proved/unknown/partial/blocked/disputed/invalid" "lib/result-status.lisp" "crates/my-lisp/tests/result_status.rs" - -)
(ownership knowledge-journal - lisp-owned knowledge confirmed no "Append-only журнал знань і guarded knowledge admission" "lib/knowledge.lisp" "crates/my-lisp/tests/knowledge.rs" - -)
(ownership immutable-worlds - lisp-owned knowledge confirmed no "Immutable world snapshots і явні переходи стану світу" "lib/world.lisp" "crates/my-lisp/tests/world.rs" - -)
(ownership translation-review - lisp-owned knowledge confirmed no "Валідація зовнішніх translation candidates і admission review" "lib/translation.lisp" "crates/my-lisp/tests/translation_boundary.rs" - -)
(ownership outcome-narration - lisp-owned reasoning confirmed no "Людське пояснення поверх структурованих reasoning outcomes" "lib/narrate.lisp" "crates/my-lisp/tests/narrate_outcomes.rs" - -)

(ownership time-semantics - lisp-owned stdlib confirmed no "UTC/calendar/deadline meaning виводиться в Lisp із raw clock observations" "lib/time.lisp;crates/my-lisp/src/lib.rs" "crates/my-lisp/tests/time_host_surface.rs;crates/my-lisp/tests/clock.rs" - -)
(ownership utf8-interpretation - lisp-owned stdlib confirmed no "Валідація та інтерпретація UTF-8 bytes → text" "lib/utf8.lisp" "crates/my-lisp-host/tests/process_text.rs" - -)
(ownership process-public-result - lisp-owned stdlib confirmed no "Публічна інтерпретація process-run result поверх process-run-raw" "lib/process.lisp;crates/my-lisp/src/lib.rs" "crates/my-lisp-host/tests/process_surface.rs;crates/my-lisp-host/tests/process_text.rs" - -)
(ownership tcp-text-semantics - lisp-owned stdlib confirmed no "Публічне декодування TCP text поверх raw socket bytes" "lib/tcp.lisp;crates/my-lisp/src/lib.rs" "crates/my-lisp-host/tests/portable_substrate.rs" - -)

(ownership monotonic-clock - host-observation host-capability confirmed no "Monotonic nanosecond observation без calendar policy" "crates/my-lisp/src/eval/builtins.rs" "crates/my-lisp/tests/clock.rs" - -)
(ownership process-run-raw - host-mechanism host-capability confirmed no "OS process execution і захоплення raw bytes" "crates/my-lisp-host/src/process_raw.rs;crates/my-lisp-host/src/lib.rs" "crates/my-lisp-host/tests/process_raw.rs;crates/my-lisp-host/tests/process_surface.rs" - -)
(ownership filesystem-authorization - host-authorization host-capability confirmed no "Per-session filesystem read/write scope і host canonicalization enforcement" "crates/my-lisp/src/environment.rs;crates/my-lisp-host/src/lib.rs" "crates/my-lisp-host/tests/capability_scoping.rs" - -)
(ownership process-authorization - host-authorization host-capability confirmed no "Per-session process allowlist, який Lisp-код не може видати собі сам" "crates/my-lisp/src/environment.rs;crates/my-lisp-host/src/process_raw.rs" "crates/my-lisp-host/tests/process_raw.rs;crates/my-lisp-host/tests/capability_scoping.rs" - -)
(ownership tcp-authorization - host-authorization host-capability confirmed no "Per-session connect/listen allowlists, перевірені до OS-операції" "crates/my-lisp/src/environment.rs;crates/my-lisp-host/src/lib.rs" "crates/my-lisp-host/tests/capability_scoping.rs" - -)
(ownership tcp-resource-representation - host-mechanism host-capability confirmed no "Concrete TcpStream/TcpListener storage is confined to core Value; semantics and OS operations remain host-only; opaque Rc<dyn Any> experiment proves representation can be erased when a real portability trigger appears" "crates/my-lisp/src/value.rs;crates/my-lisp-host/src/lib.rs" "crates/my-lisp/tests/host_resource_boundary.rs;crates/my-lisp-host/tests/tcp_handle_semantics.rs;crates/my-lisp-host/tests/tcp.rs" - -)

(ownership surface-registry-projection - host-mechanism tooling confirmed no "Rust projection/index mechanism читає numeric surface authority, не володіючи людськими spelling" "crates/my-lisp/src/semantic_registry.rs;lib/surface/semantic-registry.lisp" "crates/my-lisp/src/semantic_registry.rs;crates/my-lisp/tests/runtime_peer_operators.rs" host-hardcoded 668794caf6f3e2e1d0d6c8e740f218cc6ef04db9)
(ownership tooling-syntax-discovery - derived-tooling tooling confirmed no "Tooling metadata ключується semantic identity, а spelling отримує з registry" "crates/my-lisp/src/language_items.rs;crates/my-lisp/src/semantic_registry.rs" "crates/my-lisp/src/language_items.rs;crates/my-lisp/tests/uk_surface_inventory.rs" human-spelling-tooling e8f60f659199686205376ca4fd1c570034c05de6)

; migration KEY FROM_OWNER TO_OWNER STATUS COMMIT "BEHAVIOR" "CURRENT_EVIDENCE_PATHS"
(migration list-rust-to-lisp host-mechanism lisp-owned confirmed efdd9252fd4ca4af4503b219ab3ae79130ef0e64 "Rust special form list видалено; list визначено в lib/core.lisp" "lib/core.lisp;crates/my-lisp/tests/mccarthy.rs")
(migration defmacro-fallback-to-lisp host-mechanism lisp-owned confirmed 3fff9e9fbb7171a81ba128baedd68f093fc0c65b "Rust defmacro evaluator fallback видалено; поведінкою володіє language macro path" "lib/macro.lisp;crates/my-lisp/tests/macro_derivation.rs")
(migration necessary-form-surface-authority host-hardcoded registry-data confirmed 3fa2ae1f5e5786cd5c0b41489648a23bb1f405f5 "LAMBDA/DEFINE stable surface routing перенесено з Rust spelling tables у numeric registry projection" "crates/my-lisp/src/eval/necessary_forms.rs;crates/my-lisp/src/semantic_registry.rs")
(migration canon-surface-authority host-hardcoded registry-data confirmed 668794caf6f3e2e1d0d6c8e740f218cc6ef04db9 "Canon stable surface routing перенесено у shared numeric semantic registry projection" "crates/my-lisp/src/eval/canon.rs;crates/my-lisp/src/semantic_registry.rs")
(migration peer-builtin-surface-authority host-hardcoded registry-data confirmed dd4d9ae7d7bccbe465a0ae8ceb1b2f17f5f80f4e "Arithmetic/comparison peer names перенесено з Rust arrays у registry-derived bindings" "crates/my-lisp/src/eval/builtins.rs;crates/my-lisp/tests/runtime_peer_operators.rs")
(migration macro-peer-surface-authority host-hardcoded registry-data confirmed baa03b7acf0793bec3184a48099c484231922bea "00001010 stable і compatibility peer names перенесено з loader literals у registry admission" "crates/my-lisp/src/lib.rs;crates/my-lisp/tests/macro_derivation.rs")
(migration tooling-human-key-to-semantic-id human-spelling-tooling semantic-id-tooling confirmed e8f60f659199686205376ca4fd1c570034c05de6 "Tooling syntax discovery перенесено з human spelling keys на semantic identities" "crates/my-lisp/src/language_items.rs;crates/my-lisp/tests/uk_surface_inventory.rs")
(migration core-host-capability-split core-os-code host-adapter confirmed f565f6692c36a97f80afe0233f0bdb8dca506b81 "OS-touching filesystem/process/TCP операції перенесено з my-lisp core у my-lisp-host" "crates/my-lisp/src/eval/capabilities.rs;crates/my-lisp-host/src/lib.rs;crates/my-lisp-host/tests/portable_substrate.rs")
