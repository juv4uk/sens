//! #3451/#3454 — describe exact D5 binary functions from an axiom corpus.
//!
//! Human function names are deliberately absent from the witness.
//! The function identities under test are exact D5 bit patterns.

use sens::{
    eval_parsed_expressions, parse_mixed_exact_domain, BinaryNumber, Session, Value,
};
use std::collections::HashSet;

const FUNCTIONS: [u8; 4] = [0b01010, 0b01011, 0b10110, 0b10111];

// Only the transport of seed operands is host-owned. Exact 24-bit D24
// numbers are admitted as data, never inferred from "1" or a short Dn word.
// Every derived integer, NEG and RATIO below is computed by actual SENS D5.
fn d24_seed(value: u32) -> Value {
    let mut bits = vec![0; 24];
    for offset in 0..24 {
        bits[23 - offset] = ((value >> offset) & 1) as u8;
    }
    Value::BinaryNumber(
        BinaryNumber::from_numeric_domain_bits(24, &bits)
            .expect("only explicitly qualified 24-bit source data"),
    )
}

fn run_exact_d5(source: &str, session: &mut Session) -> Result<Value, sens::LanguageError> {
    let forms = parse_mixed_exact_domain(source)?;
    eval_parsed_expressions(&forms, session).map(|out| out.value)
}

fn admitted_seed(spelling: &str, session: &mut Session) -> Value {
    match spelling {
        "0" => d24_seed(0),
        "1" => d24_seed(1),
        "-1" => {
            session.environment.define("d24-zero", d24_seed(0));
            session.environment.define("d24-one", d24_seed(1));
            run_exact_d5("(01011 d24-zero d24-one)", session)
                .expect("D5:01011 derives NEG(1) from explicit D24 seeds")
        }
        "2" => {
            session.environment.define("d24-one", d24_seed(1));
            run_exact_d5("(01010 d24-one d24-one)", session)
                .expect("D5:01010 derives 2 from explicit D24 seeds")
        }
        _ => panic!("unadmitted axiom fixture: {spelling}"),
    }
}

fn exact_d5_result(bits: u8, args: &str) -> String {
    let operands = args.split_whitespace().collect::<Vec<_>>();
    assert_eq!(operands.len(), 2, "binary D5 law has exactly two operands");
    assert!(bits < 32, "D5 function code is exactly five bits");

    let mut session = Session::default();
    let left = admitted_seed(operands[0], &mut session);
    let right = admitted_seed(operands[1], &mut session);
    session.environment.define("left", left);
    session.environment.define("right", right);
    // Native SENS decides the outcome. No Rust arithmetic or numeric
    // interpretation of D1-D10 code words is involved here.
    let source = format!("({bits:05b} left right)");
    match run_exact_d5(&source, &mut session) {
        Ok(value) => value.to_string(),
        Err(error) => format!("ERR:{:?}", error.kind),
    }
}

fn signature(a: &str, b: &str) -> Vec<String> {
    FUNCTIONS
        .iter()
        .map(|bits| exact_d5_result(*bits, &format!("{a} {b}")))
        .collect()
}

fn distinct_count(values: &[String]) -> usize {
    values.iter().cloned().collect::<HashSet<_>>().len()
}

#[test]
fn primitive_seed_pairs_alone_have_no_single_tuple_that_separates_all_four_functions() {
    let primitive = ["-1", "0", "1"];

    for a in primitive {
        for b in primitive {
            let sig = signature(a, b);
            assert!(
                distinct_count(&sig) < FUNCTIONS.len(),
                "primitive-only tuple ({a},{b}) unexpectedly separated all exact D5 function identities: {sig:?}"
            );
        }
    }
}

#[test]
fn language_derived_two_creates_a_one_tuple_separating_witness() {
    // 2 is not added as another premise. It is produced by one of the
    // admitted exact D5 function numbers acting on the primitive seed 1.
    let two = exact_d5_result(0b01010, "1 1");
    assert_eq!(two, "2");

    let sig = signature("1", &two);
    assert_eq!(sig, vec!["3", "-1", "2", "1/2"]);
    assert_eq!(distinct_count(&sig), FUNCTIONS.len());

    // Name-erased certificate: one derived tuple is enough to distinguish
    // all four exact function identities on this bounded arithmetic slice.
    let certificate = FUNCTIONS
        .iter()
        .zip(sig.iter())
        .map(|(bits, result)| (format!("{bits:05b}"), result.clone()))
        .collect::<Vec<_>>();

    assert_eq!(
        certificate,
        vec![
            ("01010".to_string(), "3".to_string()),
            ("01011".to_string(), "-1".to_string()),
            ("10110".to_string(), "2".to_string()),
            ("10111".to_string(), "1/2".to_string()),
        ]
    );
}

#[test]
fn bounded_search_confirms_separating_tuple_appears_after_certified_closure() {
    let primitive = ["-1", "0", "1"];
    let two = exact_d5_result(0b01010, "1 1");
    let closure = ["-1", "0", "1", two.as_str()];

    let primitive_separators = primitive
        .iter()
        .flat_map(|a| primitive.iter().map(move |b| (*a, *b)))
        .filter(|(a, b)| distinct_count(&signature(a, b)) == FUNCTIONS.len())
        .collect::<Vec<_>>();
    assert!(primitive_separators.is_empty());

    let closure_separators = closure
        .iter()
        .flat_map(|a| closure.iter().map(move |b| (*a, *b)))
        .filter(|(a, b)| distinct_count(&signature(a, b)) == FUNCTIONS.len())
        .collect::<Vec<_>>();

    assert!(
        closure_separators.contains(&("1", "2")),
        "derived closure must contain the one-tuple witness (1,2): {closure_separators:?}"
    );
    assert!(
        !closure_separators.is_empty(),
        "certified closure should create at least one separating tuple"
    );
}
