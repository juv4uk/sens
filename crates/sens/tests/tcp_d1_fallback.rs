//! Механічний transport двійкового SENS-свідка; жодного Rust-оракула логіки.
use sens::{
    decode_ternary_program, encode_ternary_words, eval_t5_program,
    load_core_library, load_tcp_library, parse_binary_source_words,
    parse_mixed_exact_domain_process_tcp_source, ExprKind, Session,
};

const TCP_PATH: &str = "lib/tcp.lisp";
const TCP_SOURCE: &str = include_str!("../../../lib/tcp.lisp");
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
        .into_iter().map(|token| token.word).collect::<Vec<_>>();
    assert_eq!(words.len(), 51, "точний D2 синтаксичний транспорт");
    assert_eq!(words.iter().map(|word| word.width()).sum::<usize>(), 127);
    let physical = encode_ternary_words(&words).expect("безвтратне D2/T5");
    assert_eq!(decode_ternary_program(&physical).expect("фізичний T5"), words);

    let verdict = eval_t5_program(&physical, &mut session)
        .expect("фізичний SENS-виконавець виконує власний TCP-свідок");
    assert_eq!(verdict.value.as_predicate_bit(), Some(true), "SENS повернув D1:NO");
}

#[test]
fn tcp_two_one_binding_sites_are_d4_lambda_not_d6_let() {
    let forms = parse_mixed_exact_domain_process_tcp_source(TCP_PATH, TCP_SOURCE)
        .expect("лише власний TCP шлях може інтерпретувати ці доменні голови");
    assert_eq!(forms.len(), 7, "сім зовнішніх TCP визначень збережено");

    for name in ["tcp-read-bytes->text", "tcp-write-via-raw"] {
        let entry = forms.iter().find(|expr| {
            let ExprKind::List(parts) = &expr.kind else { return false };
            matches!(
                parts.get(1).map(|part| &part.kind),
                Some(ExprKind::Symbol(symbol)) if symbol.as_ref() == name
            )
        }).expect("точне визначення не зникло");

        let ExprKind::List(define) = &entry.kind else { panic!("DEFINE") };
        let ExprKind::List(lambda) = &define[2].kind else { panic!("LAMBDA") };
        let ExprKind::List(application) = &lambda[2].kind else { panic!("застосування") };
        assert_eq!(application.len(), 2, "рівно один ініціалізатор");
        let ExprKind::List(closure) = &application[0].kind else { panic!("внутрішня LAMBDA") };
        assert!(matches!(
            &closure[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 4 && id.packed_bits() == 0b0010
        ), "D4:0010 має власну ширину, не старе D6:001000");
        assert_eq!(closure.len(), 3, "одне тіло");
        let ExprKind::List(parameters) = &closure[1].kind else { panic!("параметри") };
        assert_eq!(parameters.len(), 1);
    }

    assert!(!TCP_SOURCE.contains("(001000 "), "історичний D6 LET не лишається");
    assert!(parse_mixed_exact_domain_process_tcp_source("lib/untrusted.lisp", SELFTEST).is_err());
}
