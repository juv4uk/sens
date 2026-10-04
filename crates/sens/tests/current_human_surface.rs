use sens::{
    eval_lowered_expressions, lower_program, parse, parse_canonical_binary, wire_encode_program,
    Session,
};

#[test]
fn binary_en_uk_and_sa_lower_to_byte_identical_current_domain_wire() {
    const BINARY: &str =
        "10 111 00 10 001 00 000 01 00 10 001 00 000 01 01";
    const EN: &str = "(eq (quote ()) (quote ()))";
    const UK: &str = "(тотожне? (як-є ()) (як-є ()))";
    const SA: &str = "(abheda (svarūpa ()) (svarūpa ()))";

    let binary = lower_program(&parse_canonical_binary(BINARY).expect("binary parses"));
    let en = lower_program(&parse(EN).expect("EN surface parses"));
    let uk = lower_program(&parse(UK).expect("UK surface parses"));
    let sa = lower_program(&parse(SA).expect("SA surface parses"));

    let binary_wire = wire_encode_program(&binary);
    assert_eq!(wire_encode_program(&en), binary_wire);
    assert_eq!(wire_encode_program(&uk), binary_wire);
    assert_eq!(wire_encode_program(&sa), binary_wire);

    for spelling in ["eq", "quote", "тотожне?", "як-є", "abheda", "svarūpa"] {
        assert!(
            !binary_wire
                .windows(spelling.as_bytes().len())
                .any(|window| window == spelling.as_bytes()),
            "human surface spelling leaked into canonical wire: {spelling}"
        );
    }
}

#[test]
fn binary_en_uk_and_sa_execute_to_the_same_d3_observable_result() {
    // Pure D3 selector witness: independent from the separate D1 predicate-result
    // boundary migration tracked by #2184/#3145.
    const BINARY: &str =
        "10 101 00 10 001 00 10 000 01 01 01";
    const EN: &str = "(car (quote (())))";
    const UK: &str = "(перше (як-є (())))";
    const SA: &str = "(ādi (svarūpa (())))";

    let binary = lower_program(&parse_canonical_binary(BINARY).expect("binary parses"));
    let en = lower_program(&parse(EN).expect("EN surface parses"));
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
    assert_eq!(run(&en, "EN"), binary_value);
    assert_eq!(run(&uk, "UK"), binary_value);
    assert_eq!(run(&sa, "SA"), binary_value);
}
