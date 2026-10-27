//! Physical SENS source may be only exact binary words and D2 framing.
//! Human surface names and retired flat function IDs play no part in execution.

use sens::{parse_canonical_binary, wire_decode_program, wire_encode_program, Expr, ExprKind};

const SOURCE: &str = include_str!("../../../tests/fixtures/canonical-binary-smoke.bits");

fn assert_exact_binary_tree(expr: &Expr) {
    match &expr.kind {
        ExprKind::DomainIdentity(_) => {}
        ExprKind::List(items) => {
            for item in items.iter() {
                assert_exact_binary_tree(item);
            }
        }
        ExprKind::Pair(head, tail) => {
            assert_exact_binary_tree(head);
            assert_exact_binary_tree(tail);
        }
        other => panic!("canonical binary source invented non-binary identity: {other:?}"),
    }
}

#[test]
fn canonical_binary_source_preserves_exact_width_framing() {
    assert!(
        SOURCE
            .bytes()
            .all(|byte| byte == b'0' || byte == b'1' || byte.is_ascii_whitespace()),
        "exact-bit .bits witness must contain no human names or punctuation"
    );

    let parsed = parse_canonical_binary(SOURCE).expect("canonical D1/D2/D3 binary program");
    assert_eq!(parsed.len(), 4);
    for expression in &parsed {
        assert_exact_binary_tree(expression);
    }

    // The physical representation must preserve every domain width before
    // executing the SENS-owned D3 rules, without historical SID decoding.
    let restored = wire_decode_program(&wire_encode_program(&parsed))
        .expect("binary program width-preserving wire roundtrip");
    assert_eq!(restored.len(), parsed.len());
    for expression in &restored {
        assert_exact_binary_tree(expression);
    }


}

#[test]
fn named_lisp_is_not_canonical_binary_source() {
    for source in [
        "(QUOTE ())",
        "10 ATOM 00 000 01",
        "(110 ((1 1)))",
        "0000000000",
    ] {
        assert!(parse_canonical_binary(source).is_err(), "{source}");
    }
}
