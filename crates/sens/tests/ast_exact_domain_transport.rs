//! Незалежні свідки поточної доменної AST без збірки чужих unit-тестів.

use sens::{
    Bija3, Bit3, Bit4, Bit8, Bit9, BinaryNumber, CoreD4, CoreD8, CoreD9,
    DomainIdentity, Expr, ExprKind, Exactness, Sens8, Span,
};
use sens::syntax::{
    decode_exact_fasl_program, decode_exact_wire_program,
    encode_exact_fasl_program, encode_exact_wire_program,
};

fn expression(kind: ExprKind) -> Expr {
    Expr { kind, span: Span::default() }
}

#[test]
fn точна_ширина_домену_не_зливається_за_однаковими_бітами() {
    let program = [
        expression(ExprKind::DomainIdentity(DomainIdentity::D3(
            Bija3::from_word(Bit3::new(0b001).unwrap()),
        ))),
        expression(ExprKind::DomainIdentity(DomainIdentity::D4(
            CoreD4::from_word(Bit4::new(0b0001).unwrap()),
        ))),
        expression(ExprKind::DomainIdentity(DomainIdentity::D8(
            CoreD8::from_word(Bit8::new(0b10101000).unwrap()),
        ))),
        expression(ExprKind::DomainIdentity(DomainIdentity::D9(
            CoreD9::from_word(Bit9::new(0b1_00000001).unwrap()),
        ))),
    ];

    let encoded = encode_exact_wire_program(&program).expect("доменний wire");
    let decoded = decode_exact_wire_program(&encoded).expect("доменний wire decode");
    assert_eq!(decoded.len(), program.len());
    for (actual, expected) in decoded.iter().zip(program.iter()) {
        assert_eq!(actual.kind, expected.kind);
    }
    assert_ne!(decoded[0].kind, decoded[1].kind);
    let hash = [17u8; 32];
    let encoded = encode_exact_fasl_program(&program, &hash).expect("доменний FASL");
    let (decoded, actual_hash) = decode_exact_fasl_program(&encoded).expect("доменний FASL decode");
    assert_eq!(actual_hash, hash);
    for (actual, expected) in decoded.iter().zip(program.iter()) {
        assert_eq!(actual.kind, expected.kind);
    }
}

#[test]
fn історичний_w8_під_цитатою_не_стає_d8() {
    let quoted = expression(ExprKind::List(vec![
        expression(ExprKind::DomainIdentity(DomainIdentity::D3(
            Bija3::from_word(Bit3::new(0b001).unwrap()),
        ))),
        expression(ExprKind::Pair(
            std::rc::Rc::new(expression(ExprKind::String("дані".into()))),
            std::rc::Rc::new(expression(ExprKind::Sid(
                Sens8::from_packed_byte(0b10101000),
            ))),
        )),
    ].into()));
    assert!(encode_exact_wire_program(std::slice::from_ref(&quoted)).is_none());
    assert!(encode_exact_fasl_program(std::slice::from_ref(&quoted), &[0; 32]).is_none());
    let old_wire = sens::wire_encode_program(std::slice::from_ref(&quoted));
    assert!(sens::wire_decode_program(&old_wire).is_some());
    assert!(decode_exact_wire_program(&old_wire).is_none());
    let old_fasl = sens::fasl_encode_program(&[quoted], &[0; 32]);
    assert!(sens::fasl_decode_program(&old_fasl).is_some());
    assert!(decode_exact_fasl_program(&old_fasl).is_none());
}

#[test]
fn тільки_d24_або_більше_є_числом_у_новому_форматі() {
    let number = expression(ExprKind::Number(2.0, Exactness::Exact));
    assert!(encode_exact_wire_program(&[number]).is_none());
    let raw = expression(ExprKind::BinaryNumber(BinaryNumber::from_bits([1, 0, 1]).unwrap()));
    assert!(encode_exact_wire_program(&[raw]).is_none());
    let bits = vec![0u8; 24];
    let qualified = expression(ExprKind::BinaryNumber(
        BinaryNumber::from_numeric_domain_bits(24, &bits).unwrap(),
    ));
    let encoded = encode_exact_wire_program(std::slice::from_ref(&qualified)).unwrap();
    let decoded = decode_exact_wire_program(&encoded).unwrap();
    assert_eq!(decoded[0].kind, qualified.kind);
}

#[test]
fn відсутній_d8_механізм_не_стає_виконуваним() {
    let d8 = sens::CoreDomainIdentity::D8(
        CoreD8::from_word(Bit8::new(0b10101000).unwrap()),
    );
    let data = expression(ExprKind::DomainIdentity(d8.into()));
    assert!(encode_exact_wire_program(&[data]).is_some());
    let call = expression(ExprKind::DomainCall(d8, [].into()));
    assert!(encode_exact_wire_program(&[call.clone()]).is_none());
    assert!(encode_exact_fasl_program(&[call], &[0; 32]).is_none());
}
