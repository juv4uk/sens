//! Conservative executable-code admissibility witness for Frame3 candidates.
//!
//! IMPORTANT: "not proved impossible" never means semantically valid.
//! This only rejects *provably* impossible statically-headed D3 call arities.
//! Quoted syntax is data, not an executable call; COND and dynamic heads
//! are not statically excluded without an independent authoritative law.
//! This module changes neither the canonical reader nor the physical codec.

use crate::syntax::{Expr, ExprKind};
use crate::DomainIdentity;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AdmissionWitness {
    ProvablyImpossible,
    NotProvenImpossible,
}

/// This is a safe negative witness, NOT an executable program validator.
///
/// D3: 001 QUOTE, 010 ATOM, 011 CDR, 100 CAR, 101 EQ, 111 CONS.
/// QUOTE does not evaluate its one data argument. Arguments of the other
/// five known fixed-arity primitives must be executable expressions.
/// COND=110 and dynamic/application forms require separate rules.
pub fn check_executable_code(expr: &Expr) -> AdmissionWitness {
    if impossible(expr) {
        AdmissionWitness::ProvablyImpossible
    } else {
        AdmissionWitness::NotProvenImpossible
    }
}

fn impossible(expr: &Expr) -> bool {
    let ExprKind::List(items) = &expr.kind else {
        return false; // Bare atoms/values and quoted pair data are not calls.
    };
    let Some((head, args)) = items.split_first() else {
        return false; // () is a value; it is not an empty application.
    };

    // A head that must be evaluated but cannot be a valid call poisons the
    // outer executable form. Not every nested list is statically callable.
    if matches!(&head.kind, ExprKind::List(_)) && impossible(head) {
        return true;
    }

    let ExprKind::DomainIdentity(DomainIdentity::D3(identity)) = &head.kind else {
        return false; // Dynamic/unknown/textual forms are not disproven here.
    };
    let bits = identity.word().packed_bits();
    let expected = match bits {
        0b001..=0b100 => 1usize,
        0b101 | 0b111 => 2usize,
        _ => return false, // COND, D3 empty, other future laws.
    };
    if args.len() != expected {
        return true;
    }
    if bits == 0b001 {
        return false; // QUOTE body is data: do NOT inspect it as executable.
    }
    args.iter().any(impossible)
}
