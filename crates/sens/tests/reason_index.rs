use sens::{
    eval_parsed_expressions, eval_program, parse_canonical_binary, parse_exact_domain_source,
    parse_mixed_exact_domain_reasoning_source, Session,
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
fn binary_sens_semantic_migration_witness_covers_reason_index_and_narration() {
    let mut s = session();

    // SENS itself owns the reason-index CAR/EQ law and its exact D1 verdict.
    let reason_bits = include_str!("../../../tests/semantic/reason-index-car-eq-guard-law.bits");
    assert!(
        reason_bits.bytes().all(|b| b.is_ascii_whitespace() || matches!(b, b'0' | b'1')),
        "reason-index law must contain only binary words and separators"
    );
    let reason_exprs =
        parse_canonical_binary(reason_bits).expect("canonical binary reason-index law");
    let reason_verdict = eval_parsed_expressions(&reason_exprs, &mut s)
        .expect("SENS rejected its reason-index CAR/EQ law");
    assert_eq!(
        reason_verdict.value.as_predicate_bit(),
        Some(true),
        "reason-index law must return exact D1:YES"
    );

    let statuses = parse_exact_domain_source(include_str!("../../../lib/result-status.lisp"))
        .expect("result-status source must preserve exact domain identities");
    eval_parsed_expressions(&statuses, &mut s)
        .expect("exact-domain result-status source must load");
    let narration = parse_exact_domain_source(include_str!("../../../lib/narrate.lisp"))
        .expect("narration source must preserve D1/D3/D4 widths");
    eval_parsed_expressions(&narration, &mut s)
        .expect("exact-domain narration source must load");

    let narrate_bits = include_str!("../../../tests/semantic/narrate-arity-d1-d4-law.bits");
    assert!(
        narrate_bits.bytes().all(|b| b.is_ascii_whitespace() || matches!(b, b'0' | b'1')),
        "narration law must contain only binary words and separators"
    );
    let narrate_exprs =
        parse_canonical_binary(narrate_bits).expect("canonical binary narration law");
    let narrate_verdict = eval_parsed_expressions(&narrate_exprs, &mut s)
        .expect("SENS rejected its narration arity law");
    assert_eq!(
        narrate_verdict.value.as_predicate_bit(),
        Some(true),
        "narration law must return exact D1:YES"
    );
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

#[test]
fn reason_index_builder_diagnostic_first_failing_stage() {
    let mut s = session();
    let probes = [
        ("(reason-term-predicate (quote (p a)))", "p"),
        ("(reason-rule-predicate (quote ((p a))))", "p"),
        ("(reason-index-add-reversed (quote p) (quote ((p a))) (quote ()))", "((p ((p a))))"),
        ("(reason-index-normalize-buckets (reason-index-add-reversed (quote p) (quote ((p a))) (quote ())))", "((p ((p a))))"),
        ("(reason-index-build-scan (quote ()) (quote ()) (quote ()) *reason-index-fuel*)",
         "(reason-index/1 indexed () ())"),
        ("(reason-make-index (quote (((p a)))))",
         "(reason-index/1 indexed (((p a))) ((p ((p a)))))"),
    ];
    for (probe, expected) in probes {
        assert_eq!(eval(&mut s, probe), expected, "first failing index stage: {probe}");
    }
}
