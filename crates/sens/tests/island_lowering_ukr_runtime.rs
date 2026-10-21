//! Справжній SENS-eval: обрізане повідомлення маршруту не дістає D6 четверте.
//! Ця перевірка не є T5M-атестацією всього корпуса й не використовує Python.
use sens::{eval_parsed_expressions, load_core_library, lower_program, parse_mixed_exact_domain, Session};
const ISLAND: &str = include_str!("../../../lib/island-lowering.lisp");

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session)
        .expect("штатний bootstrap SENS має встановити виконавчі закони");
    let parsed = parse_mixed_exact_domain(ISLAND)
        .expect("український текст островів має розбиратися точним SENS reader");
    // Ратифіковані українські «так» й «ні» мають власні біти D1.
    // Без точного зниження тест шукав би їх як незв'язані змінні.
    let lowered = lower_program(&parsed);
    eval_parsed_expressions(&lowered, &mut session)
        .expect("поточні визначення островів мають виконатися у SENS");
    session
}

fn evaluated(s: &mut Session, source: &str) -> Result<sens::Value, sens::LanguageError> {
    let parsed = parse_mixed_exact_domain(source)?;
    let lowered = lower_program(&parsed);
    Ok(eval_parsed_expressions(&lowered, s)?.value)
}

fn observed(s: &mut Session, source: &str) -> String {
    evaluated(s, source)
        .unwrap_or_else(|error| panic!("SENS має виконати {source}: {error:?}"))
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
        let value = evaluated(&mut s, &format!("(острів-є-четверте-поле? {source})"))
            .expect("D3/CAR/CDR structural negative proof");
        assert_eq!(value.as_predicate_bit(), Some(false), "{source}");
    }
    for source in [
        "(як-є (mechanism-selected id common-lisp bounded-exact-add))",
        "(як-є (mechanism-selected id common-lisp (невідомий-механізм)))",
    ] {
        let value = evaluated(&mut s, &format!("(острів-є-четверте-поле? {source})"))
            .expect("D3 structural positive proof");
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
