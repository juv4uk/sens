//! Macro-produced code must carry exact domain identities, not flat SID bytes.
use sens::{eval_exact_domain_program, DomainD10, DomainIdentity, ErrorKind, Session, Value};

#[test]
fn generated_quote_stage_preserves_the_exact_domain_coordinate() {
    // D4 LAMBDA receives the exact D10 LISTP identity through a quoted
    // argument. The value remains D10; neither the macro stage nor the host
    // evaluator narrows it to a byte or infers a role from its payload.
    let result = eval_exact_domain_program(
        "((0010 (head) head) (001 0100001100))",
        &mut Session::bare(),
    )
    .expect("D4 lambda/quote must transport the D10 coordinate as data");

    assert!(matches!(
        result.value,
        Value::DomainIdentity(DomainIdentity::D10(word))
            if word.packed_bits() == 0b0100001100
    ));
}

#[test]
fn transported_d10_definition_remains_callable_only_when_bound() {
    let mut session = Session::bare();
    sens::load_core_library(&mut session).expect("current Core definitions load");

    let result =
        eval_exact_domain_program("(((0010 (head) head) 0100001100) (001 ()))", &mut session)
            .expect("transported concrete D10 LISTP closure remains callable");
    assert!(matches!(
        result.value,
        Value::DomainIdentity(DomainIdentity::D1(bit)) if bit.word().packed_bits() == 1
    ));

    let mut bare = Session::bare();
    let error = eval_exact_domain_program("(((0010 (head) head) 0100001100) (001 ()))", &mut bare)
        .expect_err("identity transport alone must not install a callable mechanism");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn d10_identity_is_not_a_d8_or_legacy_byte_alias() {
    let d10 = DomainIdentity::D10(DomainD10::new(0b0100001100).unwrap());
    assert_eq!(d10.width(), 10);
    assert_eq!(d10.packed_bits(), 0b0100001100);
    let d8 = DomainIdentity::D8(sens::CoreD8::from_word(
        sens::Bit8::new(0b01000011).unwrap(),
    ));
    assert_ne!(d10, d8);
}
