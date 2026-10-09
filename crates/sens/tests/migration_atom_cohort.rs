//! Bounded #4455 current exact-domain ATOM physical T5 canary.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    load_core_library, open_ternary_program, parse_canonical_binary, render_ternary_words_spaced,
    Session, Value,
};

const SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-atom-cohort/atom-empty.lisp");
const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-atom-cohort/atom-empty.sens");

#[test]
fn physical_atom_empty_roundtrips_and_executes() {
    assert_eq!(SOURCE, "10 010 00 000 01\n");
    assert_eq!(T5, [0x64, 0x38, 0x06, 0xa1]);

    let words = decode_ternary_program(T5).expect("canonical T5 bytes decode");
    let visible = render_ternary_words_spaced(&words);
    assert_eq!(visible, "10 010 00 000 01");
    assert_eq!(open_ternary_program(T5).unwrap(), visible);
    assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), T5);

    let expressions = parse_canonical_binary(&visible).expect("canonical exact source parses");
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core library loads");
    let result = eval_parsed_expressions(&expressions, &mut session)
        .expect("current SENS executes D3 ATOM over D3 EMPTY");

    assert_eq!(result.value, Value::predicate_bit(true));
}

#[test]
fn malformed_physical_bytes_fail_closed() {
    assert!(decode_ternary_program(&[243]).is_err());
    let mut bad = T5.to_vec();
    bad.push(242);
    assert!(decode_ternary_program(&bad).is_err());
}
