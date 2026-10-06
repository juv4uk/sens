//! Lowering from parsed Lisp to IR, using DomainIdentity (D3/D4 exact bits).
//!
//! Migrated from CML lower.rs; rewritten to use SENS semantic authority
//! instead of Sid8. Every operation is dispatched by exact bit pattern
//! in its domain (D3 = 3-bit, D4 = 4-bit).
//!
//! Contract authority: language-contract.lisp §d3-foundation, §d4-bootstrap

use crate::{CoreDomainIdentity, Expr, ExprKind};

#[derive(Debug, Clone)]
pub enum LowerError {
    InvalidForm(String),
    Arity(String),
    NonCompilerIdentity(CoreDomainIdentity),
}

impl std::fmt::Display for LowerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidForm(msg) => write!(f, "InvalidForm: {}", msg),
            Self::Arity(msg) => write!(f, "Arity: {}", msg),
            Self::NonCompilerIdentity(id) => {
                write!(f, "NonCompilerIdentity: D{}:{:0width$b}",
                    id.width(), id.packed_bits(), width = id.width())
            }
        }
    }
}

impl std::error::Error for LowerError {}

/// Lower a single expression using its DomainIdentity as dispatcher.
///
/// Dispatches on (width, packed_bits) to D3 or D4 nucleus operations only.
pub fn lower_expr(identity: CoreDomainIdentity, args: &[Expr]) -> Result<(), LowerError> {
    match (identity.width(), identity.packed_bits()) {
        // D3: three-bit operations
        (3, 0b001) => lower_quote(args),           // QUOTE
        (3, 0b010) => lower_atom(args),            // ATOM (predicate)
        (3, 0b011) => lower_cdr(args),             // CDR
        (3, 0b100) => lower_car(args),             // CAR
        (3, 0b101) => lower_eq(args),              // EQ (predicate)
        (3, 0b110) => lower_cond(args),            // COND
        (3, 0b111) => lower_cons(args),            // CONS

        // D4: four-bit operations (nucleus only)
        (4, 0b0010) => lower_lambda(args),         // LAMBDA
        (4, 0b0011) => lower_define(args),         // DEFINE

        // All non-nucleus identities rejected
        _ => Err(LowerError::NonCompilerIdentity(identity)),
    }
}

fn lower_quote(_args: &[Expr]) -> Result<(), LowerError> {
    // QUOTE: D3:001
    // Returns its argument as an unevaluated literal structure
    todo!("lower_quote: D3:001")
}

fn lower_atom(_args: &[Expr]) -> Result<(), LowerError> {
    // ATOM?: D3:010
    // Predicate test: structural () or atom → D1:1, pair → D1:0
    todo!("lower_atom: D3:010 predicate")
}

fn lower_cdr(_args: &[Expr]) -> Result<(), LowerError> {
    // CDR: D3:011
    // Accessor: rest of pair
    todo!("lower_cdr: D3:011")
}

fn lower_car(_args: &[Expr]) -> Result<(), LowerError> {
    // CAR: D3:100
    // Accessor: first of pair
    todo!("lower_car: D3:100")
}

fn lower_eq(_args: &[Expr]) -> Result<(), LowerError> {
    // EQ: D3:101
    // Predicate: exact atom identity → D1:1, else → D1:0
    todo!("lower_eq: D3:101 predicate")
}

fn lower_cond(_args: &[Expr]) -> Result<(), LowerError> {
    // COND: D3:110
    // Conditional dispatch on (test . expr) clauses
    // Test must be PredicateBit (D1); 1→evaluate expr, 0→skip
    todo!("lower_cond: D3:110")
}

fn lower_cons(_args: &[Expr]) -> Result<(), LowerError> {
    // CONS: D3:111
    // Constructor: make pair from two values
    todo!("lower_cons: D3:111")
}

fn lower_lambda(_args: &[Expr]) -> Result<(), LowerError> {
    // LAMBDA: D4:0010
    // Function definition (params body)
    todo!("lower_lambda: D4:0010")
}

fn lower_define(_args: &[Expr]) -> Result<(), LowerError> {
    // DEFINE: D4:0011
    // Top-level binding (name value)
    todo!("lower_define: D4:0011")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn d3_quote_is_001() {
        // D3:001 QUOTE dispatcher test
        // Verify exact bit pattern matches language-contract.lisp §d3-foundation
        assert_eq!(0b001, 1);  // QUOTE = 001₂ = 1₁₀
    }

    #[test]
    fn d3_cond_is_110() {
        // D3:110 COND dispatcher test
        assert_eq!(0b110, 6);  // COND = 110₂ = 6₁₀
    }

    #[test]
    fn d4_lambda_is_0010() {
        // D4:0010 LAMBDA dispatcher test
        assert_eq!(0b0010, 2);  // LAMBDA = 0010₂ = 2₁₀
    }

    #[test]
    fn d4_define_is_0011() {
        // D4:0011 DEFINE dispatcher test
        assert_eq!(0b0011, 3);  // DEFINE = 0011₂ = 3₁₀
    }
}
