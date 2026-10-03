use sens::{eval_program, load_core_library, Session};

fn eval(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("{source}: {error}"))
        .value
        .to_string()
}

#[test]
fn existing_selector_surfaces_execute_after_d4_domain_cutover() {
    assert_eq!(eval("(caar '((11 12) 13))"), "11");
    assert_eq!(eval("(cadr '(11 12 13))"), "12");
    assert_eq!(eval("(cddr '(11 12 13))"), "(13)");
}
