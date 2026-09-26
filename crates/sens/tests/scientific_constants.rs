use sens::{eval_program, Session};

fn eval_science(source: &str) -> String {
    let mut session = Session::default();
    for library in [
        include_str!("../../../lib/core.lisp"),
        include_str!("../../../lib/quantity.lisp"),
        include_str!("../../../lib/si.lisp"),
    ] {
        eval_program(library, &mut session).expect("science library should load");
    }
    eval_program(source, &mut session)
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
        eval_program(library, &mut session).expect("science/knowledge library should load");
    }
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("science knowledge expression failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn bare_number_quantity_and_scientific_constant_are_distinct_data_levels() {
    let source = r#"
        (list
          (quantity? 299792458)
          (quantity?
            (scientific-constant-quantity si:defining-speed-of-light))
          (scientific-constant? si:defining-speed-of-light)
          (scientific-constant? 299792458))
    "#;
    assert_eq!(eval_science(source), "(() t t ())");
}

#[test]
fn units_require_named_dimension_terms_not_anonymous_pairs() {
    let source = r#"
        (list
          (unit? (quote (unit/1 (dimension/1 metre 1) (dimension/1 second -1))))
          (unit? (quote (unit/1 (metre 1) (second -1))))
          (dimension? (quote (dimension/1 metre 1)))
          (dimension? (quote (metre 1))))
    "#;
    assert_eq!(eval_science(source), "(t () t ())");
}

#[test]
fn speed_of_light_record_keeps_value_unit_status_kind_system_and_source() {
    let source = r#"
        (list
          (scientific-constant-name si:defining-speed-of-light)
          (scientific-constant-value si:defining-speed-of-light)
          (unit-dimensions
            (scientific-constant-unit si:defining-speed-of-light))
          (scientific-constant-status si:defining-speed-of-light)
          (scientific-constant-kind si:defining-speed-of-light)
          (scientific-constant-system si:defining-speed-of-light)
          (scientific-constant-source si:defining-speed-of-light))
    "#;
    assert_eq!(
        eval_science(source),
        "(si:speed-of-light 299792458 ((dimension/1 metre 1) (dimension/1 second -1)) exact-by-definition physical-defining si (science-source/1 bipm-si-brochure-9 2019))"
    );
}

#[test]
fn all_seven_si_records_are_valid_exact_defining_constants() {
    let source = r#"
        (map
          (lambda (constant)
            (list
              (scientific-constant? constant)
              (scientific-constant-status constant)
              (scientific-constant-kind constant)
              (scientific-constant-system constant)))
          (list
            si:defining-cesium-frequency
            si:defining-speed-of-light
            si:defining-planck-constant
            si:defining-elementary-charge
            si:defining-boltzmann-constant
            si:defining-avogadro-constant
            si:defining-luminous-efficacy))
    "#;
    assert_eq!(
        eval_science(source),
        "((t exact-by-definition physical-defining si) (t exact-by-definition physical-defining si) (t exact-by-definition physical-defining si) (t exact-by-definition physical-defining si) (t exact-by-definition physical-defining si) (t exact-by-definition physical-defining si) (t exact-by-definition physical-defining si))"
    );
}

#[test]
fn exact_rational_values_remain_unchanged_after_structuring() {
    assert_eq!(
        eval_science("si:planck-constant"),
        "132521403/200000000000000000000000000000000000000000"
    );
    assert_eq!(
        eval_science("si:elementary-charge"),
        "801088317/5000000000000000000000000000"
    );
    assert_eq!(
        eval_science("si:boltzmann-constant"),
        "1380649/100000000000000000000000000000"
    );
    assert_eq!(
        eval_science("si:avogadro-constant"),
        "602214076000000000000000"
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
            (scientific-constant->clauses si:defining-speed-of-light)))
        (list
          (car admission)
          (result-status
            (reason-in-observe
              (quote science)
              (quote (constant-value si:speed-of-light 299792458))))
          (result-status
            (reason-in-observe
              (quote science)
              (quote (constant-status si:speed-of-light exact-by-definition))))
          (result-status
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
        (scientific-constant->clauses
          (quote (scientific-constant/1 broken)))
    "#;
    assert_eq!(eval_science(source), "()");
}

#[test]
fn si_source_does_not_reintroduce_a_second_literal_authority_for_numeric_views() {
    let si = include_str!("../../../lib/si.lisp");

    for forbidden in [
        "(def si:cesium-frequency 9192631770)",
        "(def si:speed-of-light 299792458)",
        "(def si:avogadro-constant 602214076000000000000000)",
        "(def si:luminous-efficacy 683)",
    ] {
        assert!(
            !si.contains(forbidden),
            "numeric view must be derived from its scientific-constant record: {forbidden}"
        );
    }

    for derived in [
        "(def si:cesium-frequency (si:constant-value si:defining-cesium-frequency))",
        "(def si:speed-of-light (si:constant-value si:defining-speed-of-light))",
        "(def si:planck-constant (si:constant-value si:defining-planck-constant))",
        "(def si:elementary-charge (si:constant-value si:defining-elementary-charge))",
        "(def si:boltzmann-constant (si:constant-value si:defining-boltzmann-constant))",
        "(def si:avogadro-constant (si:constant-value si:defining-avogadro-constant))",
        "(def si:luminous-efficacy (si:constant-value si:defining-luminous-efficacy))",
    ] {
        assert!(si.contains(derived), "missing derived SI numeric view: {derived}");
    }
}
