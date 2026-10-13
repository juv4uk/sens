//! Mechanical transport/execution witness only.
//! Semantic verdicts are owned by self-checking programs under tests/semantic/.
//! This Rust file may check canonical bytes, framing and executability, but
//! must not encode a language truth table or expected D1 result.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary,
    eval_parsed_expressions, open_ternary_program, parse_canonical_binary,
    ternary_transport_accounting, Session,
};

const LOGIC: &str = include_str!("../../../tests/oracles/d1-cond-law/proof.lisp");
const PHYSICAL: &[u8] = include_bytes!("../../../tests/oracles/d1-cond-law/proof.sens");

#[test]
fn physical_binary_sens_transport_and_execution_are_mechanical_only() {
    // Text file is a view of the exact W1/W2/W3/W4 source, not an alternate Lisp program.
    assert!(LOGIC.split_whitespace().all(|w| w.bytes().all(|c| c == b'0' || c == b'1')));
    let words = decode_ternary_program(PHYSICAL).expect("valid physical T5 SENS program");
    assert_eq!(encode_binary_projection_ternary(LOGIC).unwrap(), PHYSICAL);
    let opened = open_ternary_program(PHYSICAL).expect("physical program decodes");
    assert_eq!(
        opened.split_whitespace().collect::<Vec<_>>(),
        LOGIC.split_whitespace().collect::<Vec<_>>()
    );
    let accounting = ternary_transport_accounting(&words).unwrap();
    assert_eq!(accounting.physical_bytes, PHYSICAL.len());
    assert_eq!(accounting.semantic_bits, LOGIC.split_whitespace().map(str::len).sum());
    assert_eq!(accounting.word_count, LOGIC.split_whitespace().count());
    println!(
        "binary SENS: {} words, {} exact semantic bits, {} separator trits, {} physical bytes",
        accounting.word_count, accounting.semantic_bits,
        accounting.separating_trits, accounting.physical_bytes
    );

    // Execution here is a mechanism smoke only. Do not compare the returned
    // values against a host-side semantic expectation; language-law verdicts
    // live in self-checking binary SENS witnesses under tests/semantic/.
    let expressions = parse_canonical_binary(&opened).expect("D2-framed exact SENS");
    for (i, expression) in expressions.iter().enumerate() {
        eval_parsed_expressions(std::slice::from_ref(expression), &mut Session::default())
            .unwrap_or_else(|err| panic!("binary SENS mechanism witness {} execution: {err:?}", i + 1));
    }
}

#[test]
fn physical_binary_sens_rejects_corrupted_transport() {
    let mut bad = PHYSICAL.to_vec();
    bad.push(243);
    assert!(decode_ternary_program(&bad).is_err());
    assert!(parse_canonical_binary("#d1:1").is_err(),
        "human projection is not a canonical one-bit SENS word");
}
