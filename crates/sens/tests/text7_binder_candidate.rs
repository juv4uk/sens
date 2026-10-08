//! #3910 candidate: D2-framed D7/Text7 binding identities.
//!
//! These witnesses are intentionally kept outside release admission until the
//! framing law is ratified. They prove only that one canonical Text7 atom can
//! participate in existing local/global binding machinery without a new SID
//! or a new AST payload variant.

use sens::{eval_parsed_expressions, parse_canonical_binary, Bit1, DomainIdentity, Session, Value};

fn t7(name: &[u8]) -> String {
    let body = name
        .iter()
        .map(|cell| format!("{cell:07b}"))
        .collect::<Vec<_>>()
        .join(" 00 ");
    format!("10 {body} 01")
}

fn eval_canonical(source: &str) -> Value {
    let expressions = parse_canonical_binary(source).expect("canonical binary source");
    let mut session = Session::default();
    eval_parsed_expressions(&expressions, &mut session)
        .expect("candidate Text7 program must evaluate")
        .value
}

#[test]
fn framed_text7_parameter_resolves_to_existing_local_slot() {
    let name = t7(&[0x41, 0x42]);
    // (lambda (<Text7-name>) <Text7-name>) 1
    let source = format!(
        "10 0010 00 10 {name} 01 00 {name} 01 00 1 01"
    );
    let value = eval_canonical(&source);
    assert_eq!(
        value,
        Value::DomainIdentity(DomainIdentity::D1(
            sens::PredicateBit::from_word(Bit1::new(1).unwrap())
        ))
    );
}

#[test]
fn framed_text7_global_definition_resolves_to_existing_closure_binding() {
    let name = t7(&[0x41, 0x42]);
    // (define <Text7-name> (lambda () 0)) ; (<Text7-name>)
    let source = format!(
        "10 0011 00 {name} 00 10 0010 00 10 01 00 0 01 01 00 {name} 01"
    );
    let value = eval_canonical(&source);
    assert_eq!(
        value,
        Value::DomainIdentity(DomainIdentity::D1(
            sens::PredicateBit::from_word(Bit1::new(0).unwrap())
        ))
    );
}

#[test]
fn quoted_d2_w7_frame_remains_structural_data_not_a_binding_lookup() {
    let name = t7(&[0x41, 0x42]);
    // (quote <Text7-name>)
    let source = format!("10 001 00 {name} 01");
    let value = eval_canonical(&source);
    assert!(matches!(value, Value::Pair(_, _)), "quoted D2/W7 frame must remain a structural list: {value:?}");
}

#[test]
fn malformed_text7_shape_never_becomes_a_binding_identity() {
    // Mixed W7 + D3 content is an ordinary structural list, not Text7.
    let expressions = parse_canonical_binary("10 1000001 00 001 01")
        .expect("mixed canonical structure remains parseable");
    let mut session = Session::default();
    let error = eval_parsed_expressions(&expressions, &mut session)
        .expect_err("mixed structure is not a resolvable Text7 binding");
    assert!(
        error.message.contains("expression is not callable")
            || error.message.contains("unknown symbol")
            || error.message.contains("unknown Text7 binding"),
        "unexpected error: {error:?}"
    );
}
