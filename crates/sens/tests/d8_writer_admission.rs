//! Перевіряються лише текстові механізми D8, допущені до виклику.
//! READ є D8-резидентом, але його surface ще не допущено; резидентність сама
//! по собі не дає викличності. Без W8-голів чи згенерованих машинних тегів.
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
    ] {
        let actual = run(source, &mut session)
            .unwrap_or_else(|error| panic!("D8 text projection {source}: {error:?}"));
        assert_eq!(actual.to_string(), expected, "writer mismatch for {source}");
        assert!(
            !actual.to_string().contains("#q2"),
            "machine tags are not human output"
        );
    }
}

#[test]
fn d8_writer_survives_d4_lambdas_and_user_defined_calls() {
    let mut session = session();
    run(
        "(визначити внутрішній-текст (функція (значення) (значення-у-текст значення)))",
        &mut session,
    )
    .expect("ordinary Ukrainian DEFINE/LAMBDA must load");
    let source = "(внутрішній-текст (як-є (a b)))";
    let expected = "\"(a b)\"";
    assert_eq!(
        run(source, &mut session)
            .expect("user D4 closure calls current D8 mechanism")
            .to_string(),
        expected
    );
}

// Закон D8 TEXT→SYMBOL та його мутант виконуються тільки SENS із Lisp:
// tests/semantic/d8-string-symbol-roundtrip-{law,mutant}.lisp.
// Негатив Type також живе у tests/semantic/d8-string-symbol-nontext-type-negative.lisp.
// Rust не дублює цей вердикт: CI перевіряє його через Zig/T5M та реальний SENS.

#[test]
fn d8_writer_rejects_incorrect_arity() {
    let mut session = session();
    let error = run("(значення-у-текст 1 2)", &mut session)
        .expect_err("D8 writer accepts exactly one input");
    assert_eq!(error.kind, sens::ErrorKind::Arity);
}
