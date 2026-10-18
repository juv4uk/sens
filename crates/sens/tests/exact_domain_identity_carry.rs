use sens::{eval_exact_domain_program, DomainIdentity, ErrorKind, Session, Value};

#[test]
fn quote_carries_the_exact_domain_identity_as_data() {
    let result = eval_exact_domain_program("(001 00000001)", &mut Session::bare())
        .expect("D3 quote returns the W8 value as an exact D8 datum");

    assert!(matches!(
        result.value,
        Value::DomainIdentity(DomainIdentity::D8(word))
            if word.word().packed_bits() == 1
    ));
}

#[test]
fn a_resident_domain_identity_does_not_gain_callability_from_its_bits() {
    let error = eval_exact_domain_program("(00000001 (001 1))", &mut Session::bare())
        .expect_err("D8 identity has no callable mechanism in this test");

    assert_eq!(error.kind, ErrorKind::Type);
}
