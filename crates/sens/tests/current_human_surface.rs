//! #3141/#3142/#3143 — executable parity for bīja3 A human surfaces.

use sens::{
    eval_lowered_expressions, lower_program, parse, parse_canonical_binary, Session,
};

#[test]
fn binary_uk_and_sa_execute_to_the_same_bija3_a_result() {
    // CAR=100, QUOTE=001, EMPTY=000 under bīja3 A.
    const BINARY: &str = "10 100 00 10 001 00 10 000 01 01 01";
    const UK: &str = "(перше (як-є (())))";
    const SA: &str = "(ādi (svarūpa (())))";

    let binary = lower_program(&parse_canonical_binary(BINARY).expect("binary parses"));
    let uk = lower_program(&parse(UK).expect("UK surface parses"));
    let sa = lower_program(&parse(SA).expect("SA surface parses"));

    let run = |program: &[sens::Expr], label: &str| {
        eval_lowered_expressions(program, &mut Session::default())
            .unwrap_or_else(|error| panic!("{label} witness failed: {error:?}"))
            .value
            .to_string()
    };

    let binary_value = run(&binary, "binary");
    assert_eq!(binary_value, "()");
    assert_eq!(run(&uk, "UK"), binary_value);
    assert_eq!(run(&sa, "SA"), binary_value);
}
