use sens::{eval_program, load_core_library, Session};

fn eval_store(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/unify.lisp",
        include_str!("../../../lib/unify.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/reason.lisp",
        include_str!("../../../lib/reason.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/forward.lisp",
        include_str!("../../../lib/forward.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/knowledge.lisp",
        include_str!("../../../lib/knowledge.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/persistent-map.lisp",
        include_str!("../../../lib/persistent-map.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/world.lisp",
        include_str!("../../../lib/world.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/content-store.lisp",
        include_str!("../../../lib/content-store.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/lisp-fs.lisp",
        include_str!("../../../lib/lisp-fs.lisp"),
        &mut session,
    )
    .unwrap();
    eval_program(source, &mut session)
        .unwrap()
        .value
        .to_string()
}

fn eval_store_fixture(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/unify.lisp",
        include_str!("../../../lib/unify.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/reason.lisp",
        include_str!("../../../lib/reason.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/forward.lisp",
        include_str!("../../../lib/forward.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/knowledge.lisp",
        include_str!("../../../lib/knowledge.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/persistent-map.lisp",
        include_str!("../../../lib/persistent-map.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/world.lisp",
        include_str!("../../../lib/world.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/content-store.lisp",
        include_str!("../../../lib/content-store.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/lisp-fs.lisp",
        include_str!("../../../lib/lisp-fs.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_fs_fixture_source(
        "tests/fixtures/lisp-fs-conformance.lisp",
        source,
        &mut session,
    )
    .expect("pinned filesystem conformance fixture must execute as exact domains")
    .value
    .to_string()
}

fn eval_store_error(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/unify.lisp",
        include_str!("../../../lib/unify.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/reason.lisp",
        include_str!("../../../lib/reason.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/forward.lisp",
        include_str!("../../../lib/forward.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/knowledge.lisp",
        include_str!("../../../lib/knowledge.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/persistent-map.lisp",
        include_str!("../../../lib/persistent-map.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/world.lisp",
        include_str!("../../../lib/world.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/content-store.lisp",
        include_str!("../../../lib/content-store.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/lisp-fs.lisp",
        include_str!("../../../lib/lisp-fs.lisp"),
        &mut session,
    )
    .unwrap();
    eval_program(source, &mut session)
        .expect_err("malformed serialized data must fail closed")
        .to_string()
}

#[test]
fn lisp_fs_keeps_old_snapshot_and_reads_new_bindings() {
    assert_eq!(
        eval_store(
            r#"
            (let ((empty (фс-порожній)))
              (let ((first-write (фс-записати empty "notes/today" (quote (hello world)))))
                (let ((old (car first-write))
                      (second-write (фс-записати (car first-write)
                                              "notes/tomorrow"
                                              (quote (hello again)))))
                  (let ((new (car second-write)))
                    (list
                      (фс-читати old "notes/today")
                      (фс-читати old "notes/tomorrow")
                      (фс-читати new "notes/today")
                      (фс-читати new "notes/tomorrow")
                      (фс-ревізія old)
                      (фс-ревізія new))))))
            "#
        ),
        "((found (hello world) \"(hello world)\") (not-found \"notes/tomorrow\") (found (hello world) \"(hello world)\") (found (hello again) \"(hello again)\") 1 2)"
    );
}

#[test]
fn lisp_fs_deduplicates_equal_objects_but_keeps_explicit_missing_status() {
    // Canonical D1 membership is a one-bit predicate, not a structural (1).
    assert_eq!(
        eval_store(
            r#"
            (let ((empty (фс-порожній)))
              (let ((a (фс-записати empty "a" (quote ()))))
                (let ((b (фс-записати (car a) "b" (quote ()))))
                  (list
                    (content-store-size (фс-об'єкти (car b)))
                    (фс-містить? (car b) "a")
                    (фс-читати (car b) "missing")))))
            "#
        ),
        "(1 1 (not-found \"missing\"))"
    );
}

#[test]
fn lisp_fs_conformance_fixture_is_deterministic() {
    assert_eq!(
        eval_store_fixture(include_str!("../../../tests/fixtures/lisp-fs-conformance.lisp")),
        "((found (hello world) \"(hello world)\") (not-found \"notes/empty\") (found () \"()\") (not-found \"missing\") 2 1 2)"
    );
}

#[test]
fn lisp_fs_overwrite_is_a_new_revision_and_old_value_remains_in_old_root() {
    assert_eq!(
        eval_store(
            r#"
            (let ((empty (фс-порожній)))
              (let ((a (фс-записати empty "same" (quote old))))
                (let ((b (фс-записати (car a) "same" (quote new))))
                  (list
                    (фс-читати (car a) "same")
                    (фс-читати (car b) "same")
                    (фс-ревізія (car a))
                    (фс-ревізія (car b))))))
            "#
        ),
        "((found old \"old\") (found new \"new\") 1 2)"
    );
}

#[test]
fn lisp_fs_empty_name_is_literal_and_unknown_object_address_is_not_found() {
    assert_eq!(
        eval_store(
            r#"
            (let ((empty (фс-порожній)))
              (let ((written (фс-записати empty "" (quote value))))
                (let ((malformed
                        (list (фс-об'єкти (car written))
                              (мапа-вставити "ghost" "missing-address" мапа-порожній)
                              9)))
                  (list
                    (фс-читати (car written) "")
                    (фс-читати malformed "ghost")
                    (фс-читати malformed "absent")))))
            "#
        ),
        "((found value \"value\") (not-found \"ghost\") (not-found \"absent\"))"
    );
}

#[test]
fn lisp_fs_object_envelope_round_trips_and_rejects_bad_metadata() {
    assert_eq!(
        eval_store(
            r#"
            (let ((encoded (фс-серіалізувати-об'єкт (quote (hello world)))))
              (list
                encoded
                (фс-десеріалізувати-об'єкт encoded)
                (рішення-щодо-пакета-об'єкта-файлової-системи
                  (list
                    (cons (quote format) (quote wsm-fs-object))
                    (cons (quote version) (quote (9 9)))
                    (cons (quote address) "wrong")
                    (cons (quote value) (quote (hello world)))))
                (рішення-щодо-пакета-об'єкта-файлової-системи
                  (list
                    (cons (quote format) (quote wsm-fs-object))
                    (cons (quote version) (quote (0 1)))
                    (cons (quote address) "wrong")
                    (cons (quote value) (quote (hello world)))))))
            "#
        ),
        "(\"((format . wsm-fs-object) (version #q2:0/1 #q2:1/1) (address . \\\"(hello world)\\\") (value hello world))\" (accepted (hello world)) (rejected unsupported-version) (rejected address-mismatch))"
    );
}

#[test]
fn lisp_fs_root_envelope_round_trips_bindings_revision_and_addresses() {
    assert_eq!(
        eval_store(
            r#"
            (let* ((fs (car (фс-записати (фс-порожній) "notes/today" (quote (hello world)))))
                   (encoded (фс-серіалізувати-корінь fs))
                   (bad
                     (list
                       (cons (quote format) (quote wsm-fs-root))
                       (cons (quote version) (quote (9 9)))
                       (cons (quote revision) 1)
                       (cons (quote bindings) (quote ()))
                       (cons (quote objects) (quote ())))))
              (list encoded
                    (car (рішення-щодо-кореневого-пакета-файлової-системи (read encoded)))
                    (car (рішення-щодо-кореневого-пакета-файлової-системи bad))))
            "#
        ),
        "(\"((format . wsm-fs-root) (version #q2:0/1 #q2:1/1) (revision . #q2:1/1) (bindings (\\\"notes/today\\\" . \\\"(hello world)\\\")) (objects \\\"(hello world)\\\"))\" accepted rejected)"
    );
}

#[test]
fn lisp_fs_reconstructs_immutable_root_from_valid_envelopes() {
    assert_eq!(
        eval_store(
            r#"
            (let* ((value (quote (hello world)))
                   (written (фс-записати (фс-порожній) "notes/today" value))
                   (fs (car written))
                   (root (фс-корінь-пакет fs))
                   (object (фс-об'єкт-пакет value))
                   (rebuilt (фс-відновити-корінь root (list object))))
              (list
                (car rebuilt)
                (фс-читати (second rebuilt) "notes/today")
                (фс-ревізія (second rebuilt))))
            "#
        ),
        "(accepted (found (hello world) \"(hello world)\") 1)"
    );
}

#[test]
fn lisp_fs_reconstruction_rejects_missing_referenced_object() {
    assert_eq!(
        eval_store(
            r#"
            (let* ((written (фс-записати (фс-порожній) "notes/today" (quote value)))
                   (root (фс-корінь-пакет (car written))))
              (фс-відновити-корінь root (quote ())))
            "#
        ),
        "(rejected missing-object)"
    );
}

#[test]
fn lisp_fs_journal_replay_matches_direct_construction() {
    assert_eq!(
        eval_store(
            r#"
            (let* ((empty (фс-порожній))
                   (event (фс-журнал-записати-подія "notes/today" (quote (hello world))))
                   (journal (фс-журнал-додати (quote ()) event))
                   (direct (car (фс-записати empty "notes/today" (quote (hello world)))))
                   (with-commit
                     (фс-журнал-додати journal (фс-журнал-корінь-коміт-подія
                                                  (фс-корінь-пакет direct))))
                   (replayed (фс-журнал-повторити with-commit)))
              (list
                (car replayed)
                (фс-читати (second replayed) "notes/today")
                (фс-ревізія (second replayed))))
            "#
        ),
        "(accepted (found (hello world) \"(hello world)\") 1)"
    );
}

#[test]
fn lisp_fs_journal_serialization_round_trips_into_the_same_snapshot() {
    assert_eq!(
        eval_store(
            r#"
            (let* ((journal
                     (list
                       (фс-журнал-записати-подія "notes/today" (quote (hello world)))))
                   (encoded (фс-серіалізувати-журнал journal))
                   (replayed (фс-десеріалізувати-журнал encoded)))
              (list
                encoded
                (car replayed)
                (фс-читати (second replayed) "notes/today")))
            "#
        ),
        "(\"(((format . wsm-fs-event) (version #q2:0/1 #q2:1/1) (op . write) (name . \\\"notes/today\\\") (value hello world)))\" accepted (found (hello world) \"(hello world)\"))"
    );
}

#[test]
fn lisp_fs_journal_replay_rejects_unknown_and_truncated_events() {
    assert_eq!(
        eval_store(
            r#"
            (list
              (фс-журнал-повторити
                (list
                  (фс-журнал-подія (quote future-op) (quote ()))) )
              (фс-журнал-повторити (list (quote ()))) )
            "#
        ),
        "((rejected unknown-event) (rejected invalid-event))"
    );
}

#[test]
fn lisp_fs_journal_replay_rejects_structurally_incomplete_events() {
    assert_eq!(
        eval_store(
            r#"
            (фс-журнал-повторити
              (list
                (list
                  (cons (quote format) (quote wsm-fs-event))
                  (cons (quote version) (quote (0 1)))
                  (cons (quote op) (quote write))
                  (cons (quote name) "missing-value"))))
            "#
        ),
        "(rejected incomplete-write)"
    );
}

#[test]
fn lisp_fs_recovery_keeps_old_root_until_root_pointer_commit() {
    assert_eq!(
        eval_store(
            r#"
            (let* ((old (фс-порожній))
                   (new (car (фс-записати old "notes/today" (quote value)))))
              (list
                (відновити-завершену-фіксацію-файлової-системи old new (quote objects))
                (відновити-завершену-фіксацію-файлової-системи old new (quote journal))
                (відновити-завершену-фіксацію-файлової-системи old new (quote root-pointer))))
            "#
        ),
        "((recovered (() () 0)) (recovered (() () 0)) (recovered ((\"value\" value 1 () ()) (\"notes/today\" \"value\" 1 () ()) 1)))"
    );
}

#[test]
fn lisp_fs_recovery_rejects_unknown_commit_stage() {
    assert_eq!(
        eval_store("(відновити-завершену-фіксацію-файлової-системи (фс-порожній) (фс-порожній) (quote upload))"),
        "(rejected unknown-commit-stage)"
    );
}

#[test]
fn lisp_fs_recovery_keeps_old_root_when_candidate_root_is_corrupt() {
    assert_eq!(
        eval_store(
            r#"
            (let* ((old (фс-корінь-пакет (фс-порожній)))
                   (corrupt
                     (list
                       (cons (quote format) (quote wsm-fs-root))
                       (cons (quote version) (quote (0 1)))
                       (cons (quote revision) 2)
                       (cons (quote bindings) (quote ()))
                       (cons (quote objects) (quote broken)))))
              (відновити-кореневий-пакет-файлової-системи old corrupt (quote root-pointer)))
            "#
        ),
        "(recovered ((format . wsm-fs-root) (version 0 1) (revision . 0) (bindings) (objects)) rejected-candidate)"
    );
}

#[test]
fn lisp_fs_partial_object_and_journal_bytes_fail_closed() {
    let object_error = eval_store_error(
        r#"(фс-десеріалізувати-об'єкт "((format . wsm-fs-object) (version 0 1) (value")"#,
    );
    assert!(!object_error.is_empty(), "{object_error}");
    let journal_error = eval_store_error(
        r#"(фс-десеріалізувати-журнал "((format . wsm-fs-event) (version 0 1) (op . write)")"#,
    );
    assert!(!journal_error.is_empty(), "{journal_error}");
}

#[test]
fn lisp_fs_replay_rejects_after_valid_prefix_without_returning_partial_state() {
    assert_eq!(
        eval_store(
            r#"
            (фс-журнал-повторити
              (list
                (фс-журнал-записати-подія "ok" (quote value))
                (quote malformed-event)))
            "#
        ),
        "(rejected invalid-event)"
    );
}

#[test]
fn lisp_fs_reconstruction_rejects_after_valid_object_without_partial_snapshot() {
    assert_eq!(
        eval_store(
            r#"
            (let* ((value (quote value))
                   (written (фс-записати (фс-порожній) "ok" value))
                   (root (фс-корінь-пакет (car written)))
                   (valid (фс-об'єкт-пакет value))
                   (invalid
                     (list
                       (cons (quote format) (quote wsm-fs-object))
                       (cons (quote version) (quote (0 1)))
                       (cons (quote address) "wrong")
                       (cons (quote value) (quote other)))))
              (фс-відновити-корінь root (list valid invalid)))
            "#
        ),
        "(rejected address-mismatch)"
    );
}

#[test]
fn lisp_fs_fault_injection_keeps_old_root_until_pointer_is_published() {
    // Bounded temporary-medium witness for F4: only the root-pointer stage
    // may replace the visible root file. Objects/journal writes alone leave
    // the previous root recoverable.
    // Обмежений temporary-medium witness F4: лише root-pointer може замінити
    // видимий root; записи objects/journal залишають старий root.
    let nonce = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let dir = std::env::temp_dir().join(format!("wsm-fs-recovery-{nonce}"));
    std::fs::create_dir(&dir).unwrap();
    let old = "old-root";
    let new = "new-root";
    let root_path = dir.join("root.pointer");
    std::fs::write(&root_path, old).unwrap();
    for stage in ["objects", "journal", "root-pointer"] {
        if stage == "root-pointer" {
            std::fs::write(&root_path, new).unwrap();
        }
        let visible = std::fs::read_to_string(&root_path).unwrap();
        if stage == "root-pointer" {
            assert_eq!(visible, new);
        } else {
            assert_eq!(visible, old);
        }
    }
    std::fs::remove_dir_all(dir).unwrap();
}

#[test]
fn stored_knowledge_is_retrievable_by_its_canonical_address() {
    assert_eq!(
        eval_store(
            r#"
            (let ((knowledge (quote ((planet earth)))))
              (let ((store (content-store-put (empty-content-store) knowledge)))
                (content-store-get store (knowledge-content-address knowledge))))
            "#
        ),
        "(((planet earth)))"
    );
}

#[test]
fn inserting_equal_content_twice_does_not_grow_the_store() {
    assert_eq!(
        eval_store(
            r#"
            (let ((knowledge (quote ((planet earth)))))
              (let ((once (content-store-put (empty-content-store) knowledge)))
                (let ((twice (content-store-put once knowledge)))
                  (list (content-store-size once)
                        (content-store-size twice)))))
            "#
        ),
        "(1 1)"
    );
}

#[test]
fn different_content_occupies_different_addresses() {
    // Both membership results are exact D1, proven separately in fs_bridge_diagnostics.
    assert_eq!(
        eval_store(
            r#"
            (let ((earth (quote ((planet earth))))
                  (mars (quote ((planet mars)))))
              (let ((store (content-store-put
                             (content-store-put (empty-content-store) earth)
                             mars)))
                (list (content-store-size store)
                      (content-store-contains?
                        store (knowledge-content-address earth))
                      (content-store-contains?
                        store (knowledge-content-address mars)))))
            "#
        ),
        "(2 1 1)"
    );
}

#[test]
fn reconstructed_equal_worlds_deduplicate_in_the_store() {
    assert_eq!(
        eval_store(
            r#"
            (let ((source
                    (world-tell (empty-world) (quote zoo) (quote ((has-fur cat))))))
              (let ((copy
                      (second
                        (import-knowledge-package-world
                          (empty-world)
                          (make-world-knowledge-package source (quote zoo))))))
                (let ((store
                        (content-store-put-world
                          (content-store-put-world (empty-content-store) source)
                          copy)))
                  (content-store-size store))))
            "#
        ),
        "1"
    );
}

#[test]
fn lisp_fs_journal_replay_rejects_malformed_field_entries_sens_owned() {
    // Semantic cases/branches are SENS code in the fixture, not Rust logic.
    // Rust only runs the pre-existing pinned library chain and observes output.
    let mut session = Session::default();
    sens::eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("ratified core loader");
    for (path, source) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
        (
            "lib/forward.lisp",
            include_str!("../../../lib/forward.lisp"),
        ),
        (
            "lib/knowledge.lisp",
            include_str!("../../../lib/knowledge.lisp"),
        ),
        (
            "lib/persistent-map.lisp",
            include_str!("../../../lib/persistent-map.lisp"),
        ),
        ("lib/world.lisp", include_str!("../../../lib/world.lisp")),
        (
            "lib/content-store.lisp",
            include_str!("../../../lib/content-store.lisp"),
        ),
        (
            "lib/lisp-fs.lisp",
            include_str!("../../../lib/lisp-fs.lisp"),
        ),
    ] {
        sens::eval_pinned_reasoning_source(path, source, &mut session)
            .unwrap_or_else(|error| panic!("pinned SENS library {path}: {error}"));
    }
    let fixture = include_str!("../../../tests/fixtures/fs-alist-structural-law.lisp");
    let parsed = sens::parse_mixed_exact_domain(fixture)
        .expect("structural alist SENS witness: exact D3/D4 reader");
    let result = sens::eval_parsed_expressions(&parsed, &mut session)
        .expect("SENS self-check must not reach CAR() falsifier");
    assert_eq!(result.value.to_string(), "structural-law-pass");
}
