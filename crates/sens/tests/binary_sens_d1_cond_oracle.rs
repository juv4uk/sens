//! Mechanical transport/execution witness only via Zig T5M corridor.
//! Semantic verdicts are owned by self-checking programs under tests/semantic/.
//! This Rust file may check canonical bytes, framing and executability, but
//! must not encode a language truth table or expected D1 result.

use sens::{eval_parsed_expressions, parse_canonical_binary, Session};
use sens_cli::zig_transport;

const LOGIC: &str = include_str!("../../../tests/oracles/d1-cond-law/proof.bits");
const PHYSICAL: &[u8] = include_bytes!("../../../tests/oracles/d1-cond-law/proof.sens");
const PROCESS_BINDING_LOGIC: &str =
    include_str!("../../../tests/semantic/process-d4-lambda-law.bits");

fn encode_via_zig(source: &str) -> Vec<u8> {
    let tokens = sens::parse_binary_source_words(source)
        .expect("binary projection parses to exact-width tokens");
    let words = tokens
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    zig_transport::encode_t5m_direct(&words).expect("Zig T5M encoder must produce physical bytes")
}

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn render_binary_words_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    words
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>()
        .join(" ")
}

#[test]
fn physical_binary_sens_transport_and_execution_are_mechanical_only() {
    // Text file is a view of the exact W1/W2/W3/W4 source, not an alternate Lisp program.
    assert!(LOGIC
        .split_whitespace()
        .all(|w| w.bytes().all(|c| c == b'0' || c == b'1')));

    let words = decode_t5m_via_zig(PHYSICAL);
    let physical_zig = encode_via_zig(LOGIC);
    assert_eq!(physical_zig, PHYSICAL);
    let opened = render_binary_words_via_zig(PHYSICAL);
    assert_eq!(
        opened.split_whitespace().collect::<Vec<_>>(),
        LOGIC.split_whitespace().collect::<Vec<_>>()
    );

    let semantic_bits = words.iter().map(|word| word.width()).sum::<usize>();
    assert_eq!(PHYSICAL.len(), physical_zig.len());
    assert_eq!(semantic_bits, LOGIC.split_whitespace().map(str::len).sum());
    assert_eq!(words.len(), LOGIC.split_whitespace().count());
    println!(
        "binary SENS: {} words, {} exact semantic bits, {} physical bytes",
        words.len(),
        semantic_bits,
        PHYSICAL.len()
    );

    // Execution here is a mechanism smoke only. Do not compare the returned
    // values against a host-side semantic expectation; language-law verdicts
    // live in self-checking binary SENS witnesses under tests/semantic/.
    let expressions = parse_canonical_binary(&opened).expect("D2-framed exact SENS");
    for (i, expression) in expressions.iter().enumerate() {
        eval_parsed_expressions(std::slice::from_ref(expression), &mut Session::default())
            .unwrap_or_else(|err| {
                panic!("binary SENS mechanism witness {} execution: {err:?}", i + 1)
            });
    }
}

#[test]
fn physical_binary_sens_rejects_corrupted_transport() {
    let mut bad = PHYSICAL.to_vec();
    bad.push(243);
    assert!(zig_transport::decode_t5m_words(&bad).is_err());
    assert!(
        parse_canonical_binary("#d1:1").is_err(),
        "human projection is not a canonical one-bit SENS word"
    );
}

#[test]
fn process_binding_semantics_are_self_verdicts_written_in_binary_sens() {
    // Очікувана логіка — лише в двійковому SENS-свідку.
    // Host не має таблиці істинності, тільки transport та execution.
    // У помилковій гілці SENS викликає не-callable D1:0 і падає.
    assert!(PROCESS_BINDING_LOGIC
        .split_whitespace()
        .all(|word| word.bytes().all(|bit| bit == b'0' || bit == b'1')));
    let physical = encode_via_zig(PROCESS_BINDING_LOGIC);
    let opened = render_binary_words_via_zig(&physical);
    assert_eq!(
        opened.split_whitespace().collect::<Vec<_>>(),
        PROCESS_BINDING_LOGIC.split_whitespace().collect::<Vec<_>>(),
        "transport must preserve each codeword's full width"
    );
    let proofs = parse_canonical_binary(&opened).expect("bounded D2 grammar");
    assert!(!proofs.is_empty(), "there must be executable SENS proofs");
    for (index, proof) in proofs.iter().enumerate() {
        eval_parsed_expressions(std::slice::from_ref(proof), &mut Session::default())
            .unwrap_or_else(|err| panic!("SENS self-verdict #{} rejected: {err:?}", index + 1));
    }
}
