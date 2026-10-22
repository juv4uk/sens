use sens::{
    eval_parsed_expressions, Bit5, Bit6, Bit7, Bit8, CoreD5, CoreD6, CoreD8, D7DataWord,
    DomainIdentity, Expr, ExprKind, Rational, Session, Span,
};

fn exact_d6_call(
    bits: u8,
    args: &str,
    session: &mut Session,
) -> Result<String, sens::LanguageError> {
    let mut parsed = sens::parse(&format!("(__d6_probe__ {args})")).expect("probe payload");
    let mut form = parsed.remove(0);
    let ExprKind::List(items) = form.kind else {
        panic!("probe list");
    };
    let mut items = items.to_vec();
    items[0] = Expr {
        kind: ExprKind::DomainIdentity(DomainIdentity::D6(CoreD6::from_word(
            Bit6::new(bits).expect("D6 bits"),
        ))),
        span: Span::default(),
    };
    form.kind = ExprKind::List(items.into());
    eval_parsed_expressions(&[form], session).map(|result| result.value.to_string())
}

#[test]
fn only_proven_d6_arithmetic_and_integerp_project_to_callable_core() {
    for bits in 0u8..64 {
        let identity = DomainIdentity::D6(CoreD6::from_word(Bit6::new(bits).unwrap()));
        assert_eq!(
            identity.core_operation().is_some(),
            matches!(bits, 0b001110 | 0b001111 | 0b010010 | 0b111110),
            "D6:{bits:06b}"
        );
    }
}

#[test]
fn exact_d6_add1_sub1_execute_as_exact_lower_domain_composition() {
    let mut session = Session::default();
    sens::load_core_library(&mut session).expect("core");

    for (bits, args, expected) in [
        (0b001110, "1/2", "3/2"),
        (0b001110, "-2", "-1"),
        (0b001111, "1/2", "-1/2"),
        (0b001111, "-2", "-3"),
        (0b001110, "41", "42"),
        (0b001111, "41", "40"),
    ] {
        assert_eq!(
            exact_d6_call(bits, args, &mut session).expect("admitted D6 mechanism"),
            expected,
            "D6:{bits:06b}({args})"
        );
    }
}

#[test]
fn d6_neg_executes_in_the_sens_evaluator_with_signed_and_fractional_operands() {
    let mut session = Session::default();
    sens::load_core_library(&mut session).expect("SENS core");
    for (argument, expected) in [
        ("0", "0"),
        ("7", "-7"),
        ("-7", "7"),
        ("1/2", "-1/2"),
        ("-1/2", "1/2"),
    ] {
        assert_eq!(
            exact_d6_call(0b010010, argument, &mut session)
                .expect("SENS-owned D6 NEG via exact D5 subtraction"),
            expected,
            "D6:010010({argument})"
        );
    }
    for argument in ["", "1 2"] {
        assert_eq!(
            exact_d6_call(0b010010, argument, &mut session)
                .unwrap_err()
                .kind,
            sens::ErrorKind::Arity
        );
    }
    assert_eq!(
        exact_d6_call(0b010010, "(як-є х)", &mut session)
            .unwrap_err()
            .kind,
        sens::ErrorKind::Type
    );
    let same_payload_d7 = DomainIdentity::D7(
        D7DataWord::from_word(Bit7::new(0b010010).unwrap())
    );
    assert!(same_payload_d7.core_operation().is_none());
}

#[test]
fn d6_add1_sub1_preserve_exact_arity_and_numeric_errors() {
    let mut session = Session::default();
    sens::load_core_library(&mut session).expect("core");

    for source in [(0b001110, ""), (0b001111, "1 2")] {
        let error = exact_d6_call(source.0, source.1, &mut session)
            .expect_err("D6 ADD1/SUB1 must keep unary arity");
        assert_eq!(error.kind, sens::ErrorKind::Arity);
    }

    let error = exact_d6_call(0b001110, "(quote x)", &mut session)
        .expect_err("ADD1 on non-number must preserve D5 numeric type law");
    assert_eq!(error.kind, sens::ErrorKind::Type);
}

#[test]
fn equal_payloads_in_other_domains_do_not_inherit_d6_mechanisms() {
    // Same packed payload 14 has independent identities across widths.
    let d5 = DomainIdentity::D5(CoreD5::from_word(Bit5::new(14).unwrap()));
    let d6 = DomainIdentity::D6(CoreD6::from_word(Bit6::new(14).unwrap()));
    let d7 = DomainIdentity::D7(D7DataWord::from_word(Bit7::new(14).unwrap()));
    let d8 = DomainIdentity::D8(CoreD8::from_word(Bit8::new(14).unwrap()));

    assert_eq!(d5.packed_bits(), d6.packed_bits());
    assert_eq!(d6.packed_bits(), d7.packed_bits());
    assert_eq!(d7.packed_bits(), d8.packed_bits());

    assert_eq!(d5.width(), 5);
    assert_eq!(d6.width(), 6);
    assert_eq!(d7.width(), 7);
    assert_eq!(d8.width(), 8);

    assert!(d6.core_operation().is_some());
    assert!(d7.core_operation().is_none());
    assert!(d8.core_operation().is_none());

    // D5:01110 is an independently admitted selector, not ADD1.
    let d5_core = d5.core_operation().expect("D5 selector remains callable");
    assert_eq!((d5_core.width(), d5_core.packed_bits()), (5, 14));
}

#[test]
fn d6_identity_remains_exact_and_not_a_legacy_sid() {
    let add1 = DomainIdentity::D6(CoreD6::from_word(Bit6::new(0b001110).unwrap()));
    let sub1 = DomainIdentity::D6(CoreD6::from_word(Bit6::new(0b001111).unwrap()));

    assert_eq!(format!("{add1}"), "001110");
    assert_eq!(format!("{sub1}"), "001111");

    // Exact rational witness: the mechanism composes with exact 1 rather than
    // converting through a floating or legacy byte carrier.
    assert_eq!(Rational::new(1, 2).unwrap().to_string(), "1/2");
}
