//! D9 map coordinates without admitted mechanisms must remain fail-closed.
//! These tests exercise separately named Lisp-owned AVL closures only.
use sens::{eval_program, eval_pinned_legacy_core_source, eval_pinned_reasoning_source, Session};

fn session() -> Session {
    let mut session = Session::default();
    eval_pinned_legacy_core_source(
        "lib/core.lisp", include_str!("../../../lib/core.lisp"), &mut session
    ).expect("derived core bootstrap");
    eval_pinned_reasoning_source(
        "lib/persistent-map.lisp", include_str!("../../../lib/persistent-map.lisp"), &mut session
    ).expect("Lisp-owned AVL map bootstrap");
    session
}

#[test]
fn source_cutover_blocks_old_d6_let_and_unadmitted_d9_map_heads() {
    for (path, source, expected_macro_count) in [
        ("lib/persistent-map.lisp", include_str!("../../../lib/persistent-map.lisp"), 2),
        ("lib/content-store.lisp", include_str!("../../../lib/content-store.lisp"), 0),
        ("lib/lisp-fs.lisp", include_str!("../../../lib/lisp-fs.lisp"), 14),
    ] {
        for head in [
            "001000",    // D6 LET: replaced with the Lisp-owned ЛІХТАР macro
            "101001100", // D9 MAP->LIST
            "101100101", // D9 MAP-GET
            "101100010", // D9 MAP-CONTAINS?
            "101101110", // D9 MAP-INSERT
            "110111011", // D9 ANSWER-NOT: D1-only cases use D4 NOT
        ] {
            assert!(
                !source.contains(&format!("({head} ")),
                "obsolete executable head {head} reappeared in {path}"
            );
        }
        assert_eq!(
            source.matches("(нехай-похідне").count(),
            expected_macro_count,
            "source macro cutover drift in {path}"
        );
    }
}

#[test]
fn internal_map_facade_is_not_d9_auto_dispatch() {
    let mut session = session();
    let empty = eval_program("(внутрішня-мапа-список map-empty)", &mut session)
        .expect("private derived map->list closure");
    assert_eq!(empty.value.to_string(), "()");
    let failure = sens::parse_mixed_exact_domain("(101001100 (001 ()))")
        .expect("exact D9 source must not silently reinterpret a numeric value");
    // D9 has no admitted callable mechanism. A number is never promoted
    // to a function merely because the spelling happens to be binary.
    let error = sens::eval_parsed_expressions(&failure, &mut session)
        .expect_err("unadmitted 9-bit head must fail closed");
    assert!(
        error.message.contains("not callable"),
        "expected the named non-callable diagnostic: {error:?}"
    );
}

#[test]
fn internal_map_facade_inserts_and_reads_one_element() {
    let mut session = session();
    let inserted = eval_program(
        "(внутрішня-мапа-отримати \"a\" (внутрішня-мапа-вставити \"a\" 7 map-empty))",
        &mut session
    ).expect("one-key AVL insert and read use Lisp closures");
    assert_eq!(inserted.value.to_string(), "(7)");
    let listed = eval_program(
        "(внутрішня-мапа-список (внутрішня-мапа-вставити \"a\" 7 map-empty))",
        &mut session
    ).expect("one-key AVL map should traverse without D9 dispatch");
    assert_eq!(listed.value.to_string(), "((\"a\" . 7))");
}
