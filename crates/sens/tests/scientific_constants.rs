use sens::{eval_parsed_expressions, parse, Session};

fn eval_ukr(source: &str, session: &mut Session) -> Result<sens::EvalResult, sens::LanguageError> {
    let parsed = parse(source)?;
    let projected = sens::source_projection::project_ukr_decimal_integer_literals(&parsed, source)?;
    eval_parsed_expressions(&projected, session)
}

fn eval_science(source: &str) -> String {
    let mut session = Session::default();
    for library in [
        include_str!("../../../lib/core.lisp"),
        include_str!("../../../lib/quantity.lisp"),
        include_str!("../../../lib/si.lisp"),
    ] {
        eval_ukr(library, &mut session)
            .unwrap_or_else(|e| panic!("science library should load: {e}"));
    }
    eval_ukr(source, &mut session)
        .unwrap_or_else(|e| panic!("science expression failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

fn eval_science_knowledge(source: &str) -> String {
    let mut session = Session::default();
    for library in [
        include_str!("../../../lib/core.lisp"),
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
        include_str!("../../../lib/result-status.lisp"),
        include_str!("../../../lib/quantity.lisp"),
        include_str!("../../../lib/si.lisp"),
    ] {
        eval_ukr(library, &mut session)
            .unwrap_or_else(|e| panic!("science/knowledge library should load: {e}"));
    }
    eval_ukr(source, &mut session)
        .unwrap_or_else(|e| panic!("science knowledge expression failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn speed_of_light_record_keeps_value_unit_status_kind_system_and_source() {
    let source = r#"
        (list
          (науковий-константа-ім'я сі:визначальна-швидкість-світла)
          (науковий-константа-значення сі:визначальна-швидкість-світла)
          (одиниця-розмірності
            (науковий-константа-одиниця сі:визначальна-швидкість-світла))
          (науковий-константа-стан сі:визначальна-швидкість-світла)
          (науковий-константа-вид сі:визначальна-швидкість-світла)
          (науковий-константа-система сі:визначальна-швидкість-світла)
          (науковий-константа-джерело сі:визначальна-швидкість-світла))
    "#;
    assert_eq!(
        eval_science(source),
        "(si:speed-of-light 299792458 ((dimension/1 metre 1) (dimension/1 second -1)) exact-by-definition physical-defining si (science-source/1 bipm-si-brochure-9 2019))"
    );
}

#[test]
fn exact_rational_values_remain_unchanged_after_structuring() {
    assert_eq!(
        eval_science("сі:стала-планка"),
        "132521403/200000000000000000000000000000000000000000"
    );
    assert_eq!(
        eval_science("сі:елементарний-заряд"),
        "801088317/5000000000000000000000000000"
    );
    assert_eq!(
        eval_science("сі:стала-больцмана"),
        "1380649/100000000000000000000000000000"
    );
    assert_eq!(
        eval_science("сі:стала-авогадро"),
        "602214076000000000000000"
    );
    assert_eq!(
        eval_science("(сі:значення-константи сі:визначальна-швидкість-світла)"),
        "299792458"
    );
}

#[test]
fn advice_taker_can_reason_about_an_admitted_scientific_constant() {
    let source = r#"
        (def expected-unit
          (quote
            (unit/1
              (dimension/1 metre 1)
              (dimension/1 second -1))))
        (def admission
          (advise-all science
            (науковий-константа-клаузи сі:визначальна-швидкість-світла)))
        (list
          (car admission)
          (результат-стан
            (reason-in-observe
              (quote science)
              (quote (constant-value si:speed-of-light 299792458))))
          (результат-стан
            (reason-in-observe
              (quote science)
              (quote (constant-status si:speed-of-light exact-by-definition))))
          (результат-стан
            (reason-in-observe
              (quote science)
              (list
                (quote constant-unit)
                (quote si:speed-of-light)
                expected-unit))))
    "#;
    assert_eq!(eval_science_knowledge(source), "(accepted proved proved proved)");
}

#[test]
fn malformed_constant_cannot_project_into_knowledge() {
    let source = r#"
        (науковий-константа-клаузи
          (quote (scientific-constant/1 broken)))
    "#;
    assert_eq!(eval_science(source), "()");
}

/// Перевіряти чинну українську D4:0011-проєкцію визначень у SI.
/// Історичні SID8-голови і `def` не є допустимими активними визначеннями.
fn si_defines(si: &str, rest: &str) -> bool {
    si.contains(&format!("(визначити {rest}"))
}

#[test]
fn si_source_does_not_reintroduce_a_second_literal_authority_for_numeric_views() {
    let si = include_str!("../../../lib/si.lisp");

    for forbidden in [
        "сі:частота-цезію 9192631770)",
        "сі:швидкість-світла 299792458)",
        "сі:стала-авогадро 602214076000000000000000)",
        "сі:світлова-ефективність 683)",
    ] {
        assert!(
            !si_defines(si, forbidden),
            "numeric view must be derived from its scientific-constant record: {forbidden}"
        );
    }

    for derived in [
        "сі:частота-цезію (сі:значення-константи сі:визначальна-частота-цезію)",
        "сі:швидкість-світла (сі:значення-константи сі:визначальна-швидкість-світла)",
        "сі:стала-планка (сі:значення-константи сі:визначальна-стала-планка)",
        "сі:елементарний-заряд (сі:значення-константи сі:визначальний-елементарний-заряд)",
        "сі:стала-больцмана (сі:значення-константи сі:визначальна-стала-больцмана)",
        "сі:стала-авогадро (сі:значення-константи сі:визначальна-стала-авогадро)",
        "сі:світлова-ефективність (сі:значення-константи сі:визначальна-світлова-ефективність)",
    ] {
        assert!(si_defines(si, derived), "missing derived SI numeric view: {derived}");
    }
}
