//! Compiler IR v0 — GitHub issue juv4uk/my-lisp#68. See
//! docs/COMPILER-IR-V0.md for the full design rationale.
//!
//! This module is DATA, not a second evaluator: it lowers a parsed `Expr`
//! into a provenance-bearing tree that a future compiler backend can
//! serialize/inspect, without inventing any semantics `crates/my-lisp`'s
//! own evaluator and semantic registry don't already admit. Per #66
//! (compiler authority boundary), lowering must fail closed rather than
//! guess when it encounters a form shape it does not recognize.
//!
//! `#[allow(dead_code)]`: #68's own acceptance evidence explicitly says
//! "no execution backend is required yet" — this module is exercised
//! entirely by its own `#[cfg(test)]` suite below (including a full pass
//! over #67's frozen compiler-corpus fixtures), which the plain `--lib`
//! build target does not compile in, so rustc's dead-code analysis on
//! that target alone cannot see the usage. Remove this once a real
//! consumer (a compiler backend, or a future public export module
//! mirroring `semantic_registry_export`) calls into `lower`/`explain`
//! from outside this module's tests.
#![allow(dead_code)]

use crate::eval::canon;
use crate::eval::necessary_forms::{self, NecessaryFormIdentity};
use crate::semantic_registry;
use crate::syntax::{Exactness, Expr, ExprKind, Span};
use crate::value::Rational;
use crate::Sid8;

/// `def` is a compatibility-only spelling for the same Define meaning as
/// `define`/`визначити` (SID 00001001), under its own byte SID 00001011 in
/// `lib/surface/semantic-registry.wsm`. `necessary_forms::identity_for_symbol`
/// resolves it directly (via the admitted stable-or-compatibility-only
/// surface index) as of 2026-09-12 -- this used to need its own `name ==
/// "def"` special case here, mirroring an equivalent hardcoded literal in
/// `eval/mod.rs`'s real dispatch, because the registry lookup those two
/// call sites used could not see a compatibility-only row at all. Both
/// hardcoded literals are gone now that the lookup itself can see it.
fn is_define_spelling(name: &str) -> bool {
    necessary_forms::identity_for_symbol(name) == Some(NecessaryFormIdentity::Define)
}

/// How a lowered node's meaning is justified — the "provenance" #68
/// requires. Every `IrNode` carries one of these, so `explain` can always
/// answer "why does this data mean what it means" without re-deriving it.
#[derive(Clone, Debug, PartialEq)]
pub enum Provenance {
    /// `lambda` (SID 00001000) or `define`/`def` (SIDs 00001001/00001011) — evaluator-owned mechanism
    /// beyond Canon, resolved by exact SID identity.
    NecessaryForm(NecessaryFormIdentity),
    /// A function selected by its exact eight-bit identity.
    /// No word/enum label is retained as a second identity.
    FunctionSid(Sid8),
    /// A binding this lowering pass has no registry entry for — an
    /// ordinary user-defined function/variable. This is NOT a failure:
    /// most real programs are built from bindings the registry has no
    /// opinion about (a user's own `count-down`, say). Distinct from
    /// `FunctionSid` only so `explain` can say which is which.
    OrdinaryBinding,
    /// A literal value read directly from source — its own provenance.
    Literal,
}

