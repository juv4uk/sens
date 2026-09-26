use sens::{eval_program, Session};

fn session() -> Session {
    let mut session = Session::default();
    for library in [
        include_str!("../../../lib/core.lisp"),
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
    ] {
        eval_program(library, &mut session).expect("reason index fixture should load");
    }
    session
}

fn eval(session: &mut Session, source: &str) -> String {
    eval_program(source, session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn indexed_bucket_preserves_source_rule_order_exactly() {
    let mut s = session();
    let source = r#"
      (def rules
        (quote
          (((p first))
           ((q irrelevant))
           ((p second))
           ((r irrelevant))
           ((p third)))))
      (reason-index-candidates (quote (p target)) (reason-make-index rules))
    "#;
    assert_eq!(
        eval(&mut s, source),
        "(((p first)) ((p second)) ((p third)))"
    );
}

#[test]
fn variable_goal_falls_back_to_every_rule() {
    let mut s = session();
    let source = r#"
      (def rules (quote (((p one)) ((q two)) ((r three)))))
      (length
        (reason-index-candidates
          (quote (var x))
          (reason-make-index rules)))
    "#;
    assert_eq!(eval(&mut s, source), "3");
}

#[test]
fn variable_rule_head_disables_index_instead_of_changing_unification() {
    let mut s = session();
    let source = r#"
      (def rules
        (quote
          (((p one))
           ((var whole-head))
           ((q two)))))
      (reason-index-mode (reason-make-index rules))
    "#;
    assert_eq!(eval(&mut s, source), "linear");
}

#[test]
fn too_many_distinct_predicates_fall_back_to_linear_mode() {
    let mut s = session();
    let mut source = String::from("(reason-index-mode (reason-make-index (quote (");
    for i in 0..65 {
        source.push_str(&format!("((pred{i} value))"));
    }
    source.push_str("))))");
    assert_eq!(eval(&mut s, &source), "linear");
}
