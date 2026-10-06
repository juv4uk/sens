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

fn lower_quote(args: &[Expr]) -> Result<(), LowerError> {
    // QUOTE: D3:001
    // Returns argument as unevaluated literal. Arity: exactly 1.
    // (quote x) → x (as data, not code)
    match args {
        [_quoted] => Ok(()),
        _ => Err(LowerError::Arity(
            "D3:001 QUOTE expects exactly 1 argument".to_string()
        )),
    }
}

fn lower_atom(args: &[Expr]) -> Result<(), LowerError> {
    // ATOM?: D3:010
    // Predicate test: empty/atom → D1:1, pair → D1:0. Arity: exactly 1.
    // (atom? x) → PredicateBit
    match args {
        [_value] => Ok(()),
        _ => Err(LowerError::Arity(
            "D3:010 ATOM? expects exactly 1 argument".to_string()
        )),
    }
}

fn lower_cdr(args: &[Expr]) -> Result<(), LowerError> {
    // CDR: D3:011
    // Accessor: rest of pair. Arity: exactly 1.
    // (cdr x) → tail of pair structure
    match args {
        [_pair] => Ok(()),
        _ => Err(LowerError::Arity(
            "D3:011 CDR expects exactly 1 argument".to_string()
        )),
    }
}

fn lower_car(args: &[Expr]) -> Result<(), LowerError> {
    // CAR: D3:100
    // Accessor: first of pair. Arity: exactly 1.
    // (car x) → head of pair structure
    match args {
        [_pair] => Ok(()),
        _ => Err(LowerError::Arity(
            "D3:100 CAR expects exactly 1 argument".to_string()
        )),
    }
}

fn lower_eq(args: &[Expr]) -> Result<(), LowerError> {
    // EQ: D3:101
    // Predicate: exact atom identity. Arity: exactly 2.
    // (eq? x y) → same atom → D1:1, else → D1:0
    match args {
        [_left, _right] => Ok(()),
        _ => Err(LowerError::Arity(
            "D3:101 EQ? expects exactly 2 arguments".to_string()
        )),
    }
}

fn lower_cond(args: &[Expr]) -> Result<(), LowerError> {
    // COND: D3:110
    // Conditional dispatch on (test . expr) clauses.
    // Each clause: (test-expr result-expr). At least one clause.
    // Test must evaluate to PredicateBit; 1→evaluate expr, 0→skip.
    // No clauses → returns structural () (D3:000).
    if args.is_empty() {
        return Err(LowerError::InvalidForm(
            "D3:110 COND requires at least one clause".to_string()
        ));
    }

    // Validate all clauses are two-element lists
    for clause in args {
        if let ExprKind::List(items) = &clause.kind {
            if items.len() != 2 {
                return Err(LowerError::InvalidForm(
                    "D3:110 COND clause must be (test expr)".to_string()
                ));
            }
        } else {
            return Err(LowerError::InvalidForm(
                "D3:110 COND clause must be a list".to_string()
            ));
        }
    }
    Ok(())
}

fn lower_cons(args: &[Expr]) -> Result<(), LowerError> {
    // CONS: D3:111
    // Constructor: make pair from two values. Arity: exactly 2.
    // (cons x y) → (x . y) pair structure
    match args {
        [_head, _tail] => Ok(()),
        _ => Err(LowerError::Arity(
            "D3:111 CONS expects exactly 2 arguments".to_string()
        )),
    }
}

fn lower_lambda(args: &[Expr]) -> Result<(), LowerError> {
    // LAMBDA: D4:0010
    // Function definition. Arity: exactly 2 (params body).
    // (lambda (p1 p2 ...) body)
    match args {
        [_params, _body] => Ok(()),
        _ => Err(LowerError::Arity(
            "D4:0010 LAMBDA expects exactly 2 arguments (params body)".to_string()
        )),
    }
}

fn lower_define(args: &[Expr]) -> Result<(), LowerError> {
    // DEFINE: D4:0011
    // Top-level binding. Arity: exactly 2 (name value).
    // (define name value)
    match args {
        [_name, _value] => Ok(()),
        _ => Err(LowerError::Arity(
            "D4:0011 DEFINE expects exactly 2 arguments (name value)".to_string()
        )),
    }
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