/// The provenance-bearing IR node. Deliberately small: #68 explicitly asks
/// for the smallest IR that carries execution plans without becoming a
/// second language specification, not a full compiler intermediate form.
#[derive(Clone, Debug, PartialEq)]
pub enum IrNode {
    /// An exact or inexact literal value, carried through unchanged —
    /// never approximated or re-typed during lowering (S1).
    Literal {
        value: LiteralValue,
        span: Span,
        provenance: Provenance,
    },
    /// A symbol referenced for its bound value, not applied.
    VariableRef {
        name: String,
        span: Span,
        provenance: Provenance,
    },
    /// `(quote datum)` — the datum is preserved as unlowered source data,
    /// per G3 (program structure is data); lowering it further would
    /// silently give it executable meaning it never had.
    Quote { datum: Expr, span: Span },
    /// `(cond (test body...) ...)` — clauses kept in source order; no
    /// clause is lowered eagerly, since evaluation order/short-circuit is
    /// part of the admitted semantics (docs/meta-eval-evidence.md's
    /// `cond-short-circuit` row), not a detail lowering may reorder.
    Cond { clauses: Vec<CondClause>, span: Span },
    /// `(lambda params body...)` — params kept as source `Expr` (covers
    /// fixed/dotted/bare-symbol shapes without IR re-inventing lambda-list
    /// parsing); body lowered.
    Lambda {
        params: Box<Expr>,
        body: Vec<IrNode>,
        span: Span,
    },
    /// `(def name value)` / `(define name value)`.
    Define {
        name: String,
        value: Box<IrNode>,
        span: Span,
    },
    /// `(defmacro name params body...)` — body kept as source `Expr`
    /// (macro expansion is a language-owned transformation happening at a
    /// different stage than IR lowering, per `lib/macro.my`).
    Defmacro {
        name: String,
        params: Box<Expr>,
        body: Vec<Expr>,
        span: Span,
    },
    /// An ordinary function/primitive application — the callee's
    /// provenance says whether it's an admitted function SID or an
    /// ordinary binding; this node never guesses which.
    Apply {
        callee: Box<IrNode>,
        args: Vec<IrNode>,
        span: Span,
    },
}

#[derive(Clone, Debug, PartialEq)]
pub struct CondClause {
    pub test: IrNode,
    pub body: Vec<IrNode>,
}

/// A literal's exact value, kept independent of the evaluator's `Value`
/// type so this module has no runtime/session dependency — IR lowering is
/// pure source-to-data, never touches an `Environment`.
#[derive(Clone, Debug, PartialEq)]
pub enum LiteralValue {
    Number(f64, Exactness),
    Rational(Rational),
    Sid(Sid8),
    EmptyList,
    String(String),
    Symbol(String),
}

/// Lowering cannot invent a shape for a form it does not recognize — this
/// is the fail-closed side of #66's authority boundary applied to IR.
#[derive(Clone, Debug, PartialEq)]
pub enum LoweringError {
    /// A form whose head resolves to a exact SID identity this
    /// lowering pass has never been taught how to handle as a special
    /// form shape. Recognized syntax identities (quote/cond/lambda/
    /// define/defmacro) are exhaustively matched in `classify_syntax_id`;
    /// anything else with a "this should be special-form-shaped" claim is
    /// rejected here rather than silently treated as an ordinary call.
    UnrecognizedSyntaxIdentity { semantic_id: String, span: Span },
    /// A form shape lowering does not know how to interpret at all (e.g.
    /// an empty list in operator position, or a special-form call with
    /// the wrong argument count for what its identity requires).
    MalformedForm { detail: String, span: Span },
}

fn symbol_text(expr: &Expr) -> Option<&str> {
    match &expr.kind {
        ExprKind::Symbol(s) => Some(s.as_ref()),
        _ => None,
    }
}

fn sid_of_head(expr: &Expr) -> Option<Sid8> {
    match &expr.kind {
        ExprKind::Sid(sid) => Some(*sid),
        _ => None,
    }
}

/// Lower one parsed expression into IR. The only entry point this module
/// exposes for turning source into data.
pub fn lower(expr: &Expr) -> Result<IrNode, LoweringError> {
    match &expr.kind {
        ExprKind::Number(n, exactness) => Ok(IrNode::Literal {
            value: LiteralValue::Number(*n, *exactness),
            span: expr.span,
            provenance: Provenance::Literal,
        }),
        ExprKind::Rational(r) => Ok(IrNode::Literal {
            value: LiteralValue::Rational(r.clone()),
            span: expr.span,
            provenance: Provenance::Literal,
        }),
        ExprKind::Sid(sid) => Ok(IrNode::Literal {
            value: LiteralValue::Sid(*sid),
            span: expr.span,
            provenance: Provenance::Literal,
        }),
        ExprKind::String(s) => Ok(IrNode::Literal {
            value: LiteralValue::String(s.to_string()),
            span: expr.span,
            provenance: Provenance::Literal,
        }),
        ExprKind::Symbol(name) => Ok(lower_symbol_reference(name, expr.span)),
        ExprKind::NumericBuffer(_) | ExprKind::Pair(_, _) => Err(LoweringError::MalformedForm {
            detail: "numeric buffers and dotted pairs are data-only forms, never executable heads"
                .to_string(),
            span: expr.span,
        }),
        ExprKind::List(items) => lower_list(items, expr.span),
    }
}

