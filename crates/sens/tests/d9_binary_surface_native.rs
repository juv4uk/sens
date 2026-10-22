//! D9: канонічне українське ім'я двійковий не створює новий код.
//! Дескриптор виконує саме SENS Core4; Rust лише читає D1 результат.
//! W8:10101001 (історична поверхня) НЕ тотожний D9:110110110.

use sens::{eval_program, load_core_library, Session};

#[test]
fn d9_binary_has_only_one_canonical_ukrainian_surface_and_no_decimal_resident() {
    const TABLE: &str = include_str!("../../../lib/domains/d9.lisp");
    const ROW: &str = "(110110110 (ук двійковий) (укр двійковий) (san dvimāna) (en binary) (LISP BINARY) (sym ()))";
    const NUMBER_ROW: &str = "(110111001 (ук число-рядок) (укр число-рядок) (san saṅkhyā-śabda) (en number->string) (LISP NUMBER->STRING) (sym ()))";
    assert!(TABLE.contains(ROW), "test_id=D9-BINARY-SURFACE layer=canonical_table expected=D9:110110110 ukr=двійковий");
    assert!(TABLE.contains(NUMBER_ROW), "test_id=D9-NUMBER-STRING layer=canonical_table expected=D9:110111001");
    assert_eq!(TABLE.matches("(110110110 ").count(), 1, "test_id=D9-BINARY-UNIQUE");
    assert_eq!(TABLE.matches("(110111001 ").count(), 1, "test_id=D9-NUMBER-STRING-UNIQUE");
    assert!(!TABLE.contains("(ук десятковий)"), "test_id=D9-NO-DECIMAL-RESIDENT");
    assert!(!TABLE.contains("(укр десятковий)"), "test_id=D9-NO-DECIMAL-RESIDENT-UKR");
}

#[test]
fn d9_binary_descriptor_is_executed_by_native_sens() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("чинне ядро SENS і D9-замикання Core4");
    for (id, source, expected) in [
        ("код-дескриптора", "(однакові? (двійковий (як-є ширина)) (як-є (binary ширина)))", true),
        ("порожня-ширина", "(однакові? (двійковий (як-є ())) (як-є (binary ())))", true),
        ("складена-ширина", "(однакові? (двійковий (як-є (а б))) (як-є (binary (а б))))", true),
        ("однакові-виклики", "(однакові? (двійковий (як-є а)) (двійковий (як-є а)))", true),
        ("чужа-ширина", "(однакові? (двійковий (як-є ширина)) (як-є (binary інша)))", false),
        ("поміняний-порядок", "(однакові? (двійковий (як-є а)) (як-є (а binary)))", false),
        ("результат-не-атом", "(атом? (двійковий (як-є а)))", false),
        ("різні-аргументи", "(однакові? (двійковий (як-є а)) (двійковий (як-є б)))", false),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=D9-BINARY-{id} layer=SENS input={source} expected=D1:{expected} actual_error={error}"
            ))
            .value;
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "test_id=D9-BINARY-{id} layer=SENS input={source} expected=D1:{expected} actual={value}"
        );
    }
}
