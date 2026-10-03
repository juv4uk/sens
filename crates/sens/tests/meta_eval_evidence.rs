use sens::{eval_program, ErrorKind, Session};

fn meta_session() -> Session {
    let mut session = Session::default();
    sens::load_core_library(&mut session).expect("core bootstrap");
    sens::load_meta_evaluator_library(&mut session)
        .expect("meta-eval bootstrap");
    session
}

fn escaped(source: &str) -> String {
    source.replace('\\', "\\\\").replace('"', "\\\"")
}

fn meta_eval(expr: &str) -> String {
    let mut session = meta_session();
    eval_program(
        &format!(r#"(my-eval (read "{}") (quote ()))"#, escaped(expr)),
        &mut session,
    )
    .unwrap_or_else(|error| panic!("host failure while meta-evaluating {expr}: {error}"))
    .value
    .to_string()
}

fn meta_eval_program(program: &str, probe: &str) -> String {
    let mut session = meta_session();
    let source = format!(
        r#"(let ((loaded (my-eval-program (read-all "{}") (quote ()))))
             (my-eval (read "{}") (car loaded)))"#,
        escaped(program),
        escaped(probe),
    );
    eval_program(&source, &mut session)
        .unwrap_or_else(|error| panic!("host failure while probing meta program: {error}"))
        .value
        .to_string()
}

fn meta_program_result(program: &str) -> String {
    let mut session = meta_session();
    eval_program(
        &format!(
            r#"(cdr (my-eval-program (read-all "{}") (quote ())))"#,
            escaped(program)
        ),
        &mut session,
    )
    .unwrap_or_else(|error| panic!("host failure while running meta program: {error}"))
    .value
    .to_string()
}

fn native_value(program: &str) -> String {
    let mut session = Session::default();
    eval_program(program, &mut session)
        .unwrap_or_else(|error| panic!("reference evaluator failed for {program}: {error}"))
        .value
        .to_string()
}

fn native_error_kind(program: &str) -> ErrorKind {
    let mut session = Session::default();
    eval_program(program, &mut session)
        .expect_err("reference program must fail")
        .kind
}

fn meta_error_kind(value: &str) -> Option<&str> {
    let mut tokens = value.trim_start_matches('(').split_whitespace();
    if tokens.next() == Some("error") {
        tokens.next()
    } else {
        None
    }
}

#[test]
fn named_error_pressure_preserves_explicit_reference_to_meta_correspondence() {
    let cases = [
        ("(missing)", ErrorKind::UnknownSymbol, "unbound-symbol"),
        ("((quote missing))", ErrorKind::Type, "not-callable"),
        ("((lambda (x) x))", ErrorKind::Arity, "arity"),
        ("(lambda (x x) x)", ErrorKind::InvalidForm, "invalid-form"),
        ("(lambda (car) car)", ErrorKind::InvalidForm, "invalid-form"),
    ];

    for (source, native_kind, meta_kind) in cases {
        assert_eq!(native_error_kind(source), native_kind, "source: {source}");
        let meta = meta_eval(source);
        assert_eq!(meta_error_kind(&meta), Some(meta_kind), "source: {source}");
    }
}

#[test]
fn bare_unresolved_symbol_has_reference_meta_parity() {
    assert_eq!(native_error_kind("missing"), ErrorKind::UnknownSymbol);
    assert_eq!(
        meta_error_kind(&meta_eval("missing")),
        Some("unbound-symbol"),
        "bare unresolved atom lookup must produce the same named unresolved observation as operator lookup"
    );
}

#[test]
fn application_evaluation_order_preserves_the_first_error() {
    let operator_first = "(missing-operator ((lambda (z) z)))";
    assert_eq!(native_error_kind(operator_first), ErrorKind::UnknownSymbol);
    assert_eq!(
        meta_error_kind(&meta_eval(operator_first)),
        Some("unbound-symbol"),
        "operator resolution must fail before any argument is evaluated"
    );

    let first_argument_first = "((lambda (x y) y) missing-first ((lambda (z) z)))";
    assert_eq!(
        native_error_kind(first_argument_first),
        ErrorKind::UnknownSymbol,
        "reference evaluation must stop at the first argument before reaching the later arity error"
    );
    assert_eq!(
        meta_error_kind(&meta_eval(first_argument_first)),
        Some("unbound-symbol"),
        "meta evaluation must stop at the first argument error instead of evaluating later arguments"
    );
}

#[test]
fn macro_arity_has_reference_meta_parity() {
    let program = "(defmacro one (x) x) (one)";
    assert_eq!(native_error_kind(program), ErrorKind::Arity);

    let meta = meta_program_result(program);
    assert_eq!(
        meta_error_kind(&meta),
        Some("arity"),
        "macro application must preserve its arity failure instead of re-evaluating that error as expansion code"
    );
}

#[test]
fn later_binding_visibility_has_reference_meta_parity() {
    let program = r#"
(def f (lambda () (g)))
(def separator 0)
(def g (lambda () 42))
"#;

    let expected = "42";
    assert_eq!(native_value(&format!("{program} (f)")), expected);
    assert_eq!(meta_eval_program(program, "(f)"), expected);
}

