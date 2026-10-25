//! Д11: частоти Clojure як SENS-композиція з унарною кратністю.
//! Виконавцем є eval_program SENS; Rust не підраховує й не групує.
//! Позитивні й негативні приклади мають канонічний результат D1.
//! Це не ратифікація машинних адрес і не атестація фізичного T5M.

use sens::{eval_program, load_core_library, Session};

#[test]
fn d11_clojure_frequencies_unary_run_in_sens() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("чинний Core SENS");
    eval_program(
        include_str!("../../../lib/d11-clojure-group-by.lisp"),
        &mut session,
    )
    .expect("визначити базове групування у SENS");
    eval_program(
        include_str!("../../../lib/d11-clojure-frequencies-unary.lisp"),
        &mut session,
    )
    .expect("визначити унарні частоти у SENS");

    for (id, source, expected) in [
        ("порожньо", r#"(однакові? (частоти-елементів-унарно (як-є ())) (як-є ()))"#, true),
        ("один", r#"(однакові? (частоти-елементів-унарно (як-є (а))) (як-є ((а (о)))))"#, true),
        ("однакова-пара", r#"(однакові? (частоти-елементів-унарно (як-є (а а))) (як-є ((а (о о)))))"#, true),
        ("несуміжний-повтор", r#"(однакові? (частоти-елементів-унарно (як-є (а б а))) (як-є ((а (о о)) (б (о)))))"#, true),
        ("перший-б", r#"(однакові? (частоти-елементів-унарно (як-є (б а б))) (як-є ((б (о о)) (а (о)))))"#, true),
        ("чотири-входження", r#"(однакові? (частоти-елементів-унарно (як-є (а б а в а г а))) (як-є ((а (о о о о)) (б (о)) (в (о)) (г (о)))))"#, true),
        ("усі-різні", r#"(однакові? (частоти-елементів-унарно (як-є (а б в))) (як-є ((а (о)) (б (о)) (в (о)))))"#, true),
        ("три-серії", r#"(однакові? (частоти-елементів-унарно (як-є (а а б б а))) (як-є ((а (о о о)) (б (о о)))))"#, true),
        ("атом-не-список", r#"(однакові? (частоти-елементів-унарно (як-є (а (а) а))) (як-є ((а (о о)) ((а) (о)))))"#, true),
        ("складені-ключі", r#"(однакові? (частоти-елементів-унарно (як-є ((а) (б) (а)))) (як-є (((а) (о о)) ((б) (о)))))"#, true),
        ("порожній-ключ", r#"(однакові? (частоти-елементів-унарно (як-є (() (а) ()))) (як-є ((() (о о)) ((а) (о)))))"#, true),
        ("за-першим", r#"(однакові? (частоти-за-ключем-унарно (функція (елемент) (перше елемент)) (як-є ((а л) (б м) (а н)))) (як-є ((а (о о)) (б (о)))))"#, true),
        ("за-першим-спершу-б", r#"(однакові? (частоти-за-ключем-унарно (функція (елемент) (перше елемент)) (як-є ((б л) (а м) (б н) (а о)))) (як-є ((б (о о)) (а (о о)))))"#, true),
        ("за-ключем-константа", r#"(однакові? (частоти-за-ключем-унарно (функція (елемент) (як-є спільне)) (як-є (а б в))) (як-є ((спільне (о о о)))))"#, true),
        ("порожньо-за-ключем", r#"(однакові? (частоти-за-ключем-унарно (функція (елемент) (перше елемент)) (як-є ())) (як-є ()))"#, true),
        ("за-складеним-ключем", r#"(однакові? (частоти-за-ключем-унарно (функція (елемент) (решта елемент)) (як-є ((а х) (б у) (в х)))) (як-є (((х) (о о)) ((у) (о)))))"#, true),
        ("не-плутати-із-серіями", r#"(однакові? (частоти-елементів-унарно (як-є (а б а))) (як-є ((а (о)) (б (о)) (а (о)))))"#, false),
        ("не-втратити-повтор", r#"(однакові? (частоти-елементів-унарно (як-є (а б а))) (як-є ((а (о)) (б (о)))))"#, false),
        ("не-поміняти-порядок", r#"(однакові? (частоти-елементів-унарно (як-є (б а б))) (як-є ((а (о)) (б (о о)))))"#, false),
        ("не-плутати-кратність", r#"(однакові? (частоти-елементів-унарно (як-є (а а б))) (як-є ((а (о)) (б (о)))))"#, false),
        ("не-злити-атом-список", r#"(однакові? (частоти-елементів-унарно (як-є (а (а)))) (як-є ((а (о о)))))"#, false),
        ("не-ігнорувати-ключ", r#"(однакові? (частоти-за-ключем-унарно (функція (елемент) (перше елемент)) (як-є ((а л) (б м) (а н)))) (як-є ((а (о)) (б (о)) (а (о)))))"#, false),
        ("не-унарний-нуль", r#"(однакові? (частоти-елементів-унарно (як-є (а))) (як-є ((а ()))))"#, false),
        ("не-глобальний-підрахунок", r#"(однакові? (частоти-за-ключем-унарно (функція (елемент) (як-є спільне)) (як-є (а б в))) (як-є ((спільне (о)))))"#, false),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| {
                panic!(
                    "test_id=D11-FREQUENCIES-{id} layer=SENS input={source} expected=D1:{expected} actual_error={error}"
                )
            })
            .value;
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "test_id=D11-FREQUENCIES-{id} layer=SENS input={source} expected=D1:{expected} actual={value}"
        );
    }
}

#[test]
fn d11_frequencies_group_records_are_exact_pairs_in_native_sens() {
    // Тільки SENS обчислює закон. Rust перевіряє точний D1/Type.
    let mut s = Session::bare();
    load_core_library(&mut s).expect("чинний Core SENS");
    eval_program(include_str!("../../../lib/d11-clojure-group-by.lisp"), &mut s)
        .expect("групування SENS");
    eval_program(include_str!("../../../lib/d11-clojure-frequencies-unary.lisp"), &mut s)
        .expect("частоти SENS");
    for (id, source, expected) in [
        ("d11-group-pair-positive", include_str!("../../../tests/fixtures/d11-frequencies-exact-group-pair-law.lisp"), true),
        ("d11-group-pair-mutant", include_str!("../../../tests/fixtures/d11-frequencies-exact-group-pair-mutant.lisp"), false),
    ] {
        let result = eval_program(source, &mut s)
            .unwrap_or_else(|e| panic!("test_id={id} layer=SENS error={e}")).value;
        assert_eq!(result.as_predicate_bit(), Some(expected),
            "test_id={id} layer=SENS expected=D1:{expected} actual={result}");
    }
    for (id, source) in [
        ("d11-group-extra-field", include_str!("../../../tests/fixtures/d11-frequencies-extra-group-field-negative.lisp")),
        ("d11-group-missing-field", include_str!("../../../tests/fixtures/d11-frequencies-missing-group-field-negative.lisp")),
    ] {
        let error = eval_program(source, &mut s).err()
            .unwrap_or_else(|| panic!("test_id={id} layer=SENS expected=D3-CAR-Type actual=accepted"));
        assert!(error.to_string().contains("car expects a non-empty list"),
            "test_id={id} layer=SENS expected=D3-CAR-Type actual={error}");
    }
}
