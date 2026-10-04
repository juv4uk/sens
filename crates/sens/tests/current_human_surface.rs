//! #3141/#3142/#3143 — executable parity for current exact-domain D3 surfaces.
//!
//! Human Ukrainian and Sanskrit spellings must disappear before execution:
//! all three source forms below lower to the same exact D3 program and produce
//! the same observable value.

use sens::{
    eval_lowered_expressions, lower_program, parse, parse_canonical_binary, Session,
};

#[test]
fn binary_uk_and_sa_execute_to_the_same_d3_observable_result() {
    // CAR(QUOTE((()))) uses only the ratified D2/D3 foundation and avoids
    // depending on a wider-domain operation or historical Function8 identity.
    const BINARY: &str = "10 101 00 10 001 00 10 000 01 01 01";
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
