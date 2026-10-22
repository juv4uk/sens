//! D11: наявні похідні закони першокласного MetaEval через реальний SENS.
//! Жодної Rust/Python семантики обчислення, жодного нового resident opcode.
//! Адресні позитиви та контрприклади — точні спостережувані SENS-значення.

use sens::{
    eval_parsed_expressions, load_core_library, parse_mixed_exact_domain, Session,
};

fn session() -> Session {
    let mut s = Session::default();
    load_core_library(&mut s).expect("test_id=D11-FC-EVAL-CORE");
    let forms = parse_mixed_exact_domain(include_str!(
        "../../../lib/meta-eval-first-class.lisp"
    ))
    .expect("test_id=D11-FC-EVAL-READ");
    eval_parsed_expressions(&forms, &mut s).expect("test_id=D11-FC-EVAL-LOAD");
    s
}

fn assert_native_law(s: &mut Session, family: &str, cases: &[(&str, &str, &str)]) {
    for (id, source, expected) in cases {
        let parsed = parse_mixed_exact_domain(source).unwrap_or_else(|error| {
            panic!("test_id=D11-FC-{family}-{id} layer=reader input={source} error={error}")
        });
        let actual = eval_parsed_expressions(&parsed, s)
            .unwrap_or_else(|error| {
                panic!(
                    "test_id=D11-FC-{family}-{id} layer=eval input={source} expected={expected} actual_error={error}"
                )
            })
            .value
            .to_string();
        assert_eq!(
            actual, *expected,
            "test_id=D11-FC-{family}-{id} layer=SENS input={source} expected={expected} actual={actual}"
        );
    }
}

#[test]
fn d11_first_class_eval_list_keeps_argument_order_and_nested_values() {
    let mut s = session();
    assert_native_law(&mut s, "EVAL-LIST", &[
        ("empty", "(першокласне-обчислити-список (як-є ()) першокласне-початкове-середовище)", "()"),
        ("one", "(першокласне-обчислити-список (як-є ((як-є а))) першокласне-початкове-середовище)", "(а)"),
        ("two-in-order", "(першокласне-обчислити-список (як-є ((як-є а) (як-є б))) першокласне-початкове-середовище)", "(а б)"),
        ("nested-list", "(першокласне-обчислити-список (як-є ((як-є (а б)) (як-є в))) першокласне-початкове-середовище)", "((а б) в)"),
        ("empty-as-argument", "(першокласне-обчислити-список (як-є ((як-є ()) (як-є а))) першокласне-початкове-середовище)", "(() а)"),
        ("lexical-before-quote", "(першокласне-обчислити-список (як-є (х (як-є б))) (як-є ((х . а))))", "(а б)"),
        ("negative-not-reversed", "(першокласне-обчислити-список (як-є ((як-є б) (як-є а))) першокласне-початкове-середовище)", "(б а)"),
    ]);
}

#[test]
fn d11_first_class_eval_body_returns_last_expression_not_first() {
    let mut s = session();
    assert_native_law(&mut s, "EVAL-BODY", &[
        ("single", "(першокласне-обчислити-тіло (як-є ((як-є а))) першокласне-початкове-середовище)", "а"),
        ("two-final", "(першокласне-обчислити-тіло (як-є ((як-є а) (як-є б))) першокласне-початкове-середовище)", "б"),
        ("three-final", "(першокласне-обчислити-тіло (як-є ((як-є а) (як-є б) (як-є в))) першокласне-початкове-середовище)", "в"),
        ("final-empty", "(першокласне-обчислити-тіло (як-є ((як-є а) (як-є ()))) першокласне-початкове-середовище)", "()"),
        ("last-is-nested", "(першокласне-обчислити-тіло (як-є ((як-є а) (як-є (б (в))))) першокласне-початкове-середовище)", "(б (в))"),
        ("lexical-final", "(першокласне-обчислити-тіло (як-є ((як-є старе) х)) (як-є ((х . нове))))", "нове"),
    ]);
}

#[test]
fn d11_first_class_eval_cond_chooses_first_truthy_clause_and_skips_false() {
    let mut s = session();
    assert_native_law(&mut s, "EVAL-COND", &[
        ("empty", "(першокласне-обчислити-умови (як-є ()) першокласне-початкове-середовище)", "()"),
        ("first-yes", "(першокласне-обчислити-умови (як-є (((атом? (як-є ())) (як-є а)) ((атом? (як-є (б))) (як-є б)))) першокласне-початкове-середовище)", "а"),
        ("skip-false", "(першокласне-обчислити-умови (як-є (((атом? (як-є (а))) (як-є а)) ((атом? (як-є ())) (як-є б)))) першокласне-початкове-середовище)", "б"),
        ("all-false", "(першокласне-обчислити-умови (як-є (((атом? (як-є (а))) (як-є а)) ((атом? (як-є (б))) (як-є б)))) першокласне-початкове-середовище)", "()"),
        ("skip-two-false", "(першокласне-обчислити-умови (як-є (((атом? (як-є (а))) (як-є а)) ((атом? (як-є (б))) (як-є б)) ((атом? (як-є ())) (як-є в)))) першокласне-початкове-середовище)", "в"),
        ("lexical-then", "(першокласне-обчислити-умови (як-є (((атом? (як-є ())) х))) (як-є ((х . захоплене))))", "захоплене"),
    ]);
}

#[test]
fn d11_first_class_apply_discriminates_primitive_and_noncallable() {
    let mut s = session();
    assert_native_law(&mut s, "APPLY", &[
        ("car", "(першокласне-застосувати (першокласний-примітив (як-є перше)) (як-є ((а б))))", "а"),
        ("cdr", "(першокласне-застосувати (першокласний-примітив (як-є решта)) (як-є ((а б))))", "(б)"),
        ("cons", "(першокласне-застосувати (першокласний-примітив (як-є сполучити)) (як-є (а (б))))", "(а б)"),
        ("unknown-primitive", "(першокласне-застосувати (першокласний-примітив (як-є немає)) (як-є ()))", "(невідомий-примітив немає)"),
        ("noncallable-atom", "(першокласне-застосувати (як-є немає) (як-є ()))", "(не-викликається немає)"),
        ("noncallable-empty", "(першокласне-застосувати (як-є ()) (як-є ()))", "(не-викликається ())"),
    ]);
}

#[test]
fn d11_first_class_entrypoint_executes_first_class_closures_in_sens() {
    let mut s = session();
    assert_native_law(&mut s, "ENTRY", &[
        ("quoted-atom", "(обчислити-першокласні-функції (як-є (як-є а)))", "а"),
        ("quoted-pair", "(обчислити-першокласні-функції (як-є (як-є (а (б)))))", "(а (б))"),
        ("identity-closure", "(обчислити-першокласні-функції (як-є ((функція (х) х) (як-є а))))", "а"),
        ("shadowed-primitive", "(обчислити-першокласні-функції (як-є ((функція (перше) перше) (як-є нове))))", "нове"),
        ("first-class-primitive", "(обчислити-першокласні-функції (як-є (перше (як-є (а б)))))", "а"),
    ]);
}
