//! Живі SENS-свідки чинного пакетного оракула та генератора функцій.
//! Rust лише запускає справжній SENS та порівнює обчислені значення.
//! Не воскресати вилучені HTTP/TCP-вузли та історичні параметри.
//! Ні Python, ні JSON не є семантичним оракулом.

use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse_mixed_exact_domain, Session,
};

fn install_section(source: &str, begin: &str, end: &str, session: &mut Session) {
    let from = source
        .find(begin)
        .expect("test_id=script-d1 source definition exists");
    let to = source[from..]
        .find(end)
        .expect("test_id=script-d1 definition boundary");
    let fragment = &source[from..from + to];
    let forms = parse_mixed_exact_domain(fragment)
        .unwrap_or_else(|error| panic!("test_id=script-d1 layer=reader input={begin}: {error}"));
    eval_parsed_expressions(&forms, session)
        .unwrap_or_else(|error| panic!("test_id=script-d1 layer=SENS define={begin}: {error}"));
}

#[test]
fn oracle_batch_current_definition_executes_as_sens_data() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("test_id=oracle-batch-live SENS core");
    let source = include_str!("../../../scripts/oracle-batch.lisp");

    // Виконуємо джерело повністю: його останній вираз є викликом власної функції.
    let observed = eval_program(source, &mut session)
        .expect("test_id=oracle-batch-live layer=SENS execute committed program");
    let expected = eval_program("(як-є (oracle-batch (status pass)))", &mut session)
        .expect("test_id=oracle-batch-live layer=SENS expected quoted D7 data");
    assert_eq!(
        observed.value, expected.value,
        "test_id=oracle-batch-live layer=SENS input=committed-program expected=quoted-status-pass"
    );

    let invoked = eval_program("(пакетний-оракул)", &mut session)
        .expect("test_id=oracle-batch-live layer=SENS explicit re-execution");
    assert_eq!(
        invoked.value, observed.value,
        "test_id=oracle-batch-live layer=SENS repeated invocation must preserve result"
    );
}

#[test]
fn oracle_batch_status_mutation_has_a_real_negative_sens_witness() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("test_id=oracle-batch-mutant SENS core");
    let original = include_str!("../../../scripts/oracle-batch.lisp");
    let mutation_source = original.replace("(status pass)", "(status fail)");
    assert_ne!(
        mutation_source, original,
        "test_id=oracle-batch-mutant source must contain status pass"
    );

    let accepted = eval_program(original, &mut session)
        .expect("test_id=oracle-batch-mutant layer=SENS original program");
    let changed = eval_program(&mutation_source, &mut session)
        .expect("test_id=oracle-batch-mutant layer=SENS mutated program");
    let expected_mutation = eval_program("(як-є (oracle-batch (status fail)))", &mut session)
        .expect("test_id=oracle-batch-mutant layer=SENS negative quoted data");
    assert_eq!(
        changed.value, expected_mutation.value,
        "test_id=oracle-batch-mutant layer=SENS mutated program must execute exact changed data"
    );
    assert_ne!(
        accepted.value, changed.value,
        "test_id=oracle-batch-mutant layer=SENS negative status must not be accepted as pass"
    );
}

#[test]
fn function_listing_empty_input_evaluates_real_d1_without_textual_true() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("test_id=gen-functions-d1 SENS core");
    let source = include_str!("../../../scripts/gen-functions.lisp");
    install_section(
        source,
        "(визначити видати-пару",
        "\n(видати вбудовані)",
        &mut session,
    );
    let observed = eval_program("(видати (як-є ()))", &mut session)
        .expect("test_id=gen-functions-d1 layer=SENS empty list");
    let expected =
        eval_program("(як-є ())", &mut session).expect("test_id=gen-functions-d1 quoted D3 empty");
    assert_eq!(
        observed.value, expected.value,
        "test_id=gen-functions-d1 layer=SENS input=() expected=D3:000 empty"
    );
}
