//! #3052/#3053/#3070 — exact Core.D5 list/search law witnesses.
//!
//! The compatibility parser deliberately treats non-8-bit numeric tokens as
//! ordinary decimal numbers. Therefore this witness constructs the exact D5
//! call head as typed AST and uses the compatibility parser only for payload
//! syntax. No human operation name or historical Function8/Sens8 byte selects
//! the operation under test.

use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse, Bit5, CoreD5, DomainIdentity,
    ErrorKind, Expr, ExprKind, Session, Span,
};

fn run_d5(bits: u8, arguments_source: &str) -> String {
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
        .to_string()
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
fn legacy_quotient_requires_its_lisp_binding_and_never_borrows_direct_d5_primitive() {
    let mut bare = Session::default();
    let error = eval_program("(00010100 6 3)", &mut bare)
        .expect_err("legacy QUOTIENT must not enter exact D5 arithmetic without Core binding");
    assert_eq!(error.kind, ErrorKind::Type);

    let mut loaded = Session::default();
    load_core_library(&mut loaded).expect("active Core should load");
    let value = eval_program("(00010100 6 3)", &mut loaded)
        .expect("legacy QUOTIENT should use the bound Lisp closure")
        .value;
    assert_eq!(value.to_string(), "2");
}
#[test]
fn exact_d5_append_reverse_form_a_local_list_algebra() {
    // CURRENT OD-005 identities:
    // 10000 APPEND
    // 10001 REVERSE
    assert_eq!(run_d5(0b10000, "'(a b) '(c d)"), "(a b c d)");
    assert_eq!(run_d5(0b10001, "'(a b c)"), "(c b a)");

    // Involution.
    let once = run_d5(0b10001, "'(a b c d)");
    let twice = run_d5(0b10001, &format!("'{once}"));
    assert_eq!(twice, "(a b c d)");

    // Anti-homomorphism:
    // reverse(append(x,y)) = append(reverse(y), reverse(x)).
    let appended = run_d5(0b10000, "'(a b) '(c d)");
    let left = run_d5(0b10001, &format!("'{appended}"));

    let reverse_y = run_d5(0b10001, "'(c d)");
    let reverse_x = run_d5(0b10001, "'(a b)");
    let right = run_d5(
        0b10000,
        &format!("'{reverse_y} '{reverse_x}"),
    );
    assert_eq!(left, right);
    assert_eq!(left, "(d c b a)");

    // Nested payload is opaque list data, not flattened by either operation.
    assert_eq!(
        run_d5(0b10001, "'((a b) c (d e))"),
        "((d e) c (a b))"
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

    // MEMBER exposes predicate-like hit/miss rather than the matching pair.
    assert_eq!(run_d5(0b11101, "'b '(a b c)"), "t");
    assert_eq!(run_d5(0b11101, "'z '(a b c)"), "()");

    // MEMBER also uses structural equality for list elements.
    assert_eq!(
        run_d5(0b11101, "'(a b) '((x y) (a b) (c d))"),
        "t"
    );
}
