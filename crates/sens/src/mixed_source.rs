//! Mixed human/source parser bridge for the exact-domain migration.
//!
//! The ordinary Lisp parser remains unchanged. This bridge is intentionally
//! bounded to executable list heads:
//! - exact 3/4/5/6-bit binary heads become DomainIdentity;
//! - exact 7-bit heads fail closed because current D7 is Sound/Text/local-ordinal, not callable;
//! - exact 8-bit heads remain the ordinary parser's compatibility path; this bridge does not infer current D8;
//! - non-head data keeps the ordinary parser's interpretation.
//!
//! This gives active Core migration a mixed symbol + exact-domain path without
//! teaching the compatibility parser to infer domains from historical bytes.

use crate::syntax::{Expr, ExprKind, MAX_STRUCTURE_DEPTH};
use crate::{parse_binary_source_words, DomainIdentity, ErrorKind, LanguageError};
use std::rc::Rc;

/// Parse ordinary mixed Lisp source, then lift only exact-width callable heads
/// into domain identity.
///
/// This is a migration bridge, not a new canonical wire syntax.
pub fn parse_mixed_exact_domain(source: &str) -> Result<Vec<Expr>, LanguageError> {
    crate::parser::parse(source)?
        .into_iter()
        .map(|expression| lift_expression(source, expression, 0))
        .collect()
}

fn lift_expression(source: &str, expression: Expr, depth: u32) -> Result<Expr, LanguageError> {
    if depth > MAX_STRUCTURE_DEPTH {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "mixed exact-domain source exceeds structure depth",
            expression.span,
        ));
    }

    let Expr { kind, span } = expression;
    match kind {
        ExprKind::List(items) if !items.is_empty() => {
            let mut lifted = items.to_vec();
            lifted[0] = lift_head(source, lifted[0].clone())?;

            // Legacy exact-eight heads belong to the ordinary compatibility
            // parser. They are OPAQUE while their historical source-era and
            // owner-ratified current successor remain unproved. In particular
            // old W8 QUOTE must never convert a quoted (100 ...) data list
            // into a current D3 CAR call merely because that nested head is
            // three bits wide. Do not infer current D8 from spelling.
            if is_opaque_legacy_w8_head(source, &lifted[0]) {
                return Ok(Expr {
                    kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
                    span,
                });
            }

            // Exact D3 QUOTE keeps its argument as reader data. Apostrophe
            // sugar also stays data-owned without naming legacy byte identity.
            let quote_data =
                is_exact_quote(&lifted[0]) || source_spelling(source, &lifted[0]) == Some("'");

            if !quote_data {
                if is_exact_cond(&lifted[0]) {
                    for clause in lifted.iter_mut().skip(1) {
                        *clause = lift_cond_clause(source, clause.clone(), depth + 1)?;
                    }
                } else {
                    // D4 LAMBDA parameter declarations and D4 DEFINE binding
                    // targets are DATA, never callable expression positions.
                    // Preserve their exact parsed structure; only bodies and
                    // value expressions may lift executable domain heads.
                    let binding_head = is_exact_d4_binding_head(&lifted[0]);
                    for (index, item) in lifted.iter_mut().enumerate().skip(1) {
                        if binding_head && index == 1 {
                            continue;
                        }
                        *item = lift_expression(source, item.clone(), depth + 1)?;
                    }
                }
            }

            Ok(Expr {
                kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
                span,
            })
        }
        other => Ok(Expr { kind: other, span }),
    }
}

fn lift_head(source: &str, head: Expr) -> Result<Expr, LanguageError> {
    let Some(spelling) = source_spelling(source, &head) else {
        return Ok(head);
    };

    if !spelling.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
        return Ok(head);
    }

    match spelling.len() {
        3..=6 => {
            let tokens = parse_binary_source_words(spelling)?;
            let Some(token) = tokens.first().copied() else {
                return Ok(head);
            };
            debug_assert_eq!(tokens.len(), 1);

            Ok(Expr {
                kind: ExprKind::DomainIdentity(DomainIdentity::from_source_word(token.word)),
                span: head.span,
            })
        }
        7 => Err(LanguageError::new(
            ErrorKind::Parse,
            "D7 exact-domain call heads are current but non-callable in mixed source",
            head.span,
        )),
        // The ordinary parser intentionally owns exact-eight compatibility.
        // Never reinterpret that historical spelling as D8 here.
        8 => Ok(head),
        _ => Ok(head),
    }
}

