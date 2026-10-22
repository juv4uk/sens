use sens::{eval_program, ErrorKind, Session, Value};
use std::rc::Rc;

#[test]
fn d5_transformer_placement_preserves_lambda_closure_payload_identity() {
    let mut session = Session::default();

    let closure = eval_program(
        "(визначити кандидатна-основа (функція (a b) a)) кандидатна-основа",
        &mut session,
    )
    .expect("ordinary LAMBDA closure should be constructible")
    .value;

    let transformer = eval_program("(макрос кандидатна-основа)", &mut session)
        .expect("surrogate transformer materializer should accept a closure")
        .value;

    match (&closure, &transformer) {
        (Value::Closure(base), Value::Macro(staged)) => assert!(
            Rc::ptr_eq(base, staged),
            "transformer must preserve the exact LAMBDA closure payload"
        ),
        other => panic!("expected Closure -> Macro over one payload, got {other:?}"),
    }
}

#[test]
fn d5_transformer_placement_materializer_rejects_non_closure_input() {
    let mut session = Session::default();
    let error = eval_program("(макрос 42)", &mut session)
        .expect_err("surrogate transformer materializer must require a closure");

    assert_eq!(error.kind, ErrorKind::Type);
    assert!(error.message.contains("замикання"));
}

#[test]
fn d5_transformer_placement_changes_call_mode_not_body_payload() {
    let mut session = Session::default();

    eval_program(
        r#"
        (визначити однакове-тіло (функція (a b) a))
        (визначити staged-однакове-тіло (макрос однакове-тіло))
        "#,
        &mut session,
    )
    .expect("base and staged views should share one closure body");

    let ordinary = eval_program("(однакове-тіло (як-є ok) невідоме-імя)", &mut session)
        .expect_err("ordinary closure must eagerly evaluate невідоме-імя");
    assert_eq!(ordinary.kind, ErrorKind::UnknownSymbol);

    let staged = eval_program(
        "(staged-однакове-тіло (як-є ok) невідоме-імя)",
        &mut session,
    )
    .expect("staged view must preserve unused raw operand")
    .value
    .to_string();

    assert_eq!(staged, "ok");
}

#[test]
fn d5_macro_uses_only_the_ratified_d5_identity() {
    use sens::{parse_mixed_exact_domain, Expr, ExprKind};

    fn collect_d5(expr: &Expr, identities: &mut Vec<u16>) {
        match &expr.kind {
            ExprKind::DomainIdentity(identity) if identity.width() == 5 => {
                identities.push(identity.packed_bits());
            }
            ExprKind::List(items) => {
                for child in items.iter() {
                    collect_d5(child, identities);
                }
            }
            _ => {}
        }
    }

    let parsed = parse_mixed_exact_domain("(макрос)")
        .expect("український D5 резидент має читатися точним reader");
    let mut identities = Vec::new();
    for form in &parsed {
        collect_d5(form, &mut identities);
    }
    assert_eq!(
        identities,
        vec![0b00011],
        "D5 «макрос» має власну точну ширину й координату"
    );
}
