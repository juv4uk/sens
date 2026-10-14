//! Кодек, написаний SENS-ом, СУМІСНИЙ з D2-порядком T5 (lib/codec-d2.lisp).
//! Тести порівнюють вихід кодека з виходом самого `quote` (без угадування друку).
use sens::{eval_parsed_expressions, eval_program, load_core_library, parse_mixed_exact_domain, Session};

fn codec_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core library");
    let forms = parse_mixed_exact_domain(include_str!("../../../lib/codec-d2.lisp"))
        .expect("codec-d2 current D3/D4 source must parse");
    eval_parsed_expressions(&forms, &mut session).expect("codec-d2 source must load");
    session
}

fn eval(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("{source} failed: {error}"))
        .value
        .to_string()
}

#[test]
fn binary_word_literals_are_exact_width_words() {
    let mut s = codec_session();
    for (expr, want) in [
        ("(quote 10)", "10"),
        ("(quote 01)", "01"),
        ("(quote 00)", "00"),
        ("(quote 11)", "11"),
        ("(quote 000)", "000"),
    ] {
        assert_eq!(eval(expr, &mut s), want, "{expr}");
    }
}

#[test]
fn codec_matches_readme_canonical_t5_sequence() {
    let mut s = codec_session();
    // README: (CAR (CONS () ())) -> 10 100 00 10 111 00 000 00 000 01 01
    assert_eq!(
        eval("(t5-encode (quote (100 (111 () ()))))", &mut s),
        eval("(quote (10 100 00 10 111 00 000 00 000 01 01))", &mut s),
        "canonical T5 D2 sequence"
    );
}

#[test]
fn codec_round_trips_t5_sequence_for_every_shape() {
    let mut s = codec_session();
    for src in ["101", "()", "(000 001 010)", "(000 . 001)", "((000) 001)"] {
        let got = eval(&format!("(t5-roundtrip (quote {src}))"), &mut s);
        let want = eval(&format!("(quote {src})"), &mut s);
        assert_eq!(got, want, "round-trip for {src}");
    }
}
