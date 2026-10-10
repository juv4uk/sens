//! Незалежний бар'єр Rust T5 ↔ D2 для епіка #5438 / ядра #5439.
//!
//! Канонічний .sens лишається T5. Перевіряється структура та точні ширини,
//! а НЕ ратифікація всіх D9-резидентів чи семантика дослідного .senc.
//! Це паритет двох входів до СПІЛЬНОГО CanonicalReader; незалежний
//! зовнішній D2-оракул лишається окремою задачею #5313.

use sens::{
    decode_ternary_program, decode_ternary_words, encode_ternary_words,
    parse_binary_source_words, parse_canonical_binary, parse_canonical_word_sequence,
    render_ternary_words_spaced, PhysicalT5Program, T5ExecutionError,
    TernaryTransportError,
};

fn exact_words(source: &str) -> Vec<sens::BinarySourceWord> {
    parse_binary_source_words(source)
        .expect("чинні 1–9-бітові слова")
        .into_iter()
        .map(|token| token.word)
        .collect()
}

#[test]
fn all_1022_exact_single_words_keep_width_and_agree_on_d2_admission() {
    let mut checked = 0usize;
    for width in 1usize..=9 {
        for payload in 0..(1u16 << width) {
            let visible = format!("{payload:0width$b}");
            let words = exact_words(&visible);
            assert_eq!(words.len(), 1, "ширина {width}, значення {payload}");
            assert_eq!(words[0].width(), width, "загублено початкові нулі");

            let physical = encode_ternary_words(&words).expect("канонічне T5-пакування");
            assert!(
                physical.iter().all(|byte| *byte <= 242),
                "жоден байт T5 не може бути F3/F4"
            );
            let recovered = decode_ternary_words(&physical).expect("повний фізичний оборот");
            assert_eq!(recovered, words, "ширина {width}, значення {payload}");
            assert_eq!(
                render_ternary_words_spaced(&recovered),
                visible,
                "початкові нулі є частиною точної двійкової ідентичності"
            );
            assert_eq!(encode_ternary_words(&recovered).unwrap(), physical);

            // Два незалежні способи подати ОДНІ й ті самі точні слова
            // чинному D2 reader: уже типізовані слова й видимі 0/1.
            let typed = parse_canonical_word_sequence(&recovered);
            let reference = parse_canonical_binary(&visible);
            assert_eq!(
                typed.is_ok(),
                reference.is_ok(),
                "D2 не погоджується для ширини {width}, значення {payload}"
            );

            let admitted = PhysicalT5Program::decode(&physical);
            assert_eq!(
                admitted.is_ok(),
                reference.is_ok(),
                "фізичний reader не погоджується з D2 для {visible}"
            );
            match (reference, typed, admitted) {
                (Ok(reference_forms), Ok(typed_forms), Ok(physical_program)) => {
                    assert_eq!(reference_forms.len(), typed_forms.len(), "{visible}");
                    assert_eq!(physical_program.form_count(), typed_forms.len(), "{visible}");
                    assert_eq!(decode_ternary_program(&physical).unwrap(), words);
                }
                (Err(_), Err(_), Err(T5ExecutionError::Language(_))) => {
                    assert_eq!(
                        decode_ternary_program(&physical),
                        Err(TernaryTransportError::InvalidProgramSyntax),
                        "правильний T5, неправильна граматика D2"
                    );
                }
                _ => panic!("неприпустима розбіжність між фізичним і двома D2 читачами: {visible}"),
            }
            checked += 1;
        }
    }
    assert_eq!(checked, 1022);
}

#[test]
fn f3_and_f4_are_named_invalid_t5_bytes_even_after_a_valid_payload() {
    let mut checked = 0usize;
    for width in 1usize..=9 {
        for payload in 0..(1u16 << width) {
            let visible = format!("{payload:0width$b}");
            let physical = encode_ternary_words(&exact_words(&visible)).unwrap();
            for marker in [0xf3u8, 0xf4u8] {
                let mut wrong_carrier = physical.clone();
                wrong_carrier.push(marker);
                assert_eq!(
                    decode_ternary_words(&wrong_carrier),
                    Err(TernaryTransportError::InvalidPhysicalByte),
                    "маркер F3/F4 ніколи не є продовженням T5"
                );
                assert!(matches!(
                    PhysicalT5Program::decode(&wrong_carrier),
                    Err(T5ExecutionError::Transport(
                        TernaryTransportError::InvalidPhysicalByte
                    ))
                ));
                checked += 1;
            }
        }
    }
    assert_eq!(checked, 2044);
}

#[test]
fn nested_and_multiform_t5_agree_with_the_canonical_d2_reference() {
    // Дві верхні форми; перша містить вкладену структуру з W9.
    // Це лише D2-структурна допустимість, не вимога виконати W9.
    let visible = "10 001 00 10 000000001 01 01 10 001 00 000 01";
    let words = exact_words(visible);
    let physical = encode_ternary_words(&words).expect("два верхні D2 вирази");
    assert_eq!(decode_ternary_words(&physical).unwrap(), words);
    let reference = parse_canonical_binary(visible).expect("видимий D2");
    let typed = parse_canonical_word_sequence(&words).expect("прямий typed D2");
    let physical_program = PhysicalT5Program::decode(&physical).expect("фізичний T5 D2");
    assert_eq!(reference.len(), 2);
    assert_eq!(typed.len(), 2);
    assert_eq!(physical_program.form_count(), 2);
    assert_eq!(decode_ternary_program(&physical).unwrap(), words);
}

#[test]
fn d2_grammar_failure_does_not_become_a_transport_or_adaptive_success() {
    for visible in ["01", "11", "10", "10 001", "10 11 01"] {
        let words = exact_words(visible);
        let physical = encode_ternary_words(&words).expect("фізична рамка існує");
        assert_eq!(decode_ternary_words(&physical).unwrap(), words);
        assert!(parse_canonical_binary(visible).is_err(), "{visible}");
        assert!(parse_canonical_word_sequence(&words).is_err(), "{visible}");
        assert_eq!(
            decode_ternary_program(&physical),
            Err(TernaryTransportError::InvalidProgramSyntax),
            "{visible}"
        );
        assert!(matches!(
            PhysicalT5Program::decode(&physical),
            Err(T5ExecutionError::Language(_))
        ));
    }
}
