use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse_mixed_exact_domain,
    parse_mixed_exact_domain_reasoning_source, Session,
};

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session)
        .expect("canonical current Core4 bootstrap must load");

    for (path, library) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
    ] {
        let parsed = parse_mixed_exact_domain_reasoning_source(path, library)
            .unwrap_or_else(|error| panic!("exact reasoning parse failed for {path}: {error}"));
        eval_parsed_expressions(&parsed, &mut session)
            .unwrap_or_else(|error| panic!("exact reasoning load failed for {path}: {error}"));
    }
    session
}

fn eval(session: &mut Session, source: &str) -> String {
    let parsed = parse_mixed_exact_domain(source)
        .unwrap_or_else(|error| panic!("exact fixture parse failed: {error}\nsource: {source}"));
    eval_parsed_expressions(&parsed, session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn normal_nested_rule_list_is_not_probed_with_eq_as_a_schema_tag() {
    let mut s = session();
    let source = r#"
      (def rules (quote (((mortal socrates))
                         ((not? (mortal socrates))))))
      (reason-index-mode (reason-ensure-index rules))
    "#;
    assert_eq!(eval(&mut s, source), "indexed");
}

#[test]
fn canonical_index_is_recognized_and_malformed_index_falls_back_safely() {
    let mut s = session();
    let source = r#"
      (def rules (quote (((p one)) ((q two)))))
      (list
        (cond ((reason-index? (reason-make-index rules))
               (quote canonical-index)))
        (reason-index-mode
          (reason-ensure-index (quote (not-an-index indexed))))
    "#;
    assert_eq!(eval(&mut s, source), "(canonical-index linear)");
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
