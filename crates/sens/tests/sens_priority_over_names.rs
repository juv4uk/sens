//! Чинний закон: українські викличні голови → точні D3/D4/D5,
//! а не старий восьмибітний Function8. Дані й вільні імена не переписуються.
//! Семантику перевіряє лише справжній evaluator SENS.

use sens::{
    eval_program, lower_program, parse, DomainIdentity, ExprKind, Session, Value,
};

#[test]
fn ukrainian_surfaces_lower_to_exact_ratified_domains() {
    let a = "#d24:000000000000000000000001";
    let b = "#d24:000000000000000000000010";
    for (surface, domain_width, bits) in [
        ("додати", 5, 0b01010),
        ("відняти", 5, 0b01011),
        ("помножити", 5, 0b10110),
        ("частка", 5, 0b10111),
    ] {
        let source = format!("({surface} {a} {b})");
        let lowered = lower_program(&parse(&source).expect("читач СЕНС"));
        let [expr] = lowered.as_slice() else {
            panic!("потрібен один виклик: {surface}");
        };
        match &expr.kind {
            ExprKind::DomainCall(identity, _) => assert_eq!(
                (identity.width(), identity.packed_bits()),
                (domain_width, bits),
                "поверхня {surface}: неправильний ратифікований код",
            ),
            other => panic!("голова {surface} не стала точним доменом: {other:?}"),
        }
    }
}

#[test]
fn ukrainian_name_outside_call_head_is_not_a_domain() {
    for surface in ["додати", "відняти", "помножити", "частка", "атом?"] {
        let parsed = parse(surface).expect("назва має залишатися допустимими даними");
        let lowered = lower_program(&parsed);
        assert_eq!(lowered.len(), 1, "{surface}");
        assert!(matches!(&lowered[0].kind, ExprKind::Symbol(name) if name.as_ref() == surface),
            "вільне ім'я не є машинною тотожністю: {surface}");
    }

    // Цитоване ім'я залишається даними — обов'язкова негативна межа.
    let lowered = lower_program(&parse("(як-є додати)").expect("цитата"));
    let ExprKind::DomainCall(_, args) = &lowered[0].kind else {
        panic!("цитування має знижуватися до ратифікованої D3:001");
    };
    assert!(matches!(&args[0].kind, ExprKind::Symbol(name) if name.as_ref() == "додати"));
}

#[test]
fn same_binary_value_in_d5_and_d8_is_not_the_same_identity() {
    let d5 = sens::parse_exact_domain_source("01010").expect("D5");
    let d8 = sens::parse_exact_domain_source("00001010").expect("D8");
    assert!(matches!(&d5[0].kind, ExprKind::DomainIdentity(DomainIdentity::D5(_))));
    assert!(matches!(&d8[0].kind, ExprKind::DomainIdentity(DomainIdentity::D8(_))));
    assert_ne!(d5[0].kind, d8[0].kind);
}