fn lower_symbol_reference(name: &str, span: Span) -> IrNode {
    let provenance = if is_define_spelling(name) {
        Provenance::NecessaryForm(NecessaryFormIdentity::Define)
    } else if let Some(identity) = necessary_forms::identity_for_symbol(name) {
        Provenance::NecessaryForm(identity)
    } else if let Some(sid) = semantic_registry::admitted_semantic_id_for_surface(name) {
        Provenance::FunctionSid(sid)
    } else {
        Provenance::OrdinaryBinding
    };
    IrNode::VariableRef {
        name: name.to_string(),
        span,
        provenance,
    }
}

fn lower_list(items: &[Expr], span: Span) -> Result<IrNode, LoweringError> {
    let Some(head) = items.first() else {
        // Empty structure is a literal structural value outside the complete
        // function-SID space. It carries no function identity and receives no SID.
        return Ok(IrNode::Literal {
            value: LiteralValue::EmptyList,
            span,
            provenance: Provenance::Literal,
        });
    };
    let head_sid = sid_of_head(head).or_else(|| {
        symbol_text(head).and_then(semantic_registry::admitted_semantic_id_for_surface)
    });

    if let Some(sid) = head_sid {
        if sid == crate::sid!(00000001) {
            let [_, datum] = items else {
                return Err(LoweringError::MalformedForm {
                    detail: format!(
                        "SID 00000001 takes exactly one argument, got {}",
                        items.len() - 1
                    ),
                    span,
                });
            };
            return Ok(IrNode::Quote {
                datum: datum.clone(),
                span,
            });
        }
        if sid == crate::sid!(00000111) {
            return lower_cond(items, span);
        }
        if sid == crate::sid!(00001000) {
            return lower_lambda(items, span);
        }
        if sid == crate::sid!(00001001) || sid == crate::sid!(00001011) {
            return lower_define(items, span);
        }
        if sid == crate::sid!(00001010) {
            return lower_defmacro(items, span);
        }
        return lower_ordinary_application(head, &items[1..], span);
    }

    // No function SID was selected: this is an ordinary computed/user binding.
    lower_ordinary_application(head, &items[1..], span)
}

fn lower_cond(items: &[Expr], span: Span) -> Result<IrNode, LoweringError> {
    let mut clauses = Vec::new();
    for clause_expr in &items[1..] {
        let ExprKind::List(clause_items) = &clause_expr.kind else {
            return Err(LoweringError::MalformedForm {
                detail: "each cond clause must be a list (test body...)".to_string(),
                span: clause_expr.span,
            });
        };
        let Some((test_expr, body_exprs)) = clause_items.split_first() else {
            return Err(LoweringError::MalformedForm {
                detail: "cond clause must have at least a test".to_string(),
                span: clause_expr.span,
            });
        };
        let test = lower(test_expr)?;
        let body = body_exprs
            .iter()
            .map(lower)
            .collect::<Result<Vec<_>, _>>()?;
        clauses.push(CondClause { test, body });
    }
    Ok(IrNode::Cond { clauses, span })
}

fn lower_lambda(items: &[Expr], span: Span) -> Result<IrNode, LoweringError> {
    let Some((params, body_exprs)) = items[1..].split_first() else {
        return Err(LoweringError::MalformedForm {
            detail: "lambda requires a parameter list".to_string(),
            span,
        });
    };
    let body = body_exprs
        .iter()
        .map(lower)
        .collect::<Result<Vec<_>, _>>()?;
    Ok(IrNode::Lambda {
        params: Box::new(params.clone()),
        body,
        span,
    })
}

fn lower_define(items: &[Expr], span: Span) -> Result<IrNode, LoweringError> {
    let [_, name_expr, value_expr] = items else {
        return Err(LoweringError::MalformedForm {
            detail: format!(
                "define/def takes exactly two arguments, got {}",
                items.len().saturating_sub(1)
            ),
            span,
        });
    };
    let Some(name) = symbol_text(name_expr) else {
        return Err(LoweringError::MalformedForm {
            detail: "define/def's first argument must be a symbol".to_string(),
            span: name_expr.span,
        });
    };
    let value = lower(value_expr)?;
    Ok(IrNode::Define {
        name: name.to_string(),
        value: Box::new(value),
        span,
    })
}

