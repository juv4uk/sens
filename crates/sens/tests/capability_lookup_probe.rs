use sens::{eval_program, load_core_library, Session};
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn probe(name: &str, source: &str, session: &mut Session) {
    let outcome = eval_program(source, session)
        .map(|result| result.value.to_string())
        .unwrap_or_else(|error| format!("ERROR {error:?}"));
    println!("CAPABILITY_LOOKUP_PROBE {name}: {outcome}");
}

#[test]
fn report_first_non_callable_capability_lookup_stage() {
    let mut session = Session::default();
    if let Err(error) = load_core_library(&mut session) {
        println!("CAPABILITY_LOOKUP_PROBE core-load: ERROR {error:?}");
        return;
    }
    let axis_path = repo_root().join("lib/machine/capability-axis.lisp");
    let axis = fs::read_to_string(&axis_path).expect("capability axis source");
    if let Err(error) = eval_program(&axis, &mut session) {
        println!("CAPABILITY_LOOKUP_PROBE axis-load: ERROR {error:?}");
        return;
    }
    println!("CAPABILITY_LOOKUP_PROBE axis-load: PASS");

    for (name, source) in [
        ("ukr-atom", "(атом? ())"),
        ("ukr-eq", "(тотожне? 5 5)"),
        ("ukr-car", "(перше (сполучити 5 10))"),
        ("ukr-cdr", "(решта (сполучити 5 10))"),
        ("eng-atom", "(atom? ())"),
        ("eng-eq", "(eq? 5 5)"),
        ("eng-car", "(car (cons 5 10))"),
        ("eng-cdr", "(cdr (cons 5 10))"),
        ("eng-cond", "(cond ((eq? 5 5) 1) ((atom? ()) 0))"),
        ("legacy-let", "(10011100 ((row 42)) row)"),
        ("core-let-star", "(let* ((row 42)) row)"),
        ("find-d3-row", "(machine-capability-find-domain-row 3 5 machine-capability-axis-v3)"),
        ("lookup-d3", "(machine-capabilities-for-domain 3 5)"),
        ("find-d5-row", "(machine-capability-find-domain-row 5 10 machine-capability-axis-v3)"),
        ("lookup-d5", "(machine-capabilities-for-domain 5 10)"),
    ] {
        probe(name, source, &mut session);
    }
}
