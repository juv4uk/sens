//! Д11: реальні композиції множин, кратностей, стійкого поділу,
//! оберненої ротації та лінійного паліндрому — без нових opcode.
//! Семантичні свідки виконує SENS через eval_program, Rust лише вимагає D1.
//! Кожний перевірений позитив має адресний негативний контрприклад.

use sens::{eval_program, load_core_library, Session};

fn with_source(source: &str) -> Session {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити чинне ядро SENS");
    eval_program(source, &mut session).expect("виконати нативні визначення SENS");
    session
}

fn witness(session: &mut Session, family: &str, cases: &[(&str, &str, bool)]) {
    for (id, program, expected) in cases {
        let actual = eval_program(program, session)
            .unwrap_or_else(|error| {
                panic!(
                    "test_id=D11-LAW-{family}-{id} layer=SENS input={program} expected=D1:{expected} actual_error={error}"
                )
            })
            .value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(*expected),
            "test_id=D11-LAW-{family}-{id} layer=SENS input={program} expected=D1:{expected} actual={actual}"
        );
    }
}

#[test]
fn d11_stable_symmetric_difference_keeps_nonshared_multiplicities_and_order() {
    let mut session = with_source(include_str!(
        "../../../lib/list-stable-symmetric-difference-general.lisp"
    ));
    witness(&mut session, "SYMDIFF", &[
        ("nil", r#"(однакові? (симетрична-різниця-атомів (як-є ()) (як-є ())) (як-є ()))"#, true),
        ("left", r#"(однакові? (симетрична-різниця-атомів (як-є (а а б)) (як-є ())) (як-є (а а б)))"#, true),
        ("right", r#"(однакові? (симетрична-різниця-атомів (як-є ()) (як-є (а б б))) (як-є (а б б)))"#, true),
        ("disjoint", r#"(однакові? (симетрична-різниця-атомів (як-є (а б)) (як-є (в г))) (як-є (а б в г)))"#, true),
        ("shared", r#"(однакові? (симетрична-різниця-атомів (як-є (а а б в)) (як-є (б г))) (як-є (а а в г)))"#, true),
        ("both-shared", r#"(однакові? (симетрична-різниця-атомів (як-є (а а б)) (як-є (б а))) (як-є ()))"#, true),
        ("reject-multiset", r#"(однакові? (симетрична-різниця-атомів (як-є (а а)) (як-є (а))) (як-є (а)))"#, false),
        ("reject-union", r#"(однакові? (симетрична-різниця-атомів (як-є (а б)) (як-є (б в))) (як-є (а б в)))"#, false),
    ]);
}

#[test]
fn d11_stable_intersection_retains_left_multiplicity_not_right_counts() {
    let mut session = with_source(include_str!(
        "../../../lib/list-stable-intersection-general.lisp"
    ));
    witness(&mut session, "STABLE-INTERSECTION", &[
        ("empty", r#"(однакові? (сталий-перетин-атомів (як-є ()) (як-є (а))) (як-є ()))"#, true),
        ("no-right", r#"(однакові? (сталий-перетин-атомів (як-є (а б)) (як-є ())) (як-є ()))"#, true),
        ("disjoint", r#"(однакові? (сталий-перетин-атомів (як-є (а б)) (як-є (в г))) (як-є ()))"#, true),
        ("ordered", r#"(однакові? (сталий-перетин-атомів (як-є (а б а в б)) (як-є (а б))) (як-є (а б а б)))"#, true),
        ("left-repeated", r#"(однакові? (сталий-перетин-атомів (як-є (а а а)) (як-є (а))) (як-є (а а а)))"#, true),
        ("right-repeated", r#"(однакові? (сталий-перетин-атомів (як-є (а б)) (як-є (а а а))) (як-є (а)))"#, true),
        ("reject-set-collapse", r#"(однакові? (сталий-перетин-атомів (як-є (а а б)) (як-є (а))) (як-є (а)))"#, false),
        ("reject-order", r#"(однакові? (сталий-перетин-атомів (як-є (б а б)) (як-є (а б))) (як-є (а б б)))"#, false),
    ]);
}

#[test]
fn d11_multiset_difference_consumes_copies_in_left_order() {
    // Rust лише викликає справжній SENS: усі відповіді породжує eval_program.
    // Перевіряємо кратності, порядок і негативи без окремого host-алгоритму.
    let mut session = with_source(include_str!(
        "../../../lib/list-multiset-difference-general.lisp"
    ));
    witness(&mut session, "MULTISET-DIFFERENCE", &[
        ("empty", r#"(однакові? (різниця-мультимножин (як-є ()) (як-є ())) (як-є ()))"#, true),
        ("empty-right", r#"(однакові? (різниця-мультимножин (як-є (а б а)) (як-є ())) (як-є (а б а)))"#, true),
        ("no-match", r#"(однакові? (різниця-мультимножин (як-є (а б а)) (як-є (г))) (як-є (а б а)))"#, true),
        ("remove-first", r#"(однакові? (різниця-мультимножин (як-є (а б а)) (як-є (а))) (як-є (б а)))"#, true),
        ("remove-middle", r#"(однакові? (різниця-мультимножин (як-є (а б в)) (як-є (б))) (як-є (а в)))"#, true),
        ("remove-last", r#"(однакові? (різниця-мультимножин (як-є (а б в)) (як-є (в))) (як-є (а б)))"#, true),
        ("ordered-min", r#"(однакові? (різниця-мультимножин (як-є (а б а а в)) (як-є (а а б))) (як-є (а в)))"#, true),
        ("right-surplus", r#"(однакові? (різниця-мультимножин (як-є (а б)) (як-є (а а б б))) (як-є ()))"#, true),
        ("reject-set-subtraction", r#"(однакові? (різниця-мультимножин (як-є (а а а)) (як-є (а))) (як-є ()))"#, false),
        ("reject-reordering", r#"(однакові? (різниця-мультимножин (як-є (а б а)) (як-є (а))) (як-є (а б)))"#, false),
    ]);
}

#[test]
fn d11_multiset_intersection_has_minimum_multiplicity() {
    let mut session = with_source(include_str!(
        "../../../lib/list-multiset-intersection-general.lisp"
    ));
    witness(&mut session, "MULTISET-INTERSECTION", &[
        ("empty", r#"(однакові? (перетнути-мультимножини (як-є ()) (як-є ())) (як-є ()))"#, true),
        ("left-empty", r#"(однакові? (перетнути-мультимножини (як-є ()) (як-є (а))) (як-є ()))"#, true),
        ("right-empty", r#"(однакові? (перетнути-мультимножини (як-є (а)) (як-є ())) (як-є ()))"#, true),
        ("ordered-min", r#"(однакові? (перетнути-мультимножини (як-є (а б а а в)) (як-є (а а б))) (як-є (а б а)))"#, true),
        ("right-surplus", r#"(однакові? (перетнути-мультимножини (як-є (а б)) (як-є (а а б б))) (як-є (а б)))"#, true),
        ("left-surplus", r#"(однакові? (перетнути-мультимножини (як-є (а а а)) (як-є (а))) (як-є (а)))"#, true),
        ("disjoint", r#"(однакові? (перетнути-мультимножини (як-є (а б)) (як-є (в г))) (як-є ()))"#, true),
        ("reject-set-membership", r#"(однакові? (перетнути-мультимножини (як-є (а а а)) (як-є (а))) (як-є (а а а)))"#, false),
        ("reject-reordering", r#"(однакові? (перетнути-мультимножини (як-є (а б а)) (як-є (а а б))) (як-є (а а б)))"#, false),
    ]);
}

#[test]
fn d11_stable_bipartition_preserves_multiplicities_in_both_streams() {
    let mut session = with_source(include_str!(
        "../../../lib/list-stable-bipartition-general.lisp"
    ));
    witness(&mut session, "BIPARTITION", &[
        ("empty", r#"(однакові? (поділити-стійко-за-набором (як-є ()) (як-є (а))) (як-є (() ())))"#, true),
        ("empty-set", r#"(однакові? (поділити-стійко-за-набором (як-є (а б а)) (як-є ())) (як-є (() (а б а))))"#, true),
        ("full-set", r#"(однакові? (поділити-стійко-за-набором (як-є (а б а)) (як-є (а б))) (як-є ((а б а) ())))"#, true),
        ("split-repeats", r#"(однакові? (поділити-стійко-за-набором (як-є (а в а б в)) (як-є (а б))) (як-є ((а а б) (в в))))"#, true),
        ("split-reverse", r#"(однакові? (поділити-стійко-за-набором (як-є (в б а в б)) (як-є (а б))) (як-є ((б а б) (в в))))"#, true),
        ("duplicated-set", r#"(однакові? (поділити-стійко-за-набором (як-є (а в а)) (як-є (а а))) (як-є ((а а) (в))))"#, true),
        ("reject-loss", r#"(однакові? (поділити-стійко-за-набором (як-є (а в а)) (як-є (а))) (як-є ((а) (в))))"#, false),
        ("reject-unsorted", r#"(однакові? (поділити-стійко-за-набором (як-є (а в б а)) (як-є (а б))) (як-є ((б а а) (в))))"#, false),
    ]);
}

#[test]
fn d11_left_and_right_rotation_are_mutual_inverses_for_proper_lists() {
    let mut session = with_source(include_str!(
        "../../../lib/list-rotation-inverse-general.lisp"
    ));
    witness(&mut session, "ROTATE", &[
        ("empty-left", r#"(однакові? (обернути-ліворуч-на-один (як-є ())) (як-є ()))"#, true),
        ("empty-right", r#"(однакові? (обернути-праворуч-на-один (як-є ())) (як-є ()))"#, true),
        ("one", r#"(однакові? (обернути-ліворуч-на-один (як-є (а))) (як-є (а)))"#, true),
        ("two", r#"(однакові? (обернути-праворуч-на-один (як-є (а б))) (як-є (б а)))"#, true),
        ("left", r#"(однакові? (обернути-ліворуч-на-один (як-є (а б в))) (як-є (б в а)))"#, true),
        ("right", r#"(однакові? (обернути-праворуч-на-один (як-є (а б в))) (як-є (в а б)))"#, true),
        ("inverse-left", r#"(однакові? (обернути-праворуч-на-один (обернути-ліворуч-на-один (як-є (а б в г)))) (як-є (а б в г)))"#, true),
        ("inverse-right", r#"(однакові? (обернути-ліворуч-на-один (обернути-праворуч-на-один (як-є (а б в г)))) (як-є (а б в г)))"#, true),
        ("reject-reverse", r#"(однакові? (обернути-ліворуч-на-один (як-є (а б в))) (як-є (в б а)))"#, false),
        ("reject-right-order", r#"(однакові? (обернути-праворуч-на-один (як-є (а б в))) (як-є (б в а)))"#, false),
    ]);
}

#[test]
fn d11_linear_palindrome_accepts_only_symmetric_atomic_sequences() {
    let mut session = with_source(include_str!(
        "../../../lib/list-palindrome-linear-atoms-general.lisp"
    ));
    witness(&mut session, "PALINDROME", &[
        ("empty", r#"(паліндром-лінійний? (як-є ()))"#, true),
        ("single", r#"(паліндром-лінійний? (як-є (а)))"#, true),
        ("two-yes", r#"(паліндром-лінійний? (як-є (а а)))"#, true),
        ("two-no", r#"(паліндром-лінійний? (як-є (а б)))"#, false),
        ("odd", r#"(паліндром-лінійний? (як-є (а б в б а)))"#, true),
        ("even", r#"(паліндром-лінійний? (як-є (а б б а)))"#, true),
        ("long-even", r#"(паліндром-лінійний? (як-є (а б в г г в б а)))"#, true),
        ("long-odd", r#"(паліндром-лінійний? (як-є (а б в г д г в б а)))"#, true),
        ("reject-middle", r#"(паліндром-лінійний? (як-є (а б в в а)))"#, false),
        ("reject-end", r#"(паліндром-лінійний? (як-є (а б в б г)))"#, false),
    ]);
}
