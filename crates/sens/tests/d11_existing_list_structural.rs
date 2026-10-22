//! D11: конкретні бібліотечні закони вкладених дерев, унарних серій, розрізів
//! і першого розходження. Семантику обчислює нативний SENS через eval_program.
//! Це дослідні похідні функції без нових координат, не ратифікація D11.
//! Rust тільки запускає SENS та перевіряє його канонічний результат D1.

use sens::{eval_program, load_core_library, Session};

fn load_native(source: &str) -> Session {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити ядро SENS");
    eval_program(source, &mut session).expect("виконати бібліотечні визначення SENS");
    session
}

fn check(session: &mut Session, family: &str, cases: &[(&str, &str, bool)]) {
    for (id, program, expected) in cases {
        let actual = eval_program(program, session).unwrap_or_else(|error| {
            panic!(
                "test_id=D11-STRUCT-{family}-{id} layer=SENS input={program} expected=D1:{expected} actual_error={error}"
            )
        }).value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(*expected),
            "test_id=D11-STRUCT-{family}-{id} layer=SENS input={program} expected=D1:{expected} actual={actual}"
        );
    }
}

#[test]
fn d11_tree_mirror_is_an_involution_not_just_flat_reverse() {
    let mut session = load_native(include_str!(
        "../../../lib/list-tree-mirror-general.lisp"
    ));
    check(&mut session, "MIRROR", &[
        ("empty", r#"(однакові? (дзеркалити-дерево (як-є ())) (як-є ()))"#, true),
        ("atom", r#"(однакові? (дзеркалити-дерево (як-є а)) (як-є а))"#, true),
        ("flat", r#"(однакові? (дзеркалити-дерево (як-є (а б в))) (як-є (в б а)))"#, true),
        ("nested", r#"(однакові? (дзеркалити-дерево (як-є (а (б в) ()))) (як-є (() (в б) а)))"#, true),
        ("double-nested", r#"(однакові? (дзеркалити-дерево (як-є ((а б) ((в)) г))) (як-є (г ((в)) (б а))))"#, true),
        ("inverse-nested", r#"(однакові? (дзеркалити-дерево (дзеркалити-дерево (як-є (а (б в) ())))) (як-є (а (б в) ())))"#, true),
        ("inverse-repeat", r#"(однакові? (дзеркалити-дерево (дзеркалити-дерево (як-є (а а (а б))))) (як-є (а а (а б))))"#, true),
        ("reject-shallow-reverse", r#"(однакові? (дзеркалити-дерево (як-є (а (б в)))) (як-є ((б в) а)))"#, false),
        ("reject-atom-loss", r#"(однакові? (дзеркалити-дерево (як-є (а б в))) (як-є (в а)))"#, false),
    ]);
}

#[test]
fn d11_unary_run_length_roundtrip_preserves_multiplicity_and_order() {
    let mut session = load_native(include_str!(
        "../../../lib/list-run-length-unary-general.lisp"
    ));
    check(&mut session, "UNARY-RUNS", &[
        ("empty-encode", r#"(однакові? (закодувати-унарні-серії (як-є ())) (як-є ()))"#, true),
        ("empty-decode", r#"(однакові? (розкодувати-унарні-серії (як-є ())) (як-є ()))"#, true),
        ("one", r#"(однакові? (закодувати-унарні-серії (як-є (а))) (як-є ((а (атом?)))))"#, true),
        ("two-runs", r#"(однакові? (закодувати-унарні-серії (як-є (а а б))) (як-є ((а (атом? атом?)) (б (атом?)))))"#, true),
        ("separated-repeat", r#"(однакові? (закодувати-унарні-серії (як-є (а б а))) (як-є ((а (атом?)) (б (атом?)) (а (атом?)))))"#, true),
        ("decode-explicit", r#"(однакові? (розкодувати-унарні-серії (як-є ((а (атом? атом?)) (б (атом?))))) (як-є (а а б)))"#, true),
        ("inverse-repetitions", r#"(однакові? (розкодувати-унарні-серії (закодувати-унарні-серії (як-є (а а б б б а)))) (як-є (а а б б б а)))"#, true),
        ("inverse-single", r#"(однакові? (розкодувати-унарні-серії (закодувати-унарні-серії (як-є (а)))) (як-є (а)))"#, true),
        ("reject-count-loss", r#"(однакові? (закодувати-унарні-серії (як-є (а а б))) (як-є ((а (атом?)) (б (атом?)))))"#, false),
        ("reject-global-merge", r#"(однакові? (закодувати-унарні-серії (як-є (а б а))) (як-є ((а (атом? атом?)) (б (атом?)))))"#, false),
    ]);
}

#[test]
fn d11_split_at_first_occurrence_and_reconstruct() {
    let mut session = load_native(include_str!(
        "../../../lib/list-split-first-occurrence-general.lisp"
    ));
    check(&mut session, "FIRST-SPLIT", &[
        ("empty", r#"(однакові? (розділити-перед-першим (як-є ()) (як-є а)) (як-є (() ())))"#, true),
        ("first", r#"(однакові? (розділити-перед-першим (як-є (а б а)) (як-є а)) (як-є (() (а б а))))"#, true),
        ("middle", r#"(однакові? (розділити-перед-першим (як-є (а б а)) (як-є б)) (як-є ((а) (б а))))"#, true),
        ("missing", r#"(однакові? (розділити-перед-першим (як-є (а б а)) (як-є в)) (як-є ((а б а) ())))"#, true),
        ("repeat-first-only", r#"(однакові? (розділити-перед-першим (як-є (а б а)) (як-є а)) (як-є ((а б) (а))))"#, false),
        ("restore-middle", r#"(однакові? (зібрати-після-розбиття (розділити-перед-першим (як-є (а б в)) (як-є б))) (як-є (а б в)))"#, true),
        ("restore-missing", r#"(однакові? (зібрати-після-розбиття (розділити-перед-першим (як-є (а б)) (як-є в))) (як-є (а б)))"#, true),
        ("restore-empty", r#"(однакові? (зібрати-після-розбиття (розділити-перед-першим (як-є ()) (як-є а))) (як-є ()))"#, true),
        ("reject-lost-match", r#"(однакові? (розділити-перед-першим (як-є (а б в)) (як-є б)) (як-є ((а) (в))))"#, false),
        ("reject-reordered", r#"(однакові? (зібрати-після-розбиття (розділити-перед-першим (як-є (а б в)) (як-є б))) (як-є (б а в)))"#, false),
    ]);
}

#[test]
fn d11_first_divergent_suffixes_reuse_original_tails() {
    let mut session = load_native(include_str!(
        "../../../lib/list-first-divergence-suffix-general.lisp"
    ));
    check(&mut session, "DIVERGENCE", &[
        ("both-empty", r#"(однакові? (хвости-першого-розходження (як-є ()) (як-є ())) (як-є (() ())))"#, true),
        ("equal", r#"(однакові? (хвости-першого-розходження (як-є (а б)) (як-є (а б))) (як-є (() ())))"#, true),
        ("first", r#"(однакові? (хвости-першого-розходження (як-є (а б)) (як-є (х б))) (як-є ((а б) (х б))))"#, true),
        ("second", r#"(однакові? (хвости-першого-розходження (як-є (а б в)) (як-є (а х в))) (як-є ((б в) (х в))))"#, true),
        ("shorter-left", r#"(однакові? (хвости-першого-розходження (як-є (а б)) (як-є (а б в))) (як-є (() (в))))"#, true),
        ("shorter-right", r#"(однакові? (хвости-першого-розходження (як-є (а б в)) (як-є (а б))) (як-є ((в) ())))"#, true),
        ("reject-late-disagreement", r#"(однакові? (хвости-першого-розходження (як-є (а б в)) (як-є (а х в))) (як-є ((в) (в))))"#, false),
        ("reject-false-equality", r#"(однакові? (хвости-першого-розходження (як-є (а б)) (як-є (а х))) (як-є (() ())))"#, false),
    ]);
}
