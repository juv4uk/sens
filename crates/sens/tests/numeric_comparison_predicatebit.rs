use sens::{eval_program, load_core_library, ErrorKind, Session};

#[test]
fn legacy_numeric_comparison_heads_return_exact_d1() {
    for (source, expected) in [
        ("(00011010 2 3)", true),
        ("(00011010 3 2)", false),
        ("(00011011 3 2)", true),
        ("(00011011 2 3)", false),
        ("(00011100 2 2)", true),
        ("(00011100 2 3)", false),
    ] {
        let value = eval_program(source, &mut Session::default())
            .unwrap_or_else(|error| panic!("{source}: {error}"))
            .value;
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "{source} must return exact D1 rather than numeric 1/0"
        );
    }
}

#[test]
fn inexact_numeric_comparison_fails_named_instead_of_returning_empty_or_no() {
    let error = eval_program(
        "(00011010 (numeric-buffer-ref #f32(2.0) 0) (numeric-buffer-ref #f32(3.0) 0))",
        &mut Session::default(),
    )
    .expect_err("inexact comparison has no admitted D1 answer");

    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn derived_order_comparisons_return_exact_d1() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");

    for (source, expected) in [
        ("(00011101 2 3)", true),
        ("(00011101 3 2)", false),
        ("(00011101 2 2)", true),
        ("(00011101 1 1 2 3)", true),
        ("(00011101 1 3 2)", false),
        ("(00011110 3 2)", true),
        ("(00011110 2 3)", false),
        ("(00011110 2 2)", true),
        ("(00011110 3 3 2 1)", true),
        ("(00011110 3 1 2)", false),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("{source}: {error}"))
            .value;
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "{source} must return exact D1"
        );
    }
}
