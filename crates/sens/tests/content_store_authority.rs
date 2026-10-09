use sens::{eval_program, Session};

fn store_session() -> Session {
    let mut session = Session::default();
    for source in [
        include_str!("../../../lib/core.lisp"),
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
        include_str!("../../../lib/persistent-map.lisp"),
        include_str!("../../../lib/world.lisp"),
        include_str!("../../../lib/content-store.lisp"),
        include_str!("../../../lib/lisp-fs.lisp"),
    ] {
        eval_program(source, &mut session).expect("content-store dependency must load");
    }
    session
}

fn observe(session: &mut Session, source: &str) -> String {
    eval_program(source, session)
        .expect("content-store observation must execute")
        .value
        .to_string()
}

#[test]
fn content_store_semantic_relations_are_owned_by_lisp_witness() {
    let mut session = store_session();
    eval_program(
        include_str!("../../../tests/fixtures/content-store-authority-witness.lisp"),
        &mut session,
    )
    .expect("Lisp-owned content-store witness must load");

    let probes = [
        ("no-helper-on-yes", "(content-store-no? (00100010 (00000001 same) (00000001 same)))"),
        ("no-helper-on-no", "(content-store-no? (00100010 (00000001 left) (00000001 right)))"),
        ("root-relation", r#"(00100010
            (fs-serialize-root (car (fs-write (fs-empty) "code" (quote (lambda (x) x)))))
            (fs-serialize-root (car (fs-write (fs-empty) "code" (quote (lambda (x) x))))))"#),
        ("object-relation", r#"(00100010
            (fs-serialize-object (quote (lambda (x) x)))
            (fs-serialize-object (quote (lambda (x) x))))"#),
        ("projection-relations", r#"(10011101
          ((direct (world-tell (empty-world) (00000001 zoo) (00000001 ((has-fur cat)))))
           (retold (world-tell
             (world-retract
               (world-tell (empty-world) (00000001 zoo) (00000001 ((has-fur cat))))
               (00000001 zoo) (00000001 ((has-fur cat))))
             (00000001 zoo) (00000001 ((has-fur cat)))))
          (00100111
            (world-clauses direct (00000001 zoo))
            (world-clauses retold (00000001 zoo))
            (00100010 (world-clauses direct (00000001 zoo))
                      (world-clauses retold (00000001 zoo)))
            (content-store-no?
              (00100010 (world-clauses direct (00000001 zoo))
                        (world-clauses retold (00000001 zoo)))))))"#)
    ];
    for (label, probe) in probes {
        let result = eval_program(probe, &mut session)
            .map(|value| format!("value={:?}; display={}", value.value, value.value))
            .map_err(|error| format!("{:?}: {}", error.kind, error));
        eprintln!("CONTENT-STORE-RESULT: {label} => {result:?}");
    }

    eprintln!("CONTENT-STORE-PROBE: witness observe BEGIN");
    let verdict = observe(&mut session, "(content-store-authority-witness)");
    eprintln!("CONTENT-STORE-PROBE: witness observe END => {verdict}");
    assert!(
        verdict.starts_with("(content-store-authority-witness (status pass)"),
        "Lisp-owned content-store witness rejected the current runtime: {verdict}"
    );
}

#[test]
fn content_store_mechanism_keeps_deterministic_images_and_distinct_history_entries() {
    let mut session = store_session();

    let root_image = r#"
        (let* ((value (quote (lambda (x) x)))
               (fs (car (fs-write (fs-empty) "code" value))))
          (fs-serialize-root fs))
    "#;
    let fs_expr = r#"(car (fs-write (fs-empty) "code" (quote (lambda (x) x))))"#;
    for (label, probe) in [
        ("objects", format!("(fs-objects {fs_expr})")),
        ("objects-as-list", format!("(map->list (fs-objects {fs_expr}))")),
        ("object-addresses", format!("(fs-object-addresses (map->list (fs-objects {fs_expr})))")),
        ("root-package", format!("(fs-root-package {fs_expr})")),
        ("root-package-string", format!("(write-to-string (fs-root-package {fs_expr}))")),
        ("root-serialize", format!("(fs-serialize-root {fs_expr})")),
    ] {
        let result = eval_program(&probe, &mut session)
            .map(|value| value.value.to_string())
            .map_err(|error| format!("{:?}: {}", error.kind, error));
        eprintln!("CONTENT-STORE-STAGE: {label} => {result:?}");
    }

    eprintln!("CONTENT-STORE-PROBE: root_a BEGIN");
    let root_a = observe(&mut session, root_image);
    eprintln!("CONTENT-STORE-PROBE: root_a END => {root_a}");
    eprintln!("CONTENT-STORE-PROBE: root_b BEGIN");
    let root_b = observe(&mut session, root_image);
    eprintln!("CONTENT-STORE-PROBE: root_b END => {root_b}");
    assert_eq!(
        root_a, root_b,
        "repeating the same root serialization must preserve the exact image"
    );

    let object_image = "(fs-serialize-object (quote (lambda (x) x)))";
    eprintln!("CONTENT-STORE-PROBE: object_a BEGIN");
    let object_a = observe(&mut session, object_image);
    eprintln!("CONTENT-STORE-PROBE: object_a END => {object_a}");
    eprintln!("CONTENT-STORE-PROBE: object_b BEGIN");
    let object_b = observe(&mut session, object_image);
    eprintln!("CONTENT-STORE-PROBE: object_b END => {object_b}");
    assert_eq!(
        object_a, object_b,
        "repeating the same object serialization must preserve the exact image"
    );

    let history_cardinality = r#"
        (let ((direct
                (world-tell (empty-world) (quote zoo) (quote ((has-fur cat))))))
          (let ((retold
                  (world-tell
                    (world-retract
                      (world-tell (empty-world) (quote zoo) (quote ((has-fur cat))))
                      (quote zoo) (quote ((has-fur cat))))
                    (quote zoo) (quote ((has-fur cat))))))
            (let ((store
                    (content-store-put-world
                      (content-store-put-world (empty-content-store) direct)
                      retold)))
              (content-store-size store))))
    "#;
    eprintln!("CONTENT-STORE-PROBE: history_cardinality BEGIN");
    let history = observe(&mut session, history_cardinality);
    eprintln!("CONTENT-STORE-PROBE: history_cardinality END => {history}");
    assert_eq!(
        history,
        "2",
        "equal current projections with distinct histories must occupy two store entries"
    );
}
