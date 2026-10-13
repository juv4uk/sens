//! Механічний transport двійкового SENS-свідка; жодного Rust-оракула логіки.
use sens::{
    eval_parsed_expressions, load_core_library, load_tcp_library,
    parse_mixed_exact_domain_process_tcp_source, ExprKind, Session,
};

const TCP_PATH: &str = "lib/tcp.lisp";
const TCP_SOURCE: &str = include_str!("../../../lib/tcp.lisp");
const SELFTEST: &str = include_str!("../../../tests/fixtures/semantic/tcp-exact-selftest.lisp");

#[test]
fn tcp_semantic_law_is_decided_by_binary_sens_only() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("допущене ядро D3/D4");
    load_tcp_library(&mut session).expect("чинний TCP-модуль SENS");
    let program = parse_mixed_exact_domain_process_tcp_source(TCP_PATH, SELFTEST)
        .expect("двійкові D3/D4/D8/D9 голови, дані не виконуються як код");
    let result = eval_parsed_expressions(&program, &mut session)
        .expect("SENS-виконавець на власній програмі-свідку");
    // Rust лише спостерігає єдиний підсумковий D1; усі умови та
    // позитивні/негативні гілки сформульовані самою мовою SENS.
    assert_eq!(result.value.as_predicate_bit(), Some(true), "SENS повернув D1:NO");
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
