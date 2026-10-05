//! Backend-neutral compiler lowering roles for the current exact-domain nucleus.
//!
//! This module owns no raw domain coordinate table. Every role is projected
//! from an existing production semantic classifier already used by the SENS
//! evaluator/lowerer.

use crate::CoreDomainIdentity;

/// Semantic shape a compiler may lower before target-specific mechanism choice.
///
/// These roles stop at the language/compiler boundary. They are not CML IR
/// variants, opcodes, register operations, or backend mechanism names.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum CompilerLoweringRole {
    QuoteForm,
    AtomPredicate,
    SelectorTail,
    SelectorHead,
    AtomEquality,
    CondForm,
    PairConstruct,
    LambdaForm,
    DefineForm,
}

/// Project one current exact identity to the lowering role used by the
/// SENS-written compiler frontend.
///
/// Ownership is delegated to the same production classifiers that drive
/// evaluation/source lowering; this function is only a composition point.
pub fn compiler_lowering_role(
    identity: CoreDomainIdentity,
) -> Option<CompilerLoweringRole> {
    if let Some(syntax) = crate::eval::lower::d3_syntax_kind(identity) {
        return Some(match syntax {
            crate::eval::lower::D3SyntaxKind::Quote => CompilerLoweringRole::QuoteForm,
            crate::eval::lower::D3SyntaxKind::Cond => CompilerLoweringRole::CondForm,
        });
    }

    if let Some(selector) = crate::eval::selector_law::compiler_execution_role(identity) {
        return Some(match selector {
            crate::CompilerExecutionRole::SelectorHead => CompilerLoweringRole::SelectorHead,
            crate::CompilerExecutionRole::SelectorTail => CompilerLoweringRole::SelectorTail,
            crate::CompilerExecutionRole::PairConstruct => {
                unreachable!("selector law cannot own PairConstruct")
            }
        });
    }

    if let Some(primitive) = crate::eval::canon::domain_primitive_kind(identity) {
        return Some(match primitive {
            crate::eval::canon::DomainPrimitiveKind::AtomPredicate => {
                CompilerLoweringRole::AtomPredicate
            }
            crate::eval::canon::DomainPrimitiveKind::AtomEquality => {
                CompilerLoweringRole::AtomEquality
            }
            crate::eval::canon::DomainPrimitiveKind::PairConstruct => {
                CompilerLoweringRole::PairConstruct
            }
        });
    }

    if let Some(form) = crate::eval::necessary_forms::identity_for_domain_identity(identity) {
        return Some(match form {
            crate::eval::necessary_forms::NecessaryFormIdentity::Lambda => {
                CompilerLoweringRole::LambdaForm
            }
            crate::eval::necessary_forms::NecessaryFormIdentity::Define => {
                CompilerLoweringRole::DefineForm
            }
        });
    }

    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::syntax::{Expr, ExprKind};
    use crate::{lower_program, parse};

    const NUCLEUS: &str = include_str!("../../../lib/compiler-nucleus.lisp");

    fn collect_roles(expr: &Expr, roles: &mut Vec<CompilerLoweringRole>) {
        match &expr.kind {
            ExprKind::DomainCall(identity, args) => {
                let role = compiler_lowering_role(*identity).unwrap_or_else(|| {
                    panic!(
                        "current compiler nucleus lowered an exact domain call without a compiler lowering role: {identity}"
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
    fn every_exact_domain_call_in_current_compiler_nucleus_has_a_lowering_role() {
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
                "current compiler nucleus did not exercise expected lowering role {expected:?}; observed {roles:?}"
            );
        }
    }

    #[test]
    fn equal_payloads_outside_the_owning_domain_fail_closed() {
        let d4_quote_payload = CoreDomainIdentity::D4(crate::CoreD4::from_word(
            crate::Bit4::new(0b0001).unwrap(),
        ));
        let d5_cons_payload = CoreDomainIdentity::D5(crate::CoreD5::from_word(
            crate::Bit5::new(0b00111).unwrap(),
        ));
        let d8_lambda_payload = CoreDomainIdentity::D8(crate::CoreD8::from_word(
            crate::Bit8::new(0b0000_0010).unwrap(),
        ));

        assert_eq!(compiler_lowering_role(d4_quote_payload), None);
        assert_eq!(compiler_lowering_role(d5_cons_payload), None);
        assert_eq!(compiler_lowering_role(d8_lambda_payload), None);
    }
}
