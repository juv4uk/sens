//! Exercises lib/reason.my — the symbolic inference engine written in sens
//! itself, fulfilling the Advice Taker vision of deriving new facts from rules.
//! Loads core, unify, and reason into one session.
//! Pereviriaie lib/reason.my — rushii symvolnoho vysnovku, napysanyi samoiu
//! sens, shcho vtiliuie bachennia Advice Taker shchodo vyvedennia faktiv z pravyl.
//! Zavantazhuie core, unify ta reason v odnu sesiiu.
//! Prüft lib/reason.my — die symbolische Inferenz-Engine, geschrieben in
//! sens selbst, die die Advice-Taker-Vision erfüllt. Lädt core, unify
//! und reason in eine Sitzung.

use sens::{eval_program, Session};

fn eval_reason(source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/reason.lisp"), &mut session).unwrap();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

fn eval_reason_with_output(source: &str) -> Vec<String> {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/reason.lisp"), &mut session).unwrap();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .output
}

#[test]
fn simple_fact_retrieval() {
    let source = r#"
        (let ((rules (quote (((parent alice bob))))))
             (reason (quote (parent alice bob)) rules))
    "#;
    // Returns a list containing one empty substitution and its proof tree
    assert_eq!(
        eval_reason(source),
        "((() (proved (parent alice bob) (parent alice bob) ())))"
    );
}

#[test]
fn variable_binding_from_fact() {
    let source = r#"
        (let ((rules (quote (((parent alice bob))))))
             (reason (list (quote parent) (logic-var (quote x)) (quote bob)) rules))
    "#;
    // Returns a list of substitutions and proof trees. One successful path binding x to alice.
    assert_eq!(
        eval_reason(source),
        "((((x . alice)) (proved (parent (var x) bob) (parent alice bob) ())))"
    );
}

#[test]
fn rule_with_condition_backward_chaining() {
    let source = r#"
        (let ((rules (quote (
                 ((grandparent (var x) (var y)) (parent (var x) (var z)) (parent (var z) (var y)))
                 ((parent alice bob))
                 ((parent bob charlie))
               ))))
             (length (reason (list (quote grandparent) (logic-var (quote a)) (logic-var (quote b))) rules)))
    "#;
    // Should find exactly one valid path
    assert_eq!(eval_reason(source), "1");
}

#[test]
fn multiple_valid_paths() {
    let source = r#"
        (let ((rules (quote (
                 ((sibling (var x) (var y)) (parent (var z) (var x)) (parent (var z) (var y)))
                 ((parent alice bob))
                 ((parent alice charlie))
               ))))
             (length (reason (list (quote sibling) (quote bob) (quote charlie)) rules)))
    "#;
    // Should find a path via parent (quote alice'.)
    assert_eq!(eval_reason(source), "1");
}

#[test]
fn recursive_rule_standardizing_apart() {
    // Tests that variable names don't collide across recursive rule invocations.
    // Without standardizing apart, the `z` in the first invocation of the recursive rule
    // would collide with the `x`, `y`, or `z` in the inner invocations.
    let source = r#"
        (let ((rules (quote (
                 ((ancestor (var x) (var y)) (parent (var x) (var y)))
                 ((ancestor (var x) (var y)) (parent (var x) (var z)) (ancestor (var z) (var y)))
                 
                 ((parent alice bob))
                 ((parent bob charlie))
                 ((parent charlie dave))
               ))))
             (length (reason (list (quote ancestor) (quote alice) (quote dave)) rules)))
    "#;
    // alice -> bob -> charlie -> dave = 1 valid path
    assert_eq!(eval_reason(source), "1");
}


#[test]
fn reason_explain_explains_a_provable_goal() {
    let source = r#"
        (let ((rules (quote (((parent alice bob))))))
             (reason-explain (quote (parent alice bob)) rules))
    "#;
    let output = eval_reason_with_output(source);
    assert_eq!(
        output,
        vec![
            "Proved:",
            "(parent alice bob)",
            "using",
            "rule:",
            "(parent alice bob)"
        ]
    );
}

#[test]
fn reason_explain_says_so_when_a_goal_cannot_be_proved() {
    let source = r#"
        (let ((rules (quote (((parent alice bob))))))
             (reason-explain (quote (parent bob alice)) rules))
    "#;
    // Distinct from a silent empty list: the engine states outright that it
    // could not derive the goal from what it knows.
    let output = eval_reason_with_output(source);
    assert_eq!(output, vec!["Cannot", "prove:", "(parent bob alice)"]);
}

#[test]
fn count_usage_counts_each_rule_head_that_contributed_to_a_proof() {
    let source = r#"
        (let ((rules (quote (
                 ((grandparent (var x) (var y)) (parent (var x) (var z)) (parent (var z) (var y)))
                 ((parent alice bob))
                 ((parent bob charlie))
               ))))
             (let* ((results (reason (list (quote grandparent) (logic-var (quote a)) (logic-var (quote b))) rules))
                    (proof (second (car results))))
               (count-usage proof)))
    "#;
    // The grandparent rule fired once, and each `parent` fact it leaned on
    // fired once too — three distinct rule heads, each used once.
    assert_eq!(
        eval_reason(source),
        "(((parent bob charlie) . 1) ((parent alice bob) . 1) ((grandparent (var (x . 0)) (var (y . 0))) . 1))"
    );
}

#[test]
fn count_usage_sums_repeated_use_of_the_same_fact() {
    let source = r#"
        (let ((rules (quote (
                 ((sibling (var x) (var y)) (parent (var z) (var x)) (parent (var z) (var y)))
                 ((parent alice bob))
                 ((parent alice charlie))
               ))))
             (let* ((results (reason (list (quote sibling) (quote bob) (quote charlie)) rules))
                    (proof (second (car results))))
               (count-usage proof)))
    "#;
    // Two distinct `parent` facts fire once each within the same proof
    // (bob's and charlie's), alongside the `sibling` rule that used both.
    assert_eq!(
        eval_reason(source),
        "(((parent alice charlie) . 1) ((parent alice bob) . 1) ((sibling (var (x . 0)) (var (y . 0))) . 1))"
    );
}

#[test]
fn provenance_marks_a_bare_fact_as_source_fact_with_no_derivation() {
    let source = r#"
        (let ((rules (quote (((parent alice bob))))))
             (let* ((results (reason (quote (parent alice bob)) rules))
                    (proof (second (car results))))
               (provenance proof)))
    "#;
    assert_eq!(
        eval_reason(source),
        "(statement (parent alice bob) (source fact) (rule (parent alice bob)) (derived-from ()))"
    );
}

#[test]
fn provenance_marks_a_rule_application_as_source_rule_with_its_derivation() {
    let source = r#"
        (let ((rules (quote (
                 ((grandparent (var x) (var y)) (parent (var x) (var z)) (parent (var z) (var y)))
                 ((parent alice bob))
                 ((parent bob charlie))
               ))))
             (let* ((results (reason (list (quote grandparent) (logic-var (quote a)) (logic-var (quote b))) rules))
                    (proof (second (car results))))
               (provenance proof)))
    "#;
    assert_eq!(
        eval_reason(source),
        "(statement (grandparent (var a) (var b)) (source rule) (rule (grandparent (var (x . 0)) (var (y . 0)))) (derived-from ((statement (parent (var (x . 0)) (var (z . 0))) (source fact) (rule (parent alice bob)) (derived-from ())) (statement (parent (var (z . 0)) (var (y . 0))) (source fact) (rule (parent bob charlie)) (derived-from ())))))"
    );
}
