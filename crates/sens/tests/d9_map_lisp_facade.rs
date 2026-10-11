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
        ("lib/lisp-fs.lisp", include_str!("../../../lib/lisp-fs.lisp"), 13),
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
fn historical_string_order_surface_has_explicit_result_shape() {
    let mut session = session();
    let forward = eval_program("(string<? \"a\" \"b\")", &mut session)
        .expect("historical Lisp comparator should evaluate as a closure");
    let backward = eval_program("(string<? \"b\" \"a\")", &mut session)
        .expect("reverse lexical ordering should evaluate");
    assert_eq!(
        forward.value.to_string(), "t",
        "the only positive legacy marker approved for an explicit D1 bridge"
    );
    assert_eq!(
        backward.value.to_string(), "()",
        "the only negative legacy marker approved for an explicit D1 bridge"
    );
}

#[test]
fn private_two_argument_string_order_preserves_distinct_avl_keys() {
    let mut session = session();
    let left_then_right = eval_program(
        "(внутрішня-мапа-отримати \"b\" (внутрішня-мапа-вставити \"b\" 9 (внутрішня-мапа-вставити \"a\" 7 map-empty)))",
        &mut session
    ).expect("two string-key insertions must not call an unadmitted D8 byte head");
    assert_eq!(left_then_right.value.to_string(), "(9)");
    let reverse = eval_program(
        "(внутрішня-мапа-отримати \"a\" (внутрішня-мапа-вставити \"a\" 7 (внутрішня-мапа-вставити \"b\" 9 map-empty)))",
        &mut session
    ).expect("comparison must be stable regardless of insertion order");
    assert_eq!(reverse.value.to_string(), "(7)");
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
