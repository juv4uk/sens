use sens::{eval_program, parse, ErrorKind, ExprKind, Session};

fn eval(source: &str) -> String {
    let mut session = Session::default();
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("{source}: {error}"))
        .value
        .to_string()
}

#[test]
fn bare_d5_words_execute_without_function8_projection() {
    assert_eq!(eval("(01010 2 3)"), "5");
    assert_eq!(eval("(01011 7 2)"), "5");
    assert_eq!(eval("(10010 3 4)"), "12");
    assert_eq!(eval("(10011 8 2)"), "4");
    assert_eq!(eval("(01110 2 3)"), "1");
    assert_eq!(eval("(01111 3 2)"), "1");
}

#[test]
fn reader_preserves_exact_d3_d6_widths() {
    for (source, width, bits) in [
        ("101", 3, 0b101),
        ("1010", 4, 0b1010),
        ("01010", 5, 0b01010),
        ("010100", 6, 0b010100),
    ] {
        let expressions = parse(source).unwrap();
        let ExprKind::DomainIdentity(identity) = expressions[0].kind else {
            panic!("{source}: expected exact domain identity");
        };
        assert_eq!((identity.width(), identity.packed_bits()), (width, bits));
    }
}

#[test]
fn bare_function8_is_not_a_second_language() {
    let error = parse("00001100").expect_err("legacy bare W8 must fail");
    assert_eq!(error.kind, ErrorKind::Parse);
}
