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

/// Негативний доказ для обох форм виклику: до та після точного
/// D3 lowering. Спільний закон не залежить від історичного W8-коду.
fn impossible(expr: &Expr) -> bool {
    match &expr.kind {
        ExprKind::DomainCall(crate::CoreDomainIdentity::D3(head), arguments) => {
            impossible_d3_fixed_arity(head.word().packed_bits(), arguments)
        }
        ExprKind::List(items) => {
            let Some((head, arguments)) = items.split_first() else {
                return false; // () — значення, а не порожній виклик.
            };

            // Обчислювана голова з гарантовано неможливою формою
            // робить зовнішній виклик неможливим.
            if matches!(&head.kind, ExprKind::List(_) | ExprKind::DomainCall(_, _))
                && impossible(head)
            {
                return true;
            }
            let ExprKind::DomainIdentity(DomainIdentity::D3(identity)) = &head.kind else {
                return false; // Динамічну голову або інший домен не вгадуємо.
            };
            impossible_d3_fixed_arity(identity.word().packed_bits(), arguments)
        }
        _ => false, // Інші домени та дані — поза вузьким доказом.
    }
}

/// Від'ємний свідок застосовний лише там, де арність D3 уже встановлена.
/// Неретифікована виконуваність, D3:000 та COND — не підміна доказу.
fn impossible_d3_fixed_arity(bits: u8, arguments: &[Expr]) -> bool {
    let expected = match bits {
        0b001..=0b100 => 1,
        0b101 | 0b111 => 2,
        _ => return false, // D3:000 та 110 COND не мають тут fixed-arity доказу.
    };
    if arguments.len() != expected {
        return true;
    }
    if bits == 0b001 {
        return false; // QUOTE: аргумент є даними, не виконується.
    }
    arguments.iter().any(impossible)
}
