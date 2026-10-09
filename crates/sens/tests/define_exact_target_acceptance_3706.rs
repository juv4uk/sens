//! #3706 — black-box acceptance witnesses for exact DomainIdentity DEFINE.
//!
//! Test-only lane for #3655. These tests are ignored until the evaluator-side
//! exact-target DEFINE implementation lands. They compile against the current
//! D6 runtime spine and intentionally use no human/surface name as authority.

use sens::{
    eval_parsed_expressions, parse, Bit1, Bit2, Bit4, Bit5, Bit6, Bit7, Bit8, CoreD4, CoreD5,
    CoreD6, CoreD8, DomainIdentity, Environment, Expr, ExprKind, PredicateBit, Racana2, Session,
    SoundD7,
};

fn d1(bits: u8) -> DomainIdentity {
    DomainIdentity::D1(PredicateBit::from_word(Bit1::new(bits).unwrap()))
}

fn d2(bits: u8) -> DomainIdentity {
    DomainIdentity::D2(Racana2::from_word(Bit2::new(bits).unwrap()))
}

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

/// Build exact D4 DEFINE whose target is an exact domain identity and whose
/// value is a language closure implementing ADD1 as exact D5 PLUS(x, 1).
///
/// Ratified identities used here:
/// - D4:0011 DEFINE
/// - D4:0010 LAMBDA
/// - D5:01010 PLUS
/// - D6:001110 ADD1 (target in positive witnesses)
fn exact_define_add1(target: DomainIdentity, increment: i32) -> Expr {
    let source = format!(
        "(__define__ __target__ (__lambda__ (x) (__plus__ x {increment})))"
    );
    let mut form = parse(&source).expect("acceptance probe must parse").remove(0);

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

fn run(env: &Environment, expressions: &[Expr]) -> Result<String, sens::LanguageError> {
    let mut session = Session {
        environment: env.clone(),
    };
    eval_parsed_expressions(expressions, &mut session).map(|result| result.value.to_string())
}

fn visible_names(env: &Environment) -> Vec<String> {
    env.snapshot()
        .into_iter()
        .map(|(name, _)| name.to_string())
        .collect()
}

#[test]
fn exact_d6_define_installs_language_owned_add1_and_exact_call_invokes_it() {
    let env = Environment::root();
    let add1 = d6(0b001110);

    let names_before = visible_names(&env);
    run(&env, &[exact_define_add1(add1, 1)]).expect("exact D6 DEFINE must bind ADD1 closure");
    let names_after = visible_names(&env);

    assert_eq!(
        names_after, names_before,
        "exact-domain DEFINE must not create a symbol/surface binding"
    );

    assert_eq!(
        run(&env, &[exact_call(add1, 41)]).expect("exact D6 ADD1 invocation"),
        "42"
    );
}

#[test]
fn exact_domain_define_is_one_binding_and_preserves_the_first_closure() {
    let env = Environment::root();
    let add1 = d6(0b001110);

    run(&env, &[exact_define_add1(add1, 1)]).expect("first exact bind");

    run(&env, &[exact_define_add1(add1, 2)])
        .expect_err("second exact bind of the same domain slot must fail");

    assert_eq!(
        run(&env, &[exact_call(add1, 41)]).expect("first closure must remain installed"),
        "42",
        "failed redefinition must not replace the original exact-domain closure"
    );
}

#[test]
fn noncallable_or_research_domain_targets_fail_closed() {
    for (label, target) in [
        ("D1", d1(1)),
        ("D2", d2(0b01)),
        ("D7", d7(0b0000000)),
        ("D8", d8(0b00000000)),
    ] {
        let env = Environment::root();
        run(&env, &[exact_define_add1(target, 1)])
            .unwrap_err_or_else(|_| panic!("{label} exact DEFINE target must fail closed"));
    }
}

// Small helper because Result::expect_err requires the success type to be Debug;
// the acceptance harness only needs to prove that the operation fails.
trait ResultMustFail {
    fn unwrap_err_or_else(self, on_success: impl FnOnce());
}

impl<T, E> ResultMustFail for Result<T, E> {
    fn unwrap_err_or_else(self, on_success: impl FnOnce()) {
        if self.is_ok() {
            on_success();
        }
    }
}
