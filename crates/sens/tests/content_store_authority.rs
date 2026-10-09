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
        ("fs-empty", r#"(fs-empty)"#),
        ("fs-empty-car", r#"(car (fs-empty))"#),
        ("fs-empty-cdr", r#"(cdr (fs-empty))"#),
        ("empty-content-store", r#"(empty-content-store)"#),
        ("empty-content-store-size", r#"(content-store-size (empty-content-store))"#),
        ("empty-content-store-map-list", r#"(map->list (empty-content-store))"#),
        ("content-address", r#"(knowledge-content-address (quote (lambda (x) x)))"#),
        ("fs-write", r#"(fs-write (fs-empty) "code" (quote (lambda (x) x)))"#),
        ("fs-write-first", r#"(car (fs-write (fs-empty) "code" (quote (lambda (x) x))))"#),
        ("let-star-one-binding-result", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) ) written)"#),
        ("let-star-one-binding-car", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) ) (car written))"#),
        ("let-star-two-binding-snapshot", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (snapshot (car written))) snapshot)"#),
        ("let-star-two-binding-snapshot-car", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (snapshot (car written))) (car snapshot))"#),
        ("let-one-binding-car", r#"(let ((written (fs-write (fs-empty) "code" (quote (lambda (x) x))))) (car written))"#),
        ("let-one-binding-snapshot-car", r#"(let ((written (fs-write (fs-empty) "code" (quote (lambda (x) x))))) (car (car written)))"#),
        ("fs-write-first-car", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (fs (car written))) (car fs))"#),
        ("fs-write-first-cdr", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (fs (car written))) (cdr fs))"#),
        ("fs-objects-alias", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (fs (car written))) (fs-objects fs))"#),
        ("fs-bindings-alias", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (fs (car written))) (fs-bindings fs))"#),
        ("fs-revision-alias", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (fs (car written))) (fs-revision fs))"#),
        ("raw-00000101", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (fs (car written))) (00000101 fs))"#),
        ("raw-00000110", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (fs (car written))) (00000110 fs))"#),
        ("object-map-list", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (fs (car written))) (map->list (car fs))"#),
        ("object-addresses", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (fs (car written))) (fs-object-addresses (map->list (car fs)))"#),
        ("root-package", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (fs (car written))) (fs-root-package fs)"#),
        ("root-image", r#"(let* ((written (fs-write (fs-empty) "code" (quote (lambda (x) x)))) (fs (car written))) (fs-serialize-root fs)"#),
    ];   for (name, source) in probes {
        eprintln!("CONTENT-STORE-DIAG: {name} => {}", observe(&mut session, source));
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