fn lift_cond_clause(
    source: &str,
    clause: Expr,
    depth: u32,
) -> Result<Expr, LanguageError> {
    let Expr { kind, span } = clause;
    match kind {
        ExprKind::List(items) => {
            let mut lifted = items.to_vec();
            for item in &mut lifted {
                *item = lift_expression(source, item.clone(), depth + 1)?;
            }
            Ok(Expr {
                kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
                span,
            })
        }
        other => Ok(Expr { kind: other, span }),
    }
}

fn source_spelling<'a>(source: &'a str, expression: &Expr) -> Option<&'a str> {
    source.get(expression.span.start..expression.span.end)
}

/// Opaque W8 compatibility syntax is not an admission of current D8.
fn is_opaque_legacy_w8_head(source: &str, head: &Expr) -> bool {
    source_spelling(source, head).is_some_and(|spelling| {
        spelling.len() == 8 && spelling.bytes().all(|byte| matches!(byte, b'0' | b'1'))
    })
}

fn is_exact_d4_binding_head(expression: &Expr) -> bool {
    matches!(
        &expression.kind,
        ExprKind::DomainIdentity(identity)
            if identity.width() == 4
                && matches!(identity.packed_bits(), 0b0010 | 0b0011)
    )
}

fn is_exact_quote(expression: &Expr) -> bool {
    matches!(
        &expression.kind,
        ExprKind::DomainIdentity(identity)
            if identity.width() == 3 && identity.packed_bits() == 0b001
    )
}

