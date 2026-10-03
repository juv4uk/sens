use sens::{eval_program, lower_program, parse, ExprKind, Exactness, Session, Value};

fn eval(source: &str) -> Value {
    eval_program(source, &mut Session::default())
        .unwrap_or_else(|error| panic!("{source}: {error:?}"))
        .value
}

fn assert_domain_head(source: &str, width: usize, bits: u8) {
    let parsed = parse(source).expect("source must parse");
    let lowered = lower_program(&parsed);
    let ExprKind::DomainCall(identity, _) = &lowered[0].kind else {
        panic!("{source}: expected canonical DomainCall, got {:?}", lowered[0].kind);
    };
    assert_eq!(identity.width(), width, "{source}");
    assert_eq!(identity.packed_bits(), bits, "{source}");
}

#[test]
fn d5_arithmetic_executes_after_domain_first_lowering() {
    for (source, expected, bits) in [
        ("(+ 20 22)", Value::Number(42.0, Exactness::Exact), 0b01010),
        ("(- 50 8)", Value::Number(42.0, Exactness::Exact), 0b01011),
        ("(* 6 7)", Value::Number(42.0, Exactness::Exact), 0b10010),
    ] {
        assert_domain_head(source, 5, bits);
        assert_eq!(eval(source), expected, "{source}");
    }
}

#[test]
fn peer_surfaces_share_the_same_d5_identity() {
    for source in ["(+ 20 22)", "(додати 20 22)", "(plus 20 22)", "(yoga 20 22)"] {
        assert_domain_head(source, 5, 0b01010);
        assert_eq!(eval(source), Value::Number(42.0, Exactness::Exact), "{source}");
    }
}

#[test]
fn d6_abs_executes_from_its_domain_identity() {
    assert_domain_head("(abs -42)", 6, 0b010101);
    assert_eq!(eval("(abs -42)"), Value::Number(42.0, Exactness::Exact));
}
