use sens::{
    eval_parsed_expressions, load_core_library, load_process_library, parse_mixed_exact_domain,
    Session,
};
use std::fs;

#[test]
fn linter_bootstrap_executes_over_exact_domain_data() {
    let mut session = Session::default();

    load_core_library(&mut session).expect("Core4 bootstrap");
    load_process_library(&mut session).expect("process and TCP Zig/T5M bootstrap");
    let linter_src = fs::read_to_string("../../lib/linter.lisp").unwrap();
    // Load the actual Ukrainian linter source through exact domain identities.
    let linter_forms = parse_mixed_exact_domain(&linter_src)
        .expect("linter source resolves through the current ratified ladder");
    eval_parsed_expressions(&linter_forms, &mut session).expect("load exact-domain linter");

    let probe = parse_mixed_exact_domain("(аналіз-розмір (як-є (визначити (функція (ікс) ікс))))")
        .expect("probe uses Ukrainian source names and a quoted D3 tree");
    // Rust перевіряє лише механічне виконання; тип мовного результату визначає SENS.
    let _ = eval_parsed_expressions(&probe, &mut session).expect("execute Lisp linter");
}
