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

#[test]
fn reason_index_predicate_returns_exact_d1_not_atom_or_legacy_boolean() {
    let mut session = session();
    for (source, expected) in [
        ("(reason-index? (quote ()))", false),
        ("(reason-index? (quote atom))", false),
        ("(reason-index? (quote (other linear () ())))", false),
        ("(reason-index? (reason-index-linear (quote ())))", true),
        ("(reason-index? (reason-make-index (quote (((p a))))))", true),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|err| panic!("{source}: {err}")).value;
        assert_eq!(value.as_predicate_bit(), Some(expected),
            "reason-index? must produce exact D1; source: {source}, value: {value}");
    }
}

#[test]
fn reason_index_migration_exhausts_all_2046_exact_width_coordinate_candidates() {
    // This counts 2046 mechanical coordinates (NOT 2046 callable functions).
    // The test detects truncation, cross-domain aliasing and accidental
    // logical padding, independently of display labels or legacy SID8.
    use sens::domain_ladder::DomainCoordinate;
    use std::collections::HashSet;

    let mut seen = HashSet::new();
    let mut bit_count = 0usize;
    for width in 1u8..=10 {
        let capacity = 1u16 << width;
        for payload in 0..capacity {
            let coordinate = DomainCoordinate::new(width, payload)
                .expect("every in-width pair must be representable");
            assert!(seen.insert(coordinate),
                "collision in D{width}: {payload:0w$b}", w = usize::from(width));
            assert_eq!(coordinate.width(), width);
            assert_eq!(coordinate.bits(), payload);
            assert_ne!(DomainCoordinate::new(width, capacity), Some(coordinate));
            bit_count += usize::from(width);
        }
        assert!(DomainCoordinate::new(width, capacity).is_none(),
            "oversize value must not truncate into D{width}");
        assert!(DomainCoordinate::new(width, u16::MAX).is_none());
    }
    assert_eq!(seen.len(), 2046);
    assert_eq!(bit_count, 18_434);
    assert_eq!((bit_count + 7) / 8, 2305);
    assert_eq!(8 * ((bit_count + 7) / 8) - bit_count, 6);
    for width in 1u8..=9 {
        assert_ne!(DomainCoordinate::new(width, 1),
                   DomainCoordinate::new(width + 1, 1));
    }
    assert_eq!(DomainCoordinate::new(10, 1024), None);
}
