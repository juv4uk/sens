//! #3738 — existing FASL v3 persists an exact-domain language program.
//!
//! This is a persistence witness, not a new format and not a TAKE/DROP
//! implementation. The host transports an AST; the closure semantics remain
//! ordinary language semantics.

use sens::{
    eval_parsed_expressions, fasl_decode_program, fasl_encode_program, parse, Bit4, Bit5, Bit6,
    Bit7, Bit8, CoreD4, CoreD5, CoreD6, CoreD8, DomainIdentity, Environment, ErrorKind, Expr,
    ExprKind, Session, SoundD7,
};

fn d4(bits: u8) -> DomainIdentity {
    DomainIdentity::D4(CoreD4::from_word(Bit4::new(bits).unwrap()))
}

fn d5(bits: u8) -> DomainIdentity {
    DomainIdentity::D5(CoreD5::from_word(Bit5::new(bits).unwrap()))
}

fn d6(bits: u8) -> DomainIdentity {
    DomainIdentity::D6(CoreD6::from_word(Bit6::new(bits).unwrap()))
}

fn d7(bits: u8) -> DomainIdentity {
    DomainIdentity::D7(SoundD7::from_word(Bit7::new(bits).unwrap()))
}

fn d8(bits: u8) -> DomainIdentity {
    DomainIdentity::D8(CoreD8::from_word(Bit8::new(bits).unwrap()))
}

fn identity_expr(template: &Expr, identity: DomainIdentity) -> Expr {
    Expr {
        kind: ExprKind::DomainIdentity(identity),
        span: template.span,
    }
}

/// Exact D4 DEFINE of one D6 slot with a language closure:
///   ADD1(x) := PLUS(x, 1)
///
/// Current identities:
/// - D4:0011 DEFINE
/// - D4:0010 LAMBDA
/// - D5:01010 PLUS
/// - D6:001110 ADD1 (target)
fn exact_define_add1(target: DomainIdentity) -> Expr {
    let mut form = parse("(__define__ __target__ (__lambda__ (x) (__plus__ x 1)))")
        .expect("persistence probe must parse")
        .remove(0);

    let ExprKind::List(items) = form.kind else {
        panic!("DEFINE probe must parse as list");
    };
    let mut items = items.to_vec();

    items[0] = identity_expr(&items[0], d4(0b0011));
    items[1] = identity_expr(&items[1], target);

    let mut lambda = items[2].clone();
    let ExprKind::List(lambda_items) = lambda.kind else {
        panic!("lambda probe must parse as list");
    };
    let mut lambda_items = lambda_items.to_vec();
    lambda_items[0] = identity_expr(&lambda_items[0], d4(0b0010));

    let mut body = lambda_items[2].clone();
    let ExprKind::List(body_items) = body.kind else {
        panic!("lambda body must parse as list");
    };
    let mut body_items = body_items.to_vec();
    body_items[0] = identity_expr(&body_items[0], d5(0b01010));
    body.kind = ExprKind::List(body_items.into());

    lambda_items[2] = body;
    lambda.kind = ExprKind::List(lambda_items.into());
    items[2] = lambda;
    form.kind = ExprKind::List(items.into());
    form
}

fn exact_call(target: DomainIdentity, argument: i32) -> Expr {
    let mut form = parse(&format!("(__call__ {argument})"))
        .expect("call probe must parse")
        .remove(0);
    let ExprKind::List(items) = form.kind else {
        panic!("call probe must parse as list");
    };
    let mut items = items.to_vec();
    items[0] = identity_expr(&items[0], target);
    form.kind = ExprKind::List(items.into());
    form
}

fn persist(program: &[Expr]) -> Vec<u8> {
    fasl_encode_program(program, &[0x38; 32])
}

fn restore(bytes: &[u8]) -> Vec<Expr> {
    let (program, hash) = fasl_decode_program(bytes).expect("FASL program must decode");
    assert_eq!(hash, [0x38; 32]);
    program
}

fn run(env: &Environment, program: &[Expr]) -> Result<String, sens::LanguageError> {
    let mut session = Session {
        environment: env.clone(),
    };
    eval_parsed_expressions(program, &mut session).map(|result| result.value.to_string())
}

#[test]
fn fasl_round_trip_persists_exact_d6_define_closure_and_exact_invocation() {
    let add1 = d6(0b001110);
    let source_program = vec![exact_define_add1(add1), exact_call(add1, 41)];

    let bytes_a = persist(&source_program);
    let bytes_b = persist(&source_program);
    assert_eq!(bytes_a, bytes_b, "FASL bytes must be deterministic");

    let restored = restore(&bytes_a);
    assert_eq!(
        persist(&restored),
        bytes_a,
        "decode/re-encode must be byte-stable"
    );

    let env = Environment::root();
    assert_eq!(
        run(&env, &restored).expect("persisted exact-domain program must execute"),
        "42"
    );
}

#[test]
fn persisted_exact_domain_program_keeps_single_assignment() {
    let add1 = d6(0b001110);
    let bytes = persist(&[exact_define_add1(add1)]);
    let restored = restore(&bytes);
    let env = Environment::root();

    run(&env, &restored).expect("first persisted exact definition must bind");

    let error = run(&env, &restored)
        .expect_err("second replay of the same artifact must fail one-binding law");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
    assert!(
        error.message.contains("already has a language-owned binding"),
        "unexpected duplicate-definition error: {error:?}"
    );

    assert_eq!(
        run(&env, &[exact_call(add1, 41)]).expect("first closure must remain installed"),
        "42"
    );
}

#[test]
fn fasl_transport_does_not_make_d7_or_d8_callable_define_targets() {
    for target in [d7(0b0101101), d8(0b00101101)] {
        let restored = restore(&persist(&[exact_define_add1(target)]));
        let error = run(&Environment::root(), &restored)
            .expect_err("persisted D7/D8 DEFINE target must stay fail-closed");
        assert_eq!(error.kind, ErrorKind::InvalidForm);
        assert!(
            error.message.contains("callable D3/D4/D5/D6"),
            "unexpected non-callable target error: {error:?}"
        );
    }
}
