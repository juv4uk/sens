use sens::{eval_parsed_expressions, eval_program, load_core_library, load_process_library, parse_mixed_exact_domain_utf8_source, Session};

fn utf8_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    let source = include_str!("../../../lib/utf8.lisp");
    let exact = parse_mixed_exact_domain_utf8_source("lib/utf8.lisp", source)
        .expect("UTF-8 current exact-domain source must parse");
    eval_parsed_expressions(&exact, &mut session)
        .expect("UTF-8 source must load through its width-preserving reader");
    session
}

fn eval(source: &str) -> String {
    let mut session = utf8_session();
    eval_program(source, &mut session).unwrap().value.to_string()
}

#[test]
fn utf8_decodes_ascii_exactly() {
    assert_eq!(eval("(utf8-decode (quote (65 66 67)))"), "(decoded (65 66 67))");
}

#[test]
fn utf8_decodes_multibyte_scalars_exactly() {
    // U+00A2 CENT SIGN, U+20AC EURO SIGN, U+1F600 GRINNING FACE.
    assert_eq!(
        eval("(utf8-decode (quote (194 162 226 130 172 240 159 152 128)))"),
        "(decoded (162 8364 128512))"
    );
}

#[test]
fn utf8_decodes_valid_bytes_to_a_runtime_string_without_lossy_host_policy() {
    assert_eq!(
        eval("(utf8-decode-string (quote (65 194 162 226 130 172 240 159 152 128)))"),
        "(decoded \"A¢€😀\")"
    );
}

#[test]
fn utf8_encodes_runtime_strings_to_exact_wire_bytes() {
    assert_eq!(eval("(utf8-encode-string \"ABC\")"), "(65 66 67)");
    assert_eq!(
        eval("(utf8-encode-string \"A¢€😀\")"),
        "(65 194 162 226 130 172 240 159 152 128)"
    );
}

#[test]
fn utf8_encode_decode_round_trip_is_language_owned() {
    assert_eq!(
        eval("(utf8-decode-string (utf8-encode-string \"Привіт 😀\"))"),
        "(decoded \"Привіт 😀\")"
    );
}

#[test]
fn utf8_rejects_overlong_surrogate_and_out_of_range_sequences() {
    for bytes in [
        "(192 128)",       // overlong 2-byte form
        "(224 128 128)",   // overlong 3-byte form
        "(237 160 128)",   // UTF-16 surrogate U+D800
        "(244 144 128 128)", // above U+10FFFF
    ] {
        assert_eq!(
            eval(&format!("(utf8-decode (quote {bytes}))")),
            "(rejected invalid-utf8)"
        );
    }
}

#[test]
fn utf8_rejects_truncation_and_bad_continuation() {
    for bytes in ["(226 130)", "(240 159 152)", "(226 65 172)"] {
        assert_eq!(
            eval(&format!("(utf8-decode (quote {bytes}))")),
            "(rejected invalid-utf8)"
        );
    }
}

#[test]
fn utf8_rejects_non_bytes_before_protocol_interpretation() {
    assert_eq!(
        eval("(utf8-decode (quote (65 256 66)))"),
        "(rejected invalid-byte)"
    );
    assert_eq!(
        eval("(utf8-decode (quote (65 -1 66)))"),
        "(rejected invalid-byte)"
    );
}


#[test]
fn utf8_atomic_d3_eq_matches_d8_equal_for_all_256_bytes_at_five_boundaries() {
    // D3:101 EQ та D8:11110111 EQUAL мають різну ширину й семантику
    // для списків. Рівність допустима лише для двох атомарних чисел.
    let mut session = Session::default();
    let mut checked = 0_usize;
    for byte in 0_u16..=255 {
        for boundary in [0_u16, 224, 237, 240, 244] {
            for (head, expected_width) in [("101", 3), ("11110111", 8)] {
                let source = format!("({head} {byte} {boundary})");
                let parsed = parse_mixed_exact_domain_utf8_source(
                    "lib/utf8.lisp", &source,
                ).expect("цей функційний код має читатися лише за своєю шириною");
                let sens::ExprKind::List(args) = &parsed[0].kind else {
                    panic!("очікується одна форма виклику")
                };
                assert!(matches!(
                    &args[0].kind,
                    sens::ExprKind::DomainIdentity(identity) if identity.width() == expected_width
                ), "{source}: ширина функції не збігається з доменом");
                let result = eval_parsed_expressions(&parsed, &mut session)
                    .unwrap_or_else(|error| panic!("{source}: {error}"));
                assert_eq!(
                    result.value.as_predicate_bit(),
                    Some(byte == boundary),
                    "{source}: атомарна рівність повинна повертати точний D1"
                );
                checked += 1;
            }
        }
    }
    assert_eq!(checked, 256 * 5 * 2);
}

#[test]
fn utf8_d3_atom_eq_must_not_replace_structural_d8_equal() {
    let mut session = Session::default();
    let atomic_only = parse_mixed_exact_domain_utf8_source(
        "lib/utf8.lisp", "(101 (001 (a b)) (001 (a b)))",
    ).expect("синтаксис допустимий");
    let error = eval_parsed_expressions(&atomic_only, &mut session)
        .expect_err("D3 EQ не приймає список як атом");
    assert_eq!(error.kind, sens::ErrorKind::Type);

    let structural = parse_mixed_exact_domain_utf8_source(
        "lib/utf8.lisp", "(11110111 (001 (a b)) (001 (a b)))",
    ).expect("D8 EQUAL залишається окремою ратифікованою функцією");
    let outcome = eval_parsed_expressions(&structural, &mut session)
        .expect("D8 EQUAL має підтримувати структурне порівняння");
    assert_eq!(outcome.value.as_predicate_bit(), Some(true));
}

#[test]
fn utf8_layer_keeps_process_library_as_a_separate_top_level_load() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_process_library(&mut session)
        .expect("UTF-8, process and TCP language layers must load sequentially");
}

#[test]
fn utf8_helper_returns_exact_d1_predicate_on_boundaries() {
    let mut session = utf8_session();
    for (source, expected) in [
        ("(utf8-in-range? 0 0 255)", true),
        ("(utf8-in-range? 255 0 255)", true),
        ("(utf8-in-range? 256 0 255)", false),
        ("(utf8-in-range? -1 0 255)", false),
        ("(utf8-continuation-byte? 127)", false),
        ("(utf8-continuation-byte? 128)", true),
        ("(utf8-continuation-byte? 191)", true),
        ("(utf8-continuation-byte? 192)", false),
        ("(utf8-byte? 0)", true),
        ("(utf8-byte? 255)", true),
        ("(utf8-byte? 256)", false),
        ("(utf8-all-bytes? (quote ()))", true),
        ("(utf8-all-bytes? (quote (0 127 255)))", true),
        ("(utf8-all-bytes? (quote (0 256)))", false),
        ("(utf8-two-continuations? 128 191)", true),
        ("(utf8-two-continuations? 128 192)", false),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|e| panic!("{source} failed: {e:?}")).value;
        assert_eq!(
            actual.as_predicate_bit(), Some(expected),
            "{source}: expected an exact D1 bit, never ordinary Number 0/1"
        );
    }
}
