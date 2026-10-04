use sens::{
    eval_parsed_expressions, eval_program, parse_canonical_binary, Bit4, Bit5, CoreD4, CoreD5,
    DomainIdentity, Session, Value,
};

fn session_with_active_core() -> Session {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("active Core must load without rebinding generated D4 selectors");
    session
}

fn d4(bits: u8) -> DomainIdentity {
    DomainIdentity::from(CoreD4::from_word(Bit4::new(bits).unwrap()))
}

fn d5(bits: u8) -> Value {
    Value::DomainIdentity(DomainIdentity::from(CoreD5::from_word(
        Bit5::new(bits).unwrap(),
    )))
}

fn eval_binary(source: &str) -> Value {
    let expressions = parse_canonical_binary(source)
        .unwrap_or_else(|error| panic!("canonical binary parse failed for {source}: {error}"));
    let mut session = Session::default();
    eval_parsed_expressions(&expressions, &mut session)
        .unwrap_or_else(|error| panic!("canonical binary eval failed for {source}: {error}"))
        .value
}

#[test]
fn ratified_d4_selectors_execute_from_canonical_d2_source() {
    // CAAR ((D5:a D5:b) D5:c) -> D5:a
    assert_eq!(
        eval_binary(
            "10 1010 00 10 001 00 10 10 01010 00 01011 01 00 10010 01 01 01"
        ),
        d5(0b01010)
    );

    // CADR (D5:a D5:b D5:c) -> D5:b
    assert_eq!(
        eval_binary(
            "10 1011 00 10 001 00 10 01010 00 01011 00 10010 01 01 01"
        ),
        d5(0b01011)
    );

    // CDAR ((D5:a D5:b) D5:c) -> (D5:b)
    assert_eq!(
        eval_binary(
            "10 1100 00 10 001 00 10 10 01010 00 01011 01 00 10010 01 01 01"
        ),
        Value::list([d5(0b01011)])
    );

    // CDDR (D5:a D5:b D5:c) -> (D5:c)
    assert_eq!(
        eval_binary(
            "10 1101 00 10 001 00 10 01010 00 01011 00 10010 01 01 01"
        ),
        Value::list([d5(0b10010)])
    );
}

#[test]
fn active_core_does_not_redefine_generated_selector_descendants() {
    let core = include_str!("../../../lib/core.lisp");

    for legacy_definition in [
        "(00001001 caar",
        "(00001001 cadr",
        "(00001001 cdar",
        "(00001001 cddr",
    ] {
        assert!(
            !core.contains(legacy_definition),
            "generated selector must not have a second closure definition: {legacy_definition}"
        );
    }
}

#[test]
fn selector_surface_is_the_first_class_exact_domain_value() {
    let mut session = session_with_active_core();

    let cadr = eval_program("cadr", &mut session)
        .expect("cadr surface must resolve as a first-class value")
        .value;
    assert_eq!(cadr, Value::DomainIdentity(d4(0b1011)));

    // Higher-order use proves that removing the old Lisp closure did not make
    // the selector call-head-only.
    assert_eq!(
        eval_program("(map cadr '((1 2) (3 4)))", &mut session)
            .expect("first-class exact-domain CADR must work through map")
            .value
            .to_string(),
        "(2 4)"
    );
}

#[test]
fn cdar_is_a_real_d4_resident_without_historical_descendant_row() {
    assert_eq!(
        eval_binary(
            "10 1100 00 10 001 00 10 10 01010 00 01011 01 00 10010 01 01 01"
        ),
        Value::list([d5(0b01011)])
    );
}
