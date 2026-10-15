//! ЛИШЕ нативний виконавець Lisp-свідків REPL, без семантичного дублювання.
//! Реальний self-hosting evaluator завантажується вже чинним pinned reader.
//! Виклик і фінальний D1-вердикт належать виключно SENS.
use sens::{
    eval_parsed_expressions, load_core_library, load_meta_evaluator_library,
    parse_mixed_exact_domain, Session,
};

const REPL: &str = include_str!("../../../lib/repl-core.lisp");
const KROK: &str = include_str!("../../../tests/semantic/repl-uk-step-law.lisp");
const KROK_MUTANT: &str = include_str!("../../../tests/semantic/repl-uk-step-mutant.lisp");
const CYKL: &str = include_str!("../../../tests/semantic/repl-uk-loop-law.lisp");
const CYKL_MUTANT: &str = include_str!("../../../tests/semantic/repl-uk-loop-mutant.lisp");
const CHERHA: &str = include_str!("../../../tests/semantic/repl-uk-queue-law.lisp");
const CHERHA_MUTANT: &str = include_str!("../../../tests/semantic/repl-uk-queue-mutant.lisp");
const VYZNACHYTY: &str = include_str!("../../../tests/semantic/repl-uk-define-function-law.lisp");
const VYZNACHYTY_MUTANT: &str = include_str!("../../../tests/semantic/repl-uk-define-function-mutant.lisp");

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session)
        .expect("test_id=repl-uk-native layer=eval core SENS bootstrap");
    load_meta_evaluator_library(&mut session)
        .expect("test_id=repl-uk-native layer=parse pinned exact-domain metacircular bootstrap");
    let program = parse_mixed_exact_domain(REPL)
        .expect("test_id=repl-uk-native layer=parse Ukrainian Lisp REPL source");
    eval_parsed_expressions(&program, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id=repl-uk-native layer=eval fixture=lib/repl-core.lisp actual={}",
            error.render(REPL)
        ));
    session
}

fn prove(positive: &str, mutant: &str, id: &str, expected_output_lines: Option<usize>) {
    let mut session = session();
    let law = parse_mixed_exact_domain(positive)
        .unwrap_or_else(|error| panic!(
            "test_id={id} layer=parse fixture=positive actual={}",
            error.render(positive)
        ));
    let evidence = eval_parsed_expressions(&law, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id={id} layer=eval fixture=positive actual={}",
            error.render(positive)
        ));
    // Лише кількість фізично опублікованих рядків: результат
    // та закон збереження стану вирішує сама SENS-програма.
    if let Some(count) = expected_output_lines {
        assert_eq!(
            evidence.output.len(),
            count,
            "test_id={id} layer=transport expected_lines={count} actual_lines={} first_diff=output_count",
            evidence.output.len()
        );
    }
    assert_eq!(
        evidence.value.as_predicate_bit(),
        Some(true),
        "test_id={id} layer=eval expected=D1:YES actual={} semantic_authority=SENS",
        evidence.value
    );
    let bad = parse_mixed_exact_domain(mutant)
        .unwrap_or_else(|error| panic!(
            "test_id={id}-mutant layer=parse fixture=mutant actual={}",
            error.render(mutant)
        ));
    let refusal = eval_parsed_expressions(&bad, &mut session)
        .expect_err("mutated SENS law must be rejected by noncallable D1");
    assert!(
        refusal.message.contains("domain identity is not callable under its ratified law: D1"),
        "test_id={id}-mutant layer=eval expected=D1-noncallable actual={}",
        refusal.render(mutant)
    );
    println!("NATIVE_SENS_PASS test_id={id} positive=D1:YES mutant=D1-noncallable");
}

#[test]
fn repl_uk_lisp_state_d1_native_self_verdict() {
    prove(KROK, KROK_MUTANT, "repl-uk-step", None);
}

#[test]
fn repl_uk_lisp_text_command_d1_native_self_verdict() {
    prove(CYKL, CYKL_MUTANT, "repl-uk-loop", None);
}

#[test]
fn repl_uk_lisp_queue_recovery_and_stop_d1_native_self_verdict() {
    // Позитивна SENS-програма містить невідоме ім'я посередині,
    // відновлює значення й відкидає небезпечний рядок після виходу.
    prove(CHERHA, CHERHA_MUTANT, "repl-uk-queue", Some(3));
}

#[test]
fn repl_uk_language_owned_d4_define_and_lambda_native_self_verdict() {
    // Сам SENS створює вирази D4 ФУНКЦІЯ/ВИЗНАЧИТИ, визначає
    // функцію та значення і доводить виконання тільки D1:1.
    prove(VYZNACHYTY, VYZNACHYTY_MUTANT, "repl-uk-define-function", None);
}
