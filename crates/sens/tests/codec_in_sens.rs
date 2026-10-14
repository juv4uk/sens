//! Кодек, написаний SENS-ом, у ТОЧНОМУ D2-порядку T5 (lib/codec-d2.lisp).
//! Маркери названо d2-open/d2-sep/d2-close/d2-dot — 1:1 до слів 10/00/01/11.
//! (Mixed-читач .lisp читає голе `01` як десяткове 1, тож D2-слово як дані там
//!  поки не виражається; порядок перевіряємо на іменованих маркерах.)
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
        .value.to_string()
}

#[test]
fn codec_emits_exact_t5_d2_order() {
    let mut s = codec_session();
    // README: (CAR (CONS () ())) -> 10 100 00 10 111 00 000 00 000 01 01
    // 1:1 до маркерів: 10=d2-open, 00=d2-sep, 01=d2-close, ()=елемент
    assert_eq!(
        eval("(t5-encode (quote (100 (111 () ()))))", &mut s),
        eval("(quote (d2-open 100 d2-sep d2-open 111 d2-sep () d2-sep () d2-close d2-close))", &mut s)
    );
}

// These are *named* D2 proxies in a mixed .lisp interpreter. The expected
// order is fixed by SENS's D2 law (10 open, 00 separator, 11 dot, 01 close).
// This test does NOT assert actual T5 physical bytes or callable admission.
#[test]
fn codec_distinguishes_exact_d2_dot_from_separator() {
    let mut s = codec_session();
    for (source, expected_words) in [
        ("100", "(100)"),
        ("(100 111)", "(d2-open 100 d2-sep 111 d2-close)"),
        ("(100 . 111)", "(d2-open 100 d2-dot 111 d2-close)"),
    ] {
        let actual = eval(&format!("(t5-encode (quote {source}))"), &mut s);
        let expected = eval(&format!("(quote {expected_words})"), &mut s);
        assert_eq!(
            actual, expected,
            "D2 marker-order mismatch: source={source}; expected={expected_words}"
        );

        let decoded = eval(
            &format!("(t5-decode (t5-encode (quote {source})))"),
            &mut s,
        );
        let source_value = eval(&format!("(quote {source})"), &mut s);
        assert_eq!(
            decoded, source_value,
            "D2 round-trip mismatch for {source}; encoded={actual}"
        );
    }
}

#[test]
fn codec_round_trips_every_shape() {
    let mut s = codec_session();
    for src in ["101", "()", "(100 111 000)", "(100 . 111)", "((100) 111)"] {
        let got = eval(&format!("(t5-roundtrip (quote {src}))"), &mut s);
        let want = eval(&format!("(quote {src})"), &mut s);
        assert_eq!(got, want, "round-trip for {src}");
    }
}

#[test]
fn codec_really_transforms() {
    let mut s = codec_session();
    let enc = eval("(t5-encode (quote (100 111)))", &mut s);
    assert_ne!(enc, eval("(quote (100 111))", &mut s), "must transform");
    assert!(enc.contains("d2-open") && enc.contains("d2-close") && enc.contains("d2-sep"), "{enc}");
}
