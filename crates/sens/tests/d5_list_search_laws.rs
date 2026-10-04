//! Exact Core.D5 list/search witnesses for the current #3305 map (preserved by Contract 11.5).
//!
//! The compatibility parser deliberately treats non-8-bit numeric tokens as
//! ordinary decimal numbers. Therefore this witness constructs the exact D5
//! call head as typed AST and uses the compatibility parser only for payload
//! syntax. No human operation name or historical Function8/Sens8 byte selects
//! the operation under test.

use sens::{
    eval_parsed_expressions, load_core_library, parse, Bit5, CoreD5, DomainIdentity, Expr,
    ExprKind, Session, Span,
};

fn run_d5_value(bits: u8, arguments_source: &str) -> sens::Value {
    let mut session = Session::default();
    load_core_library(&mut session).expect("active Core should load");

    // Parse only the payload with a deliberately non-semantic placeholder head.
    // Then replace that head with the exact five-bit domain identity before
    // lowering/evaluation. This prevents compatibility reader rules from
    // participating in operation selection.
    let wrapped = format!("(__d5_witness__ {arguments_source})");
    let mut parsed = parse(&wrapped).expect("witness payload should parse");
    assert_eq!(parsed.len(), 1);

    let mut form = parsed.remove(0);
    let ExprKind::List(items) = form.kind else {
        panic!("witness wrapper must parse as one list");
    };
    let mut items = items.to_vec();
    assert!(!items.is_empty());

    let identity = DomainIdentity::D5(CoreD5::from_word(
        Bit5::new(bits).expect("D5 witness coordinate"),
    ));
    items[0] = Expr {
        kind: ExprKind::DomainIdentity(identity),
        span: Span {
            start: 0,
            end: "__d5_witness__".len(),
        },
    };
    form.kind = ExprKind::List(items.into());

    eval_parsed_expressions(&[form], &mut session)
        .unwrap_or_else(|error| panic!("D5:{bits:05b} {arguments_source}: {error:?}"))
        .value
}

fn run_d5(bits: u8, arguments_source: &str) -> String {
    run_d5_value(bits, arguments_source).to_string()
}

#[test]
fn compatibility_parser_does_not_mint_short_domain_words() {
    let parsed = parse("10000").expect("ordinary decimal source");
    assert!(matches!(
        parsed[0].kind,
        ExprKind::Number(value, _) if value == 10_000.0
    ));
}

#[test]
fn exact_d5_reverse_uses_current_coordinate_and_selector_slots_do_not_alias_old_map() {
    // Current #3305 D5 map, preserved by Contract 11.5:
    // 10100 REVERSE
    assert_eq!(run_d5(0b10100, "'(a b c)"), "(c b a)");

    // 10000 is CAAAR in the current D5 map, not historical APPEND.
    // This negative control is deliberately shape-sensitive.
    assert_eq!(
        run_d5(0b10000, "'(((a b) c) d)"),
        "a",
        "D5:10000 must execute CAAAR selector law, never stale APPEND"
    );

    // 10001 is CAADR, not historical REVERSE.
    assert_eq!(
        run_d5(0b10001, "'(z ((a b) c))"),
        "(a b)",
        "D5:10001 must execute CAADR selector law, never stale REVERSE"
    );
}

#[test]
fn exact_d5_assoc_member_share_traversal_but_not_result_semantics() {
    // CURRENT OD-005 identities:
    // 11100 ASSOC
    // 11101 MEMBER
    assert_eq!(
        run_d5(0b11100, "'x '((x . first) (y . second))"),
        "(x . first)"
    );
    assert_eq!(
        run_d5(0b11100, "'z '((x . first) (y . second))"),
        "()"
    );

    // First-match ordering is observable.
    assert_eq!(
        run_d5(0b11100, "'x '((x . first) (x . second))"),
        "(x . first)"
    );

    // ASSOC admits a structural key through the Core structural-equality path.
    assert_eq!(
        run_d5(0b11100, "'(a b) '(((a b) . first) ((a c) . second))"),
        "((a b) . first)"
    );

    // MEMBER is a D5 operation whose canonical result belongs to D1.
    // Type-check the value so printed 1/0 cannot be confused with Number 1/0.
    let hit = run_d5_value(0b11101, "'b '(a b c)");
    let miss = run_d5_value(0b11101, "'z '(a b c)");
    assert_eq!(hit.as_predicate_bit(), Some(true));
    assert_eq!(miss.as_predicate_bit(), Some(false));
    assert_eq!(hit.to_string(), "1");
    assert_eq!(miss.to_string(), "0");

    // MEMBER also uses structural equality for list elements while keeping
    // the exact D1 result carrier.
    let structural_hit = run_d5_value(0b11101, "'(a b) '((x y) (a b) (c d))");
    assert_eq!(structural_hit.as_predicate_bit(), Some(true));

    // ASSOC remains value-returning; the MEMBER migration must not spill.
    let assoc = run_d5_value(0b11100, "'x '((x . first) (y . second))");
    assert_eq!(assoc.as_predicate_bit(), None);
}
