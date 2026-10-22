//! Виклик мовних функцій через точні поточні доменні identity.
use sens::{
    eval_exact_domain_program, eval_parsed_expressions, eval_program, load_core_library,
    parse_mixed_exact_domain, ErrorKind, Session,
};

fn core_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("чинне ядро має завантажитися");
    session
}

fn eval(session: &mut Session, source: &str) -> String {
    let forms = parse_mixed_exact_domain(source)
        .unwrap_or_else(|error| panic!("не вдалося розібрати {source}: {error}"));
    eval_parsed_expressions(&forms, session)
        .unwrap_or_else(|error| panic!("не вдалося виконати {source}: {error:?}"))
        .value
        .to_string()
}

#[test]
fn current_exact_domain_codes_call_their_language_defined_functions() {
    let mut session = core_session();
    for (by_code, by_name) in [
        ("(1110 1 2 3)", "(список 1 2 3)"),
        (
            "(11101 (як-є кіт) (список (як-є кіт) (як-є пес)))",
            "(значення-у-списку? (як-є кіт) (список (як-є кіт) (як-є пес)))",
        ),
        (
            "(1111 (список (як-є кіт)) (список (як-є пес)))",
            "(приєднати (список (як-є кіт)) (список (як-є пес)))",
        ),
        ("(10111 17 5)", "(частка 17 5)"),
    ] {
        assert_eq!(
            eval(&mut session, by_code),
            eval(&mut session, by_name),
            "{by_code}"
        );
    }
}

#[test]
fn exact_domain_code_as_a_value_invokes_its_bound_definition() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("Core4 binds current exact identities");
    let result = eval_exact_domain_program("(((0010 (ф) ф) 0100001100) (001 ()))", &mut session)
        .expect("an exact D10 identity passed as a value invokes its loaded definition");
    assert!(matches!(
        result.value,
        sens::Value::DomainIdentity(sens::DomainIdentity::D1(bit))
            if bit.word().packed_bits() == 1
    ));
}

#[test]
fn an_admitted_d9_or_d10_definition_is_called_by_its_exact_code() {
    for target in ["101111001", "0100001100"] {
        let mut session = Session::bare();
        let definition = format!("(0011 {target} (0010 () (001 1)))");
        eval_exact_domain_program(&definition, &mut session)
            .unwrap_or_else(|error| panic!("admitted exact target {target}: {error}"));

        let call = format!("({target})");
        let result = eval_exact_domain_program(&call, &mut session)
            .unwrap_or_else(|error| panic!("exact code call {target}: {error}"));
        assert!(
            matches!(
                result.value,
                sens::Value::DomainIdentity(sens::DomainIdentity::D1(bit))
                    if bit.word().packed_bits() == 1
            ),
            "exact target {target} must return its D1 value, got {}",
            result.value
        );
    }

    let mut session = Session::bare();
    let error = eval_exact_domain_program("(0011 0000000 (0010 () (001 1)))", &mut session)
        .expect_err("D7 data identity cannot become callable by D4 DEFINE");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

#[test]
fn local_lexical_shadow_does_not_retarget_an_exact_domain_code() {
    let mut session = core_session();
    assert_eq!(
        eval(
            &mut session,
            "((функція (список) (1110 1 2)) (функція (значення) (як-є затінено)))",
        ),
        "(1 2)"
    );
}

#[test]
fn resident_without_an_admitted_mechanism_fails_closed() {
    let error = eval_exact_domain_program("(0000000000 (001 ()))", &mut core_session())
        .expect_err("D10 residency alone must not grant callability");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn decimal_digits_in_a_call_head_do_not_become_a_callable_identity() {
    let error = eval_program("(00100111 1 2 3)", &mut core_session())
        .expect_err("a decimal-looking legacy code must not become an opcode");
    assert_eq!(error.kind, ErrorKind::Type);
}
