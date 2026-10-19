//! D8 text and reader mechanisms are exercised from the live Ukrainian projection.
//! No W8 numeric call heads, generated bit-tag output or path-pinned Core parser.
use sens::{eval_parsed_expressions, load_core_library, parse_mixed_exact_domain, Session};

fn run(source: &str, session: &mut Session) -> Result<sens::Value, sens::LanguageError> {
    let forms = parse_mixed_exact_domain(source)?;
    Ok(eval_parsed_expressions(&forms, session)?.value)
}

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("Core library loads through its canonical loader");
    session
}

#[test]
fn d8_writer_serializes_structural_values_without_machine_width_tags() {
    let mut session = session();
    for (source, expected) in [
        ("(значення-у-текст (як-є (a b)))", "\"(a b)\""),
        ("(значення-у-текст (як-є ()))", "\"()\""),
        ("(значення-у-текст 7)", "\"7\""),
    ] {
        let actual = run(source, &mut session)
            .unwrap_or_else(|error| panic!("D8 text projection {source}: {error:?}"));
        assert_eq!(actual.to_string(), expected, "writer mismatch for {source}");
        assert!(!actual.to_string().contains("#q2"), "machine tags are not human output");
    }
}

#[test]
fn d8_writer_survives_d4_lambdas_and_user_defined_calls() {
    let mut session = session();
    run("(визначити внутрішній-текст (функція (значення) (значення-у-текст значення)))", &mut session)
        .expect("ordinary Ukrainian DEFINE/LAMBDA must load");
    for (source, expected) in [
        ("(внутрішній-текст (як-є (a b)))", "\"(a b)\""),
        ("(внутрішній-текст 7)", "\"7\""),
    ] {
        assert_eq!(
            run(source, &mut session).expect("user D4 closure calls current D8 mechanism").to_string(),
            expected
        );
    }
}

#[test]
fn d8_read_write_round_trip_uses_current_ukrainian_residents() {
    let mut session = session();
    for (source, expected) in [
        ("(прочитати \"(a b)\")", "(a b)"),
        ("(прочитати (значення-у-текст (як-є (a b))))", "(a b)"),
        ("(прочитати (значення-у-текст 7))", "7"),
    ] {
        let actual = run(source, &mut session)
            .unwrap_or_else(|error| panic!("current D8 read/write {source}: {error:?}"));
        assert_eq!(actual.to_string(), expected);
    }
}

#[test]
fn d8_string_to_symbol_is_exact_and_rejects_non_strings() {
    let mut session = session();
    assert_eq!(
        run("(текст-у-символ \"zoo\")", &mut session)
            .expect("ratified Ukrainian D8 text-to-symbol")
            .to_string(),
        "zoo"
    );
    let error = run("(текст-у-символ 7)", &mut session)
        .expect_err("number is not text");
    assert_eq!(error.kind, sens::ErrorKind::Type);
}

#[test]
fn d8_read_rejects_excess_arguments() {
    let mut session = session();
    let error = run("(прочитати \"a\" \"b\")", &mut session)
        .expect_err("D8 reader accepts exactly one input");
    assert_eq!(error.kind, sens::ErrorKind::Arity);
}

#[test]
fn d8_writer_rejects_incorrect_arity() {
    let mut session = session();
    let error = run("(значення-у-текст 1 2)", &mut session)
        .expect_err("D8 writer accepts exactly one input");
    assert_eq!(error.kind, sens::ErrorKind::Arity);
}
