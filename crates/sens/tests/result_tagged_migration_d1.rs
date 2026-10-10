//! Migration witness: strict D3:110 two-field clauses, D1:1/D1:0 result.
//! Only the one migrated definition is evaluated: other result-status helpers
//! still require separate proof and must not be silently considered migrated.

use sens::{eval_program, Session};

fn isolated_migrated_definition() -> &'static str {
    let source = include_str!("../../../lib/result-status.lisp");
    let begin = source
        .find("(00001001 result-tagged?\n")
        .expect("result-tagged? definition");
    let end = source[begin..]
        .find("\n(00001001 result-status\n")
        .map(|offset| begin + offset)
        .expect("next definition boundary");
    &source[begin..end]
}

fn eval_tagged(source: &str) -> String {
    let mut session = Session::default();
    eval_program(isolated_migrated_definition(), &mut session)
        .expect("isolated current D1/D3 language definition must load");
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("evaluating {source}: {error}"))
        .value
        .to_string()
}

#[test]
fn migrated_tag_recognizer_returns_only_exact_d1_predicate_bits() {
    for source in [
        "(result-tagged? (00000100 (00000001 proved) (00000001 ())))",
        "(result-tagged? (00000100 (00000001 unknown) (00000001 ())))",
        "(result-tagged? (00000100 (00000001 partial) (00000001 ())))",
        "(result-tagged? (00000100 (00000001 blocked) (00000001 ())))",
        "(result-tagged? (00000100 (00000001 disputed) (00000001 ())))",
        "(result-tagged? (00000100 (00000001 invalid) (00000001 ())))",
    ] {
        assert_eq!(eval_tagged(source), "1", "{source}: exact D1:YES");
    }
    for source in [
        "(result-tagged? (00000001 ()))",
        "(result-tagged? 42)",
        "(result-tagged? (00000100 (00000001 other) (00000001 ())))",
    ] {
        assert_eq!(eval_tagged(source), "0", "{source}: exact D1:NO");
    }
}

#[test]
fn no_legacy_three_field_cond_or_truthiness_in_migrated_function() {
    let src = isolated_migrated_definition();
    assert!(!src.contains("(t "));
    assert!(!src.contains("(00000010 result) ()"));
    assert!(!src.contains("(00000010 result) (1)"));
    assert!(src.contains("((00000010 result) (00000011 0 1))"));
    assert!(src.contains("((00000010 (00000001 ())) (00000011 0 1))"));
}
