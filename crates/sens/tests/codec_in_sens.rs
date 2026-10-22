//! SENS-бібліотека відображення структури D2 + незалежний exact-domain свідок.
//! d2-open/d2-sep/d2-close/d2-dot усередині Lisp — цитовані мітки ДАНИХ,
//! не D2 машинні слова. Справжня структура належить точним W2: 10/00/01/11.
use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse_binary_source_words,
    parse_mixed_exact_domain, PhysicalT5Program, Session, Value,
};

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
        .unwrap_or_else(|e| panic!("{source} failed: {e}"))
        .value
        .to_string()
}

#[test]
fn codec_emits_symbolic_d2_order_but_not_machine_words() {
    let mut s = codec_session();
    // README: (CAR (CONS () ())) -> 10 100 00 10 111 00 000 00 000 01 01
    assert_eq!(
        eval("(кодувати-структуру-д2 (quote (100 (111 () ()))))", &mut s),
        eval(
            "(quote (d2-open 100 d2-sep d2-open 111 d2-sep () d2-sep () d2-close d2-close))",
            &mut s
        )
    );
}

// Exact structural D2 order, tested through compact SENS-owned marker proxies.
// This is not yet proof of physical two-bit tokens in a packed .sens file.
#[test]
fn codec_distinguishes_d2_dot_from_separator() {
    let mut s = codec_session();
    for (source, expected) in [
        ("100", "(100)"),
        ("(100 111)", "(d2-open 100 d2-sep 111 d2-close)"),
        ("(100 . 111)", "(d2-open 100 d2-dot 111 d2-close)"),
    ] {
        let encoded = eval(&format!("(кодувати-структуру-д2 (quote {source}))"), &mut s);
        let expected_stream = eval(&format!("(quote {expected})"), &mut s);
        assert_eq!(
            encoded, expected_stream,
            "D2 marker order mismatch: source={source} expected={expected}"
        );
        let returned = eval(
            &format!("(перевірити-обертання-д2 (quote {source}))"),
            &mut s,
        );
        let wanted = eval(&format!("(quote {source})"), &mut s);
        assert_eq!(returned, wanted, "D2 roundtrip mismatch: source={source}");
    }
}

#[test]
fn codec_round_trips_every_shape() {
    let mut s = codec_session();
    for src in [
        "101",
        "()",
        "(100 111 000)",
        "(100 . 111)",
        "((100) 111)",
        "((100 . 111) . 000)",
        "(100 (111 . 000))",
        "((100 . 111) (000 . 101))",
        "((100 . 111) . (000 . 101))",
        "(100 (111 . 000) . 101)",
        "(((100 . 111) . 000) . 101)",
        // Крапка всередині й зовні вкладеної пари не може стати D2 separator.
        "(100 (111 . 000) . 101)",
        "((100 . 111) (000 . 001))",
        "(())",
        // Пара вкладена у крапкову пару: усі D2 крапки мають пережити кодек.
        "((100 . 111) . (000 . 001))",
        // Подвійна вкладеність: внутрішній D2 close не поглинає зовнішню пару.
        "(100 . (111 . (000 . 001)))",
    ] {
        let got = eval(&format!("(перевірити-обертання-д2 (quote {src}))"), &mut s);
        let want = eval(&format!("(quote {src})"), &mut s);
        assert_eq!(got, want, "round-trip for {src}");
    }
}

#[test]
fn exact_d2_quote_of_dotted_pair_executes_without_text7_marker_proxies() {
    // Canonical D2 machine source: OPEN, D3 QUOTE, SEP,
    // OPEN, D3 CAR, DOT, D3 CONS, CLOSE, CLOSE.
    // This is executable exact-domain input, not a quoted d2-open symbol.
    let exact = "10 001 00 10 100 11 111 01 01";
    let words = parse_binary_source_words(exact)
        .expect("only exact-width binary words")
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    let program = PhysicalT5Program::from_exact_words(&words)
        .expect("all four D2 markers interpreted as structure");
    assert_eq!(program.form_count(), 1);
    let result = program
        .execute(&mut Session::default())
        .expect("real SENS QUOTE executes dotted D2 pair");
    let Value::Pair(node) = &result.value else {
        panic!("D2:11 must produce a dotted SENS pair, not a proxy list");
    };
    let Value::DomainIdentity(head) = &node.head else {
        panic!("D3:100 must preserve exact identity");
    };
    let Value::DomainIdentity(tail) = &node.tail else {
        panic!("D3:111 must preserve exact identity");
    };
    assert_eq!((head.width(), head.packed_bits()), (3, 0b100));
    assert_eq!((tail.width(), tail.packed_bits()), (3, 0b111));

    // Negative forms must be rejected by the SAME exact reader used after
    // Zig/T5M: never reinterpret a stray D2 marker as D7 text or Lisp data.
    for bad in [
        "11",
        "01",
        "10 11 100 01",
        "10 100 11 01",
        "10 100 11 111 00 000 01",
        "10 100",
    ] {
        let words = parse_binary_source_words(bad)
            .expect("well-formed exact words; wrong structural grammar")
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        assert!(
            PhysicalT5Program::from_exact_words(&words).is_err(),
            "malformed D2 admitted as SENS data: {bad}"
        );
    }
}

#[test]
fn d11_кодек_д2_три_допоміжні_закони_у_sens() {
    // Перевіряємо тіла виконуваної SENS-бібліотеки, без нових
    // D11-примітивів, Python-оракулів чи підміни D2-маркерів.
    let mut s = codec_session();
    for (name, positive, expected, negative, rejected) in [
        (
            "кодек-д2-додати-префікс",
            "(кодек-д2-додати-префікс (як-є (альфа бета)) (як-є (гамма)))",
            "(альфа бета гамма)",
            "(кодек-д2-додати-префікс (як-є (альфа)) (як-є (гамма)))",
            "(альфа гамма)",
        ),
        (
            "кодек-д2-перший-декодований",
            "(кодек-д2-перший-декодований (кодек-д2-кодувати-вузол (як-є (альфа бета)) (як-є (хвіст))))",
            "(альфа бета)",
            "(кодек-д2-перший-декодований (кодек-д2-кодувати-вузол (як-є (альфа . бета)) (як-є (хвіст))))",
            "(альфа . бета)",
        ),
        (
            "кодек-д2-декодувати-вузол",
            "(кодек-д2-декодувати-вузол (кодек-д2-кодувати-вузол (як-є (альфа бета)) (як-є (хвіст))))",
            "((альфа бета) хвіст)",
            "(кодек-д2-декодувати-вузол (кодек-д2-кодувати-вузол (як-є (альфа . бета)) (як-є (хвіст))))",
            "((альфа . бета) хвіст)",
        ),
    ] {
        let actual = eval(positive, &mut s);
        assert_eq!(actual, expected,
            "test_id=D11-CODEC-{name}-POS layer=SENS source={positive} expected={expected} actual={actual}");
        let opposite = eval(negative, &mut s);
        assert_eq!(opposite, rejected,
            "test_id=D11-CODEC-{name}-NEG layer=SENS source={negative} expected={rejected} actual={opposite}");
        assert_ne!(actual, opposite,
            "test_id=D11-CODEC-{name}-DISTINCT layer=SENS");
    }
}
