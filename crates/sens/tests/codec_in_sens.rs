//! Структурний кодек, написаний SENS-ом (lib/codec-d2.lisp).
//! Тест порівнює вихід кодека з виходом самого `quote` — без угадування
//! формату друку, тож перевіряє саме round-trip, а не рядок.
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
fn codec_written_in_sens_round_trips_every_shape() {
    let mut session = codec_session();
    for src in ["x", "(a b c)", "(a . b)", "(a (b c) d)", "((a . b) c . d)"] {
        let got = eval(&format!("(codec-roundtrip (quote {src}))"), &mut session);
        let want = eval(&format!("(quote {src})"), &mut session);
        assert_eq!(got, want, "round-trip for {src}");
    }
}

#[test]
fn codec_really_transforms_and_is_not_identity() {
    let mut session = codec_session();
    let encoded = eval("(codec-encode (quote (a b)) ())", &mut session);
    let plain = eval("(quote (a b))", &mut session);
    assert_ne!(encoded, plain, "codec must transform, not echo");
    assert!(encoded.contains("codec-open"), "encoding must carry D2 open marker: {encoded}");
    assert!(encoded.contains("codec-close"), "encoding must carry D2 close marker: {encoded}");
}
