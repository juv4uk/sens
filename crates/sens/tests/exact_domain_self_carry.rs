//! Exact D1–24+ coordinates survive a language-level carry without byte aliases.
use sens::{eval_exact_domain_program, DomainD10, DomainIdentity, ErrorKind, Session, Value};

#[test]
fn exact_identity_is_carried_through_a_d4_lambda_and_quote() {
    let result = eval_exact_domain_program("((0010 (f) f) (001 0100001100))", &mut Session::bare())
        .expect("the exact D4 lambda and quote forms carry D10 as data");

    assert!(matches!(
        result.value,
        Value::DomainIdentity(DomainIdentity::D10(word))
            if word.packed_bits() == 0b0100001100
    ));
}

#[test]
fn carried_concrete_definition_executes_only_after_core_binding() {
    let program = "(((0010 (f) f) 0100001100) (001 ()))";

    let mut bound = Session::bare();
    sens::load_core_library(&mut bound).expect("Core4 definitions bind current exact slots");
    let result = eval_exact_domain_program(program, &mut bound)
        .expect("carried D10 LISTP closure is admitted after concrete binding");
    assert!(matches!(
        result.value,
        Value::DomainIdentity(DomainIdentity::D1(bit)) if bit.word().packed_bits() == 1
    ));

    let error = eval_exact_domain_program(program, &mut Session::bare())
        .expect_err("a D10 coordinate without a concrete binding is not callable");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn unbound_d10_identity_is_still_carried_without_becoming_callable() {
    let mut session = Session::bare();
    let carried = eval_exact_domain_program("((0010 (f) f) (001 1111111111))", &mut session)
        .expect("arbitrary exact D10 identity is data even when unbound");
    assert_eq!(
        carried.value,
        Value::DomainIdentity(DomainIdentity::D10(DomainD10::new(0b1111111111).unwrap()))
    );

    let error = eval_exact_domain_program("(((0010 (f) f) 1111111111) (001 ()))", &mut session)
        .expect_err("carrying identity does not admit a callable mechanism");
    assert_eq!(error.kind, ErrorKind::Type);
}
