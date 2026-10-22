//! Migration proof: direct D1 answers in the active native-first execution bridge.
//! No CPU/x86 mechanism required; unsupported plan routes remain explicit debt.
use sens::{
    eval_parsed_expressions, parse, parse_mixed_exact_domain_machine_source, DomainIdentity,
    ErrorKind, ExprKind, Session,
};
const PATH: &str = "lib/machine/dispatch/native-first-execute.lisp";
const SOURCE: &str = include_str!("../../../lib/machine/dispatch/native-first-execute.lisp");

fn eval(s: &mut Session, expression: &str) -> Result<sens::Value, sens::LanguageError> {
    let ast = parse_mixed_exact_domain_machine_source(PATH, expression)?;
    Ok(eval_parsed_expressions(&ast, s)?.value)
}
fn session() -> Session {
    let mut s = Session::default();
    let ast = parse_mixed_exact_domain_machine_source(PATH, SOURCE)
        .expect("чинний reader повинен розібрати всі визначення native-first bridge");
    eval_parsed_expressions(&ast, &mut s).expect("install full execution bridge");
    s
}
#[test]
fn exact_d1_words_not_synthetic_predicate_calls() {
    for (source, expected) in [("так", true), ("ні", false)] {
        let ast = parse_mixed_exact_domain_machine_source(PATH, source)
            .expect("чинний точнодоменний reader D1 проєкції");
        assert!(matches!(
            &ast[0].kind,
            ExprKind::DomainIdentity(DomainIdentity::D1(_))
        ));
        let mut s = Session::default();
        assert_eq!(
            eval(&mut s, source).unwrap().as_predicate_bit(),
            Some(expected)
        );
    }
    for source in ["0", "1", "(як-є ())"] {
        let parsed = parse(source).unwrap();
        assert!(
            !matches!(
                &parsed[0].kind,
                ExprKind::DomainIdentity(DomainIdentity::D1(_))
            ),
            "numeric/structural source may not alias exact D1: {source}"
        );
    }
}
#[test]
fn real_bridge_accepts_both_d1_answers_and_keeps_short_circuit() {
    let mut s = session();
    for (p, result) in [("так", "selected"), ("ні", "fallback")] {
        let source = format!("(за-умовою ({p} (як-є selected)) (так (як-є fallback)))");
        assert_eq!(eval(&mut s, &source).unwrap().to_string(), result);
    }
    assert_eq!(
        eval(
            &mut s,
            "(за-умовою (так (як-є selected)) (так (non-existent-operation)))"
        )
        .expect("unreached branch must not execute")
        .to_string(),
        "selected"
    );
}
#[test]
fn bridge_maintains_explicit_outcome_shapes_without_cpu() {
    let mut s = session();
    let completed = eval(
        &mut s,
        "(нативне-виконання-завершено (як-є evaluator) (як-є success))",
    )
    .expect("route envelope construction");
    assert!(completed.to_string().contains("execution-route"));
    assert!(completed.to_string().contains("completed"));
    let rejected = eval(
        &mut s,
        "(нативне-виконання-відхилено (як-є native) (як-є denied))",
    )
    .expect("native rejection is data, not hidden evaluator fallback");
    assert!(rejected.to_string().contains("rejected"));
    assert!(rejected.to_string().contains("denied"));
}
#[test]
fn invalid_predicate_types_and_binder_mismatch_fail_closed() {
    let mut s = session();
    let error = eval(
        &mut s,
        "(за-умовою ((як-є ()) (як-є false)) (так (як-є fallback)))",
    )
    .expect_err("empty structure is not logical NO");
    assert_eq!(error.kind, ErrorKind::Type);
    let error = eval(&mut s, "(хибне? (як-є ()))").expect_err("NOT must reject structural nil");
    assert_eq!(error.kind, ErrorKind::Type);
    assert!(parse_mixed_exact_domain_machine_source("lib/not-machine.lisp", SOURCE).is_err());
}

#[test]
fn ukrainian_lambda_bindings_preserve_plan_and_tag_semantics() {
    // Справжній SENS evaluator: позитивні/негативні маршрути D3 EQ/ATOM
    // та варіанти списку; цитовані теги не перейменовуються лексичним binder.
    let mut s = session();
    for (source, expected) in [
        (
            "(нативний-стан-мітки-плану (як-є (native-plan 8 9)) (як-є native-plan))",
            "same",
        ),
        (
            "(нативний-стан-мітки-плану (як-є (native-plan 8 9)) (як-є evaluator-fallback))",
            "distinct",
        ),
        (
            "(нативний-стан-мітки-плану (як-є ((native-plan) 8 9)) (як-є native-plan))",
            "distinct",
        ),
        (
            "(нативний-стан-мітки-плану (як-є ()) (як-є native-plan))",
            "distinct",
        ),
    ] {
        let actual = eval(&mut s, source).expect("SENS D3 comparison must execute");
        assert_eq!(actual.to_string(), expected, "{source}");
    }
    for (source, expected) in [
        ("(нативний-список-двох-елементів? (як-є (one two)))", true),
        (
            "(нативний-список-двох-елементів? (як-є (one two three)))",
            false,
        ),
        ("(нативний-список-двох-елементів? (як-є ()))", false),
    ] {
        let actual = eval(&mut s, source).expect("SENS list shape law must execute");
        assert_eq!(actual.as_predicate_bit(), Some(expected), "{source}");
    }
}
