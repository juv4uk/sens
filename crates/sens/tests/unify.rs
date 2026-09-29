//! Exercises lib/unify.my — the unification primitive written in sens
//! itself (see PLAN.md, Krok 9, item 3): the pattern-matching engine under
//! backward-chaining/Prolog-style symbolic reasoning, in the spirit of
//! McCarthy's 1958 "Advice Taker". Loads lib/core.my (for `second`) and
//! lib/unify.my into one session, same as a user loading both from a REPL.
//! Pereviriaie lib/unify.my — prymityv unification, napysanyi samoiu sens
//! (dyv. PLAN.md, Krok 9, punkt 3): mekhanizm zistavlennia z shablonom pid
//! backward-chaining/Prolog-podibnymy symvolnymy mirkuvanniamy, u dusi
//! "Advice Taker" Makkarti 1958 roku. Zavantazhuie lib/core.my (zarady
//! `second`) i lib/unify.my v odnu sesiiu, tak samo yak korystuvach z REPL.
//! Prüft lib/unify.my — das in sens selbst geschriebene
//! Unifikations-Primitiv (siehe PLAN.md, Schritt 9, Punkt 3): die
//! Mustervergleichs-Engine unter Backward-Chaining-/Prolog-artigem
//! symbolischen Schließen, im Geiste von McCarthys "Advice Taker" von 1958.
//! Lädt lib/core.my (wegen `second`) und lib/unify.my in eine Sitzung,
//! genauso wie ein Nutzer beide aus der REPL lädt.

use sens::{eval_program, Session};

fn eval_unify(source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session).unwrap();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn identical_atoms_unify_with_an_unchanged_substitution() {
    assert_eq!(
        eval_unify("(unify (quote radio) (quote radio) (quote ()))"),
        "()"
    );
}

#[test]
fn different_atoms_fail_to_unify() {
    assert_eq!(
        eval_unify("(unify (quote radio) (quote antenna) (quote ()))"),
        "fail"
    );
}

#[test]
fn a_variable_unifies_with_and_resolves_to_an_atom() {
    assert_eq!(
        eval_unify("(apply-subst (logic-var (quote x)) (unify (logic-var (quote x)) (quote antenna) (quote ())))"),
        "antenna"
    );
}

#[test]
fn structural_unification_extracts_a_binding_from_a_compound_term() {
    // The classic family-relation-style query: matching (parent ?x bob)
    // against the fact (parent alice bob) should bind ?x to alice.
    assert_eq!(
        eval_unify(
            "(apply-subst (logic-var (quote x)) (unify (list (quote parent) (logic-var (quote x)) (quote bob)) (list (quote parent) (quote alice) (quote bob)) (quote ())))"
        ),
        "alice"
    );
}

#[test]
fn structural_mismatch_fails() {
    assert_eq!(
        eval_unify("(unify (list (quote a) (quote b)) (list (quote a) (quote c)) (quote ()))"),
        "fail"
    );
}

#[test]
fn chained_variable_bindings_resolve_transitively() {
    // (?x ?y) unified against (radio ?x) binds y -> x -> radio; apply-subst
    // must walk the whole chain, not stop after one dereference.
    assert_eq!(
        eval_unify(
            "(apply-subst (logic-var (quote y)) (unify (list (logic-var (quote x)) (logic-var (quote y))) (list (quote radio) (logic-var (quote x))) (quote ())))"
        ),
        "radio"
    );
}

#[test]
fn unifying_a_variable_with_itself_creates_no_binding() {
    // Also the case that would loop forever if unify-var didn't special-case
    // same-name variable-variable unification (var bound to itself).
    assert_eq!(
        eval_unify("(apply-subst (logic-var (quote x)) (unify (logic-var (quote x)) (logic-var (quote x)) (quote ())))"),
        "(var x)"
    );
}

#[test]
fn apply_subst_resolves_every_variable_in_a_compound_query() {
    assert_eq!(
        eval_unify(
            "(apply-subst (list (quote parent) (logic-var (quote x)) (logic-var (quote y))) (unify (list (quote parent) (logic-var (quote x)) (logic-var (quote y))) (list (quote parent) (quote alice) (quote bob)) (quote ())))"
        ),
        "(parent alice bob)"
    );
}

#[test]
fn var_predicate_does_not_crash_on_a_nested_compound_subterm() {
    // Regression: var? used to call `eq` on `(car term)` unconditionally;
    // when unify recurses into a piece like ((var x) bob), `(car term)` is
    // itself a list, and `eq` requires atoms. Caught by hand-testing before
    // this test existed — kept here so it can't silently regress.
    assert_eq!(
        eval_unify("(var? (list (logic-var (quote x)) (quote bob)))"),
        "()"
    );
}

#[test]
fn occurs_check_prevents_infinite_structures() {
    let source = r#"
        (let ((bindings (unify (logic-var (quote x)) (list (quote f) (logic-var (quote x))) (quote ()))))
             bindings)
    "#;
    assert_eq!(eval_unify(source), "fail");
}

#[test]
fn thread_conjunction_finds_every_combination_satisfying_all_conditions() {
    // The shared kernel lib/reason.my and lib/forward.my both build their
    // conjunctive matching on. Here `try-one` unifies each condition
    // against a fixed candidate list, threading bindings across — the same
    // shape lib/forward.lisp's match-conditions uses, tested directly rather
    // than only indirectly through its two consumers.
    let source = r#"
        (thread-conjunction
          (list (logic-var (quote x)) (logic-var (quote y)))
          (quote ())
          (lambda (condition subst)
            (map (lambda (candidate) (unify condition candidate subst)) (quote (a b)))))
    "#;
    // Two conditions, two candidates each, no shared variables between
    // them: 2 * 2 = 4 independent combinations, each binding x and y.
    assert_eq!(
        eval_unify(source),
        "(((y . a) (x . a)) ((y . b) (x . a)) ((y . a) (x . b)) ((y . b) (x . b)))"
    );
}