#[test]
fn recursive_group_captures_outer_lexical_environment() {
    let program = r#"
(def offset 7)
(def left
  (lambda (n)
    (cond
      ((eq? n 0) offset)
      (t (right (- n 1))))))
(def right
  (lambda (n)
    (cond
      ((eq? n 0) offset)
      (t (left (- n 1))))))
"#;
    // offset=7, and left/right alternate purely on parity of n down to 0,
    // where both return offset — both probes land on offset regardless of
    // which function is entered first.
    let expected = "7";
    for probe in ["(left 5)", "(right 6)"] {
        assert_eq!(native_value(&format!("{program} {probe}")), expected, "probe: {probe}");
        assert_eq!(meta_eval_program(program, probe), expected, "probe: {probe}");
    }
}

#[test]
fn recursive_group_members_can_create_nested_closures_with_capture() {
    let program = r#"
(def offset 10)
(def make-step
  (lambda (n)
    (cond
      ((eq? n 0) (lambda (x) (+ x offset)))
      (t (bounce (- n 1))))))
(def bounce (lambda (n) (make-step n)))
"#;
    let probe = "((make-step 3) 5)";
    let expected = "15";
    assert_eq!(native_value(&format!("{program} {probe}")), expected);
    assert_eq!(meta_eval_program(program, probe), expected);
}

#[test]
fn ordinary_parameter_shadowing_beats_recursive_group_bindings() {
    let program = r#"
(def call-local (lambda (peer) (peer 5)))
(def peer (lambda (x) (+ x 1)))
"#;
    let probe = "(call-local (lambda (x) (* x 2)))";
    let expected = "10";
    assert_eq!(native_value(&format!("{program} {probe}")), expected);
    assert_eq!(meta_eval_program(program, probe), expected);

    assert!(
        meta_eval_program(program, "call-local").starts_with("(recursive-closure call-local "),
        "a parameter named peer must shadow the top-level peer during dependency analysis"
    );
}

#[test]
fn adjacent_non_recursive_lambda_defs_are_not_false_grouped() {
    let program = r#"
(def inc (lambda (x) (+ x 1)))
(def double (lambda (x) (* x 2)))
"#;
    let result = meta_program_result(program);
    assert!(
        result.starts_with("(recursive-closure double "),
        "independent definitions must remain singleton closures, got {result}"
    );
    assert!(
        !result.starts_with("(recursive-group-closure"),
        "independent definitions must not be represented as a recursive group"
    );
    for (probe, expected) in [("(inc 4)", "5"), ("(double 4)", "8")] {
        assert_eq!(native_value(&format!("{program} {probe}")), expected, "probe: {probe}");
        assert_eq!(meta_eval_program(program, probe), expected, "probe: {probe}");
    }
}

#[test]
fn quoted_group_member_name_is_data_not_a_dependency() {
    let program = r#"
(def mention-peer (lambda () (quote peer)))
(def peer (lambda () 42))
"#;

    assert!(
        meta_eval_program(program, "mention-peer").starts_with("(recursive-closure mention-peer "),
        "a quoted peer symbol must not create a dependency edge"
    );
    assert_eq!(meta_eval_program(program, "(mention-peer)"), "peer");
}

#[test]
fn a_real_recursive_scc_can_skip_an_independent_interleaved_definition() {
    let program = r#"
(def left
  (lambda (n)
    (cond
      ((eq? n 0) t)
      (t (right (- n 1))))))
(def helper (lambda (x) (+ x 100)))
(def right
  (lambda (n)
    (cond
      ((eq? n 0) (quote ()))
      (t (left (- n 1))))))
"#;

    assert!(
        meta_eval_program(program, "left").starts_with("(recursive-group-closure left "),
        "left and right form the recursive SCC"
    );
    assert!(
        meta_eval_program(program, "right").starts_with("(recursive-group-closure right "),
        "left and right form the recursive SCC"
    );
    assert!(
        meta_eval_program(program, "helper").starts_with("(recursive-closure helper "),
        "helper is not in the left/right SCC"
    );

    // left(8)/right(9) both bottom out at left(0)=t along the SCC's shared
    // countdown; helper is a plain +100 outside the SCC.
    for (probe, expected) in [("(left 8)", "t"), ("(right 9)", "t"), ("(helper 5)", "105")] {
        assert_eq!(native_value(&format!("{program} {probe}")), expected, "probe: {probe}");
        assert_eq!(meta_eval_program(program, probe), expected, "probe: {probe}");
    }
}

#[test]
fn malformed_recursive_group_preserves_invalid_form_kind() {
    let program = r#"
(def good (lambda (x) x))
(def bad (lambda (x x) x))
"#;
    assert_eq!(native_error_kind(program), ErrorKind::InvalidForm);
    let meta = meta_program_result(program);
    assert_eq!(meta_error_kind(&meta), Some("invalid-form"));
}
