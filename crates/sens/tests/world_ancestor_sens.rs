//! Native SENS executes its own self-verdicts; Rust only loads source and observes D1/error receipts.

use sens::{
    eval_parsed_expressions, eval_core_library_source,
    eval_pinned_reasoning_source, parse_mixed_exact_domain, Session,
};

const WORLD_WITNESSES: &str =
    include_str!("../../../tests/semantic/world-exact-arity-witness.lisp");
const ANCESTOR_LAW: &str =
    include_str!("../../../tests/semantic/world-ancestor-d1-law.lisp");
const ANCESTOR_MUTANT: &str =
    include_str!("../../../tests/semantic/world-ancestor-d1-mutant.lisp");

fn world_session() -> Session {
    let mut session = Session::default();
    sens::load_core_library(&mut session)
        .expect("штатний Core4 loader встановлює чинні D8 механізми");
    eval_core_library_source(include_str!("../../../lib/core.lisp"),
        &mut session,
    )
    .expect("pinned Core must load before the actual SENS World");
    for (path, source) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
        ("lib/forward.lisp", include_str!("../../../lib/forward.lisp")),
        ("lib/knowledge.lisp", include_str!("../../../lib/knowledge.lisp")),
        ("lib/world.lisp", include_str!("../../../lib/world.lisp")),
    ] {
        eval_pinned_reasoning_source(path, source, &mut session)
            .unwrap_or_else(|error| panic!("SENS library {path}: {error}"));
    }
    session
}

/// The fixture contains executable SENS self-verdicts. The host observes only
/// their exact D1:YES completion; it does not calculate the ancestor or encode
/// a second expected-result table.
fn native_sens_self_verdicts(source: &str, fixture: &str) -> usize {
    let parsed = parse_mixed_exact_domain(source)
        .unwrap_or_else(|error| panic!("test_id=world-ancestor layer=parse fixture={fixture} error={error}"));
    assert!(!parsed.is_empty(), "test_id=world-ancestor fixture={fixture} is empty");
    let mut session = world_session();
    for (i, expression) in parsed.iter().enumerate() {
        let result = eval_parsed_expressions(std::slice::from_ref(expression), &mut session)
            .unwrap_or_else(|error| {
                panic!("test_id=world-ancestor layer=eval fixture={fixture} form={i} error={error}")
            });
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(true),
            "SENS self-verdict must complete with exact D1:YES; fixture={fixture} form={i} actual={:?}",
            result.value,
        );
    }
    parsed.len()
}

#[test]
fn world_ancestor_is_proved_by_native_sens() {
    let witnessed = native_sens_self_verdicts(
        WORLD_WITNESSES,
        "tests/semantic/world-exact-arity-witness.lisp",
    );
    assert_eq!(witnessed, 28, "world self-verdict fixture retains the 28 currently admitted executable SENS assertions");
}

#[test]
fn world_ancestor_one_bit_mutant_is_rejected_by_sens() {
    assert_eq!(ANCESTOR_LAW.matches("      так)\n").count(), 1,
        "law has exactly one human-projected D1:YES witness");
    assert_eq!(ANCESTOR_MUTANT.matches("      ні)\n").count(), 1,
        "mutant has exactly one human-projected D1:NO witness");
    assert_eq!(ANCESTOR_LAW,
        ANCESTOR_MUTANT.replacen("      ні)\n", "      так)\n", 1),
        "only the D1 yes/no projection changes; UTF-8 byte lengths may differ");

    assert_eq!(
        native_sens_self_verdicts(ANCESTOR_LAW, "tests/semantic/world-ancestor-d1-law.lisp"),
        1
    );

    let parsed = parse_mixed_exact_domain(ANCESTOR_MUTANT)
        .expect("one-bit mutant remains syntactically valid exact-domain SENS");
    assert_eq!(parsed.len(), 1, "mutant must remain one executable SENS self-verdict");
    let mut session = world_session();
    let result = eval_parsed_expressions(&parsed, &mut session);
    let error = match result {
        Ok(value) => panic!("SENS admitted its one-bit falsifier; unexpected value {:?}", value.value),
        Err(error) => error,
    };
    assert!(
        error.to_string().contains("not callable"),
        "the mutated D1:NO branch must fail inside SENS as non-callable, got: {error}"
    );
}

