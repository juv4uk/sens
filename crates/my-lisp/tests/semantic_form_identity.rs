use my_lisp::{eval_program, parse, ErrorKind, Expr, ExprKind, Session};

const MACRO_LIBRARY: &str = include_str!("../../../lib/macro.lisp");

fn walk_symbols(expression: &Expr, symbols: &mut Vec<String>) {
    match &expression.kind {
        ExprKind::Symbol(symbol) => symbols.push(symbol.to_string()),
        ExprKind::List(items) => {
            for item in items.iter() {
                walk_symbols(item, symbols);
            }
        }
        ExprKind::Pair(head, tail) => {
            walk_symbols(head, symbols);
            walk_symbols(tail, symbols);
        }
        _ => {}
    }
}

#[test]
fn existing_vertical_bar_atoms_remain_reader_compatible() {
    let parsed = parse("a|b").expect("vertical bar inside an atom must remain ordinary syntax");
    assert!(matches!(
        &parsed[0].kind,
        ExprKind::Symbol(value) if value.as_ref() == "a|b"
    ));
}

#[test]
fn byte_sid_symbols_do_not_execute_as_surface_spellings() {
    let mut session = Session::default();
    let error = eval_program(
        "((eval (cons (string->symbol \"0010\") (quote ((x) x)))) 41)",
        &mut session,
    )
    .expect_err("bare SID text is metadata and deliberately not executable spelling");
    assert_eq!(error.kind, ErrorKind::UnknownSymbol);
}

#[test]
fn macro_library_uses_admitted_source_spellings_for_necessary_forms() {
    let parsed = parse(MACRO_LIBRARY).expect("embedded macro library should parse");
    let mut symbols = Vec::new();
    for expression in &parsed {
        walk_symbols(expression, &mut symbols);
    }

    assert!(symbols.iter().any(|symbol| symbol == "lambda"));
    assert!(symbols.iter().any(|symbol| symbol == "define"));
}

#[test]
fn defmacro_preserves_minimum_arity_failure_class() {
    for source in ["(defmacro)", "(defmacro only-a-name)"] {
        let error = eval_program(source, &mut Session::default())
            .expect_err("defmacro below its two-argument minimum must fail named");
        assert_eq!(error.kind, ErrorKind::Arity, "source: {source}");
    }
}

#[test]
fn defmacro_builds_and_runs_after_numeric_identity_lowering() {
    let mut session = Session::default();
    let result = eval_program(
        "(визначити-макрос identity-stage-e (x) x) (identity-stage-e 73)",
        &mut session,
    )
    .expect("direct defmacro peer should survive numeric-form lowering");
    assert_eq!(result.value.to_string(), "73");
}
