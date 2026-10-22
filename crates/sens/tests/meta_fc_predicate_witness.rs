//! CI transport only: both predicates and their expected answers live in binary SENS.
//! No Rust truth table or independent semantic authority.
use sens::{
    eval_parsed_expressions, load_core_library, parse_mixed_exact_domain, ErrorKind, EvalResult,
    LanguageError, Session,
};

const LAW: &str = include_str!("../../../tests/semantic/meta-fc-predicates-d1-law.lisp");
const MUTANT: &str = include_str!("../../../tests/semantic/meta-fc-predicates-d1-mutant.lisp");

fn exact(source: &str, session: &mut Session) -> Result<EvalResult, LanguageError> {
    let forms = parse_mixed_exact_domain(source)?;
    eval_parsed_expressions(&forms, session)
}

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session)
        .expect("test_id=meta-fc-d1: admitted exact-domain core must load");
    exact(
        include_str!("../../../lib/meta-eval-first-class.lisp"),
        &mut session,
    )
    .expect("test_id=meta-fc-d1: source must load through exact-domain reader");
    session
}

#[test]
fn first_class_sequential_body_executes_in_sens_and_preserves_last_result() {
    // Справжній SENS evaluator виконує обидві цитовані форми.
    // LET* лише впорядковує обчислення: тут немає Python/JSON oracle.
    let mut live = session();
    let source = "(першокласне-обчислити-тіло
        (як-є ((як-є ()) (як-є (()))))
        першокласне-початкове-середовище)";
    let observed = exact(source, &mut live).unwrap_or_else(|err| {
        panic!("test_id=meta-fc-body-order layer=eval expected=quoted-pair actual={err}")
    });
    assert_eq!(
        observed.value.to_string(),
        "(())",
        "test_id=meta-fc-body-order: друга форма повинна бути результатом SENS"
    );
}

#[test]
fn first_class_predicates_obey_sens_d1_law_and_reject_one_bit_mutant() {
    let changes: Vec<_> = LAW
        .bytes()
        .zip(MUTANT.bytes())
        .enumerate()
        .filter(|(_, (left, right))| left != right)
        .collect();
    assert_eq!(
        LAW.len(),
        MUTANT.len(),
        "test_id=meta-fc-d1: fixture sizes drifted"
    );
    assert_eq!(
        changes.len(),
        1,
        "test_id=meta-fc-d1: mutant must flip one physical source bit"
    );
    assert_eq!(
        changes[0].1,
        (b'0', b'1'),
        "test_id=meta-fc-d1: mutation must be D1:NO to D1:YES"
    );

    let law = exact(LAW, &mut session())
        .unwrap_or_else(|err| panic!("test_id=meta-fc-d1-law layer=eval fixture=tests/semantic/meta-fc-predicates-d1-law.lisp reproduce=cargo test --locked -p sens --test meta_fc_predicate_witness -- --nocapture actual={err}"));
    assert_eq!(
        law.value.as_predicate_bit(),
        Some(true),
        "test_id=meta-fc-d1-law: only SENS D1:YES is a positive verdict"
    );

    let error = exact(MUTANT, &mut session())
        .expect_err("test_id=meta-fc-d1-mutant: one-bit violation must invoke non-callable D1:NO");
    assert!(
        matches!(error.kind, ErrorKind::Type | ErrorKind::InvalidForm),
        "test_id=meta-fc-d1-mutant layer=eval expected=non-callable-D1 actual={error}"
    );
}

/// D11: значення-примітив і замикання розрізняються у самій SENS,
/// без нового opcode й без Rust-оракула для CAR/CDR.
#[test]
fn d11_first_class_primitive_and_closure_types_are_native_d1() {
    let mut s = session();
    for (id, input, expected) in [
        ("primitive-constructed", "(першокласний-примітив? (першокласний-примітив (як-є перше)))", true),
        ("primitive-quoted", "(першокласний-примітив? (як-є (примітив сполучити)))", true),
        ("primitive-not-closure", "(першокласне-замикання? (першокласний-примітив (як-є перше)))", false),
        ("primitive-not-empty", "(першокласний-примітив? (як-є ()))", false),
        ("primitive-not-atom", "(першокласний-примітив? (як-є примітив))", false),
        ("primitive-not-ordinary-pair", "(першокласний-примітив? (як-є (значення примітив)))", false),
        ("closure-constructed", "(першокласне-замикання? (як-є (замикання (х) (х) ())))", true),
        ("closure-not-primitive", "(першокласний-примітив? (як-є (замикання (х) (х) ())))", false),
        ("closure-not-atom", "(першокласне-замикання? (як-є замикання))", false),
        ("closure-not-empty", "(першокласне-замикання? (як-є ()))", false),
        ("closure-not-wrong-tag", "(першокласне-замикання? (як-є (примітив перше)))", false),
    ] {
        let verdict = exact(input, &mut s)
            .unwrap_or_else(|e| panic!(
                "test_id=D11-FIRST-CLASS-{id} layer=SENS input={input} expected=D1:{expected} actual_error={e}"
            ))
            .value;
        assert_eq!(
            verdict.as_predicate_bit(), Some(expected),
            "test_id=D11-FIRST-CLASS-{id} layer=SENS input={input} expected=D1:{expected} actual={verdict}"
        );
    }
}

