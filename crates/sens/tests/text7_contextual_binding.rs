//! Contextual Text7 binder/reference execution witnesses for #3910.
//!
//! D2 remains structural in the canonical reader. These tests exercise the
//! existing Text7 value/key plus lexical Environment only in explicit
//! DEFINE/LAMBDA/call-head roles.

use sens::{eval_parsed_expressions, parse_canonical_binary, DomainIdentity, PredicateBit, Value};

fn text7_frame(cells: &[u8]) -> String {
    let body = cells
        .iter()
        .map(|cell| format!("{cell:07b}"))
        .collect::<Vec<_>>()
        .join(" 00 ");
    format!("10 {body} 01")
}

#[test]
fn lambda_text7_parameter_round_trips_as_a_value_reference() {
    let name = text7_frame(&[0x41, 0x42]);
    // ((lambda (<AB>) <AB>) 1)
    let source = format!(
        "10 10 0010 00 10 {name} 01 00 {name} 01 00 1 01"
    );
    let expressions = parse_canonical_binary(&source).expect("contextual lambda parses");
    let mut session = sens::Session::default();
    let value = eval_parsed_expressions(&expressions, &mut session)
        .expect("contextual lambda executes")
        .value;
    assert_eq!(
        value,
        Value::DomainIdentity(DomainIdentity::D1(
            PredicateBit::from_word(sens::Bit1::new(1).unwrap())
        ))
    );
}

#[test]
fn global_text7_definition_can_be_called_by_its_contextual_frame() {
    let name = text7_frame(&[0x41, 0x42]);
    // (define <AB> (lambda () 1)) (<AB>)
    let source = format!(
        "10 0011 00 {name} 00 10 0010 00 10 01 00 1 01 01 00 10 {name} 01"
    );
    let expressions = parse_canonical_binary(&source).expect("contextual define parses");
    let mut session = sens::Session::default();
    let value = eval_parsed_expressions(&expressions, &mut session)
        .expect("contextual global call executes")
        .value;
    assert_eq!(
        value,
        Value::DomainIdentity(DomainIdentity::D1(
            PredicateBit::from_word(sens::Bit1::new(1).unwrap())
        ))
    );
}

#[test]
fn quoted_text7_frame_remains_structural_data() {
    let name = text7_frame(&[0x41, 0x42]);
    let source = format!("10 001 00 {name} 01");
    let expressions = parse_canonical_binary(&source).expect("quoted Text7 frame parses");
    let mut session = sens::Session::default();
    let value = eval_parsed_expressions(&expressions, &mut session)
        .expect("quoted frame evaluates as data")
        .value;
    assert!(matches!(value, Value::Pair(_, _)), "quoted frame must remain list data: {value:?}");
}

#[test]
fn plain_w7_d2_list_has_no_implicit_text7_retyping_in_reader() {
    let expressions = parse_canonical_binary("10 1000001 00 1000010 01")
        .expect("ordinary W7 list remains valid D2 structure");
    assert_eq!(expressions.len(), 1);
    let sens::syntax::ExprKind::List(items) = &expressions[0].kind else {
        panic!("ordinary W7 D2 list changed AST shape");
    };
    assert_eq!(items.len(), 2);
    assert!(matches!(&items[0].kind, sens::syntax::ExprKind::DomainIdentity(
        DomainIdentity::D7(_)
    )));
    assert!(matches!(&items[1].kind, sens::syntax::ExprKind::DomainIdentity(
        DomainIdentity::D7(_)
    )));
}
