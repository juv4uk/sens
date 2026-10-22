//! Свідок: чинне українське визначення створює механізм тієї самої тотожності D5.

use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse_mixed_exact_domain_core_source,
    Bit5, CoreD5, DomainIdentity, ErrorKind, Expr, ExprKind, Session, Span,
};

fn exact_d5_call(
    bits: u8,
    arguments: &str,
    session: &mut Session,
) -> Result<String, sens::LanguageError> {
    let source = format!("(тестовий-виклик {arguments})");
    let mut forms = parse_mixed_exact_domain_core_source("lib/core4.lisp", &source)?;
    let form = forms.first_mut().expect("one call form");
    let ExprKind::List(items) = &form.kind else {
        panic!("call list");
    };
    let mut items = items.to_vec();
    items[0] = Expr {
        kind: ExprKind::DomainIdentity(DomainIdentity::D5(CoreD5::from_word(
            Bit5::new(bits).expect("exact five-bit D5 coordinate"),
        ))),
        span: Span::default(),
    };
    form.kind = ExprKind::List(items.into());
    eval_parsed_expressions(&forms, session).map(|result| result.value.to_string())
}

#[test]
fn ukrainian_d5_definition_and_exact_domain_call_share_one_mechanism() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("Core bootstrap");

    assert_eq!(
        eval_program("(зворот (як-є (а б в)))", &mut session)
            .expect("Ukrainian D5 surface")
            .value
            .to_string(),
        "(в б а)"
    );
    assert_eq!(
        exact_d5_call(0b10100, "(як-є (а б в))", &mut session).unwrap(),
        "(в б а)"
    );
}

#[test]
fn exact_d5_reverse_needs_its_core_definition() {
    let mut bare = Session::bare();
    let error = exact_d5_call(0b10100, "(як-є (а б в))", &mut bare)
        .expect_err("D5 residency alone must not provide an execution mechanism");
    assert_eq!(error.kind, ErrorKind::Type);

    let mut loaded = Session::bare();
    load_core_library(&mut loaded).expect("Core bootstrap");
    assert_eq!(
        exact_d5_call(0b10100, "(як-є (а б в))", &mut loaded).unwrap(),
        "(в б а)"
    );
}
