
//! Exhaustive two-state D1 fallback for migrated TCP source; no UTF-8/D24 dependency.
use sens::{eval_parsed_expressions, parse_mixed_exact_domain_process_tcp_source, ErrorKind, Session};
use sens_cli::zig_transport;

const PATH: &str = "lib/tcp.lisp";
const SOURCE: &str = include_str!("../../../lib/tcp.lisp");

fn eval_exact(source: &str) -> Result<sens::Value, sens::LanguageError> {
    let parsed = parse_mixed_exact_domain_process_tcp_source(PATH, source)?;
    Ok(eval_parsed_expressions(&parsed, &mut Session::default())?.value)
}




#[test]
fn fallback_value_is_strict_d1_yes_and_not_number_one() {
    let yes = eval_exact("#d1:1").expect("current exact D1 YES");
    assert_eq!(yes.as_predicate_bit(), Some(true));
    let no = eval_exact("#d1:0").expect("current exact D1 NO");
    assert_eq!(no.as_predicate_bit(), Some(false));
    let historical =
        eval_exact("(010 (001 ()))").expect("previous D3 ATOM(QUOTE EMPTY) must yield same D1 YES");
    assert_eq!(historical.as_predicate_bit(), yes.as_predicate_bit());
    let error = eval_exact("(0100 (001 ()))")
        .expect_err("D4 NOT must reject structural EMPTY, not coerce it to D1 NO");
    assert_eq!(error.kind, ErrorKind::Type);
    assert!(error.message.contains("D1"));
}

#[test]
fn both_d1_cond_outcomes_preserve_tcp_tag_dispatch() {
    for (source, expected) in [
        (
            "(110 ((101 (001 decoded) (001 decoded)) (001 text)) (#d1:1 (001 fallback)))",
            "text",
        ),
        (
            "(110 ((101 (001 rejected) (001 decoded)) (001 text)) (#d1:1 (001 fallback)))",
            "fallback",
        ),
    ] {
        let actual = eval_exact(source).expect("D3 COND with strict D1 equality and fallback");
        assert_eq!(actual.to_string(), expected);
    }
}

#[test]
fn numeric_one_cannot_substitute_for_d1_truth_in_cond() {
    let error =
        eval_exact("(110 ((101 (001 rejected) (001 decoded)) (001 text)) (1 (001 fallback)))")
            .expect_err("unqualified number 1 is not a D1 predicate");
    assert!(matches!(
        error.kind,
        ErrorKind::Type | ErrorKind::InvalidForm
    ));
}

#[test]
fn real_tcp_file_reads_with_current_domain_widths() {
    let parsed = parse_mixed_exact_domain_process_tcp_source(PATH, SOURCE)
        .expect("pinned real TCP module must parse");
    assert_eq!(parsed.len(), 8);
    let code_only = SOURCE
        .lines()
        .filter(|line| !line.trim_start().starts_with(';'))
        .collect::<Vec<_>>()
        .join("\n");
    assert_eq!(code_only.matches("(успішно-декодовано?").count(), 1);
    assert!(!code_only.contains("(010 "));
    assert!(!code_only.contains("(0100 "));
    assert!(parse_mixed_exact_domain_process_tcp_source("lib/untrusted.lisp", SOURCE).is_err());
}

mod support;

use sens::{
    load_core_library, load_tcp_library,
    parse_binary_source_words, ExprKind,
};
const SELFTEST: &str = include_str!("../../../tests/fixtures/semantic/tcp-exact-selftest.bits");

#[test]
fn tcp_semantic_law_is_decided_by_physical_binary_sens_only() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("допущене ядро D3/D4");
    load_tcp_library(&mut session).expect("чинний TCP-модуль SENS");

    // Транспорт кодує САМІ точні слова W1/W2/W3/W9 та не визначає
    // expected UTF-8/TCP значень. Єдиний семантичний оракул — SENS.
    let words = parse_binary_source_words(SELFTEST)
        .expect("жодних людських викличних голів або некваліфікованих чисел")
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    assert_eq!(words.len(), 51, "точний D2 синтаксичний транспорт");
    assert_eq!(words.iter().map(|word| word.width()).sum::<usize>(), 127);
    let physical = zig_transport::encode_t5m_direct(&words).expect("безвтратне фізичне Zig T5M");
    assert_eq!(
        zig_transport::decode_t5m_words(&physical).expect("фізичний T5M"),
        words
    );

    let verdict = support::eval_reference_t5m(&physical, &mut session)
        .expect("фізичний SENS-виконавець виконує власний TCP-свідок");
    assert_eq!(
        verdict.value.as_predicate_bit(),
        Some(true),
        "SENS повернув D1:NO"
    );
}

#[test]
fn tcp_definitions_use_d4_function_forms_without_d6_let_heads() {
    let forms = parse_mixed_exact_domain_process_tcp_source(PATH, SOURCE)
        .expect("лише власний TCP шлях може інтерпретувати ці доменні голови");
    assert_eq!(forms.len(), 8, "вісім зовнішніх TCP визначень збережено");

    for entry in &forms {
        let ExprKind::List(define) = &entry.kind else {
            panic!("кожен зовнішній запис — визначення")
        };
        assert_eq!(define.len(), 3, "визначення має ім'я та тіло");
        let ExprKind::List(function) = &define[2].kind else {
            panic!("тіло визначення — функція D4")
        };
        assert!(
            matches!(
                &function[0].kind,
                ExprKind::DomainIdentity(id) if id.width() == 4 && id.packed_bits() == 0b0010
            ),
            "кожна визначена функція має точну identity D4:0010"
        );
        assert_eq!(function.len(), 3, "функція має параметри й тіло");
        assert!(
            matches!(&function[1].kind, ExprKind::List(_)),
            "параметри функції"
        );
    }

    assert!(
        !SOURCE.contains("(001000 "),
        "історичний D6 LET не лишається"
    );
    assert!(parse_mixed_exact_domain_process_tcp_source("lib/untrusted.lisp", SELFTEST).is_err());
}
