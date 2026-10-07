use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse_mixed_exact_domain, Session,
};
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load(path: &str, session: &mut Session) {
    let source = fs::read_to_string(repo_root().join(path)).unwrap();
    eval_program(&source, session).unwrap_or_else(|e| panic!("load {path}: {e:?}"));
}

fn load_mixed(path: &str, session: &mut Session) {
    let source = fs::read_to_string(repo_root().join(path)).unwrap();
    let forms = parse_mixed_exact_domain(&source).unwrap();
    eval_parsed_expressions(&forms, session).unwrap_or_else(|e| panic!("load mixed {path}: {e:?}"));
}

#[test]
fn diagnose_native_first_positive_path() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load("lib/machine/layout/pair-x86-64.lisp", &mut session);
    load("lib/machine/operands/x86-64.lisp", &mut session);
    load("lib/machine/lowering/semantic-x86-64.lisp", &mut session);
    load_mixed("lib/machine/dispatch/native-first.lisp", &mut session);

    let let_forms = parse_mixed_exact_domain("(001000 ((x 41)) x)").expect("exact LET parse");
    let let_value = eval_parsed_expressions(&let_forms, &mut session)
        .unwrap_or_else(|e| panic!("exact D6 LET failed: {e:?}"));
    eprintln!("exact-let={}", let_value.value);

    for source in [
        "(x86-as-u64-imm 2)",
        "(x86-u64-imm-value (x86-as-u64-imm 2))",
        "(x86-lower-cons-car-u64-forms 2 3)",
        "(native-first-native-plan (x86-lower-cons-car-u64-forms 2 3) x86-pair-cell-bytes)",
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|e| panic!("{source} failed: {e:?}"));
        eprintln!("{source} => {}", value.value);
    }
}
