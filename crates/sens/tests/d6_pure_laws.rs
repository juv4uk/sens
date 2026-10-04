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
    for value in ["()", "(1)", "(1 2 3 4)", "(5 -1 0 8)"] {
        assert_same(
            &format!("(map (lambda (x) (+ x 1)) (quote {value}))"),
            &format!("(map-onto (lambda (x) (+ x 1)) (quote {value}) (quote ()))"),
        );
        assert_same(
            &format!("(filter (lambda (x) (< x 3)) (quote {value}))"),
            &format!("(filter-onto (lambda (x) (< x 3)) (quote {value}) (quote ()))"),
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


#[test]
fn nth_obeys_indexed_projection_recurrence() {
    for value in ["(a)", "(a b)", "(a b c d)"] {
        assert_same(
            &format!("(nth 0 (quote {value}))"),
            &format!("(car (quote {value}))"),
        );
    }

    let value = "(a b c d)";
    for n in 0..3 {
        assert_same(
            &format!("(nth {} (quote {value}))", n + 1),
            &format!("(nth {n} (cdr (quote {value})))"),
        );
    }
}

#[test]
fn maplist_observes_successive_tails() {
    for value in ["()", "(a)", "(a b c)", "(1 2 3 4)"] {
        assert_same(
            &format!("(maplist (quote {value}) (lambda (tail) (car tail)))"),
            &format!("(quote {value})"),
        );
    }

    assert_same(
        "(maplist (quote (a b c)) (lambda (tail) (length tail)))",
        "(quote (3 2 1))",
    );
    assert_same(
        "(maplist (quote (a b c d)) (lambda (tail) (length tail)))",
        "(quote (4 3 2 1))",
    );
}

#[test]
fn sublis_singleton_generalizes_subst_and_multi_key_is_distinct() {
    for tree in ["a", "(a b a)", "((a) b (c a))"] {
        assert_same(
            &format!("(sublis (quote ((a z))) (quote {tree}))"),
            &format!("(subst (quote z) (quote a) (quote {tree}))"),
        );
    }

    assert_same(
        "(sublis (quote ((a x) (b y))) (quote (a (b c) a)))",
        "(quote (x (y c) x))",
    );
}

#[test]
fn rassoc_is_assoc_under_pair_transposition() {
    let prelude = r#"
        (define d6-transpose-pair
          (lambda (p) (cons (cdr p) (car p))))
        (define d6-transpose-alist
          (lambda (alist) (map d6-transpose-pair alist)))
        (define d6-rassoc
          (lambda (value alist)
            ((lambda (hit) (d6-transpose-pair hit))
             (assoc value (d6-transpose-alist alist)))))
    "#;

    for (value, expected) in [("1", "(a . 1)"), ("2", "(b . 2)"), ("3", "(c . 3)")] {
        assert_same(
            &format!(
                "{prelude} (d6-rassoc {value} (quote ((a . 1) (b . 2) (c . 3))))"
            ),
            &format!("(quote {expected})"),
        );
    }

    assert_same(
        &format!(
            "{prelude} (d6-transpose-alist (d6-transpose-alist (quote ((a . 1) (b . 2)))))"
        ),
        "(quote ((a . 1) (b . 2)))",
    );
}

#[test]
fn acons_is_pair_construction_over_cons() {
    assert_same(
        "(cons (cons (quote k) (quote v)) (quote ((old . 0))))",
        "(quote ((k . v) (old . 0)))",
    );
    assert_same(
        "(assoc (quote k) (cons (cons (quote k) (quote v)) (quote ((old . 0)))))",
        "(quote (k . v))",
    );
}

#[test]
fn add1_sub1_neg_abs_and_remainder_obey_lower_domain_laws() {
    for x in ["-9", "-1", "0", "1", "7", "42"] {
        assert_same(&format!("(- (+ {x} 1) 1)"), x);
        assert_same(&format!("(+ (- {x} 1) 1)"), x);
        assert_same(&format!("(- 0 (- 0 {x}))"), x);
        assert_same(&format!("(abs (- 0 {x}))"), &format!("(abs {x})"));
        assert_same(&format!("(abs (abs {x}))"), &format!("(abs {x})"));
    }

    for (a, b) in [("17", "5"), ("42", "8"), ("100", "9"), ("7", "7")] {
        assert_same(
            &format!("(mod {a} {b})"),
            &format!("(- {a} (* {b} (quotient {a} {b})))"),
        );
    }
}

#[test]
fn expt_is_repeated_multiplication_over_nonnegative_integers() {
    let prelude = r#"
        (define d6-expt
          (lambda (base exponent)
            (cond
              ((= exponent 0) 1)
              (t (* base (d6-expt base (- exponent 1)))))))
    "#;

    for x in ["-3", "0", "2", "7"] {
        assert_same(&format!("{prelude} (d6-expt {x} 0)"), "1");
        assert_same(&format!("{prelude} (d6-expt {x} 1)"), x);
    }

    for (x, m, n) in [("2", "2", "3"), ("3", "1", "4"), ("-2", "2", "2")] {
        assert_same(
            &format!("{prelude} (d6-expt {x} (+ {m} {n}))"),
            &format!("{prelude} (* (d6-expt {x} {m}) (d6-expt {x} {n}))"),
        );
    }
}

#[test]
fn gcd_is_euclidean_fold_over_remainder() {
    let prelude = r#"
        (define d6-gcd
          (lambda (a b)
            (cond
              ((= b 0) (abs a))
              (t (d6-gcd b (mod a b))))))
    "#;

    for (a, b, expected) in [
        ("54", "24", "6"),
        ("24", "54", "6"),
        ("17", "5", "1"),
        ("42", "14", "14"),
    ] {
        assert_same(&format!("{prelude} (d6-gcd {a} {b})"), expected);
    }

    for (a, b) in [("54", "24"), ("17", "5"), ("42", "14")] {
        assert_same(
            &format!("{prelude} (d6-gcd {a} {b})"),
            &format!("{prelude} (d6-gcd {b} (mod {a} {b}))"),
        );
    }
}

#[test]
fn curry2_is_prefix_application_via_lexical_closure() {
    let prelude = r#"
        (define d6-curry2
          (lambda (f a)
            (lambda (b) (f a b))))
    "#;

    assert_same(
        &format!("{prelude} ((d6-curry2 (lambda (x y) (+ x y)) 7) 5)"),
        "12",
    );
    assert_same(
        &format!("{prelude} ((d6-curry2 (lambda (x y) (* x y)) 6) 7)"),
        "42",
    );
}


#[test]
fn recip_is_exact_q_multiplicative_inverse() {
    for x in ["2", "-3", "1/2", "5/7"] {
        assert_same(&format!("(* {x} (/ 1 {x}))"), "1");
        assert_same(&format!("(/ 1 (/ 1 {x}))"), x);
    }
}


#[test]
fn reduce_respects_append_partitioning() {
    for (xs, ys) in [
        ("()", "()"),
        ("(1 2)", "(3 4)"),
        ("(5)", "(6 7 8)"),
    ] {
        assert_same(
            &format!(
                "(reduce (lambda (acc x) (+ acc x)) 0 (append (quote {xs}) (quote {ys})))"
            ),
            &format!(
                "(reduce (lambda (acc x) (+ acc x)) (reduce (lambda (acc x) (+ acc x)) 0 (quote {xs})) (quote {ys}))"
            ),
        );
    }
}

#[test]
fn compose_is_observationally_associative() {
    let prelude = r#"
        (define d6-compose
          (lambda (f g)
            (lambda (x) (f (g x)))))
    "#;

    for x in ["-2", "0", "5"] {
        assert_same(
            &format!(
                "{prelude}
                 ((d6-compose
                    (lambda (x) (+ x 1))
                    (d6-compose
                      (lambda (x) (* x 2))
                      (lambda (x) (- x 3))))
                  {x})"
            ),
            &format!(
                "{prelude}
                 ((d6-compose
                    (d6-compose
                      (lambda (x) (+ x 1))
                      (lambda (x) (* x 2)))
                    (lambda (x) (- x 3)))
                  {x})"
            ),
        );
    }
}

#[test]
fn flip_is_an_involution_on_binary_application() {
    let prelude = r#"
        (define d6-flip
          (lambda (f)
            (lambda (a b) (f b a))))
    "#;

    assert_same(
        &format!("{prelude} ((d6-flip (lambda (a b) (- a b))) 2 5)"),
        "3",
    );

    for (a, b) in [("2", "5"), ("7", "3"), ("-1", "4")] {
        assert_same(
            &format!(
                "{prelude} ((d6-flip (d6-flip (lambda (x y) (- x y)))) {a} {b})"
            ),
            &format!("(- {a} {b})"),
        );
    }
}

#[test]
fn take_drop_form_a_lossless_list_split() {
    let prelude = r#"
        (define d6-take
          (lambda (n xs)
            (cond
              ((= n 0) (quote ()))
              ((= (length xs) 0) (quote ()))
              (t (cons (car xs) (d6-take (- n 1) (cdr xs)))))))
        (define d6-drop
          (lambda (n xs)
            (cond
              ((= n 0) xs)
              ((= (length xs) 0) (quote ()))
              (t (d6-drop (- n 1) (cdr xs))))))
    "#;

    let xs = "(a b c d)";
    for n in 0..=6 {
        assert_same(
            &format!(
                "{prelude} (append (d6-take {n} (quote {xs})) (d6-drop {n} (quote {xs})))"
            ),
            &format!("(quote {xs})"),
        );
    }

    assert_same(
        &format!("{prelude} (length (d6-take 3 (quote {xs})))"),
        "3",
    );
    assert_same(
        &format!("{prelude} (d6-drop 0 (quote {xs}))"),
        &format!("(quote {xs})"),
    );
}


#[test]
fn while_and_do_are_tail_iteration_laws() {
    let prelude = r#"
        (define d6-while
          (lambda (pred step state)
            (cond
              ((pred state) (d6-while pred step (step state)))
              (t state))))
        (define d6-do
          (lambda (step done result state)
            (cond
              ((done state) (result state))
              (t (d6-do step done result (step state))))))
    "#;

    assert_same(
        &format!(
            "{prelude} (d6-while (lambda (x) (< x 5)) (lambda (x) (+ x 1)) 0)"
        ),
        "5",
    );

    assert_same(
        &format!(
            "{prelude}
             (d6-do
               (lambda (x) (+ x 2))
               (lambda (x) (= x 10))
               (lambda (x) (* x 3))
               0)"
        ),
        "30",
    );
}

#[test]
fn zip_unzip_are_product_inverses_on_equal_length_lists() {
    let prelude = r#"
        (define d6-zip
          (lambda (xs ys)
            (cond
              ((= (length xs) 0) (quote ()))
              ((= (length ys) 0) (quote ()))
              (t
               (cons
                 (list (car xs) (car ys))
                 (d6-zip (cdr xs) (cdr ys)))))))
        (define d6-unzip
          (lambda (pairs)
            (list
              (map (lambda (p) (car p)) pairs)
              (map (lambda (p) (car (cdr p))) pairs))))
    "#;

    for (xs, ys) in [
        ("()", "()"),
        ("(a)", "(1)"),
        ("(a b c)", "(1 2 3)"),
    ] {
        assert_same(
            &format!("{prelude} (d6-unzip (d6-zip (quote {xs}) (quote {ys})))"),
            &format!("(list (quote {xs}) (quote {ys}))"),
        );
    }
}

#[test]
fn scan_exposes_prefix_reductions_and_ends_at_reduce() {
    let prelude = r#"
        (define d6-scan
          (lambda (f acc xs)
            (cond
              ((= (length xs) 0) (quote ()))
              (t
               ((lambda (next)
                  (cons next (d6-scan f next (cdr xs))))
                (f acc (car xs)))))))
    "#;

    assert_same(
        &format!(
            "{prelude} (d6-scan (lambda (acc x) (+ acc x)) 0 (quote (1 2 3 4)))"
        ),
        "(quote (1 3 6 10))",
    );

    for xs in ["(1)", "(1 2)", "(1 2 3 4)", "(5 -2 8)"] {
        assert_same(
            &format!(
                "{prelude}
                 (car
                   (reverse
                     (d6-scan
                       (lambda (acc x) (+ acc x))
                       0
                       (quote {xs}))))"
            ),
            &format!(
                "(reduce (lambda (acc x) (+ acc x)) 0 (quote {xs}))"
            ),
        );
    }
}

#[test]
fn any_all_form_a_predicate_dual_pair() {
    let prelude = r#"
        (define d6-any
          (lambda (pred xs)
            (cond
              ((= (length xs) 0) 0)
              ((pred (car xs)) 1)
              (t (d6-any pred (cdr xs))))))
        (define d6-all
          (lambda (pred xs)
            (cond
              ((= (length xs) 0) 1)
              ((pred (car xs)) (d6-all pred (cdr xs)))
              (t 0))))
    "#;

    for xs in ["()", "(1)", "(1 2 3)", "(1 0 3)", "(-1 2 3)"] {
        assert_same(
            &format!(
                "{prelude}
                 (+
                   (d6-all (lambda (x) (> x 0)) (quote {xs}))
                   (d6-any (lambda (x) (<= x 0)) (quote {xs})))"
            ),
            "1",
        );
    }

    assert_same(
        &format!("{prelude} (d6-any (lambda (x) (= x 2)) (quote (1 2 3)))"),
        "1",
    );
    assert_same(
        &format!("{prelude} (d6-all (lambda (x) (> x 0)) (quote (1 2 3)))"),
        "1",
    );
}


#[test]
fn integerp_rationalp_derive_from_canonical_exact_q_wire() {
    let prelude = r##"
        (define d6-wire-denominator-one?
          (lambda (text)
            (cond
              ((string-empty? text) (quote ()))
              ((eq (string-first text) "/")
               ((lambda (rest)
                  (cond
                    ((string-empty? rest) (quote ()))
                    ((eq (string-first rest) "1")
                     (cond
                       ((string-empty? (string-rest rest)) t)
                       (t (quote ()))))
                    (t (quote ()))))
                (string-rest text)))
              (t (d6-wire-denominator-one? (string-rest text))))))
        (define d6-rationalp
          (lambda (value)
            (string-prefix? "#q2:" (write-to-string value))))
        (define d6-integerp
          (lambda (value)
            (cond
              ((d6-rationalp value)
               (d6-wire-denominator-one? (write-to-string value)))
              (t (quote ())))))
    "##;

    for x in ["0", "1", "-7", "42", "3.00"] {
        assert_same(&format!("{prelude} (d6-rationalp {x})"), "t");
        assert_same(&format!("{prelude} (d6-integerp {x})"), "t");
    }

    for x in ["1/2", "-5/4", "10/20"] {
        assert_same(&format!("{prelude} (d6-rationalp {x})"), "t");
        assert_same(&format!("{prelude} (d6-integerp {x})"), "(quote ())");
    }

    for x in ["(quote alpha)", "\\"text\\"", "(quote (a b))"] {
        assert_same(&format!("{prelude} (d6-rationalp {x})"), "(quote ())");
        assert_same(&format!("{prelude} (d6-integerp {x})"), "(quote ())");
    }
}
