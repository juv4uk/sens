//! #1443: функції з першого лиспу Маккартні (CACM 1960, §3d) у таблиці
//! функцій — null?, subst, sublis, maplist, apply — визначені мовою в
//! lib/core.lisp кодами СЕНС. Приклади — зі статті або прямо з її визначень.

use sens::{eval_program, load_core_library, Session};

fn eval(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("{source}: {error:?}"))
        .value
        .to_string()
}

#[test]
fn null_is_true_only_for_the_empty_list() {
    assert_eq!(eval("(null? (00000001 ()))"), "1");
    assert_eq!(eval("(null? (00000001 a))"), "0");
    assert_eq!(eval("(null? (00000001 (a)))"), "0");
}

#[test]
fn subst_matches_the_paper_example() {
    // subst[(X . A); B; ((A . B) . C)] = ((A . (X . A)) . C)
    assert_eq!(
        eval("(subst (00000001 (x . a)) (00000001 b) (00000001 ((a . b) . c)))"),
        "((a x . a) . c)"
    );
}

#[test]
fn sublis_substitutes_each_pair_and_leaves_other_atoms() {
    assert_eq!(
        eval("(sublis (00000001 ((x (a b)) (y (b c)))) (00000001 (x y z)))"),
        "((a b) (b c) z)"
    );
    assert_eq!(eval("(sublis (00000001 ()) (00000001 (x y)))"), "(x y)");
}

#[test]
fn maplist_passes_successive_tails_not_elements() {
    assert_eq!(
        eval("(maplist (00000001 (a b c)) (00001000 (l) l))"),
        "((a b c) (b c) (c))"
    );
    assert_eq!(eval("(maplist (00000001 ()) (00001000 (l) l))"), "()");
}

#[test]
fn apply_takes_a_function_as_an_s_expression() {
    // apply[f; args] = eval[cons[f; appq[args]]] — f is a name or a LAMBDA form.
    assert_eq!(
        eval(
            "(00001001 swap (00001000 (a b) (00000100 b a)))
             (apply (00000001 swap) (00000001 (1 (2))))"
        ),
        "((2) . 1)"
    );
    assert_eq!(
        eval("(apply (00000001 (00001000 (u v) (00000100 v u))) (00000001 ((p) q)))"),
        "(q p)"
    );
}
