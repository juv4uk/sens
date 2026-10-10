#![cfg(all(any(target_os = "linux", target_os = "windows"), target_arch = "x86_64"))]

use sens::{eval_parsed_expressions, parse_mixed_exact_domain, eval_program, load_core_library, Exactness, Session, Value};
use sens_host::install;
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_lisp_file(path: &str, session: &mut Session) {
    assert!(
        path.starts_with("lib/machine/"),
        "mixed exact-domain reader is reserved for machine-source fixtures: {path}"
    );
    let file_path = repo_root().join(path);
    let source = fs::read_to_string(&file_path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", file_path.display()));
    let expressions = parse_mixed_exact_domain(&source)
        .unwrap_or_else(|error| panic!("{path} must parse as mixed exact-domain machine source: {error}"));
    eval_parsed_expressions(&expressions, session)
        .unwrap_or_else(|error| panic!("{path} must load through the mixed exact-domain machine reader: {error}"));
}

#[test]
fn bounded_eq_cond_native_execution_follows_generated_cmp_jnz_branches() {
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before #196 native branch witness");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);

    // This is a machine-mechanism witness only. The lowering below explicitly
    // emits CMP + JNZ with two concrete u64 branch payloads. SENS EQ/COND
    // semantics are owned by the language contracts and Lisp/SENS witnesses,
    // not reconstructed here from a compatibility evaluator.
    for (left, right, expected_branch_value) in [
        (2_u64, 2_u64, 111_u64),
        (2_u64, 3_u64, 222_u64),
    ] {
        let native_source = format!(
            "(x86-call-admitted-u64 (x86-lower-eq-cond-u64-forms {left} {right} 111 222) 0)"
        );
        let native = eval_program(&native_source, &mut session)
            .expect("admitted bounded CMP+JNZ lowering must execute on the native CPU")
            .value;

        assert_eq!(
            native,
            Value::Number(expected_branch_value as f64, Exactness::Exact),
            "native CMP+JNZ must execute the generated machine branch for {left} and {right}"
        );
    }
}
