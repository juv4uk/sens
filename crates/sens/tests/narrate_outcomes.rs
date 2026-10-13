//! B2: presentation must preserve the semantic distinction established by
//! lib/result-status.my instead of collapsing every non-proof into one phrase.

use sens::{
    eval_parsed_expressions, load_core_library, parse_canonical_binary, parse_exact_domain_source, parse_mixed_exact_domain,
    Expr, ExprKind,
    parse_mixed_exact_domain_reasoning_source, Session,
};

fn eval_outcome_value(source: &str) -> sens::Value {
    let mut session = Session::default();
    load_core_library(&mut session)
        .expect("canonical current Core4 bootstrap must load via its public loader");
    // These reasoning libraries contain exact D9 call heads; use their
    // source-pinned reader rather than the legacy numeric compatibility parser.
    for (path, source) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
    ] {
        let parsed = parse_mixed_exact_domain_reasoning_source(path, source)
            .unwrap_or_else(|error| panic!("exact reasoning parse failed for {path}: {error}"));
        eval_parsed_expressions(&parsed, &mut session)
            .unwrap_or_else(|error| panic!("exact reasoning load failed for {path}: {error}"));
    }

    // result-status.lisp and narrate.lisp carry exact-width D8/D9 words.
    // Do not load either through the ordinary compatibility reader: it can
    // interpret e.g. 11110111 as a numeric value instead of a domain identity.
    let statuses = parse_exact_domain_source(include_str!("../../../lib/result-status.lisp"))
        .expect("canonical result-status source must preserve each domain width");
    eval_parsed_expressions(&statuses, &mut session)
        .expect("exact-domain result-status library must load");

    let narration = parse_exact_domain_source(include_str!("../../../lib/narrate.lisp"))
        .expect("canonical narration source must preserve each domain width");
    eval_parsed_expressions(&narration, &mut session)
        .expect("exact-domain narration library must load");

    let expressions = parse_mixed_exact_domain(source)
        .unwrap_or_else(|error| panic!("exact fixture parse failed: {error}\nsource: {source}"));
    eval_parsed_expressions(&expressions, &mut session)
        .unwrap_or_else(|error| panic!("evaluation failed: {error}\nsource: {source}"))
        .value
}

fn eval_outcome_narration(source: &str) -> String {
    eval_outcome_value(source).to_string()
}

fn gather_domain_widths(expr: &Expr, widths: &mut Vec<usize>) {
    if let ExprKind::DomainIdentity(identity) = &expr.kind {
        widths.push(identity.width());
    }
    if let ExprKind::List(items) = &expr.kind {
        for item in items.iter() {
            gather_domain_widths(item, widths);
        }
    }
}

#[test]
fn binary_sens_owns_d1_d4_structural_arity_law() {
    let source = include_str!("../../../tests/semantic/narrate-arity-d1-d4-law.bits");
    assert!(
        source.bytes().all(|byte| matches!(byte, b'0' | b'1' | b' ' | b'\\n' | b'\\r' | b'\\t')),
        "SENS-owned witness must contain only exact binary words and whitespace"
    );
    let mut session = Session::default();
    load_core_library(&mut session).expect("canonical Core4 must load");
    let parsed = parse_canonical_binary(source)
        .expect("canonical D2-framed binary SENS witness must parse");
    eval_parsed_expressions(&parsed, &mut session)
        .expect("SENS self-verdict rejected a D1/D3/D4 structural law");
}
#[test]
fn arity_helpers_use_exact_d1_predicates_with_d3_d4_structure() {
    let source = include_str!("../../../lib/narrate.lisp");
    let start = source
        .find("(0011 narrate-proper-list?")
        .expect("structural arity helpers are present");
    let end = source[start..]
        .find("(0011 narrate-fact")
        .expect("next production definition bounds helper source")
        + start;
    let helper_source = &source[start..end];
    let forms = parse_exact_domain_source(helper_source)
        .expect("arity helpers must parse under the exact-domain reader");
    assert_eq!(forms.len(), 3, "proper-list, exact-two, exact-three helpers");

    let mut widths = Vec::new();
    for form in &forms {
        gather_domain_widths(form, &mut widths);
    }
    widths.sort_unstable();
    widths.dedup();
    assert_eq!(
        widths,
        vec![1, 3, 4],
        "D1 is reserved for exact predicate results; only D3/D4 structure is used, not D6 LENGTH or D8 EQUAL"
    );

    let executable_source = helper_source
        .lines()
        .filter(|line| !line.trim_start().starts_with(';'))
        .collect::<Vec<_>>()
        .join("\n");
    assert!(!executable_source.contains("000000"), "D6 LENGTH must not reappear in arity helpers");
    assert!(!executable_source.contains("11110111"), "D8 EQUAL must not reappear in arity helpers");
    assert!(!executable_source.contains("(001 0)"), "quoted host zero must not stand in for D1:0");
    assert!(!executable_source.contains("(001 1)"), "quoted host one must not stand in for D1:1");
}

#[test]
fn proved_outcome_keeps_the_ground_answer_and_real_premise() {
    let source = r#"
        (let* ((rules (quote (((has (var x) mass) (planet (var x)))
                              ((planet earth)))))
               (goal (quote (has earth mass))))
          (narrate-outcome (reason-observe goal rules)))
    "#;
    assert_eq!(
        eval_outcome_narration(source),
        "(proved earth has mass because earth is a planet)"
    );
}

#[test]
fn disputed_outcome_keeps_both_evidence_sides_visible() {
    let source = r#"
        (let* ((rules (quote (((mortal socrates))
                              ((not? (mortal socrates))))))
               (narration
                 (narrate-outcome
                   (reason-observe (quote (mortal socrates)) rules))))
          (list (car narration)
                (second narration)
                (third narration)
                (length (fourth narration))))
    "#;
    assert_eq!(
        eval_outcome_narration(source),
        "(disputed because both-sides-have-evidence 2)"
    );
}

#[test]
fn invalid_outcome_names_validation_failure_and_payload() {
    assert_eq!(
        eval_outcome_narration(
            r#"(narrate-outcome (make-invalid (quote invalid-goal) 42))"#
        ),
        "(invalid because invalid-goal payload 42)"
    );
}

#[test]
fn partial_and_blocked_do_not_collapse_into_unknown() {
    assert_eq!(
        eval_outcome_narration(
            r#"(narrate-outcome (make-partial (quote ()) (quote (depth . 12))))"#
        ),
        "(partial value () bound (depth . 12))"
    );
    assert_eq!(
        eval_outcome_narration(
            r#"(narrate-outcome (make-blocked (quote (depends-on corpus))))"#
        ),
        "(blocked because (depends-on corpus))"
    );
}

#[test]
fn malformed_or_unknown_outcome_shape_is_presented_as_invalid() {
    assert_eq!(
        eval_outcome_narration(r#"(narrate-outcome 42)"#),
        "(invalid outcome-shape 42)"
    );
    assert_eq!(
        eval_outcome_narration(r#"(narrate-outcome (quote (mystery payload)))"#),
        "(invalid outcome-tag mystery)"
    );
    assert_eq!(
        eval_outcome_narration(r#"(narrate-outcome (quote (unknown)))"#),
        "(invalid outcome-shape (unknown))"
    );
    assert_eq!(
        eval_outcome_narration(r#"(narrate-outcome (quote ((bad-tag) payload)))"#),
        "(invalid outcome-tag (bad-tag))"
    );
}