const WORLD_MODULE_LAWS: &str =
    include_str!("../../../tests/semantic/d9-world-shape-module-events-laws.lisp");

/// Чинний SENS сам обчислює десять законів D9 над реальними Lisp
/// визначеннями світу. Rust перевіряє лише спостережуваний D1 результат,
/// а не імітує WORLD?/рівність або машинний D7.
#[test]
fn world_module_ten_laws_execute_in_sens() {
    let mut session = world_session();
    let forms = parse_mixed_exact_domain(WORLD_MODULE_LAWS)
        .expect("український файл десяти D9 законів повинен читатися");
    assert_eq!(forms.len(), 1, "одна виконувана форма, десять незалежних D1 результатів");
    let actual = eval_parsed_expressions(&forms, &mut session)
        .expect("SENS мусить реально виконати українську програму");
    assert_eq!(actual.value.to_string(), "(1 1 1 1 1 1 1 1 1 1)",
        "реальні D1 відповіді SENS по всіх десяти законах");

    // Один неправдивий світ не можна перетворити на успіх зміною
    // форматування/проєкції. Негативний свідок виконує той самий SENS.
    let old = "(хибне? (світ? (як-є world)))";
    let new = "(світ? (як-є world))";
    assert_eq!(WORLD_MODULE_LAWS.matches(old).count(), 1,
        "негативний якір рівно один у чинному джерелі");
    let mutant = WORLD_MODULE_LAWS.replacen(old, new, 1);
    let mutant_forms = parse_mixed_exact_domain(&mutant)
        .expect("мутант лишається синтаксично точним SENS");
    let bad = eval_parsed_expressions(&mutant_forms, &mut world_session())
        .expect("SENS обчислює також відмінний негативний свідок");
    assert_eq!(bad.value.to_string(), "(1 1 0 1 1 1 1 1 1 1)",
        "підмінений закон має дати реальний D1:NO, а не PASS");
}

#[test]
fn world_module_unknown_name_is_rejected_by_sens_d1() {
    let mut session = world_session();
    let query = "(світ-модуль-відомий? (створити-світ (як-є ()) (список (як-є (tell альфа факт-а))) (як-є ())) (як-є бета))";
    let forms = parse_mixed_exact_domain(query)
        .expect("чинний український D9 запит повинен читатися точно");
    let result = eval_parsed_expressions(&forms, &mut session)
        .expect("сам SENS має повернути D1:NO для невідомого модуля");
    assert_eq!(result.value.to_string(), "0",
        "чужий модуль не успадковує світовий журнал іншого модуля");
}

const D11_REMOVE_FIRST_LAW: &str =
    include_str!("../../../tests/semantic/d11-world-remove-first-law.lisp");

#[test]
fn d11_world_remove_first_native_law_and_mutant() {
    // Закон виконує сам SENS над чинним lib/world.lisp.
    assert_eq!(
        native_sens_self_verdicts(
            D11_REMOVE_FIRST_LAW,
            "tests/semantic/d11-world-remove-first-law.lisp",
        ),
        5,
        "test_id=D11-WORLD-REMOVE-FIRST-5"
    );

    // Однобітне негативне твердження: результат із двома вилученими
    // входженнями має повернути D1:0, а не успіх.
    let real = "(як-є (б а в)))";
    let wrong = "(як-є (б в)))";
    assert_eq!(D11_REMOVE_FIRST_LAW.matches(real).count(), 1,
        "test_id=D11-WORLD-REMOVE-FIRST-MUTATION-ANCHOR");
    let mutated = D11_REMOVE_FIRST_LAW.replacen(real, wrong, 1);
    let forms = parse_mixed_exact_domain(&mutated)
        .expect("D11 negative world-law fixture remains valid SENS");
    let mut session = world_session();
    let first = eval_parsed_expressions(std::slice::from_ref(&forms[0]), &mut session)
        .expect("D11 mutated world statement runs in SENS");
    assert_eq!(
        first.value.as_predicate_bit(),
        Some(false),
        "test_id=D11-WORLD-REMOVE-FIRST-MUTANT layer=SENS expected=D1:0 actual={:?}",
        first.value,
    );
}
