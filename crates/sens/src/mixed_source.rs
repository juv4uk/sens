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
use std::collections::HashSet;
use std::rc::Rc;

/// Parse ordinary mixed Lisp source, then lift only exact-width callable heads
/// into domain identity.
///
/// This is a migration bridge, not a new canonical wire syntax.
pub fn parse_mixed_exact_domain(source: &str) -> Result<Vec<Expr>, LanguageError> {
    let expressions = crate::parser::parse(source)?;
    // Call-head source spellings are NOT authoritative domain identities
    // when this very source declares the spelling as a DEFINE or LAMBDA
    // binding. Protect all such names across this source until the owner
    // lexical-slot resolver can prove their exact scopes. Conservatively
    // declining a projection is safer than silently calling a builtin.
    let mut bound_names = HashSet::new();
    for expression in &expressions {
        collect_source_bindings(source, expression, &mut bound_names);
    }
    expressions
        .into_iter()
        .map(|expression| lift_expression(source, expression, 0, &bound_names))
        .collect()
}

fn binding_form(source: &str, head: &Expr) -> Option<u16> {
    let spelling = source_spelling(source, head)?;
    match spelling {
        "0010" => return Some(2),
        "0011" => return Some(3),
        _ => {}
    }
    let identity = crate::semantic_registry::exact_uk_callable_for_source_head(spelling)?;
    (identity.width() == 4).then_some(identity.packed_bits())
        .filter(|bits| matches!(bits, 2 | 3))
}

fn is_source_quote(source: &str, head: &Expr) -> bool {
    if source_spelling(source, head) == Some("001") {
        return true;
    }
    source_spelling(source, head)
        .and_then(crate::semantic_registry::exact_uk_callable_for_source_head)
        .is_some_and(|id| id.width() == 3 && id.packed_bits() == 1)
}

/// Source-language binder inventory, not an inference of runtime identity.
/// Ignore quoted records and ambiguous old exact-eight forms entirely.
fn collect_source_bindings(source: &str, expression: &Expr, names: &mut HashSet<String>) {
    let ExprKind::List(items) = &expression.kind else { return };
    let Some(head) = items.first() else { return };
    if is_source_quote(source, head) || is_opaque_legacy_w8_head(source, head) {
        return;
    }
    let binding = binding_form(source, head);
    if let Some(kind) = binding {
        if let Some(target) = items.get(1) {
            if kind == 3 {
                if let ExprKind::Symbol(_) = &target.kind {
                    if let Some(name) = source_spelling(source, target) {
                        names.insert(name.to_owned());
                    }
                }
            } else if let ExprKind::List(parameters) = &target.kind {
                for parameter in parameters.iter() {
                    if let ExprKind::Symbol(_) = &parameter.kind {
                        if let Some(name) = source_spelling(source, parameter) {
                            names.insert(name.to_owned());
                        }
                    }
                }
            }
        }
    }
    // Some D2/COND clauses have a LIST as their first element, not an
    // executable callable head. Its test expression may itself introduce
    // a nested binder; do not lose it merely because the parent is a list.
    if matches!(&head.kind, ExprKind::List(_)) {
        collect_source_bindings(source, head, names);
    }
    for (index, child) in items.iter().enumerate().skip(1) {
        if binding.is_some() && index == 1 {
            continue;
        }
        collect_source_bindings(source, child, names);
    }
}

