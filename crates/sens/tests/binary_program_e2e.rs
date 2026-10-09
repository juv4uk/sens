//! Current pure-binary SENS execution: physical T5 -> canonical D2/W7
//! reader -> contextual lexical binding -> exact D1 result.
//!
//! This is an executable *mechanical* smoke, not an independent Lisp semantic
//! oracle or evidence that D10 has a ratified physical runtime representation.
//! The source contains only exact-width bits and whitespace, never name/SID
//! spellings. No compatibility parser, host clock, or Core4 boot is involved.

use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    open_ternary_program, parse_canonical_binary, DomainIdentity, Expr, ExprKind, Session,
    Value,
};

const BINARY_PROGRAM: &str =
    include_str!("../../../examples/binary/d7-first-program.lisp");

fn assert_exact_binary_ast(expr: &Expr) {
    match &expr.kind {
        ExprKind::DomainIdentity(_) => {}
        ExprKind::List(items) => {
            for item in items.iter() {
                assert_exact_binary_ast(item);
            }
        }
        ExprKind::Pair(head, tail) => {
            assert_exact_binary_ast(head);
            assert_exact_binary_ast(tail);
        }
        other => panic!("canonical binary reader invented a name or legacy slot: {other:?}"),
    }
}

#[test]
fn real_packed_t5_runs_binary_d4_d7_definition_and_d1_result() {
    assert!(
        BINARY_PROGRAM
            .bytes()
            .all(|b| b == b'0' || b == b'1' || b.is_ascii_whitespace()),
        "the executable source must contain only 0/1 and whitespace"
    );

    // Physical bytes, not a filename or a text-only claim of binary source.
    let physical = encode_binary_projection_ternary(BINARY_PROGRAM)
        .expect("exact binary executable program must encode to physical T5");
    assert!(!physical.is_empty());
    let decoded_words = decode_ternary_program(&physical)
        .expect("canonical packed T5 must decode to exact-width words");
    let visible = open_ternary_program(&physical)
        .expect("physical T5 must open as exact binary source");
    let normalized = BINARY_PROGRAM.split_whitespace().collect::<Vec<_>>().join(" ");
    assert_eq!(visible, normalized, "T5 changed an exact-width source word");
    assert_eq!(
        visible,
        sens::render_ternary_words_spaced(&decoded_words),
        "T5 word boundaries cannot be reconstructed from human names"
    );
    assert_eq!(
        encode_binary_projection_ternary(&visible).unwrap(),
        physical,
        "physical bytes must be canonical under re-encoding"
    );

    let parsed = parse_canonical_binary(&visible)
        .expect("only the canonical D2 reader may parse executable bits");
    assert_eq!(parsed.len(), 2, "one D4 definition followed by one D7 call");
    for expression in &parsed {
        assert_exact_binary_ast(expression);
    }
    let value = eval_parsed_expressions(&parsed, &mut Session::default())
        .expect("binary definition and its contextual D7 binding must execute")
        .value;
    assert_eq!(
        value,
        Value::DomainIdentity(DomainIdentity::D1(
            sens::PredicateBit::from_word(sens::Bit1::new(1).unwrap())
        )),
        "current source-level result must retain exact D1:1, not host T"
    );
}

#[test]
fn human_executable_spelling_never_passes_the_physical_binary_gate() {
    for bad in ["(CONS x y)", "(define x 1)", "(100 x)", "10 0011 00 name 01"] {
        assert!(
            encode_binary_projection_ternary(bad).is_err(),
            "human spelling passed as executable binary source: {bad}"
        );
    }
}

#[test]
fn d7_words_are_data_not_implicitly_callable_or_number() {
    // Both words carry W7 identity; the first is an owner-reserved coordinate.
    // Representation is still possible, but residency does not confer a call law.
    for head in ["0100001", "0101010", "1000001"] {
        let source = format!("10 {head} 00 1 01");
        let physical = encode_binary_projection_ternary(&source)
            .expect("7-bit words are mechanically representable");
        let visible = open_ternary_program(&physical).unwrap();
        let ast = parse_canonical_binary(&visible).unwrap();
        let error = eval_parsed_expressions(&ast, &mut Session::default());
        assert!(error.is_err(), "D7 data cannot become an executable domain head");
    }
}

#[test]
fn d10_width_is_a_coordinate_not_yet_an_admitted_t5_program_word() {
    let coordinate = sens::domain_ladder::DomainCoordinate::new(10, 1)
        .expect("D10 exact mechanical coordinate exists");
    assert_eq!((coordinate.width(), coordinate.bits()), (10, 1));
    assert!(
        encode_binary_projection_ternary("0000000001").is_err(),
        "D10 physical admission is forbidden until a ratified T5/D10 path exists"
    );
}
