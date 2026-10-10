#![cfg(all(target_os = "linux", target_arch = "x86_64"))]

use sens::{eval_program, load_core_library, Session};
use sens_host::install;
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_lisp_file(path: &str, session: &mut Session) {
    let full_path = repo_root().join(path);
    let source = fs::read_to_string(&full_path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", full_path.display()));
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{} must load: {error}", full_path.display()));
}

#[test]
fn diagnose_native_eq_cond_callable_stages() {
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("Core4 bootstrap");

    for path in [
        "lib/machine/encoding/x86-64.lisp",
        "lib/machine/admission/x86-64.lisp",
        "lib/machine/lowering/semantic-x86-64.lisp",
    ] {
        load_lisp_file(path, &mut session);
    }

    let probes = [
        ("exact-integer", "(x86-admission-exact-integer? 2)"),
        ("wire-denominator", "(x86-admission-wire-denominator-one? \"4/1\")"),
        ("range-guard", "(x86-admission-within-inclusive-integer-range? 2 0 255)"),
        ("order-guard", "(x86-current-d5-order-i63-safe? 2 3)"),
        ("lower-order", "(x86-lower-order-i64-forms 5 26 2 3)"),
        ("eq-cond-forms", "(x86-lower-eq-cond-u64-forms 2 2 111 222)"),
        ("admission", "(x86-admitted-program? (x86-lower-eq-cond-u64-forms 2 2 111 222))"),
        ("encoding", "(x86-encode-admitted-program (x86-lower-eq-cond-u64-forms 2 2 111 222))"),
        ("native-call", "(x86-call-admitted-u64 (x86-lower-eq-cond-u64-forms 2 2 111 222) 0)"),
    ];

    let mut report = Vec::new();
    for (name, source) in probes {
        match eval_program(source, &mut session) {
            Ok(result) => report.push(format!("STAGE PASS {name}: {:?}", result.value)),
            Err(error) => report.push(format!(
                "STAGE BLOCKED {name}: kind={:?} span={}..{} message={}",
                error.kind, error.span.start, error.span.end, error.message
            )),
        }
    }

    panic!(
        "NATIVE-CALLABILITY-STAGE-PROBE (diagnostic-only; expected red):\n{}",
        report.join("\n")
    );
}