fn lift_expression(
    source: &str,
    expression: Expr,
    depth: u32,
    bound_names: &HashSet<String>,
) -> Result<Expr, LanguageError> {
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
            lifted[0] = lift_head(source, lifted[0].clone(), bound_names)?;

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
                        *clause = lift_cond_clause(source, clause.clone(), depth + 1, bound_names)?;
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
                        *item = lift_expression(source, item.clone(), depth + 1, bound_names)?;
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

fn lift_head(source: &str, head: Expr, bound_names: &HashSet<String>) -> Result<Expr, LanguageError> {
    let Some(spelling) = source_spelling(source, &head) else {
        return Ok(head);
    };

    if !spelling.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
        if bound_names.contains(spelling) {
            // Locals and user-defined callables take precedence over the
            // surface registry. A future lexical resolver can refine this
            // conservative whole-source refusal into precise scopes.
            return Ok(head);
        }
        // Human-facing .lisp stays Ukrainian. Lift ONLY a ratified callable
        // list HEAD into the same exact DomainIdentity as its binary spelling.
        // This is reader-time projection, not runtime dispatch by names.
        // The source registry deliberately has NO legacy SID/English fallback.
        if let Some(identity) =
            crate::semantic_registry::exact_uk_callable_for_source_head(spelling)
        {
            return Ok(Expr {
                kind: ExprKind::DomainIdentity(identity),
                span: head.span,
            });
        }
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
    bound_names: &HashSet<String>,
) -> Result<Expr, LanguageError> {
    let Expr { kind, span } = clause;
    match kind {
        ExprKind::List(items) => {
            let mut lifted = items.to_vec();
            for item in &mut lifted {
                *item = lift_expression(source, item.clone(), depth + 1, bound_names)?;
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
    fn ukrainian_callable_heads_lower_to_exact_domain_without_rewriting_lisp() {
        let source = "(визначити хід (функція (x) (перше x)))";
        let parsed = only(parse_mixed_exact_domain(source).expect("ratified ук surface"));
        let ExprKind::List(defined) = parsed.kind else { panic!("definition"); };
        assert!(matches!(&defined[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 4 && id.packed_bits() == 0b0011));
        // Owner-ratified binding targets are lexical DATA, not callable heads.
        assert!(!matches!(&defined[1].kind, ExprKind::DomainIdentity(_)));
        let ExprKind::List(lambda) = &defined[2].kind else { panic!("звʼязування"); };
        assert!(matches!(&lambda[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 4 && id.packed_bits() == 0b0010));
        let ExprKind::List(body) = &lambda[2].kind else { panic!("lambda body"); };
        assert!(matches!(&body[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 3 && id.packed_bits() == 0b100));

        let byte_source = "(0011 хід (0010 (x) (100 x)))";
        let exact = only(parse_mixed_exact_domain(byte_source).expect("exact source"));
        let ExprKind::List(encoded) = exact.kind else { panic!("exact definition"); };
        let ExprKind::List(encoded_lambda) = &encoded[2].kind else { panic!("exact lambda"); };
        assert_eq!(defined[0].kind, encoded[0].kind);
        assert_eq!(lambda[0].kind, encoded_lambda[0].kind);
        let ExprKind::List(encoded_body) = &encoded_lambda[2].kind else { panic!("exact body"); };
        assert_eq!(body[0].kind, encoded_body[0].kind);
    }

    #[test]
    fn ukrainian_quote_data_and_binding_position_are_not_retyped() {
        let source = "(як-є (перше x))";
        let quoted = only(parse_mixed_exact_domain(source).expect("quoted data"));
        let ExprKind::List(outer) = quoted.kind else { panic!("цитування"); };
        assert!(matches!(&outer[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 3 && id.packed_bits() == 0b001));
        let ExprKind::List(data) = &outer[1].kind else { panic!("quoted data"); };
        assert!(!matches!(&data[0].kind, ExprKind::DomainIdentity(_)));

        let binder = only(parse_mixed_exact_domain(
            "(визначити перше (функція (перше) (атом? перше)))"
        ).expect("binder data"));
        let ExprKind::List(definition) = binder.kind else { panic!("definition"); };
        assert!(!matches!(&definition[1].kind, ExprKind::DomainIdentity(_)));
        let ExprKind::List(lambda) = &definition[2].kind else { panic!("звʼязування"); };
        let ExprKind::List(parameters) = &lambda[1].kind else { panic!("parameters"); };
        assert!(!matches!(&parameters[0].kind, ExprKind::DomainIdentity(_)));
        let ExprKind::List(call) = &lambda[2].kind else { panic!("call"); };
        assert!(matches!(&call[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 3 && id.packed_bits() == 0b010));
    }

    #[test]
    fn unknown_english_and_legacy_heads_get_no_new_current_identity() {
        // Literal legacy-English negative input is DATA, not executable Rust
        // or SENS. Keep its rejection test while avoiding false language-debt.
        let legacy_english_case = include_str!("../../../tests/fixtures/unknown-english-head.txt").trim();
        for source in [legacy_english_case, "(CONS x y)", "(00000101 x)", "(невідоме x)"] {
            let expr = only(parse_mixed_exact_domain(source).expect("bounded mixed syntax"));
            let ExprKind::List(items) = expr.kind else { panic!("список"); };
            assert!(!matches!(&items[0].kind, ExprKind::DomainIdentity(_)),
                "{source} must not become a ratified current domain from spelling");
        }
    }

    #[test]
    fn local_callable_shadows_ratified_uk_surface_in_lambda_body() {
        let forms = parse_mixed_exact_domain("(функція (перше) (перше x))")
            .expect("local shadowing remains valid source");
        let ExprKind::List(lambda) = &forms[0].kind else { panic!("звʼязування"); };
        assert!(matches!(&lambda[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 4 && id.packed_bits() == 0b0010));
        let ExprKind::List(body) = &lambda[2].kind else { panic!("body"); };
        assert!(matches!(&body[0].kind, ExprKind::Symbol(name)
            if &**name == "перше"), "shadowed head must NOT become D3 CAR");
    }

    #[test]
    fn globally_defined_callable_shadows_builtin_even_before_its_definition() {
        let forms = parse_mixed_exact_domain(
            "(перше x) (визначити перше (функція (x) x)) (перше y)"
        ).expect("whole source binding inventory");
        assert_eq!(forms.len(), 3);
        for index in [0, 2] {
            let ExprKind::List(call) = &forms[index].kind else { panic!("call"); };
            assert!(matches!(&call[0].kind, ExprKind::Symbol(name)
                if &**name == "перше"), "user callable wins over ratified built-in");
        }
    }

    #[test]
    fn quoted_definition_is_data_and_does_not_shadow_builtin() {
        let forms = parse_mixed_exact_domain(
            "(як-є (визначити перше (функція (x) x))) (перше x)"
        ).expect("quote remains data");
        let ExprKind::List(call) = &forms[1].kind else { panic!("call"); };
        assert!(matches!(&call[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b100),
            "quoted pseudo-definition must not bind source");
    }

    #[test]
    fn nested_local_shadowed_callable_is_not_promoted_inside_cond_clause() {
        let parsed = parse_mixed_exact_domain(
            "(функція (перше) (за-умовою ((атом? x) (перше x))))"
        ).expect("nested clause");
        let ExprKind::List(lambda) = &parsed[0].kind else { panic!("звʼязування"); };
        let ExprKind::List(cond) = &lambda[2].kind else { panic!("умова"); };
        let ExprKind::List(clause) = &cond[1].kind else { panic!("clause"); };
        let ExprKind::List(body) = &clause[1].kind else { panic!("branch"); };
        assert!(matches!(&body[0].kind, ExprKind::Symbol(name)
            if &**name == "перше"), "local binding is not D3 CAR even in COND");
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
(0011 хід
  (0010 (xs)
    (110
      ((010 xs) (001 done))
      ((101 (001 left) (001 left)) (хід (011 xs))))))
(хід (001 (a b)))
";
        let parsed = parse_mixed_exact_domain(source).expect("recursive exact-domain source parses");
        let mut session = crate::Session::default();
        let result = crate::eval_parsed_expressions(&parsed, &mut session)
            .expect("recursive named definition must execute through mixed bridge");
        assert_eq!(result.value, crate::Value::Symbol(std::rc::Rc::from("done")));
    }
}