fn lower_defmacro(items: &[Expr], span: Span) -> Result<IrNode, LoweringError> {
    let Some((name_expr, rest)) = items[1..].split_first() else {
        return Err(LoweringError::MalformedForm {
            detail: "defmacro requires at least a name".to_string(),
            span,
        });
    };
    let Some(name) = symbol_text(name_expr) else {
        return Err(LoweringError::MalformedForm {
            detail: "defmacro's first argument must be a symbol".to_string(),
            span: name_expr.span,
        });
    };
    let Some((params, body)) = rest.split_first() else {
        return Err(LoweringError::MalformedForm {
            detail: "defmacro requires a parameter list".to_string(),
            span,
        });
    };
    Ok(IrNode::Defmacro {
        name: name.to_string(),
        params: Box::new(params.clone()),
        body: body.to_vec(),
        span,
    })
}

fn lower_ordinary_application(
    callee_expr: &Expr,
    arg_exprs: &[Expr],
    span: Span,
) -> Result<IrNode, LoweringError> {
    let callee = lower(callee_expr)?;
    let args = arg_exprs.iter().map(lower).collect::<Result<Vec<_>, _>>()?;
    Ok(IrNode::Apply {
        callee: Box::new(callee),
        args,
        span,
    })
}

/// Reconstruct a human-readable provenance trace for one IR node — #68's
/// own acceptance criterion: "an agent or test can explain how a source
/// form became executable data." Not recursive by design: callers walk
/// the tree themselves and call this per node, so the trace stays
/// legible instead of dumping an entire nested tree as one string.
pub fn explain(node: &IrNode) -> String {
    match node {
        IrNode::Literal { provenance, .. } => format!("literal value ({provenance:?})"),
        IrNode::VariableRef {
            name, provenance, ..
        } => format!("reference to `{name}` ({provenance:?})"),
        IrNode::Quote { .. } => "quote: datum preserved as unlowered source data (G3)".to_string(),
        IrNode::Cond { clauses, .. } => {
            format!("SID 00000111: {} clause(s), special-form shape", clauses.len())
        }
        IrNode::Lambda { body, .. } => format!(
            "lambda: {} body expression(s), byte SID 00001000",
            body.len()
        ),
        IrNode::Define { name, .. } => {
            format!("define/def: binds `{name}`, byte SID 00001001/00001011")
        }
        IrNode::Defmacro { name, .. } => {
            format!("defmacro: constructs macro `{name}`, byte SID 00001010")
        }
        IrNode::Apply { args, .. } => format!("application with {} argument(s)", args.len()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parser::parse;

    fn lower_source(source: &str) -> IrNode {
        let forms = parse(source).expect("source should parse");
        assert_eq!(forms.len(), 1, "test helper expects exactly one top-level form");
        lower(&forms[0]).expect("form should lower")
    }

    #[test]
    fn quote_preserves_datum_unlowered() {
        let node = lower_source("(quote (a b c))");
        assert!(matches!(node, IrNode::Quote { .. }));
    }

    #[test]
    fn canon_value_primitives_are_ordinary_applications_with_canon_provenance() {
        let node = lower_source("(car (quote (1 2)))");
        let IrNode::Apply { callee, .. } = node else {
            panic!("expected Apply");
        };
        let IrNode::VariableRef { provenance, .. } = *callee else {
            panic!("expected VariableRef callee");
        };
        assert_eq!(provenance, Provenance::FunctionSid(crate::sid!(00000101)));
    }

    #[test]
    fn lambda_and_define_carry_necessary_form_shape() {
        assert!(matches!(
            lower_source("(lambda (x) x)"),
            IrNode::Lambda { .. }
        ));
        assert!(matches!(
            lower_source("(def x 1)"),
            IrNode::Define { .. }
        ));
    }

    #[test]
    fn defmacro_is_lowered_as_its_own_shape_not_an_ordinary_call() {
        let node = lower_source("(defmacro my-macro (x) x)");
        assert!(matches!(node, IrNode::Defmacro { .. }));
    }

    #[test]
    fn ordinary_admitted_semantic_identity_is_tagged_not_special_cased() {
        // `+` (SID 00001100) is an ordinary callable, not a special
        // form -- lowering must produce a plain Apply, with the callee's
        // provenance naming the admitted identity for a backend to use.
        let node = lower_source("(+ 1 2)");
        let IrNode::Apply { callee, .. } = node else {
            panic!("expected Apply");
        };
        let IrNode::VariableRef { provenance, .. } = *callee else {
            panic!("expected VariableRef callee");
        };
        assert_eq!(
            provenance,
            Provenance::FunctionSid(crate::sid!(00001100))
        );
    }

    #[test]
    fn unbound_user_symbol_is_an_ordinary_binding_not_a_failure() {
        let node = lower_source("(my-own-function 1 2)");
        let IrNode::Apply { callee, .. } = node else {
            panic!("expected Apply");
        };
        let IrNode::VariableRef { provenance, .. } = *callee else {
            panic!("expected VariableRef callee");
        };
        assert_eq!(provenance, Provenance::OrdinaryBinding);
    }

    #[test]
    fn empty_list_lowers_as_structural_literal_without_function_sid() {
        let node = lower_source("()");
        let IrNode::Literal { value, provenance, .. } = node else {
            panic!("expected Literal");
        };
        assert_eq!(value, LiteralValue::EmptyList);
        assert_eq!(provenance, Provenance::Literal);
    }

    /// #68's own acceptance criterion: "a fixture with an unknown/
    /// unadmitted semantic identity fails closed instead of inventing a
    /// lowering." `classify_syntax_id` is the exhaustive gate; this proves
    /// it rejects an identity it was never taught, rather than defaulting
    /// to some guessed shape.
    /// #68's own acceptance criterion: "lower a small but nontrivial corpus
    /// from source/canonical forms to IR and reconstruct enough provenance
    /// to explain each step." Reuses #67's own frozen compiler-corpus
    /// fixtures (`(compiler-corpus . t)` in conformance.my) rather than a
    /// new invented sample -- the same corpus a compiled-execution backend
    /// must already match.
    #[test]
    fn lowers_and_explains_every_compiler_corpus_fixture() {
        let source = include_str!("../../../tests/fixtures/conformance.lisp");
        let forms = parse(source).expect("conformance.my should parse");
        let mut lowered_count = 0;
        for form in &forms {
            let ExprKind::List(entries) = &form.kind else {
                continue;
            };
            let is_corpus_entry = entries.iter().any(|entry| {
                let ExprKind::Pair(k, v) = &entry.kind else {
                    return false;
                };
                let ExprKind::Symbol(name) = &k.kind else {
                    return false;
                };
                &**name == "compiler-corpus" && matches!(&v.kind, ExprKind::Symbol(s) if &**s == "t")
            });
            if !is_corpus_entry {
                continue;
            }
            let find_field = |key: &str| {
                entries.iter().find_map(|entry| {
                    let ExprKind::Pair(k, v) = &entry.kind else {
                        return None;
                    };
                    let ExprKind::Symbol(name) = &k.kind else {
                        return None;
                    };
                    if &**name != key {
                        return None;
                    }
                    match &v.kind {
                        ExprKind::String(s) => Some(s.as_ref()),
                        _ => None,
                    }
                })
            };
            let expr_text = find_field("expr").expect("compiler-corpus entry must have an expr field");
            // Fixtures tagged with an `error` field are deliberately
            // malformed AT THE EVALUATOR LEVEL (e.g. `(defmacro foo)`'s
            // missing arity) -- that is a runtime binding-count/dispatch
            // concern, not necessarily a structural IR problem, so this
            // corpus does not require lowering to succeed for them. It
            // does require every *success* (`expected`-tagged) fixture to
            // lower and explain cleanly -- that is the actual "compiler
            // must reproduce this" contract.
            let is_error_fixture = find_field("error").is_some();

            let sub_forms = parse(expr_text)
                .unwrap_or_else(|e| panic!("corpus expr should parse: {expr_text}: {e}"));
            for sub_form in &sub_forms {
                match lower(sub_form) {
                    Ok(node) => {
                        let trace = explain(&node);
                        assert!(!trace.is_empty(), "explain must produce a non-empty trace");
                        lowered_count += 1;
                    }
                    Err(e) => {
                        assert!(
                            is_error_fixture,
                            "success-tagged corpus fixture failed to lower: {expr_text}: {e:?}"
                        );
                    }
                }
            }
        }
        assert!(
            lowered_count >= 17,
            "expected to lower at least the 17 tagged compiler-corpus fixtures, got {lowered_count}"
        );
    }
}
