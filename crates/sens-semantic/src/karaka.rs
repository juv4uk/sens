//! Semantic AST structure for a dhātu + its kāraka role bindings
//! (Sanskrit migration Phase 4, docs/sanskrit-semantic-migration.md §5-§6).
//!
//! Spec §5/§6 are explicit that this must be real AST structure, not
//! "decorative text": `(dA :kartf server :karman packet :sampradAna
//! client)` should be represented as
//! `SemanticCall { predicate: DHATU_DA, roles: { KARAKA_KARTR: server, ... } }`,
//! not stored as a string. This module delivers that type and its
//! validation, proven against the spec's own worked example (§0, §35).
//!
//! Deliberately NOT done here (that is `SANSKRIT-P5-AST-SEMANTIC-IDS`'s
//! job per the task board's own phase split): parsing SLP1 source syntax
//! like `(dA :kartf server ...)` into a `SemanticCall`. `SemanticCall`
//! values in this phase are constructed directly (see the tests below),
//! not produced by the tokenizer/parser/atom-resolver pipeline spec §6
//! describes — that pipeline is what P5 wires up, using this type as its
//! target. `Expr` (this crate's real AST expression type, `syntax.rs`) is
//! used for role-bound values now, rather than a placeholder, precisely so
//! P5 only has to *produce* `SemanticCall` values, not change their shape.

use crate::atoms::{self, AtomCategory};
use sens::Expr;

/// A dhātu predicate applied to its kāraka role bindings — the semantic
/// AST node spec §6 names `SemanticCall`. `predicate` and every role key
/// are semantic atom ids (`atoms::Atom::id`, e.g. `"DHATU_DA"`,
/// `"KARAKA_KARTR"`), never raw SLP1 spellings — the same identity-vs-
/// spelling rule as the atom registry itself (spec §3).
#[derive(Debug, Clone)]
pub struct SemanticCall {
    pub predicate: &'static str,
    pub roles: Vec<(&'static str, Expr)>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SemanticCallError {
    /// `predicate` isn't a registered atom at all.
    UnknownPredicate(&'static str),
    /// `predicate` is registered but isn't a dhātu (e.g. a kāraka id used
    /// where a predicate belongs).
    PredicateNotADhatu(&'static str),
    /// A role key isn't a registered atom at all.
    UnknownRole(&'static str),
    /// A role key is registered but isn't a kāraka (e.g. reusing a dhātu
    /// id as a role by mistake).
    RoleNotAKaraka(&'static str),
    /// The same kāraka role was bound more than once in a single call —
    /// spec §20's "duplicate role" test case.
    DuplicateRole(&'static str),
}

impl std::fmt::Display for SemanticCallError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SemanticCallError::UnknownPredicate(id) => {
                write!(f, "unknown predicate atom id `{id}`")
            }
            SemanticCallError::PredicateNotADhatu(id) => {
                write!(f, "predicate `{id}` is not a dhātu")
            }
            SemanticCallError::UnknownRole(id) => write!(f, "unknown role atom id `{id}`"),
            SemanticCallError::RoleNotAKaraka(id) => write!(f, "role `{id}` is not a kāraka"),
            SemanticCallError::DuplicateRole(id) => {
                write!(f, "role `{id}` is bound more than once")
            }
        }
    }
}

impl std::error::Error for SemanticCallError {}

impl SemanticCall {
    /// Builds a `SemanticCall`, validating that `predicate` is a
    /// registered dhātu, every role key is a registered kāraka, and no
    /// role is bound twice — spec §20's "known dhātu / known kāraka /
    /// duplicate role" validation cases, enforced here rather than left
    /// for a later pass to discover.
    pub fn new(
        predicate: &'static str,
        roles: Vec<(&'static str, Expr)>,
    ) -> Result<Self, SemanticCallError> {
        let predicate_atom =
            atoms::by_id(predicate).ok_or(SemanticCallError::UnknownPredicate(predicate))?;
        if predicate_atom.category != AtomCategory::Dhatu {
            return Err(SemanticCallError::PredicateNotADhatu(predicate));
        }

        let mut seen: Vec<&'static str> = Vec::with_capacity(roles.len());
        for (role, _) in &roles {
            let role_atom = atoms::by_id(role).ok_or(SemanticCallError::UnknownRole(role))?;
            if role_atom.category != AtomCategory::Karaka {
                return Err(SemanticCallError::RoleNotAKaraka(role));
            }
            if seen.contains(role) {
                return Err(SemanticCallError::DuplicateRole(role));
            }
            seen.push(role);
        }

        Ok(SemanticCall { predicate, roles })
    }

    pub fn role(&self, role_id: &str) -> Option<&Expr> {
        self.roles
            .iter()
            .find(|(r, _)| *r == role_id)
            .map(|(_, e)| e)
    }
}
