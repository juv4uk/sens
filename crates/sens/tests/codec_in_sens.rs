//! Компактний кодек, написаний SENS-ом, у ТОЧНОМУ D2-порядку T5 (lib/codec-d2.lisp).
//! Маркери: a=open, c=sep, b=close, d=dot (1:1 до слів 10/00/01/11).
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
    eval_program(source, session).unwrap_or_else(|e| panic!("{source} failed: {e}")).value.to_string()
}

#[test]
fn codec_emits_exact_t5_d2_order() {
    let mut s = codec_session();
    // README: (CAR (CONS () ())) -> 10 100 00 10 111 00 000 00 000 01 01
    assert_eq!(
        eval("(t5-encode (quote (100 (111 () ()))))", &mut s),
        eval("(quote (a 100 c a 111 c () c () b b))", &mut s)
    );
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