/// D11: лексична видимість — перше зв'язування перемагає, а відсутнє
/// ім'я не породжує host-значення. Свідки обчислює лише SENS.
#[test]
fn d11_first_class_lexical_lookup_and_parameter_binding_preserve_order() {
    let mut s = session();
    for (id, input, expected) in [
        ("lookup-first", "(першокласне-знайти-в-середовищі (як-є ключ) (як-є ((ключ . нове) (ключ . старе))))", "нове"),
        ("lookup-second", "(першокласне-знайти-в-середовищі (як-є другий) (як-є ((перший . а) (другий . б))))", "б"),
        ("lookup-missing", "(першокласне-знайти-в-середовищі (як-є немає) (як-є ((перший . а))))", "немає"),
        ("lookup-empty", "(першокласне-знайти-в-середовищі (як-є немає) (як-є ()))", "немає"),
        ("lookup-primitive-value", "(першокласне-знайти-в-середовищі (як-є перше) першокласне-початкове-середовище)", "(примітив перше)"),
        ("bind-empty", "(першокласне-звязати-параметри (як-є ()) (як-є ()) (як-є ((вільне . старе))))", "((вільне . старе))"),
        ("bind-one", "(першокласне-звязати-параметри (як-є (х)) (як-є (нове)) (як-є ()))", "((х . нове))"),
        ("bind-two", "(першокласне-звязати-параметри (як-є (х у)) (як-є (ліве праве)) (як-є ((вільне . збережено))))", "((х . ліве) (у . праве) (вільне . збережено))"),
        ("bind-shadows", "(першокласне-звязати-параметри (як-є (х)) (як-є (нове)) (як-є ((х . старе))))", "((х . нове) (х . старе))"),
    ] {
        let actual = exact(input, &mut s)
            .unwrap_or_else(|e| panic!(
                "test_id=D11-LEXICAL-{id} layer=SENS input={input} expected={expected} actual_error={e}"
            ))
            .value.to_string();
        assert_eq!(
            actual, expected,
            "test_id=D11-LEXICAL-{id} layer=SENS input={input} expected={expected} actual={actual}"
        );
    }
}

/// Д11: лексичне замикання зберігає оточення визначення, а формальний
/// параметр затінює однойменну змінну без зміни захопленого значення.
/// Це наскрізне виконання метаобчислювача SENS, не моделювання на Rust.
#[test]
fn d11_first_class_closure_captures_lexical_environment_and_shadows_parameters() {
    let mut s = session();
    for (id, input, expected) in [
        (
            "captures-environment",
            "(першокласне-обчислити (як-є ((функція (у) х) (як-є нове))) (як-є ((х . захоплене))))",
            "захоплене",
        ),
        (
            "parameter-shadows-capture",
            "(першокласне-обчислити (як-є ((функція (х) х) (як-є нове))) (як-є ((х . старе))))",
            "нове",
        ),
        (
            "two-parameters-preserve-order",
            "(першокласне-обчислити (як-є ((функція (х у) х) (як-є ліве) (як-є праве))) (як-є ()))",
            "ліве",
        ),
        (
            "second-parameter-selected",
            "(першокласне-обчислити (як-є ((функція (х у) у) (як-є ліве) (як-є праве))) (як-є ()))",
            "праве",
        ),
    ] {
        let actual = exact(input, &mut s)
            .unwrap_or_else(|error| panic!(
                "test_id=D11-FC-CAPTURE-{id} layer=SENS input={input} expected={expected} actual_error={error}"
            ))
            .value.to_string();
        assert_eq!(
            actual, expected,
            "test_id=D11-FC-CAPTURE-{id} layer=SENS input={input} expected={expected} actual={actual}"
        );
    }
}
