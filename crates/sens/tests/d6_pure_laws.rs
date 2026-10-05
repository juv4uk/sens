//! #3339 — pure D6 law witnesses over the current D1-D5 foundation.
//! Research-only: no D6 coordinate or residency authority is created here.

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
fn length_is_zero_accumulator_specialization() {
    for value in ["()", "(a)", "(a b c)", "((a b) c (d e))"] {
        assert_same(
            &format!("(length (quote {value}))"),
            &format!("(length-onto (quote {value}) 0)"),
        );
    }
}

#[test]
fn map_and_filter_are_empty_accumulator_specializations() {
    for (value, expected_filter) in [
        ("()", "()"),
        ("(1)", "(1)"),
        ("(1 2)", "(1 2)"),
        ("(1 2 3 4)", "(1 2)"),
        ("(5 -1 0 8)", "(-1 0)"),
        ("(5 8)", "()"),
    ] {
        assert_same(
            &format!("(map (lambda (x) (+ x 1)) (quote {value}))"),
            &format!("(map-onto (lambda (x) (+ x 1)) (quote {value}) (quote ()))"),
        );

        let filter = format!("(filter (lambda (x) (< x 3)) (quote {value}))");
        let filter_onto =
            format!("(filter-onto (lambda (x) (< x 3)) (quote {value}) (quote ()))");
        assert_same(&filter, &filter_onto);
        assert_eq!(
            run(&filter).unwrap_or_else(|e| panic!("{filter}: {e}")),
            expected_filter,
            "FILTER must consume exact predicate control for {value}"
        );
    }
}

#[test]
fn min_max_list_are_order_dual_and_permutation_invariant() {
    for value in ["(5 -2 8 1)", "(3 3 3)", "(-9 -1 -4)", "(0 7 -7 2)"] {
        assert_same(
            &format!("(min-list (quote {value}))"),
            &format!("(min-list (reverse (quote {value})))"),
        );
        assert_same(
            &format!("(max-list (quote {value}))"),
            &format!("(max-list (reverse (quote {value})))"),
        );
        assert_same(
            &format!("(min-list (map (lambda (x) (- 0 x)) (quote {value})))"),
            &format!("(- 0 (max-list (quote {value})))"),
        );
        assert_same(
            &format!("(max-list (map (lambda (x) (- 0 x)) (quote {value})))"),
            &format!("(- 0 (min-list (quote {value})))"),
        );
    }
}

#[test]
fn print_representative_results() {
    for source in [
        "(length-onto (quote (a b c)) 0)",
        "(map-onto (lambda (x) (+ x 1)) (quote (1 2 3)) (quote ()))",
        "(filter-onto (lambda (x) (< x 3)) (quote (1 2 3 4)) (quote ()))",
        "(min-list (quote (5 -2 8 1)))",
        "(max-list (quote (5 -2 8 1)))",
    ] {
        println!("D6-PURE-LAW source={source:?} result={:?}", run(source));
    }
}
