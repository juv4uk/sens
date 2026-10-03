//! Canonical evaluator dispatch for domain-qualified call heads.
//!
//! This module never projects a CoreDomainIdentity to Sens8. Only mechanisms
//! admitted directly by domain law are executable here.

use super::{closures, necessary_forms, special_forms, EvalStep};
use crate::{CoreDomainIdentity, Environment, ErrorKind, Expr, LanguageError, Span};

pub(super) fn dispatch(
    identity: CoreDomainIdentity,
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    match necessary_forms::identity_for_domain_identity(identity) {
        Some(necessary_forms::NecessaryFormIdentity::Lambda) => {
            closures::create_lambda(arguments, environment, span).map(EvalStep::Value)
        }
        Some(necessary_forms::NecessaryFormIdentity::Define) => {
            special_forms::evaluate_definition(arguments, environment, span).map(EvalStep::Value)
        }
        None => Err(LanguageError::new(
            ErrorKind::InvalidForm,
            format!(
                "domain-qualified call is not admitted by runtime routing · domenno-kvalifikovanyi vyklyk ne dopushchenyi runtime-marshrutyzatsiieiu: {identity}"
            ),
            span,
        )),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bija3, Bit3, Bit4, CoreD4, ExprKind};

    fn d4(raw: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(raw).unwrap()))
    }

    #[test]
    fn unrelated_domain_identity_fails_closed() {
        let d3_same_payload =
            CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b010).unwrap()));
        let env = Environment::root();
        let result = dispatch(
            d3_same_payload,
            &[],
            &env,
            Span { start: 0, end: 0 },
        );
        assert!(result.is_err());
    }

    #[test]
    fn d4_free_coordinate_fails_closed() {
        let env = Environment::root();
        let result = dispatch(d4(0b0101), &[], &env, Span { start: 0, end: 0 });
        assert!(result.is_err());
    }

    #[test]
    fn d4_lambda_is_routed_without_legacy_projection() {
        let env = Environment::root();
        let params = Expr {
            kind: ExprKind::List([].into()),
            span: Span { start: 0, end: 0 },
        };
        let body = Expr {
            kind: ExprKind::List([].into()),
            span: Span { start: 0, end: 0 },
        };
        let result = dispatch(
            d4(0b0010),
            &[params, body],
            &env,
            Span { start: 0, end: 0 },
        );
        assert!(result.is_ok());
    }
}
