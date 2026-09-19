use my_lisp::{eval_program, load_core_library, load_process_library, Session};

fn utf8_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    eval_program(include_str!("../../../lib/utf8.lisp"), &mut session).unwrap();
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
fn utf8_layer_keeps_process_library_as_a_separate_top_level_load() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_process_library(&mut session)
        .expect("UTF-8, process and TCP language layers must load sequentially");
}
