//! Exercises lib/persistent-map.my — the AVL-balanced persistent map
//! written in sens itself (PLAN.md item 15). Loads lib/core.my (for
//! `second`/`third`/`not`/`append`) and lib/persistent-map.my into one
//! session, same as a user loading both from a REPL.
//! Pereviriaie lib/persistent-map.my — AVL-zbalansovanu persystentnu mapu,
//! napysanu samoiu sens (PLAN.md, punkt 15). Zavantazhuie lib/core.my
//! (zarady `second`/`third`/`not`/`append`) i lib/persistent-map.my v odnu
//! sesiiu, tak samo yak korystuvach z REPL.
//! Prüft lib/persistent-map.my — die AVL-balancierte persistente Map, in
//! sens selbst geschrieben (PLAN.md, Punkt 15). Lädt lib/core.my (wegen
//! `second`/`third`/`not`/`append`) und lib/persistent-map.my in eine
//! Sitzung, genauso wie ein Nutzer beide aus der REPL lädt.

use sens::{eval_program, Session};

fn eval_map(source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/persistent-map.lisp"), &mut session).unwrap();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn empty_map_has_nothing() {
    assert_eq!(eval_map(r#"(мапа-отримати "a" мапа-порожній)"#), "()");
    assert_eq!(eval_map(r#"(мапа-містить? "a" мапа-порожній)"#), "()");
    assert_eq!(eval_map("(мапа-список мапа-порожній)"), "()");
}

#[test]
fn insert_then_get_finds_the_value() {
    assert_eq!(
        eval_map(r#"(мапа-отримати "a" (мапа-вставити "a" 1 мапа-порожній))"#),
        "(1)"
    );
    assert_eq!(
        eval_map(r#"(мапа-містить? "a" (мапа-вставити "a" 1 мапа-порожній))"#),
        "(1)"
    );
}

#[test]
fn absent_key_is_not_confused_with_a_stored_nil_value() {
    // мапа-отримати's "maybe" shape (`()` for absent, `(value)` for present)
    // exists specifically so a legitimately-stored `()` value is
    // distinguishable from "not found" — both print differently here.
    let source = r#"
        (def m (мапа-вставити "a" (quote ()) мапа-порожній))
        (list (мапа-отримати "a" m) (мапа-отримати "z" m) (мапа-містить? "a" m) (мапа-містить? "z" m))
    "#;
    assert_eq!(eval_map(source), "((()) () (1) ())");
}

#[test]
fn insert_replaces_an_existing_key_rather_than_duplicating_it() {
    let source = r#"
        (def m (мапа-вставити "a" 1 мапа-порожній))
        (def m2 (мапа-вставити "a" 100 m))
        (list (мапа-отримати "a" m2) (мапа-список m2))
    "#;
    assert_eq!(eval_map(source), "((100) ((\"a\" . 100)))");
}

#[test]
fn insert_is_persistent_the_original_tree_is_untouched() {
    let source = r#"
        (def m (мапа-вставити "a" 1 мапа-порожній))
        (def m2 (мапа-вставити "b" 2 m))
        (list (мапа-список m) (мапа-список m2))
    "#;
    assert_eq!(eval_map(source), r#"((("a" . 1)) (("a" . 1) ("b" . 2)))"#);
}

#[test]
fn map_to_list_returns_keys_in_sorted_order() {
    let source = r#"
        (def m (мапа-вставити "c" 3 (мапа-вставити "a" 1 (мапа-вставити "b" 2 мапа-порожній))))
        (мапа-список m)
    "#;
    assert_eq!(eval_map(source), "((\"a\" . 1) (\"b\" . 2) (\"c\" . 3))");
}

/// The actual point of choosing a balanced tree over a plain BST: seven
/// keys inserted in already-sorted order is the textbook worst case for
/// an unbalanced tree (degenerates into a linked list, height 7). AVL
/// rotations keep it at the theoretical minimum for 7 nodes, height 3
/// (`ceil(log2(8))`) — verified live before this test was written, not
/// assumed from the rotation code looking plausible.
/// Sama sut vyboru zbalansovanoho dereva zamist zvychainoho BST: sim
/// kliuchiv, vstavlenykh uzhe u vidsortovanomu poriadku — pidruchnykovyi
/// naihirshyi vypadok dlia nezbalansovanoho dereva (vyrodzhuietsia v
/// zviazanyi spysok, vysota 7). AVL-rotatsii trymaiut teoretychnyi minimum
/// dlia 7 vuzliv, vysotu 3 (`ceil(log2(8))`) — perevireno zhyvo pered
/// napysanniam tsoho testu, ne prypushcheno z toho, shcho kod rotatsii vyhliadaie
/// pravdopodibno.
#[test]
fn sorted_insertion_order_stays_balanced_instead_of_degenerating_into_a_list() {
    let source = r#"
        (def insert-all
          (lambda (pairs tree)
            (cond
              ((atom? pairs) () tree)
              ((atom? pairs) (1) tree)
              (t (insert-all (cdr pairs) (мапа-вставити (car (car pairs)) (second (car pairs)) tree))))))
        (def m (insert-all (list (list "a" 1) (list "b" 2) (list "c" 3) (list "d" 4)
                                  (list "e" 5) (list "f" 6) (list "g" 7))
                            мапа-порожній))
        (node-height m)
    "#;
    assert_eq!(eval_map(source), "3");
}

#[test]
fn map_to_list_stays_sorted_after_many_out_of_order_inserts() {
    let source = r#"
        (def insert-all
          (lambda (pairs tree)
            (cond
              ((atom? pairs) () tree)
              ((atom? pairs) (1) tree)
              (t (insert-all (cdr pairs) (мапа-вставити (car (car pairs)) (second (car pairs)) tree))))))
        (def m (insert-all (list (list "g" 7) (list "c" 3) (list "e" 5) (list "a" 1)
                                  (list "f" 6) (list "b" 2) (list "d" 4))
                            мапа-порожній))
        (мапа-список m)
    "#;
    assert_eq!(
        eval_map(source),
        r#"(("a" . 1) ("b" . 2) ("c" . 3) ("d" . 4) ("e" . 5) ("f" . 6) ("g" . 7))"#
    );
}
