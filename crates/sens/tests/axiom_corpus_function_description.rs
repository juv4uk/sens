//! #3451/#3454 — describe exact D5 binary functions from an axiom corpus.
//!
//! Human function names are deliberately absent from the witness.
//! The function identities under test are exact D5 bit patterns.

use sens::{
    eval_parsed_expressions, parse, Bit5, CoreD5, DomainIdentity, Expr, ExprKind, Session, Span,
};
use std::collections::HashSet;

const FUNCTIONS: [u8; 4] = [0b01010, 0b01011, 0b10110, 0b10111];

fn exact_d5_result(bits: u8, args: &str) -> String {
    let mut parsed = parse(&format!("(__axiom_probe__ {args})")).expect("probe payload");
    let mut form = parsed.remove(0);
    let ExprKind::List(items) = form.kind else {
        panic!("probe must parse as list");
    };
    let mut items = items.to_vec();
    items[0] = Expr {
        kind: ExprKind::DomainIdentity(DomainIdentity::D5(CoreD5::from_word(
            Bit5::new(bits).unwrap(),
        ))),
        span: Span::default(),
    };
    form.kind = ExprKind::List(items.into());

    match eval_parsed_expressions(&[form], &mut Session::default()) {
        Ok(result) => result.value.to_string(),
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
