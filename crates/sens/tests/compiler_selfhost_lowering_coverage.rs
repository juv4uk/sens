//! sens#3823 — whole-nucleus coverage over the production SENS-owned role API.
//!
//! This test owns no identity->role semantics. It lowers the real current
//! compiler nucleus, observes exact DomainCall identities, and asks
//! `compiler_lowering_role_from_sens` for the already-derived role.

use sens::syntax::{Expr, ExprKind};
use sens::{
    compiler_lowering_role_from_sens, lower_program, parse, Bit4, Bit5, Bit8,
    CompilerLoweringRole, CoreD4, CoreD5, CoreD8, CoreDomainIdentity,
};

const NUCLEUS: &str = include_str!("../../../lib/compiler-nucleus.lisp");

fn collect_roles(expr: &Expr, roles: &mut Vec<CompilerLoweringRole>) {
    match &expr.kind {
        ExprKind::DomainCall(identity, args) => {
            let role = compiler_lowering_role_from_sens(*identity)
                .unwrap_or_else(|error| {
                    panic!(
                        "SENS-owned role derivation failed for current nucleus identity {identity:?}: {error}"
                    )
                })
                .unwrap_or_else(|| {
                    panic!(
                        "current compiler nucleus lowered an exact domain call without an admitted lowering role: {identity:?}"
                    )
                });

            if !roles.contains(&role) {
                roles.push(role);
            }

            for arg in args.iter() {
                collect_roles(arg, roles);
            }
        }
        ExprKind::List(items) => {
            for item in items.iter() {
                collect_roles(item, roles);
            }
        }
        ExprKind::Pair(head, tail) => {
            collect_roles(head, roles);
            collect_roles(tail, roles);
        }
        ExprKind::Sid(_)
        | ExprKind::Call(_, _)
        | ExprKind::Number(_, _)
        | ExprKind::Rational(_)
        | ExprKind::BinaryNumber(_)
        | ExprKind::NumericBuffer(_)
        | ExprKind::DomainIdentity(_)
        | ExprKind::String(_)
        | ExprKind::Symbol(_)
        | ExprKind::Local { .. } => {}
    }
}

#[test]
fn every_exact_domain_call_in_current_compiler_nucleus_has_a_sens_owned_role() {
    let parsed = parse(NUCLEUS).expect("current compiler nucleus source must parse");
    let lowered = lower_program(&parsed);

    let mut roles = Vec::new();
    for expr in &lowered {
        collect_roles(expr, &mut roles);
    }

    for expected in [
        CompilerLoweringRole::QuoteForm,
        CompilerLoweringRole::AtomPredicate,
        CompilerLoweringRole::SelectorTail,
        CompilerLoweringRole::SelectorHead,
        CompilerLoweringRole::AtomEquality,
        CompilerLoweringRole::CondForm,
        CompilerLoweringRole::PairConstruct,
        CompilerLoweringRole::LambdaForm,
        CompilerLoweringRole::DefineForm,
    ] {
        assert!(
            roles.contains(&expected),
            "current compiler nucleus did not exercise expected SENS-owned lowering role {expected:?}; observed {roles:?}"
        );
    }
}

#[test]
fn equal_payloads_outside_the_owning_domain_stay_fail_closed() {
    let collisions = [
        CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0001).unwrap())),
        CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(0b00111).unwrap())),
        CoreDomainIdentity::D8(CoreD8::from_word(Bit8::new(0b0000_0010).unwrap())),
    ];

    for identity in collisions {
        assert_eq!(
            compiler_lowering_role_from_sens(identity).expect("role query"),
            None,
            "equal payload outside the owning domain must not inherit compiler meaning: {identity:?}"
        );
    }
}

#[test]
fn coverage_test_contains_no_compiler_role_projection_of_its_own() {
    let source = include_str!("compiler_selfhost_lowering_coverage.rs");
    for forbidden in [
        "d3_syntax_kind",
        "domain_primitive_kind",
        "identity_for_domain_identity",
        "match word.word().packed_bits()",
    ] {
        assert!(
            !source.contains(forbidden),
            "coverage test must consume the production SENS-owned API, not project roles through {forbidden}"
        );
    }
}
