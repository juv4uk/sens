//! #1968 / #2011: QUOTE payload boundary, CAR/CDR positive control.
//! Виконуємо реальний SENS, а не Rust-симулятор семантики.
use sens::{eval_program, Session};

#[test]
fn quote_payload_and_selector_composition_are_native_d1_laws() {
    let source = include_str!("../../../tests/semantic/d3-quote-selector-boundary-evidence.lisp");
    let mut s = Session::default();
    let truth = eval_program("(атом? (як-є ()))", &mut s)
        .expect("test_id=D3_GENERATOR_CONTROL layer=SENS expected=D1:true")
        .value;
    let result = eval_program(source, &mut s)
        .expect("test_id=D3_GENERATOR_CONTROL layer=SENS positive law failed")
        .value;
    assert_eq!(
        result, truth,
        "test_id=D3_GENERATOR_CONTROL layer=SENS expected=D1:true"
    );

    // Один точний мутаційний сайт: різні цитовані атоми вже не рівні.
    let original = "(тотожне? (як-є атом?) (як-є атом?))";
    assert_eq!(
        source.matches(original).count(), 1,
        "test_id=D3_QUOTE_PAYLOAD layer=fixture expected=unique-mutation-site"
    );
    let mutant = source.replacen(
        original,
        "(тотожне? (як-є атом?) (як-є решта))",
        1,
    );
    let mut negative = Session::default();
    match eval_program(&mutant, &mut negative) {
        Ok(value) => assert_ne!(
            value.value, truth,
            "test_id=D3_QUOTE_PAYLOAD layer=SENS mutant unexpectedly true"
        ),
        Err(_) => {} // СЕНС відхилив хибний закон; це коректна негативна відповідь.
    }
}
