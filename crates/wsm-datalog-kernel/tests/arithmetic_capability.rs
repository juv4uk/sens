use wsm_datalog_kernel::{Atom, Database, Evaluator, Program, Rule, Term, Value};

#[test]
fn integer_values_are_relational_payloads_not_implicit_arithmetic() {
    let mut db = Database::new();
    db.add_fact(
        "triple",
        vec![Value::int(1), Value::int(2), Value::int(3)],
    );

    let mut program = Program::new();
    program.add_rule(Rule::with_id(
        "copy-third",
        Atom::new("copied", vec![Term::v("Z")]),
        vec![Atom::new(
            "triple",
            vec![Term::c(Value::int(1)), Term::c(Value::int(2)), Term::v("Z")],
        )],
    ));

    Evaluator::semi_naive_fixpoint(&program, &mut db);

    assert!(
        db.relation("copied")
            .is_some_and(|relation| relation.contains(&vec![Value::int(3)])),
        "Datalog must preserve integer payloads through ordinary relational substitution"
    );
}

#[test]
fn arithmetic_spellings_remain_ordinary_relations_without_an_evaluator() {
    let mut db = Database::new();
    db.add_fact("input", vec![Value::int(2), Value::int(3)]);

    let program = Program::new();
    Evaluator::semi_naive_fixpoint(&program, &mut db);

    for spelling in ["+", "-", "*", "/", "abs", "sqrt", "sin", "cos", "exp", "log"] {
        assert!(
            db.relation(spelling).is_none(),
            "{spelling} must not appear merely because integer payloads exist"
        );
    }
}

#[test]
fn relation_names_that_look_like_math_do_not_gain_operator_semantics() {
    let mut db = Database::new();
    db.add_fact("+", vec![Value::int(2), Value::int(3), Value::int(99)]);

    let mut program = Program::new();
    program.add_rule(Rule::with_id(
        "copy-plus-row",
        Atom::new("observed", vec![Term::v("A"), Term::v("B"), Term::v("R")]),
        vec![Atom::new(
            "+",
            vec![Term::v("A"), Term::v("B"), Term::v("R")],
        )],
    ));

    Evaluator::naive_fixpoint(&program, &mut db);

    assert!(
        db.relation("observed")
            .is_some_and(|relation| relation.contains(&vec![
                Value::int(2),
                Value::int(3),
                Value::int(99),
            ])),
        "a relation named '+' must preserve supplied data verbatim, not compute 2 + 3"
    );
    assert!(
        !db.relation("observed")
            .is_some_and(|relation| relation.contains(&vec![
                Value::int(2),
                Value::int(3),
                Value::int(5),
            ])),
        "current Datalog must not synthesize arithmetic results from a relation spelling"
    );
}
