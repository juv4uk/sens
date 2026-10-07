use sens::{
    eval_parsed_expressions, parse, parse_canonical_binary, DomainIdentity, ErrorKind, Exactness,
    ExprKind, Session, Value,
};

fn eval_source(source: &str) -> Result<Value, sens::LanguageError> {
    let parsed = parse_canonical_binary(source)?;
    eval_parsed_expressions(&parsed, &mut Session::default()).map(|result| result.value)
}

#[test]
fn canonical_w1_zero_and_one_are_exact_d1_values() {
    for (source, expected) in [("0", false), ("1", true)] {
        let parsed = parse_canonical_binary(source).expect("W1 source must parse as exact D1 value");
        assert_eq!(parsed.len(), 1);

        let ExprKind::DomainIdentity(DomainIdentity::D1(_)) = parsed[0].kind else {
            panic!("W1 source must materialize exact DomainIdentity::D1");
        };

        let value = eval_parsed_expressions(&parsed, &mut Session::default())
            .expect("bare D1 value must evaluate")
            .value;
        assert_eq!(value.as_predicate_bit(), Some(expected));
    }
}

#[test]
fn canonical_d1_zero_never_collapses_to_d3_empty() {
    let no = eval_source("0").expect("D1:0 evaluates");
    let empty = eval_source("000").expect("D3:000 EMPTY evaluates");

    assert_eq!(no.as_predicate_bit(), Some(false));
    assert!(matches!(empty, Value::Nil));
    assert_eq!(empty.as_predicate_bit(), None);
    assert_ne!(no, empty);
}

#[test]
fn canonical_d1_values_are_not_callable_heads() {
    for source in ["10 0 00 000 01", "10 1 00 000 01"] {
        let parsed = parse_canonical_binary(source)
            .expect("list containing D1 head must parse structurally");
        let error = eval_parsed_expressions(&parsed, &mut Session::default())
            .expect_err("D1 value in head position must fail closed");

        assert_eq!(error.kind, ErrorKind::Type);
        assert!(
            error.message.contains("not callable"),
            "unexpected D1 head failure: {}",
            error.message
        );
    }
}

#[test]
fn human_numeric_parser_does_not_alias_canonical_d1_source() {
    for source in ["0", "1"] {
        let human = parse(source).expect("human parser accepts decimal number");
        assert!(
            matches!(human[0].kind, ExprKind::Number(_, Exactness::Exact)),
            "human compatibility parser must keep {source} numeric"
        );

        let binary = parse_canonical_binary(source).expect("canonical W1 source");
        assert!(
            matches!(binary[0].kind, ExprKind::DomainIdentity(DomainIdentity::D1(_))),
            "canonical binary reader must keep {source} in D1"
        );
    }
}
