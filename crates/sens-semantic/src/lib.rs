//! sens-semantic - EXPERIMENTAL Sanskrit/Paninian semantic layer.
//!
//! Phases 1-4 of docs/sanskrit-semantic-migration.md: transliteration
//! (SLP1<->IAST<->Devanagari), the Semantic Atom Registry, the 12-dhatu
//! core, and the six karaka roles + SemanticCall AST type. Still NOT wired
//! into the real parser/evaluator - SemanticCall values are built directly
//! in tests, not produced by parsing SLP1 source syntax. That pipeline is
//! SANSKRIT-P5-AST-SEMANTIC-IDS's job (spec section 34: don't do every
//! phase in one commit).
//!
//! Lives in its own crate so the canonical language core stays minimal;
//! the only core types used are the public Expr/ExprKind/Span.

pub mod atoms;
pub mod devanagari;
pub mod karaka;
pub mod transliteration;
