//! Public exact-domain migration boundary for host consumers.
//! The historical reader is never a fallback for this API.
use sens::{
    eval_exact_domain_program, load_core_library, parse, parse_exact_domain_source, ErrorKind,
    ExprKind, Session, Value,
};

#[test]
fn public_reader_keeps_d9_width_and_is_not_the_historical_byte_reader() {
    let current = parse_exact_domain_source("100000001")
        .expect("D9 word must be decoded without byte truncation");
    assert!(matches!(
        &current[0].kind,
        ExprKind::DomainIdentity(identity)
            if identity.width() == 9 && identity.packed_bits() == 0b100000001
    ));

    let historical = parse("11110111").expect("historical source is isolated");
    let current8 = parse_exact_domain_source("11110111").expect("current D8 source is explicit");
    assert_ne!(
        historical[0].kind, current8[0].kind,
        "the legacy reader must not silently acquire the exact-domain AST identity"
    );
    assert!(matches!(
        &current8[0].kind,
        ExprKind::DomainIdentity(identity)
            if identity.width() == 8 && identity.packed_bits() == 0b11110111
    ));
}

#[test]
fn d10_core4_defined_listp_executes_by_its_exact_word_identity() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("Core4 definitions load into exact domain slots");

    // D10:0100001100 is the existing Core4 LISTP closure. D3:001 quotes NIL;
    // its result must be exact D1:YES, not a host bool or a width-coerced D8.
    let result = eval_exact_domain_program("(0100001100 (001 ()))", &mut session)
        .expect("a concrete Core4-defined D10 function has an execution path");
    assert!(
        matches!(result.value, Value::DomainIdentity(sens::DomainIdentity::D1(bit))
        if bit.word().packed_bits() == 1)
    );

    // MKLIST is another concrete Core4 D10 definition. Passing a quoted atom
    // must produce a list, proving this is closure invocation, not a D10 opcode.
    let made_list = eval_exact_domain_program("(0011010111 (001 x))", &mut session)
        .expect("the concrete Core4 MKLIST closure is bound to its exact D10 word");
    assert!(matches!(made_list.value, Value::Pair(_)));

    // A D10 coordinate without a loaded definition remains non-callable.
    let error = eval_exact_domain_program("(0000000000 (001 ()))", &mut session)
        .expect_err("D10 residency/width alone must not admit a function");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn public_execution_quotes_current_d8_without_historical_dispatch() {
    let result = eval_exact_domain_program("(001 11110111)", &mut Session::bare())
        .expect("D3 QUOTE is executable as an admitted exact-domain form");
    assert!(matches!(
        result.value,
        Value::DomainIdentity(identity)
            if identity.width() == 8 && identity.packed_bits() == 0b11110111
    ));
}

#[test]
fn public_execution_rejects_noncallable_d8_and_unqualified_math() {
    let error = eval_exact_domain_program("(11110110 (001 1))", &mut Session::bare())
        .expect_err("ratified residency is not a runtime mechanism");
    assert_eq!(error.kind, ErrorKind::Type);

    let error = eval_exact_domain_program("(001 42)", &mut Session::bare())
        .expect_err("D24+ numeric grammar cannot be silently replaced by decimal");
    assert_eq!(error.kind, ErrorKind::Parse);
}
