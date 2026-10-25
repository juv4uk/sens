//! Механічна атестація фізичного Core4: семантика LET/LET* належить SENS.
//! Rust тут лише засвідчує наявність уже виконаного SENS-макроса у D6 слоті.
use sens::{
    eval_parsed_expressions, load_core_library, Bit6, CoreD6, DomainIdentity, Environment, Session,
};

#[test]
fn physical_core4_binds_actual_sens_let_macros_to_exact_d6_slots() {
    let mut session = Session {
        environment: Environment::root(),
    };
    load_core_library(&mut session).expect("physical Core4 bootstrap must execute");

    for (bits, surface) in [(0b001000, "нехай"), (0b001001, "нехай-послідовно")]
    {
        let identity = DomainIdentity::D6(CoreD6::from_word(
            Bit6::new(bits).expect("ratified D6 word"),
        ));
        let has_binding = session.environment.has_domain_code_slot(identity);
        assert!(
            has_binding,
            "D6:{bits:06b} {surface} must have its exact SENS-defined runtime slot"
        );
    }

    // Не створюємо Rust-версію LET: запускаємо існуючий закон мовою SENS.
    // Паралельне LET і послідовне LET* перевіряють лексичний порядок.
    let source = include_str!("../../../tests/semantic/d6-let-letstar-preflight-law.lisp");
    let forms = sens::parse(source).expect("SENS D6 LET/LET* law must parse");
    let result = eval_parsed_expressions(&forms, &mut session)
        .expect("existing SENS D6 LET/LET* law must execute after physical bootstrap");
    assert_eq!(
        result.value.as_predicate_bit(),
        Some(true),
        "SENS law must return exact D1:так, not a host boolean or D3:()"
    );
}
