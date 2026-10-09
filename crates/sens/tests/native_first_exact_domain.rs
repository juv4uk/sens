//! Domain-ladder-only guard. Native-first language laws belong to SENS witnesses.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_t5_program, open_ternary_program,
    parse_binary_source_words, parse_canonical_binary, syntax::ExprKind, DomainIdentity,
    ErrorKind, Session, Value,
};

const D3_EMPTY_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/exact-domain-ladder/empty-d3.sens");
const D3_QUOTE_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/exact-domain-ladder/d3-quote.sens");

#[test]
fn exact_domain_ladder_preserves_leading_zeroes_and_widths_d1_through_d9() {
    for width in 1usize..=9 {
        let source = format!("{value:0width$b}", value = 1u16);
        // A source word is a width-qualified carrier, not necessarily an
        // executable root. In particular, bare D2 CLOSE (01) is invalid syntax.
        let words = parse_binary_source_words(&source).expect("exact-width source word");
        assert_eq!(words.len(), 1);
        let identity = DomainIdentity::from_source_word(words[0].word);
        assert_eq!(identity.width(), width);
        assert_eq!(identity.packed_bits(), 1);
    }
}

#[test]
fn same_payload_in_different_rungs_remains_a_different_identity() {
    let d1 = parse_canonical_binary("1").expect("D1 word parses");
    let d3 = parse_canonical_binary("001").expect("D3 word parses");
    let d9 = parse_canonical_binary("000000001").expect("D9 word parses");
    let ExprKind::DomainIdentity(d1_identity) = &d1[0].kind else {
        panic!("expected D1 identity");
    };
    let ExprKind::DomainIdentity(d3_identity) = &d3[0].kind else {
        panic!("expected D3 identity");
    };
    let ExprKind::DomainIdentity(d9_identity) = &d9[0].kind else {
        panic!("expected D9 identity");
    };
    assert_eq!(d1_identity.packed_bits(), 1);
    assert_eq!(d3_identity.packed_bits(), 1);
    assert_eq!(d9_identity.packed_bits(), 1);
    assert_ne!(d1_identity, d3_identity);
    assert_ne!(d3_identity, d9_identity);
}

#[test]
fn nine_bit_payload_is_not_truncated_to_u8() {
    let forms = parse_canonical_binary("100000001").expect("D9 word parses");
    let ExprKind::DomainIdentity(identity) = &forms[0].kind else {
        panic!("D9 word must remain a domain identity");
    };
    assert_eq!(identity.width(), 9);
    assert_eq!(identity.packed_bits(), 257);
}
#[test]
fn standalone_d2_close_is_a_word_but_not_an_executable_program() {
    let close = parse_binary_source_words("01").expect("exact-width D2 source");
    assert_eq!(close.len(), 1);
    assert_eq!(DomainIdentity::from_source_word(close[0].word).width(), 2);

    let err = parse_canonical_binary("01").expect_err("unmatched D2 CLOSE must fail");
    assert_eq!(err.kind, ErrorKind::Parse);
    assert_eq!(
        parse_canonical_binary("10 01")
            .expect("paired D2 OPEN/CLOSE is a complete program")
            .len(),
        1
    );
}

#[test]
fn physical_d3_empty_is_one_canonical_packed_byte_not_text() {
    // Source word 000 plus at most four T5 padding trits 2:
    // 00022 in base 3 = 0x08, exactly one physical byte.
    assert_eq!(D3_EMPTY_T5, &[0x08]);
    assert_ne!(D3_EMPTY_T5, b"000");
    let words = decode_ternary_program(D3_EMPTY_T5).expect("real physical T5 program");
    assert_eq!(words.len(), 1);
    assert_eq!(DomainIdentity::from_source_word(words[0]).width(), 3);
    assert_eq!(
        open_ternary_program(D3_EMPTY_T5).expect("human binary projection"),
        "000"
    );
    assert_eq!(
        encode_binary_projection_ternary("000").expect("canonical T5 encoder"),
        D3_EMPTY_T5
    );

    // Corrupt padding may not silently fall back to ASCII source.
    let mut overpadded = D3_EMPTY_T5.to_vec();
    overpadded.push(0xf2);
    assert!(decode_ternary_program(&overpadded).is_err());
}

#[test]
fn physical_d3_quote_executes_as_packed_bytes_with_exact_word_boundaries() {
    // Canonical T5: 10 001 00 000 01; not UTF-8 text and not old Function8.
    assert_eq!(D3_QUOTE_T5, &[0x63, 0x89, 0x06, 0xa1]);
    assert_ne!(D3_QUOTE_T5, b"10 001 00 000 01");
    let words = decode_ternary_program(D3_QUOTE_T5)
        .expect("committed physical D3 QUOTE must pass strict D2 grammar");
    let exact = words.iter().map(ToString::to_string).collect::<Vec<_>>();
    assert_eq!(exact, ["10", "001", "00", "000", "01"]);
    assert_eq!(
        encode_binary_projection_ternary("10 001 00 000 01")
            .expect("canonical physical encoder"),
        D3_QUOTE_T5
    );
    let result = eval_t5_program(D3_QUOTE_T5, &mut Session::default())
        .expect("physical QUOTE executes in a fresh binary session");
    assert!(matches!(result.value, Value::Nil));
    assert!(result.output.is_empty());

    let mut damaged = D3_QUOTE_T5.to_vec();
    damaged.push(0xf2);
    assert!(decode_ternary_program(&damaged).is_err());
}
