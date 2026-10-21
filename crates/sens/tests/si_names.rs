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
fn full_ukrainian_si_names_are_the_primary_surface() {
    assert_eq!(eval_with_si("сі:частота-цезію"), "9192631770");
    assert_eq!(eval_with_si("сі:швидкість-світла"), "299792458");
    assert_eq!(eval_with_si("сі:світлова-ефективність"), "683");
}

#[test]
fn descriptive_names_preserve_exact_values() {
    assert_eq!(
        eval_with_si("сі:стала-планка"),
        "132521403/200000000000000000000000000000000000000000"
    );
    assert_eq!(
        eval_with_si("сі:елементарний-заряд"),
        "801088317/5000000000000000000000000000"
    );
    assert_eq!(
        eval_with_si("сі:стала-больцмана"),
        "1380649/100000000000000000000000000000"
    );
    assert_eq!(
        eval_with_si("сі:стала-авогадро"),
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
        ("сі:стала-фарадея", "120606665154137523/1250000000000"),
        ("сі:молярна-газова-стала", "207861565453831/25000000000000"),
        ("сі:стала-джозефсона", "21362355120000000000000/44173801"),
        ("сі:стала-фон-клітцинга", "5521725125000000000000/213914163877964163"),
        ("сі:квант-магнітного-потоку", "44173801/21362355120000000000000"),
        ("сі:квант-електричної-провідності", "213914163877964163/2760862562500000000000"),
        ("сі:молярна-стала-планка", "19951563564467157/50000000000000000000000000"),
    ] {
        let actual = eval_program(name, &mut session)
            .unwrap_or_else(|error| panic!("не вдалося обчислити {name}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "неточна похідна константа {name}");
    }
}

#[test]
fn derived_si_double_charge_is_evaluated_by_sens_without_numeric_shortcut() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/si.lisp"), &mut session)
        .expect("чинні визначальні сталі SI доступні");
    eval_program(include_str!("../../../lib/si-derived.lisp"), &mut session)
        .expect("українські похідні сталі завантажуються SENS");

    let double_charge = eval_program("сі:подвоєний-заряд", &mut session)
        .expect("SENS має визначити подвоєний заряд")
        .value
        .to_string();
    let addition = eval_program(
        "(додати сі:елементарний-заряд сі:елементарний-заряд)",
        &mut session,
    )
    .expect("SENS має обчислити точне додавання")
    .value
    .to_string();
    assert_eq!(double_charge, addition, "подвоєння втратило точний закон");

    for (symbol, independent_expression) in [
        (
            "сі:стала-джозефсона",
            "(частка (додати сі:елементарний-заряд сі:елементарний-заряд) сі:стала-планка)",
        ),
        (
            "сі:квант-магнітного-потоку",
            "(частка сі:стала-планка (додати сі:елементарний-заряд сі:елементарний-заряд))",
        ),
        (
            "сі:квант-електричної-провідності",
            "(частка (помножити (додати сі:елементарний-заряд сі:елементарний-заряд) сі:елементарний-заряд) сі:стала-планка)",
        ),
    ] {
        let actual = eval_program(symbol, &mut session)
            .unwrap_or_else(|error| panic!("похідна константа {symbol}: {error}"))
            .value
            .to_string();
        let expected = eval_program(independent_expression, &mut session)
            .unwrap_or_else(|error| panic!("незалежна формула {symbol}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "втрачено точну семантику {symbol}");
    }
}

#[test]
fn si_faraday_executes_but_mixed_domain_gas_is_reported_as_type_error() {
    // Виконуємо саме фрагменти чинного українського Lisp, не Rust-імітацію.
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/si.lisp"), &mut session)
        .expect("вихідні SI-константи мають завантажуватися");
    let source = include_str!("../../../lib/si-derived.lisp");
    let first = source
        .find("(визначити сі:стала-фарадея")
        .expect("українське визначення сталої Фарадея");
    let second = source
        .find("(визначити сі:молярна-газова-стала")
        .expect("українське визначення газової сталої");
    let third = source
        .find("(визначити сі:подвоєний-заряд")
        .expect("українське визначення подвоєного заряду");
    assert!(first < second && second < third);
    eval_program(&source[first..second], &mut session)
        .expect("допущена частина справді виконується у SENS");
    let faraday = eval_program("сі:стала-фарадея", &mut session)
        .expect("результат має бути доступний після виконання")
        .value
        .to_string();
    assert_eq!(faraday, "120606665154137523/1250000000000");

    let refusal = eval_program(&source[second..third], &mut session)
        .expect_err("змішані Dn без явного доменного приведення не виконуються");
    assert_eq!(refusal.kind, sens::ErrorKind::Type);
    assert!(
        refusal.message.contains("same-domain operands"),
        "справжня відмова повинна називати точну проблему: {refusal}"
    );
}
