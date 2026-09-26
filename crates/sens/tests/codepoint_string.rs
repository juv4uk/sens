use sens::{eval_program, ErrorKind, Session};

#[test]
fn codepoint_to_string_materializes_unicode_scalars() {
    let mut session = Session::default();
    for (scalar, expected) in [
        (65, "A"),
        (162, "¢"),
        (8364, "€"),
        (128512, "😀"),
    ] {
        let result = eval_program(&format!("(codepoint->string {scalar})"), &mut session)
            .expect("valid Unicode scalar should materialize");
        assert_eq!(result.value.to_string(), format!("\"{expected}\""));
    }
}

#[test]
fn codepoint_to_string_rejects_non_scalars_and_inexact_values() {
    for source in [
        "(codepoint->string -1)",
        "(codepoint->string 55296)",
        "(codepoint->string 1114112)",
        // Decimal literals are exact in sens. JSON numbers are a real
        // source of inexact runtime values, so use that boundary here.
        "(codepoint->string (json-parse \"65.0\"))",
        "(codepoint->string 1/2)",
    ] {
        let error = eval_program(source, &mut Session::default())
            .expect_err("invalid scalar input must fail named");
        assert_eq!(error.kind, ErrorKind::Type, "source: {source}");
    }
}

#[test]
fn string_to_codepoint_observes_exactly_one_unicode_scalar() {
    let mut session = Session::default();
    for (text, expected) in [("A", "65"), ("¢", "162"), ("€", "8364"), ("😀", "128512")] {
        let result = eval_program(&format!("(string->codepoint \"{text}\")"), &mut session)
            .expect("one Unicode scalar should expose its exact value");
        assert_eq!(result.value.to_string(), expected);
    }
}

#[test]
fn string_to_codepoint_rejects_non_string_empty_and_multi_character_inputs() {
    for source in [
        "(string->codepoint 65)",
        "(string->codepoint \"\")",
        "(string->codepoint \"ab\")",
        "(string->codepoint \"😀x\")",
    ] {
        let error = eval_program(source, &mut Session::default())
            .expect_err("string->codepoint accepts exactly one scalar character");
        assert_eq!(error.kind, ErrorKind::Type, "source: {source}");
    }
}
