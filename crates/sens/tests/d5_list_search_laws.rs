//! #3052/#3053 — exact Core.D5 list/search law witnesses.
//!
//! Research-only. The test deliberately calls the ratified five-bit resident
//! identities after loading the Lisp-owned Core definitions. No human surface
//! name and no historical Function8/Sens8 byte selects the operation.

use sens::{eval_program, load_core_library, Session};

fn run(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("active Core should load");
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("{source}: {error:?}"))
        .value
        .to_string()
}

#[test]
fn exact_d5_append_reverse_form_a_local_list_algebra() {
    // CURRENT OD-005 identities:
    // 10000 APPEND
    // 10001 REVERSE
    assert_eq!(
        run("(10000 (001 (a b)) (001 (c d)))"),
        "(a b c d)"
    );
    assert_eq!(
        run("(10001 (001 (a b c)))"),
        "(c b a)"
    );

    // Involution.
    assert_eq!(
        run("(10001 (10001 (001 (a b c d))))"),
        "(a b c d)"
    );

    // Anti-homomorphism:
    // reverse(append(x,y)) = append(reverse(y), reverse(x)).
    let left = run("(10001 (10000 (001 (a b)) (001 (c d))))");
    let right = run("(10000 (10001 (001 (c d))) (10001 (001 (a b))))");
    assert_eq!(left, right);
    assert_eq!(left, "(d c b a)");

    // Nested payload is opaque list data, not flattened by either operation.
    assert_eq!(
        run("(10001 (001 ((a b) c (d e))))"),
        "((d e) c (a b))"
    );
}

#[test]
fn exact_d5_assoc_member_share_traversal_but_not_result_semantics() {
    // CURRENT OD-005 identities:
    // 11100 ASSOC
    // 11101 MEMBER
    assert_eq!(
        run("(11100 (001 x) (001 ((x . first) (y . second))))"),
        "(x . first)"
    );
    assert_eq!(
        run("(11100 (001 z) (001 ((x . first) (y . second))))"),
        "()"
    );

    // First-match ordering is observable.
    assert_eq!(
        run("(11100 (001 x) (001 ((x . first) (x . second))))"),
        "(x . first)"
    );

    // ASSOC admits a structural key through the Core structural-equality path.
    assert_eq!(
        run("(11100 (001 (a b)) (001 (((a b) . first) ((a c) . second))))"),
        "((a b) . first)"
    );

    // MEMBER exposes predicate-like hit/miss rather than the matching pair.
    assert_eq!(
        run("(11101 (001 b) (001 (a b c)))"),
        "t"
    );
    assert_eq!(
        run("(11101 (001 z) (001 (a b c)))"),
        "()"
    );

    // MEMBER also uses structural equality for list elements.
    assert_eq!(
        run("(11101 (001 (a b)) (001 ((x y) (a b) (c d))))"),
        "t"
    );
}
