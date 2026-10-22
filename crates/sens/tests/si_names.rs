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
fn admitted_si_derived_faraday_is_computed_in_actual_sens() {
    // Чинний закон допускає лише арифметику в межах одного Dn.
    // Перевіряємо саме виконувану частину оригінальної української бібліотеки,
    // а не проголошуємо всю SI-бібліотеку працездатною через статичний аналіз.
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/si.lisp"), &mut session)
        .expect("визначальні константи SI мають завантажитися");
    let src = include_str!("../../../lib/si-derived.lisp");
    let start = src.find("(визначити сі:стала-фарадея").expect("Фарадей");
    let end = src
        .find("(визначити сі:молярна-газова-стала")
        .expect("газова стала");
    eval_program(&src[start..end], &mut session)
        .expect("закон Фарадея виконується у справжньому SENS");
    assert_eq!(
        eval_program("сі:стала-фарадея", &mut session)
            .expect("обчислена константа існує")
            .value
            .to_string(),
        "120606665154137523/1250000000000"
    );
}

#[test]
fn si_double_charge_is_real_sens_and_josephson_requires_unadmitted_domain_bridge() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/si.lisp"), &mut session)
        .expect("визначальні сталі SI завантажуються");
    let src = include_str!("../../../lib/si-derived.lisp");
    let start = src
        .find("(визначити сі:подвоєний-заряд")
        .expect("подвоєний заряд");
    let end = src
        .find("(визначити сі:стала-джозефсона")
        .expect("Джозефсон");
    eval_program(&src[start..end], &mut session)
        .expect("точне подвоєння виконується самою мовою SENS");

    let actual = eval_program("сі:подвоєний-заряд", &mut session)
        .expect("подвоєний заряд доступний")
        .value
        .to_string();
    let independent = eval_program(
        "(додати сі:елементарний-заряд сі:елементарний-заряд)",
        &mut session,
    )
    .expect("справжня арифметика D5")
    .value
    .to_string();
    assert_eq!(actual, independent);

    // Це реальна негативна семантична перевірка, НЕ ігнорування RED:
    // власник ще не ратифікував Dn->D(2n) перехід для змішаних операндів.
    let err = eval_program("(частка сі:подвоєний-заряд сі:стала-планка)", &mut session)
        .expect_err("міждоменне ділення має залишатися явною відмовою");
    assert_eq!(err.kind, sens::ErrorKind::Type);
    assert!(err.message.contains("same-Dn"), "{err}");
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
