//! #3293 — REVERSE / REVERSE-ONTO / APPEND local algebra.
//! Research-only until D5 owner ratification.

use sens::{eval_program, load_core_library, Session};

fn run(source: &str) -> Result<String, String> {
    let mut session = Session::default();
    load_core_library(&mut session).map_err(|e| format!("load-core: {e:?}"))?;
    eval_program(source, &mut session)
        .map(|o| o.value.to_string())
        .map_err(|e| format!("{:?}: {}", e.kind, e.message))
}

fn assert_same(a: &str, b: &str) {
    let left = run(a).unwrap_or_else(|e| panic!("{a}: {e}"));
    let right = run(b).unwrap_or_else(|e| panic!("{b}: {e}"));
    assert_eq!(left, right, "{a} != {b}");
}

#[test]
fn reverse_is_closed_reverse_onto() {
    for value in ["()", "(a)", "(a b c)", "((a b) c (d e))"] {
        assert_same(
            &format!("(reverse (quote {value}))"),
            &format!("(reverse-onto (quote {value}) (quote ()))"),
        );
    }
}

#[test]
fn reverse_onto_is_append_of_reverse() {
    for (x,y) in [
        ("()", "()"),
        ("(a)", "(z)"),
        ("(a b)", "(c d)"),
        ("((a b) c)", "(d)"),
        ("(a b)", "(c . d)"),
    ] {
        assert_same(
            &format!("(reverse-onto (quote {x}) (quote {y}))"),
            &format!("(append (reverse (quote {x})) (quote {y}))"),
        );
    }
}

#[test]
fn append_is_generated_by_reverse_and_reverse_onto() {
    for (x,y) in [
        ("()", "()"),
        ("()", "(a b)"),
        ("(a)", "()"),
        ("(a b)", "(c d)"),
        ("((a b) c)", "(d)"),
        ("(a b)", "(c . d)"),
    ] {
        assert_same(
            &format!("(append (quote {x}) (quote {y}))"),
            &format!("(reverse-onto (reverse (quote {x})) (quote {y}))"),
        );
    }
}

#[test]
fn print_examples() {
    for source in [
        "(reverse-onto (quote ()) (quote (z)))",
        "(reverse-onto (quote (a b c)) (quote ()))",
        "(reverse-onto (quote (a b)) (quote (c d)))",
        "(reverse-onto (quote (a b)) (quote (c . d)))",
    ] {
        println!("REVERSE-ONTO-LAW source={source:?} result={:?}", run(source));
    }
}
