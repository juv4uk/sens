use sens::{eval_program, load_core_library, ErrorKind, Session, Text7, Value};

fn core_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("load one Core");
    session
}

fn render(source: &str) -> String {
    let mut session = core_session();
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("{source}: {error:?}"))
        .value
        .to_string()
}

#[test]
fn numeric_presentation_is_preserved() {
    assert_eq!(render("(number->string 42)"), "\"42\"");
    assert_eq!(render("(number->string 1/2)"), "\"1/2\"");
    assert_eq!(render("(number->string -5/4)"), "\"-5/4\"");
    assert_eq!(render("(number->string 3.0)"), "\"3.0\"");
}

#[test]
fn text7_is_not_a_number() {
    let mut session = core_session();
    let text = Text7::from_cells(vec![0x3b]).expect("exact seven-bit cell");
    session.environment.define("payload", Value::Text7(text));

    let error = eval_program("(number->string payload)", &mut session)
        .expect_err("Text7 must fail the Number boundary");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn ordinary_non_numbers_fail_closed() {
    for source in [
        "(number->string \"text\")",
        "(number->string (00000001 symbol))",
        "(number->string (00000001 (1 2)))",
    ] {
        let mut session = core_session();
        let error = eval_program(source, &mut session)
            .expect_err("non-Number must fail the Number boundary");
        assert_eq!(error.kind, ErrorKind::Type, "{source}: {error:?}");
    }
}
