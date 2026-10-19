use sens::{eval_program, Session};

fn eval_with_si(source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/si.lisp"), &mut session)
        .expect("SI definitions should load");
    eval_program(source, &mut session)
        .expect("SI expression should evaluate")
        .value
        .to_string()
}

#[test]
fn descriptive_si_names_are_the_canonical_surface() {
    assert_eq!(eval_with_si("si:cesium-frequency"), "9192631770");
    assert_eq!(eval_with_si("si:speed-of-light"), "299792458");
    assert_eq!(eval_with_si("si:luminous-efficacy"), "683");
}

#[test]
fn descriptive_names_preserve_exact_values() {
    assert_eq!(
        eval_with_si("si:planck-constant"),
        "132521403/200000000000000000000000000000000000000000"
    );
    assert_eq!(
        eval_with_si("si:elementary-charge"),
        "801088317/5000000000000000000000000000"
    );
    assert_eq!(
        eval_with_si("si:boltzmann-constant"),
        "1380649/100000000000000000000000000000"
    );
    assert_eq!(
        eval_with_si("si:avogadro-constant"),
        "602214076000000000000000"
    );
}

#[test]
fn derived_si_constants_execute_through_real_sens() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/si.lisp"), &mut session)
        .expect("визначальні константи SI мають завантажитися у справжній SENS");
    eval_program(include_str!("../../../lib/si-derived.lisp"), &mut session)
        .expect("похідні константи SI мають обчислитися у справжньому SENS");

    for (name, expected) in [
        ("si:faraday-constant", "120606665154137523/1250000000000"),
        ("si:molar-gas-constant", "207861565453831/25000000000000"),
        ("si:josephson-constant", "21362355120000000000000/44173801"),
        ("si:von-klitzing-constant", "5521725125000000000000/213914163877964163"),
        ("si:magnetic-flux-quantum", "44173801/21362355120000000000000"),
        ("si:conductance-quantum", "213914163877964163/2760862562500000000000"),
        ("si:molar-planck-constant", "19951563564467157/50000000000000000000000000"),
    ] {
        let actual = eval_program(name, &mut session)
            .unwrap_or_else(|error| panic!("не вдалося обчислити {name}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "неточна похідна константа {name}");
    }
}
