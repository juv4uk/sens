//! Runtime witness for thirty exact-D1 native-first source cuts.
//! Історичні обгортки D1 фізично вилучено: використовуємо тільки прямі D1.
use sens::{
    eval_parsed_expressions, parse_mixed_exact_domain_machine_source, ErrorKind,
    Session,
};

const PATH: &str = "lib/machine/dispatch/native-first.lisp";
const SOURCE: &str = include_str!("../../../lib/machine/dispatch/native-first.lisp");

fn eval(session: &mut Session, source: &str) -> Result<sens::Value, sens::LanguageError> {
    let forms = parse_mixed_exact_domain_machine_source(PATH, source)?;
    Ok(eval_parsed_expressions(&forms, session)?.value)
}

fn session() -> Session {
    let mut s = Session::default();
    let defs = parse_mixed_exact_domain_machine_source(PATH, SOURCE)
        .expect("current exact machine reader");
    assert_eq!(defs.len(), 16);
    eval_parsed_expressions(&defs, &mut s)
        .expect("усі 16 визначень native-first завантажені через SENS");
    s
}

#[test]
fn ratified_ukr_d1_values_are_direct_predicate_bits() {
    let mut s = session();
    for (surface, expected) in [("так", true), ("ні", false)] {
        let value = eval(&mut s, surface).expect("SENS читає ратифіковане значення D1");
        assert_eq!(value.as_predicate_bit(), Some(expected));
    }
}

#[test]
fn real_native_first_classifier_still_rejects_unlowerable_forms() {
    let mut s = session();
    for argument in ["(як-є ())", "(як-є (symbol))"] {
        let source = format!("(класифікувати-нативний-вираз {argument})");
        let value = eval(&mut s, &source).expect("native-first evaluation for unsupported form");
        assert!(value.to_string().starts_with("(evaluator-fallback "),
            "{source} must use evaluator-fallback; got {value}");
    }
}

#[test]
fn real_native_first_classifier_handles_atomic_and_compound_heads() {
    let mut s = session();
    // Атомарна голова D3 CAR із непридатним аргументом має відступити,
    // а не бути відкинута до зіставлення викличної голови.
    // Складену голову не можна подавати до D3 EQ (порівнює лише атоми).
    for source in [
        "(класифікувати-нативний-вираз (як-є (перше 1)))",
        "(класифікувати-нативний-вираз (як-є ((функція (значення) значення) 1)))",
    ] {
        let value = eval(&mut s, source)
            .expect("SENS classifier must not apply D3 EQ to a pair head");
        assert!(
            value.to_string().starts_with("(evaluator-fallback "),
            "{source} must preserve evaluator fallback; got {value}"
        );
    }
}

#[test]
fn dotted_tail_is_not_a_valid_single_argument_car_plan() {
    let mut s = session();
    // Це реальна Lisp-структура, прочитана SENS, а не текстовий підрахунок.
    let source = "(класифікувати-нативний-вираз (як-є (перше (сполучити 2 3) . зайвий-хвіст)))";
    let result = eval(&mut s, source).expect("SENS має відхилити dotted CAR до x86");
    assert!(
        result.to_string().starts_with("(evaluator-fallback "),
        "пошкоджена арність не повинна створювати native-plan: {result}"
    );
}

#[test]
fn typed_native_operands_use_named_sens_execution_not_anonymous_d5_value_call() {
    let mut s = session();
    // Позитивні runtime-свідки: непридатний лівий чи правий операнд
    // зберігає исходний вираз; невикличний D5 FUNCTION не виконується.
    for source in [
        "(нативний-план-пари-типізовані-операнди (як-є джерело) (як-є ()) (як-є (u64-imm аргумент)))",
        "(нативний-план-пари-типізовані-операнди (як-є джерело) (як-є (u64-imm аргумент)) (як-є ()))",
    ] {
        let result = eval(&mut s, source).expect("іменована функція SENS повинна виконатися");
        assert_eq!(result.to_string(), "(evaluator-fallback джерело)", "{source}");
    }
    // Негативний свідок: історична анонімна голова не допущена.
    let error = eval(&mut s, "((функція (значення) значення) (як-є джерело))")
        .expect_err("не можна повернути нератифікований D5 value-call");
    assert!(error.message.contains("00001"), "{error}");
}

#[test]
fn no_coercion_from_empty_list_or_numeric_one_into_d1() {
    let mut s = session();
    for source in ["(хибне? (як-є ()))", "(хибне? 1)"] {
        let error = eval(&mut s, source).expect_err("exact D4 NOT must reject non-D1");
        assert_eq!(error.kind, ErrorKind::Type);
    }
}

#[test]
fn exact_reader_does_not_generalize_machine_source_paths() {
    assert!(!SOURCE.contains("#d1:"));
    assert!(!SOURCE.contains("(визначити native-first-domain-true"));
    assert!(!SOURCE.contains("(визначити native-first-domain-false"));
    assert!(parse_mixed_exact_domain_machine_source("lib/untrusted.lisp", SOURCE).is_err());
}


#[test]
fn lexical_shape_callback_preserves_exact_d3_width_and_predicate_bits() {
    // Реальний SENS eval викликає лексичну функцію форма-або-порожньо
    // у позиції голови, а не SID8/D8 dispatcher.
    // SHAPE-OR-EMPTY повертає (width (D1 D1 D1)).
    let mut s = session();
    for (width, a, b, c, expected_car, expected_cons) in [
        (3, "так", "ні", "ні", true, false),
        (3, "так", "так", "так", false, true),
        (4, "так", "ні", "ні", false, false),
    ] {
        let callback = format!(
            "(функція (проба) (сполучити {width} (сполучити \
             (сполучити {a} (сполучити {b} (сполучити {c} ()))) ())))"
        );
        for (head, expected) in [
            ("нативний-домен-перше?", expected_car),
            ("нативний-домен-сполучити?", expected_cons),
        ] {
            let source = format!("({head} {callback} (як-є довільне))");
            let actual = eval(&mut s, &source)
                .expect("SENS must apply the lexically bound shape callback");
            assert_eq!(actual.as_predicate_bit(), Some(expected), "{source}");
        }
    }
}
