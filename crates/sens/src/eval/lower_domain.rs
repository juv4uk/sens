//! Canonical lowering for exact-domain call heads.
//!
//! This module never sees Sens8. It admits only domain identities whose
//! callability is already established by the canonical routing law.

use super::{lower, necessary_forms};
use crate::syntax::{Expr, ExprKind};
use crate::CoreDomainIdentity;
use std::rc::Rc;

fn head_identity(head: &Expr) -> Option<CoreDomainIdentity> {
    match &head.kind {
        ExprKind::DomainIdentity(identity) => Some(*identity),
        ExprKind::Symbol(name) => necessary_forms::domain_identity_for_symbol(name),
        _ => None,
    }
}

/// Lower one D4 necessary-form list into a canonical DomainCall.
///
/// This intentionally covers only LAMBDA/DEFINE. Other D3/D4 residents are
/// migrated in their own law-aware slices because QUOTE/COND have distinct
/// evaluation-order rules.
pub(super) fn try_lower_necessary_form(
    items: &[Expr],
    depth: u32,
) -> Option<ExprKind> {
    let head = items.first()?;
    let identity = head_identity(head)?;
    necessary_forms::identity_for_domain_identity(identity)?;

    let arguments: Rc<[Expr]> = items[1..]
        .iter()
        .enumerate()
        .map(|(index, argument)| {
            if index == 0 {
                argument.clone()
            } else {
                lower::lower(argument, depth + 1)
            }
        })
        .collect();

    Some(ExprKind::DomainCall(identity, arguments))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bija3, Bit3, Exactness, Span};

    fn symbol(name: &str) -> Expr {
        Expr {
            kind: ExprKind::Symbol(name.into()),
            span: Span { start: 0, end: 0 },
        }
    }

    #[test]
    fn same_payload_d3_does_not_gain_d4_necessary_form_callability() {
        let d3 = CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b010).unwrap()));
        let items = [
            Expr {
                kind: ExprKind::DomainIdentity(d3),
                span: Span { start: 0, end: 0 },
            },
            Expr {
                kind: ExprKind::Number(1.0, Exactness::Exact),
                span: Span { start: 0, end: 0 },
            },
        ];
        assert!(try_lower_necessary_form(&items, 0).is_none());
    }

    #[test]
    fn lambda_surface_lowers_to_d4_domain_call() {
        let items = [symbol("lambda"), symbol("args"), symbol("body")];
        let kind = try_lower_necessary_form(&items, 0).expect("lambda domain call");
        let ExprKind::DomainCall(identity, arguments) = kind else {
            panic!("expected DomainCall");
        };
        assert_eq!((identity.width(), identity.packed_bits()), (4, 0b0010));
        assert_eq!(arguments.len(), 2);
    }

    #[test]
    fn define_and_def_normalize_to_same_d4_identity() {
        let define = try_lower_necessary_form(
            &[symbol("define"), symbol("x"), symbol("value")],
            0,
        )
        .expect("define domain call");
        let compat_def = try_lower_necessary_form(
            &[symbol("def"), symbol("x"), symbol("value")],
            0,
        )
        .expect("def canonical normalization");

        let ExprKind::DomainCall(define_id, _) = define else {
            panic!("expected DomainCall");
        };
        let ExprKind::DomainCall(def_id, _) = compat_def else {
            panic!("expected DomainCall");
        };
        assert_eq!(define_id, def_id);
        assert_eq!((define_id.width(), define_id.packed_bits()), (4, 0b0011));
    }
}
