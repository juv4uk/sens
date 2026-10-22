//! Виконуваний SENS-свідок українського D1 для генератора FUNCTIONS.
//! Rust спостерігає результат; істину обчислює лише справжній SENS D3.
use sens::{eval_parsed_expressions, parse_mixed_exact_domain, Session};

const SOURCE: &str = include_str!("../../../scripts/generate-functions-md.lisp");

#[test]
fn generator_definition_head_uses_real_d3_d1_without_legacy_truth_atoms() {
    let start = SOURCE
        .find("(визначити голова-визначення?")
        .expect("поточний український DEFINE");
    let end = SOURCE[start..]
        .find("\n\n(визначити назви-визначень")
        .map(|offset| start + offset)
        .expect("межа першої виконуваної D4-функції");
    let helper = &SOURCE[start..end];
    assert!(!helper.contains("(так "), "старий D1 сурогат не є законом");
    assert!(!helper.contains(" ні)"), "старий D1 сурогат не є законом");
    let mut session = Session::default();
    sens::eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("чинний SENS core D3/D4/D5");
    let definitions = parse_mixed_exact_domain(helper).expect("тільки українські канонічні голови");
    eval_parsed_expressions(&definitions, &mut session)
        .expect("іменована функція дійсно визначається в SENS");
    for (program, expected) in [
        ("(голова-визначення? (як-є визначити))", true),
        ("(голова-визначення? (як-є атом?))", false),
        ("(голова-визначення? (як-є (визначити)))", false),
    ] {
        let calls = parse_mixed_exact_domain(program).expect("SENS source reader: D3/D4 і D7-дані");
        let actual = eval_parsed_expressions(&calls, &mut session)
            .unwrap_or_else(|err| panic!("SENS D1 input={program}: {err}"))
            .value;
        assert_eq!(
            actual.as_predicate_bit(), Some(expected),
            "test_id=functions-md-d1 layer=SENS input={program} expected={expected} actual={actual}"
        );
    }
}
