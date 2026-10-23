//! D5 compatibility-reader boundary: short words are not silently treated as domain IDs.

use sens::{parse, ExprKind};

#[test]
fn compatibility_parser_does_not_mint_short_domain_words() {
    let parsed = parse("10000").expect("ordinary decimal source");
    assert!(matches!(
        parsed[0].kind,
        ExprKind::Number(value, _) if value == 10_000.0
    ));
}

#[test]
fn parser_rejects_an_unclosed_form_before_evaluation() {
    // Rust owns reader failures; this test does not decide Lisp truth or EQ.
    assert!(parse("(як-є (радіо антена)").is_err());
}


#[test]
fn parser_rejects_an_extra_closing_form_before_evaluation() {
    // Тест механізму читача Rust, не істинності чи семантики Lisp.
    assert!(parse("(як-є радіо))").is_err());
}