fn is_exact_cond(expression: &Expr) -> bool {
    matches!(
        &expression.kind,
        ExprKind::DomainIdentity(identity)
            if identity.width() == 3 && identity.packed_bits() == 0b110
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::eval::lower::lower_program;
    use crate::CoreDomainIdentity;

    fn only(mut expressions: Vec<Expr>) -> Expr {
        assert_eq!(expressions.len(), 1);
        expressions.remove(0)
    }

    #[test]
    fn mixed_lambda_preserves_symbol_binder_and_exact_d3_d4_heads() {
        let expression =
            only(parse_mixed_exact_domain("(0010 (x) (100 x))").expect("mixed parse"));

        let ExprKind::List(items) = &expression.kind else {
            panic!("expected list");
        };
        assert!(matches!(
            &items[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 4 && identity.packed_bits() == 0b0010
        ));

        let ExprKind::List(params) = &items[1].kind else {
            panic!("expected parameter list");
        };
        assert!(matches!(&params[0].kind, ExprKind::Symbol(name) if &**name == "x"));

        let ExprKind::List(body) = &items[2].kind else {
            panic!("expected body call");
        };
        assert!(matches!(
            &body[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 3 && identity.packed_bits() == 0b100
        ));
    }

    #[test]
    fn exact_d4_define_and_lambda_execute_through_mixed_bridge() {
        let parsed = parse_mixed_exact_domain(
            "(0011 f (0010 (x) (010 x)))\n(f (001 a))",
        )
        .expect("mixed exact DEFINE/LAMBDA parse");

        let mut session = crate::Session::default();
        let result = crate::eval::eval_parsed_expressions(&parsed, &mut session)
            .expect("exact D4 DEFINE/LAMBDA must execute through mixed bridge");

        assert!(result.value.as_predicate_bit().is_some());
    }

    #[test]
    fn mixed_exact_heads_lower_directly_to_domain_calls() {
        let parsed = parse_mixed_exact_domain("(0010 (x) (100 x))").unwrap();
        let lowered = only(lower_program(&parsed));

        let ExprKind::DomainCall(CoreDomainIdentity::D4(word), args) = lowered.kind else {
            panic!("expected D4 DomainCall");
        };
        assert_eq!(word.word().packed_bits(), 0b0010);

        let ExprKind::DomainCall(CoreDomainIdentity::D3(word), _) = &args[1].kind else {
            panic!("expected nested D3 DomainCall");
        };
        assert_eq!(word.word().packed_bits(), 0b100);
    }

    #[test]
    fn exact_cond_lifts_test_and_branch_heads_inside_clause_structure() {
        let expression = only(
            parse_mixed_exact_domain(
                "(110 ((101 x 0) (01010 x 1)) ((101 0 0) 0))",
            )
            .expect("mixed COND parse"),
        );
        let ExprKind::List(items) = expression.kind else {
            panic!("expected COND list");
        };
        let ExprKind::List(first_clause) = &items[1].kind else {
            panic!("expected first COND clause");
        };
        let ExprKind::List(test) = &first_clause[0].kind else {
            panic!("expected test expression");
        };
        assert!(matches!(
            &test[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 3 && identity.packed_bits() == 0b101
        ));
        let ExprKind::List(branch) = &first_clause[1].kind else {
            panic!("expected branch expression");
        };
        assert!(matches!(
            &branch[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 5 && identity.packed_bits() == 0b01010
        ));
    }

    #[test]
    fn exact_binary_data_outside_head_position_stays_data() {
        let expression =
            only(parse_mixed_exact_domain("(0010 (x) 100)").expect("mixed parse"));
        let ExprKind::List(items) = expression.kind else {
            panic!("expected list");
        };
        assert!(matches!(&items[2].kind, ExprKind::Number(value, _) if *value == 100.0));
    }

    #[test]
    fn exact_quote_does_not_reinterpret_quoted_binary_data() {
        let expression = only(parse_mixed_exact_domain("(001 100)").expect("mixed parse"));
        let ExprKind::List(items) = expression.kind else {
            panic!("expected list");
        };
        assert!(matches!(
            &items[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 3 && identity.packed_bits() == 0b001
        ));
        assert!(matches!(&items[1].kind, ExprKind::Number(value, _) if *value == 100.0));
    }

    #[test]
    fn exact8_head_remains_compatibility_only() {
        let expression =
            only(parse_mixed_exact_domain("(00000001 x)").expect("mixed parse"));
        let span = expression.span;
        let ExprKind::List(items) = expression.kind else {
            panic!("expected list");
        };
        assert!(matches!(&items[0].kind, ExprKind::Sid(_)));

        let lowered = only(lower_program(&[Expr {
            kind: ExprKind::List(items),
            span,
        }]));
        assert!(matches!(lowered.kind, ExprKind::Call(_, _)));
    }

    #[test]
    fn d6_exact_identity_does_not_invent_callability_and_admitted_mechanism_lowers() {
        // Every D6 binary word has a source identity, but not all D6 words
        // are current executable mechanisms. 000001 is noncallable.
        let parsed = parse_mixed_exact_domain("(000001 x)").expect("D6 source");
        let ExprKind::List(items) = &parsed[0].kind else {
            panic!("expected list");
        };
        assert!(matches!(
            &items[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 6 && identity.packed_bits() == 1
        ));
        let lowered = only(lower_program(&parsed));
        let ExprKind::List(items) = &lowered.kind else {
            panic!("unadmitted D6 must not be an executable DomainCall");
        };
        assert!(matches!(
            &items[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 6 && identity.packed_bits() == 1
        ));

        // The ratified exact D6 mechanism 001110 is callable.
        let current = parse_mixed_exact_domain("(001110 x)")
            .expect("ratified D6 mechanism source");
        let admitted = only(lower_program(&current));
        assert!(matches!(
            admitted.kind,
            ExprKind::DomainCall(CoreDomainIdentity::D6(word), _)
                if word.word().packed_bits() == 0b001110
        ));
    }

    #[test]
    fn current_noncallable_d7_exact_head_fails_closed() {
        let error = parse_mixed_exact_domain("(0000001 x)").expect_err("D7 must reject");
        assert_eq!(error.kind, ErrorKind::Parse);
        assert!(error.message.contains("non-callable"));
    }

    #[test]
    fn opaque_historical_w8_quote_never_changes_nested_binary_data() {
        // This outer W8 head is parser-owned historical compatibility, not
        // a proven current-D8 call; its inner three-bit data must stay data.
        let parsed = parse_mixed_exact_domain("(00000001 (100 x))").unwrap();
        let ExprKind::List(outer) = &parsed[0].kind else {
            panic!("expected outer legacy list");
        };
        assert!(matches!(&outer[0].kind, ExprKind::Sid(_)));
        let ExprKind::List(quoted) = &outer[1].kind else {
            panic!("expected quoted list data");
        };
        assert!(matches!(
            &quoted[0].kind,
            ExprKind::Number(value, _) if *value == 100.0
        ), "quoted source must not become a D3 executable identity");

        // Non-QUOTE W8 is also opaque: its owner/era is not yet proven.
        let unknown = parse_mixed_exact_domain("(11111111 (011 x))").unwrap();
        let ExprKind::List(form) = &unknown[0].kind else {
            panic!("legacy form");
        };
        let ExprKind::List(inner) = &form[1].kind else {
            panic!("legacy operand data");
        };
        assert!(!matches!(&inner[0].kind, ExprKind::DomainIdentity(_)));
    }

    #[test]
    fn exact_d4_lambda_and_define_binding_slots_are_source_data() {
        // Binder declarations may be structural lists whose first atom
        // looks like a D3 word; it is not an executable CAR/COND call.
        let expression = only(
            parse_mixed_exact_domain("(0010 ((100 x)) (011 x))")
                .expect("exact D4 lambda parse"),
        );
        let ExprKind::List(lambda) = &expression.kind else {
            panic!("lambda list");
        };
        let ExprKind::List(params) = &lambda[1].kind else {
            panic!("lambda binders");
        };
        let ExprKind::List(declaration) = &params[0].kind else {
            panic!("nested binder metadata");
        };
        assert!(!matches!(&declaration[0].kind, ExprKind::DomainIdentity(_)));
        let ExprKind::List(body) = &lambda[2].kind else {
            panic!("executable body");
        };
        assert!(matches!(
            &body[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 3 && identity.packed_bits() == 0b011
        ));

        let defined = only(
            parse_mixed_exact_domain("(0011 (100 x) (011 x))")
                .expect("D4 define parse"),
        );
        let ExprKind::List(items) = &defined.kind else {
            panic!("define list");
        };
        let ExprKind::List(name_record) = &items[1].kind else {
            panic!("define name data");
        };
        assert!(!matches!(&name_record[0].kind, ExprKind::DomainIdentity(_)));
        let ExprKind::List(value) = &items[2].kind else {
            panic!("define value expression");
        };
        assert!(matches!(&value[0].kind, ExprKind::DomainIdentity(_)));
    }

    #[test]
    fn ordinary_symbol_call_still_lifts_proven_nested_current_heads() {
        let parsed = parse_mixed_exact_domain("(local-f (100 x))")
            .expect("mixed ordinary call");
        let ExprKind::List(outer) = &parsed[0].kind else {
            panic!("outer call");
        };
        let ExprKind::List(inner) = &outer[1].kind else {
            panic!("inner current call");
        };
        assert!(matches!(
            &inner[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 3 && identity.packed_bits() == 0b100
        ));
    }

    #[test]
    fn d5_current_head_is_preserved_as_exact_domain_identity() {
        let expression = only(parse_mixed_exact_domain("(00000 x)").expect("mixed parse"));
        let ExprKind::List(items) = expression.kind else {
            panic!("expected list");
        };
        assert!(matches!(
            &items[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 5 && identity.packed_bits() == 0
        ));
    }

    #[test]
    fn exact_domain_named_definition_supports_recursive_symbol_calls() {
        let source = "\
(0011 walk
  (0010 (xs)
    (110
      ((010 xs) (001 done))
      ((101 (001 left) (001 left)) (walk (011 xs))))))
(walk (001 (a b)))
";
        let parsed = parse_mixed_exact_domain(source).expect("recursive exact-domain source parses");
        let mut session = crate::Session::default();
        let result = crate::eval_parsed_expressions(&parsed, &mut session)
            .expect("recursive named definition must execute through mixed bridge");
        assert_eq!(result.value, crate::Value::Symbol(std::rc::Rc::from("done")));
    }
}