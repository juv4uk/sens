#![cfg(all(any(target_os = "linux", target_os = "windows"), target_arch = "x86_64"))]

use my_lisp::{eval_program, load_core_library, Session};
use my_lisp_host::install;
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_lisp_file(path: &str, session: &mut Session) {
    let path = repo_root().join(path);
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{} must load as ordinary my-lisp: {error}", path.display()));
}

#[test]
fn bounded_eq_cond_native_execution_matches_lisp_reference_in_both_directions() {
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before #196 native COND witness");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);

    let mut references = Vec::new();

    for (left, right) in [(2_u64, 2_u64), (2_u64, 3_u64)] {
        let reference_source = format!("(cond ((eq? {left} {right}) 111) (t 222))");
        let reference = eval_program(&reference_source, &mut session)
            .expect("Lisp COND reference must evaluate")
            .value;

        let native_source = format!(
            "(x86-call-admitted-u64 (x86-lower-eq-cond-u64-forms {left} {right} 111 222) 0)"
        );
        let native = eval_program(&native_source, &mut session)
            .expect("admitted bounded COND lowering must execute on the native CPU")
            .value;

        assert_eq!(
            native, reference,
            "native CMP+JNZ control flow must preserve the Lisp-owned EQ+COND result for {left} and {right}"
        );
        references.push(reference);
    }

    assert_ne!(
        references[0], references[1],
        "the two Lisp-owned reference cases must exercise different control-flow outcomes"
    );
}
