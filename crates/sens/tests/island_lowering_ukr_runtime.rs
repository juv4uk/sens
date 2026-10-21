//! Справжній SENS-eval: обрізане повідомлення маршруту не дістає D6 четверте.
//! Ця перевірка не є T5M-атестацією всього корпуса й не використовує Python.
use sens::{eval_core_library_source, eval_program, Session};

const CORE: &str = include_str!("../../../lib/core.lisp");
const ISLAND: &str = include_str!("../../../lib/island-lowering.lisp");

fn session() -> Session {
    let mut session = Session::default();
    eval_core_library_source(CORE, &mut session)
        .expect("чинне українське ядро SENS повинно завантажитись");
    eval_program(ISLAND, &mut session)
        .expect("поточні визначення островів мають виконатися у SENS");
    session
}

fn observed(s: &mut Session, source: &str) -> String {
    eval_program(source, s)
        .unwrap_or_else(|error| panic!("SENS має виконати {source}: {error:?}"))
        .value
        .to_string()
}

#[test]
fn d3_guard_checks_the_fourth_field_before_the_d6_selector() {
    let mut s = session();
    for source in [
        "(як-є ())",
        "(як-є (mechanism-selected))",
        "(як-є (mechanism-selected id))",
        "(як-є (mechanism-selected id common-lisp))",
        "(як-є (mechanism-selected . хвіст))",
    ] {
        let value = eval_program(
            &format!("(острів-є-четверте-поле? {source})"), &mut s
        ).expect("D3/CAR/CDR structural negative proof").value;
        assert_eq!(value.as_predicate_bit(), Some(false), "{source}");
    }
    for source in [
        "(як-є (mechanism-selected id common-lisp bounded-exact-add))",
        "(як-є (mechanism-selected id common-lisp (невідомий-механізм)))",
    ] {
        let value = eval_program(
            &format!("(острів-є-четверте-поле? {source})"), &mut s
        ).expect("D3 structural positive proof").value;
        assert_eq!(value.as_predicate_bit(), Some(true), "{source}");
    }
}

#[test]
fn truncated_mechanism_selected_is_named_failure_not_cdr_error() {
    let mut s = session();
    for selected in [
        "(як-є (mechanism-selected))",
        "(як-є (mechanism-selected id))",
        "(як-є (mechanism-selected id common-lisp))",
        "(як-є (mechanism-selected . хвіст))",
    ] {
        let query = format!(
            "(острів-обробити-вибір (як-є id) (як-є common-lisp) 2 3 {selected})"
        );
        assert_eq!(
            observed(&mut s, &query),
            "(island-lowering-failure malformed-selection id common-lisp)",
            "{query}"
        );
    }
    let passthrough = observed(
        &mut s,
        "(острів-обробити-вибір (як-є id) (як-є common-lisp) 2 3 (як-є (mechanism-unavailable id common-lisp)))",
    );
    assert_eq!(passthrough, "(mechanism-unavailable id common-lisp)");
}
