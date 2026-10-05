use sens::{eval_program, ErrorKind, Session};

fn eval(source: &str) -> String {
    let mut session = Session::default();
    eval_program(source, &mut session)
        .expect("adversarial canonical program should evaluate")
        .value
        .to_string()
}

fn invalid_binding(source: &str) {
    let mut session = Session::default();
    sens::load_core_library(&mut session).expect("core bootstrap for binder adversary");
    let error = eval_program(source, &mut session)
        .expect_err("Contract 6.0 must reject Canon binding attempts");
    assert_eq!(error.kind, ErrorKind::InvalidForm, "source: {source}");
    assert!(
        error.message.contains("canonical name is immutable")
            || error.message.contains("surface routes to immutable function SID"),
        "unexpected error for {source}: {}",
        error.message
    );
}

#[test]
fn quote_surface_suppresses_evaluation_of_unknown_code() {
    assert_eq!(
        eval("(як-є (цієї-функції-не-існує 1 2))"),
        "(цієї-функції-не-існує 1 2)"
    );
    assert_eq!(
        eval("(svarūpa (ayam-na-vidyate 1 2))"),
        "(ayam-na-vidyate 1 2)"
    );
}

#[test]
fn cond_surface_stops_at_the_first_true_clause() {
    assert_eq!(
        eval("(за-умовою ((атом? ()) (як-є перша)) ((цієї-функції-не-існує) (як-є друга)))"),
        "перша"
    );
    assert_eq!(
        eval("(anukrama ((aṇu ()) (svarūpa prathama)) ((ayam-na-vidyate) (svarūpa dvitīya)))"),
        "prathama"
    );
}

#[test]
fn rest_passes_the_triple_cons_structure_test() {
    assert_eq!(eval("(решта (як-є (кіт . 42)))"), "42");
    assert_eq!(eval("(решта (як-є (1 2 3)))"), "(2 3)");
    assert_eq!(eval("(решта (як-є (1 2 . 3)))"), "(2 . 3)");

    assert_eq!(eval("(śeṣa (svarūpa (phalam . 42)))"), "42");
    assert_eq!(eval("(śeṣa (svarūpa (1 2 3)))"), "(2 3)");
    assert_eq!(eval("(śeṣa (svarūpa (1 2 . 3)))"), "(2 . 3)");
}

#[test]
fn car_and_cdr_on_canon_zero_fail_named_not_panic() {
    for source in ["(перше ())", "(решта ())", "(ādi ())", "(śeṣa ())"] {
        let mut session = Session::default();
        let error = eval_program(source, &mut session).expect_err("projection on () must fail");
        assert_eq!(error.kind, ErrorKind::Type, "source: {source}");
    }
}

#[test]
fn every_human_surface_rejects_canon_redefinition() {
    for source in [
        "(def car 42)",
        "(def перше 42)",
        "(def ādi 42)",
        "(def atom? 42)",
        "(def атом? 42)",
        "(def aṇu 42)",
        "(def quote 42)",
        "(def як-є 42)",
        "(def svarūpa 42)",
        "(def cond 42)",
        "(def за-умовою 42)",
        "(def anukrama 42)",
    ] {
        invalid_binding(source);
    }
}

#[test]
fn every_binder_shape_rejects_canon_names() {
    for source in [
        "(lambda (car) car)",
        "(lambda (перше) перше)",
        "(lambda (ādi) ādi)",
        "(lambda atom? atom?)",
        "(lambda (x . решта) x)",
        "(let ((car 42)) car)",
        "(let* ((перше 42)) перше)",
    ] {
        invalid_binding(source);
    }
}

#[test]
fn macro_expanded_canonical_binder_keeps_immutability_diagnostic() {
    let mut session = Session::default();
    sens::load_core_library(&mut session).expect("core bootstrap for binder regression");
    let error = eval_program("(let ((car 42)) car)", &mut session)
        .expect_err("canonical surface must remain immutable through macro expansion");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
    assert!(
        error.message.contains("canonical name is immutable")
            || error.message.contains("surface routes to immutable function SID"),
        "unexpected binder diagnostic: {}",
        error.message
    );
    assert!(
        !error.message.contains("lambda parameter must be a symbol"),
        "domain lowering must not erase the immutability reason: {}",
        error.message
    );
}

#[test]
fn ordinary_nonregistry_values_remain_lexical() {
    assert_eq!(
        eval("(def local-add (lambda (x y) (як-є локально))) (local-add 1 2)"),
        "локально"
    );
    assert_eq!(
        eval("(def local-map (lambda args (svarūpa sthānika))) (local-map 1 2)"),
        "sthānika"
    );
}
