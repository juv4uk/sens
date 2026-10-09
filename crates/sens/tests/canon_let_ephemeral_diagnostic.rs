//! TEMPORARY diagnosis only — not intended for merge to main.
use sens::{eval_program, load_core_library, Session};

#[test]
fn diagnose_historical_let_binding_on_github_hosted() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core load");
    let probes = [
        ("literal", "(00000001 (expected value))"),
        ("lambda", "((00001000 (expected) expected) (00000001 datum))"),
        ("atom-pair", "(00000010 (00000001 (left right)))"),
        ("atom-pair-equal-no", "(00100010 (00000010 (00000001 (left right))) (00000001 (0)))"),
        ("atom-pair-equal-yes", "(00100010 (00000010 (00000001 (left right))) (00000001 (1)))"),
        ("structural-quoted-no", "(00000001 (0))"),
        ("historical-cond-probe",
         "(00000111 ((00100010 (00000010 (00000001 (left right))) (00000001 (0))) (00000001 yes)))"),
        ("historical-cond-fallback",
         "(00000111 ((00000010 (00000001 (left right))) (00000001 wrong)) ((00100010 (00000010 (00000001 (left right))) (00000001 (0))) (00000001 yes)))"),
        ("map-onto", "(map-onto (00001000 (x) x) (00000001 (left right)) (00000001 ()))"),
        ("map", "(00110111 (00001000 (x) x) (00000001 (left right)))"),
        ("map-binding-names", "(00110111 (00001000 (b) (00000101 b)) (00000001 ((expected datum))))"),
        ("map-binding-values", "(00110111 (00001000 (b) (00101111 b)) (00000001 ((expected datum))))"),
        ("let", "(10011100 ((expected (00000001 datum))) expected)"),
        ("let-alt-name", "(10011100 ((bound-value (00000001 datum))) bound-value)"),
        ("let-lambda", "(10011100 ((expected (00000001 datum))) ((00001000 (x) x) expected))"),
    ];
    for (name, code) in probes {
        match eval_program(code, &mut session) {
            Ok(value) => eprintln!("LET-PROBE {name}: OK {}", value.value),
            Err(error) => eprintln!("LET-PROBE {name}: ERROR {error}"),
        };
    }
    let witness = include_str!("../../../tests/fixtures/witness-runner.lisp");
    match eval_program(witness, &mut session) {
        Ok(_) => eprintln!("LET-PROBE witness-runner: load OK"),
        Err(error) => eprintln!("LET-PROBE witness-runner: load ERROR {error}"),
    }
    let sample = r#"(witness-expected-outcome (quote ((expr . "canon-empty-list") (expected . "()") (active . t))))"#;
    match eval_program(sample, &mut session) {
        Ok(value) => eprintln!("LET-PROBE expected-outcome: OK {}", value.value),
        Err(error) => eprintln!("LET-PROBE expected-outcome: ERROR {error}"),
    }
    let verify = r#"(witness-verdict (quote ((expr . "canon-empty-list") (expected . "()") (active . t))) (quote (value "()")))"#;
    match eval_program(verify, &mut session) {
        Ok(value) => eprintln!("LET-PROBE witness-verdict: OK {}", value.value),
        Err(error) => eprintln!("LET-PROBE witness-verdict: ERROR {error}"),
    }
}
