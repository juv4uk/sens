use sens::{
    eval_parsed_expressions, eval_program, parse_canonical_binary, parse_mixed_exact_domain_reasoning_source, Session,
};

fn session() -> Session {
    let mut session = Session::default();
    sens::eval_pinned_legacy_core_source(
        "lib/core.lisp", include_str!("../../../lib/core.lisp"), &mut session,
    ).expect("канонічний Core має завантажуватись власним точним reader");
    for (path, source) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
    ] {
        let parsed = parse_mixed_exact_domain_reasoning_source(path, source)
            .unwrap_or_else(|error| panic!("{path}: exact source reader: {error}"));
        eval_parsed_expressions(&parsed, &mut session)
            .unwrap_or_else(|error| panic!("{path}: exact source evaluator: {error}"));
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
fn binary_sens_owns_reason_index_car_eq_guard_law() {
    let mut s = session();
    let source = include_str!("../../../tests/semantic/reason-index-car-eq-guard-law.bits");
    assert!(
        source.bytes().all(|b| b.is_ascii_whitespace() || matches!(b, b'0' | b'1')),
        "semantic law must be written as visible binary SENS words"
    );
    let expressions = parse_canonical_binary(source)
        .expect("binary law must be valid D2-framed SENS");
    eval_parsed_expressions(&expressions, &mut s)
        .expect("SENS's own CAR/ATOM/EQ law rejected its counterexample or positive control");
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
    // Довжина як некваліфіковане число нині не є D24+ арифметикою.
    // Перевіряємо сильніший інваріант: усі правила + первісний порядок.
    let source = r#"
      (def rules (quote (((p one)) ((q two)) ((r three)))))
      (reason-index-candidates
        (quote (var x))
        (reason-make-index rules))
    "#;
    assert_eq!(
        eval(&mut s, source),
        "(((p one)) ((q two)) ((r three)))"
    );
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
