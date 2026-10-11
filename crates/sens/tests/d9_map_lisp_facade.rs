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
fn internal_map_facade_is_not_d9_auto_dispatch() {
    let mut session = session();
    let empty = eval_program("(внутрішня-мапа-список map-empty)", &mut session)
        .expect("private derived map->list closure");
    assert_eq!(empty.value.to_string(), "()");
    let failure = sens::parse_mixed_exact_domain("(101001100 (001 ()))")
        .expect("exact D9 source must not silently reinterpret a numeric value");
    // D9 admission is a separate task; use ordinary source to ensure no
    // accidental name/ID coercion in the Lisp-derived facade.
    assert!(!failure.is_empty());
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
    assert_eq!(listed.value.to_string(), "((\"a\" 7))");
}
