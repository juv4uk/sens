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
        let parsed =
            parse_canonical_binary(source).expect("W1 source must parse as exact D1 value");
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
            matches!(
                binary[0].kind,
                ExprKind::DomainIdentity(DomainIdentity::D1(_))
            ),
            "canonical binary reader must keep {source} in D1"
        );
    }
}

#[test]
fn positional_cond_d1_guards_are_bare_binary_words_not_tagged_carriers() {
    // Source is D2-framed and W1-exact; the syntactic position does not
    // fabricate D1 for arbitrary expressions. No host semantic truth table.
    let canonical = "10 110 00 10 0 00 0 01 00 10 1 00 1 01 01";
    let parsed = parse_canonical_binary(canonical).expect("tag-free canonical COND");
    assert_eq!(parsed.len(), 1);
    let ExprKind::List(forms) = &parsed[0].kind else {
        panic!("D2 opening must yield a list");
    };
    assert_eq!(forms.len(), 3, "COND head and two D1 clauses");
    for (index, bit) in [(1usize, 0u16), (2usize, 1u16)] {
        let ExprKind::List(clause) = &forms[index].kind else {
            panic!("D2 clause must remain a list");
        };
        let ExprKind::DomainIdentity(identity) = &clause[0].kind else {
            panic!("bare guard must remain a domain-qualified D1 word");
        };
        assert_eq!((identity.width(), identity.packed_bits()), (1, bit));
    }
    assert!(
        parse_canonical_binary("10 110 00 10 #d1:0 00 0 01 01").is_err(),
        "human carrier must not become canonical binary"
    );
}

#[test]
fn canonical_rejects_numeric_and_tagged_literals_but_preserves_d1_words() {
    // #5789: binary domain identities are NOT unqualified numeric literals.
    // The historic #d1 textual carrier is forbidden in canonical SENS source.
    for forbidden in ["2", "42", "-1", "+1", "0.0", "1.0", "#d1:0", "#d1:1"] {
        assert!(
            parse_canonical_binary(forbidden).is_err(),
            "forbidden source literal unexpectedly admitted: {forbidden}"
        );
    }
    for bit in ["0", "1"] {
        let words = parse_canonical_binary(bit).expect("exact one-bit domain word");
        assert!(matches!(
            &words[0].kind,
            ExprKind::DomainIdentity(DomainIdentity::D1(_))
        ));
    }
}

#[test]
fn executable_axioms_use_exact_d1_for_positive_and_invalid_knowledge() {
    // Виконуємо справжній український Lisp у SENS, а не Rust-трактування
    // текстових «так»/«ні» чи структурного D3 ().
    let mut session = Session::default();
    let source = include_str!("../../../lib/axioms-d1-principle-five.lisp");
    let forms = sens::parse_mixed_exact_domain(source)
        .expect("test_id=D1-AXIOMS layer=reader current Ukrainian source");
    let positive = eval_parsed_expressions(&forms, &mut session)
        .expect("test_id=D1-AXIOMS layer=SENS complete principle-five execution")
        .value;
    assert_eq!(
        positive.as_predicate_bit(),
        Some(true),
        "test_id=D1-AXIOMS layer=domain expected=D1:1 actual={positive}"
    );

    // Самостійні негативи виконуються тією ж мовою в живій SENS-сесії.
    // Невірна форма повинна повернути саме D1:0, а не D3 NIL або Type.
    for (id, source) in [
        ("atom-not-four-words", "(принцип-п'ять-факт (як-є earth))"),
        ("incomplete-knowledge-pair", "(принцип-п'ять-слова (як-є (earth)))"),
        ("invalid-axiom-fact", "(перевірити-принцип-п'ять (як-є (earth)))"),
    ] {
        let forms = sens::parse_mixed_exact_domain(source)
            .unwrap_or_else(|error| panic!("test_id=D1-AXIOMS-{id} layer=reader {error}"));
        let actual = eval_parsed_expressions(&forms, &mut session)
            .unwrap_or_else(|error| panic!("test_id=D1-AXIOMS-{id} layer=SENS {error}"))
            .value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(false),
            "test_id=D1-AXIOMS-{id} layer=domain expected=D1:0 actual={actual}"
        );
        assert_ne!(actual, Value::Nil, "D1:0 must never equal D3:000");
    }
}
