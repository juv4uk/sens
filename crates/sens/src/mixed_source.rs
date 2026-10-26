//! Mixed human/source parser bridge for the exact-domain migration.
//!
//! The ordinary Lisp parser remains unchanged. This bridge is intentionally
//! bounded to executable list heads:
//! - exact 3/4/5/6-bit heads become DomainIdentity;
//! - exact 7-bit heads fail closed: D7 v2 is keyboard text/data, not a callable function;
//! - historical bare 8-bit heads remain opaque W8; only explicitly admitted
//!   Ukrainian D8 I/O names are exact-lifted, with other D8 mechanisms path-pinned;
//! - approved path-pinned readers lift exact D9 words; Ukrainian D9 string heads
//!   additionally require both an explicit projection allowlist and a concrete mechanism;
//! - non-head and quoted data keep the ordinary parser's interpretation.
//!
//! This gives active Core migration a mixed symbol + exact-domain path without
//! teaching the compatibility parser to infer domains from historical bytes.

use crate::syntax::{Exactness, Expr, ExprKind, Span, MAX_STRUCTURE_DEPTH};
use crate::{parse_binary_source_words, DomainIdentity, ErrorKind, LanguageError};
use std::collections::HashSet;
use std::rc::Rc;

/// Parse ordinary mixed Lisp source, then lift only exact-width callable heads
/// into domain identity.
///
/// This is a migration bridge, not a new canonical wire syntax.
pub fn parse_mixed_exact_domain(source: &str) -> Result<Vec<Expr>, LanguageError> {
    parse_mixed_source(source, false)
}

/// Parse a trusted `lib/machine/**` Lisp source file whose outer definition
/// and lambda wrappers still use historical 8-bit syntax, but whose executable
/// bodies contain current exact-width D3-D6 call heads.
///
/// This is deliberately separate from `parse_mixed_exact_domain`: ordinary
/// mixed source keeps legacy W8 forms opaque. Callers must restrict this mode
/// to the approved machine-source loader boundary; it is not a global reader
/// mode and does not reinterpret numbers, quoted data, or W8 heads as D8 laws.
pub fn parse_mixed_exact_domain_machine_source(
    path: &str,
    source: &str,
) -> Result<Vec<Expr>, LanguageError> {
    if !path.starts_with("lib/machine/") || !path.ends_with(".lisp") {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "machine-source exact-domain reader is restricted to lib/machine/**/*.lisp",
            Span::default(),
        ));
    }
    // Only the already-admitted D8 I/O identities are projected here, after
    // the exact D3-D6 machine-source pass. This does not license arbitrary D8
    // or D9 call heads; quoting and binder data remain opaque.
    let parsed = parse_mixed_source(source, true)?
        .into_iter()
        .map(|expr| lift_pinned_d8_io(source, expr, 0))
        .collect::<Result<Vec<_>, _>>()?;

    // Only the admission/encoding wire paths need these four ratified D9
    // string operations. Pin callability to those exact source files; this is
    // not general D9 call-head inference for machine code.
    if matches!(
        path,
        "lib/machine/admission/x86-64.lisp" | "lib/machine/encoding/x86-64.lisp"
    ) {
        parsed
            .into_iter()
            .map(|expr| lift_pinned_machine_wire_d9_strings(source, expr, 0))
            .collect()
    } else {
        Ok(parsed)
    }
}

/// Already-admitted D8 mechanism names and exact words from the owner domain ladder.
/// Shared by ordinary Ukrainian source and path-pinned readers. Neither bare
/// historical W8 bytes nor quoted/bound words obtain callable authority.
fn admitted_d8_uk_bits(spelling: &str) -> Option<&'static str> {
    // Admit only exact ratified words alongside their Ukrainian surfaces.
    // Ordinary source cannot infer width from arbitrary numeric-looking text;
    // quoted payloads remain opaque and do not acquire callable authority.
    match spelling {
        "код-символу" | "11100000" => Some("11100000"),
        "текст-у-символ" | "11101101" => Some("11101101"),
        "символ-у-текст" | "11101110" => Some("11101110"),
        "значення-у-текст" | "11110100" => Some("11110100"),
        "однакові?" | "11110111" => Some("11110111"),
        _ => None,
    }
}

fn lift_pinned_d8_io(source: &str, expression: Expr, depth: u32) -> Result<Expr, LanguageError> {
    if depth > MAX_STRUCTURE_DEPTH {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "pinned D8 mechanism source exceeds structure depth",
            expression.span,
        ));
    }
    let Expr { kind, span } = expression;
    let ExprKind::List(items) = kind else {
        return Ok(Expr { kind, span });
    };
    if items.is_empty() {
        return Ok(Expr {
            kind: ExprKind::List(items),
            span,
        });
    }
    let mut lifted = items.to_vec();
    let head_spelling = source_spelling(source, &lifted[0]);
    if is_legacy_w8_quote_head(source, &lifted[0])
        || is_exact_quote(&lifted[0])
        || head_spelling == Some("'")
    {
        // Quoted knowledge data preserves only already-ratified D4 NOT
        // identity; unknown names remain data and never become callable.
        let mut quoted = items.to_vec();
        for item in quoted.iter_mut().skip(1) {
            *item = lift_quoted_d4_identity_data(source, item.clone(), depth + 1)?;
        }
        return Ok(Expr {
            kind: ExprKind::List(Rc::from(quoted.into_boxed_slice())),
            span,
        });
    }

    if let Some(bits) = head_spelling.and_then(admitted_d8_uk_bits) {
        let word = parse_binary_source_words(bits)?[0].word;
        lifted[0] = Expr {
            kind: ExprKind::DomainIdentity(DomainIdentity::from_source_word(word)),
            span: lifted[0].span,
        };
    } else if matches!(&lifted[0].kind, ExprKind::List(_)) {
        lifted[0] = lift_pinned_d8_io(source, lifted[0].clone(), depth + 1)?;
    }

    let skip_binding_slot = is_legacy_w8_define_head(source, &items[0])
        || is_legacy_w8_lambda_head(source, &items[0])
        || is_legacy_w8_macro_head(source, &items[0])
        || is_exact_d4_binding_head(&items[0]);

    for (index, item) in lifted.iter_mut().enumerate().skip(1) {
        if skip_binding_slot && index == 1 {
            continue;
        }
        *item = lift_pinned_d8_io(source, item.clone(), depth + 1)?;
    }
    Ok(Expr {
        kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
        span,
    })
}

/// Lift only the D9 string operations used by the exact-integer wire
/// recognizer in lib/machine/admission/x86-64.lisp. This narrow exception is
/// source-path pinned; it does not make arbitrary D9 identities callable in
/// other machine files. Quote payloads and binding slots remain opaque.
fn lift_pinned_machine_wire_d9_strings(
    source: &str,
    expression: Expr,
    depth: u32,
) -> Result<Expr, LanguageError> {
    const ADMITTED: [&str; 4] = [
        "110011100", // string-empty?
        "110011101", // string-rest
        "110101010", // string-prefix?
        "110101011", // string-first
    ];
    if depth > MAX_STRUCTURE_DEPTH {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "pinned D9 machine-wire source exceeds structure depth",
            expression.span,
        ));
    }
    let Expr { kind, span } = expression;
    let ExprKind::List(items) = kind else {
        return Ok(Expr { kind, span });
    };
    if items.is_empty() {
        return Ok(Expr {
            kind: ExprKind::List(items),
            span,
        });
    }

    let mut lifted = items.to_vec();
    let spelling = source_spelling(source, &lifted[0]);
    if is_legacy_w8_quote_head(source, &lifted[0])
        || is_exact_quote(&lifted[0])
        || spelling == Some("'")
    {
        // Apply the narrow, ratified D4 data lift on this reader path too.
        // Unknown quoted names remain inert Symbols, never callable heads.
        let mut quoted = items.to_vec();
        for item in quoted.iter_mut().skip(1) {
            *item = lift_quoted_d4_identity_data(source, item.clone(), depth + 1)?;
        }
        return Ok(Expr {
            kind: ExprKind::List(Rc::from(quoted.into_boxed_slice())),
            span,
        });
    }

    if spelling.is_some_and(|head| ADMITTED.contains(&head)) {
        let source_word = spelling.expect("matched exact D9 string head");
        let words = parse_binary_source_words(source_word)?;
        let word = words.first().expect("one static D9 source word").word;
        lifted[0] = Expr {
            kind: ExprKind::DomainIdentity(DomainIdentity::from_source_word(word)),
            span: lifted[0].span,
        };
    } else if matches!(&lifted[0].kind, ExprKind::List(_)) {
        lifted[0] = lift_pinned_machine_wire_d9_strings(source, lifted[0].clone(), depth + 1)?;
    }

    let skip_binding_slot = is_legacy_w8_define_head(source, &items[0])
        || is_legacy_w8_lambda_head(source, &items[0])
        || is_legacy_w8_macro_head(source, &items[0])
        || is_exact_d4_binding_head(&items[0]);

    for (index, item) in lifted.iter_mut().enumerate().skip(1) {
        if skip_binding_slot && index == 1 {
            continue;
        }
        *item = lift_pinned_machine_wire_d9_strings(source, item.clone(), depth + 1)?;
    }
    Ok(Expr {
        kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
        span,
    })
}

fn parse_mixed_pinned_d8_io(source: &str) -> Result<Vec<Expr>, LanguageError> {
    parse_mixed_source(source, true)?
        .into_iter()
        .map(|expr| lift_pinned_d8_io(source, expr, 0))
        .collect()
}

/// Migrate only explicitly pinned sources. W8 syntax containers remain
/// compatible while approved exact D9 mechanisms are lifted from their
/// Ukrainian projection. D9 residency alone never grants callability.
fn lift_pinned_d9_language_calls(
    source: &str,
    expression: Expr,
    depth: u32,
) -> Result<Expr, LanguageError> {
    const UKRAINIAN_D9_MECHANISMS: [&str; 7] = [
        "рядок-додати",
        "рядок-порожній?",
        "рядок-решта",
        "рядок-префікс?",
        "рядок-перший",
        "рядок?",
        "читати-всі",
    ];
    // These Lisp-defined D9 calls are materialized only for pinned reasoning
    // sources. Exact identity does not install a runtime slot; evaluated SENS
    // definitions must still provide the concrete mechanism before dispatch.
    const UKRAINIAN_D9_LISP_CALLS: [&str; 3] = [
        "порадити-світ",
        "світ-повідомити-всі",
        "порада-рішення-у-світ",
    ];
    if depth > MAX_STRUCTURE_DEPTH {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "pinned D9 reasoning source exceeds structure depth",
            expression.span,
        ));
    }
    let Expr { kind, span } = expression;
    let ExprKind::List(items) = kind else {
        return Ok(Expr { kind, span });
    };
    if items.is_empty() {
        return Ok(Expr {
            kind: ExprKind::List(items),
            span,
        });
    }

    let mut lifted = items.to_vec();
    let spelling = source_spelling(source, &lifted[0]);
    if is_legacy_w8_quote_head(source, &lifted[0])
        || is_exact_quote(&lifted[0])
        || spelling == Some("'")
    {
        // Translation sources use the pinned reasoning path, not the D8-I/O
        // loader. Preserve the quote carrier but normalize only ratified D4
        // identities inside its payload; exact unknown names remain inert data.
        let mut quoted = items.to_vec();
        for item in quoted.iter_mut().skip(1) {
            *item = lift_quoted_d4_identity_data(source, item.clone(), depth + 1)?;
        }
        return Ok(Expr {
            kind: ExprKind::List(Rc::from(quoted.into_boxed_slice())),
            span,
        });
    }
    // The Ukrainian quote carrier can arrive as its exact source spelling
    // rather than an already-lifted D3 identity. Lift only its single payload
    // with the same ratified D4-data rule; unknown names remain inert data.
    if spelling == Some("як-є") && lifted.len() == 2 {
        let mut quoted = items.to_vec();
        // Use the enclosing quote's source span, not the payload's lossy
        // Text7-local span. Only exact D4 identity is promoted; unknown data
        // remains inert.
        if let Some(identity) = exact_quoted_d4_identity(source, span) {
            quoted[1] = Expr {
                kind: ExprKind::DomainIdentity(identity),
                span: quoted[1].span,
            };
        } else {
            quoted[1] = lift_quoted_d4_identity_data(source, quoted[1].clone(), depth + 1)?;
        }
        return Ok(Expr {
            kind: ExprKind::List(Rc::from(quoted.into_boxed_slice())),
            span,
        });
    }
    if spelling.is_some_and(|s| s.len() == 9 && s.bytes().all(|b| matches!(b, b'0' | b'1'))) {
        let word = parse_binary_source_words(spelling.expect("D9 spelling"))?[0].word;
        let identity = DomainIdentity::from_source_word(word);
        if identity.width() != 9 {
            return Err(LanguageError::new(
                ErrorKind::Parse,
                "nine-bit reasoning head must be D9",
                lifted[0].span,
            ));
        }
        lifted[0] = Expr {
            kind: ExprKind::DomainIdentity(identity),
            span: lifted[0].span,
        };
    } else if let Some(name) = spelling.filter(|name| {
        UKRAINIAN_D9_MECHANISMS.contains(name) || UKRAINIAN_D9_LISP_CALLS.contains(name)
    }) {
        if let Some(identity) = crate::semantic_registry::d9_binding_identity_for_definition(name)
            .filter(|identity| {
                (UKRAINIAN_D9_MECHANISMS.contains(&name)
                    && crate::eval::canon::has_d9_mechanism(*identity))
                    || (UKRAINIAN_D9_LISP_CALLS.contains(&name)
                        && crate::semantic_registry::is_admitted_exact_definition_target(*identity))
            })
        {
            // Native D9 operations require their concrete native mechanism.
            // The path-pinned Lisp-owned advice function requires an admitted
            // exact DEFINE target; runtime dispatch still requires its slot.
            lifted[0] = Expr {
                kind: ExprKind::DomainIdentity(identity),
                span: lifted[0].span,
            };
        }
    } else if matches!(&lifted[0].kind, ExprKind::List(_)) {
        lifted[0] = lift_pinned_d9_language_calls(source, lifted[0].clone(), depth + 1)?;
    }

    let skip_binding = is_legacy_w8_define_head(source, &items[0])
        || is_legacy_w8_lambda_head(source, &items[0])
        || is_legacy_w8_macro_head(source, &items[0])
        || is_exact_d4_binding_head(&items[0]);
    for (index, item) in lifted.iter_mut().enumerate().skip(1) {
        if skip_binding && index == 1 {
            continue;
        }
        *item = lift_pinned_d9_language_calls(source, item.clone(), depth + 1)?;
    }
    Ok(Expr {
        kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
        span,
    })
}

/// Path-pinned reasoning reader. Materializing a D9 identity here does not make
/// it callable: dispatch still requires a concrete mechanism slot installed by
/// its evaluated Lisp definition.
pub fn parse_mixed_exact_domain_reasoning_source(
    path: &str,
    source: &str,
) -> Result<Vec<Expr>, LanguageError> {
    if !matches!(
        path,
        "lib/world.lisp"
            | "lib/forward.lisp"
            | "lib/knowledge.lisp"
            | "lib/unify.lisp"
            | "lib/reason.lisp"
            | "lib/result-status.lisp"
            | "lib/persistent-map.lisp"
            | "lib/content-store.lisp"
            | "lib/lisp-fs.lisp"
            | "lib/clips-import.lisp"
            | "lib/translation.lisp"
    ) {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "reasoning-source exact-domain reader requires a pinned source path",
            Span::default(),
        ));
    }
    let base = if matches!(
        path,
        "lib/world.lisp"
            | "lib/knowledge.lisp"
            | "lib/persistent-map.lisp"
            | "lib/lisp-fs.lisp"
            | "lib/clips-import.lisp"
    ) {
        parse_mixed_pinned_d8_io(source)?
    } else {
        parse_mixed_source(source, true)?
    };
    base.into_iter()
        .map(|expr| lift_pinned_d9_language_calls(source, expr, 0))
        .collect()
}

/// Parse the curated Guard reference directory as data, not as a source file.
/// The file's outer DEFINE still uses the pinned legacy W8 QUOTE carrier;
/// this path-bound reader preserves that payload wholesale instead of
/// interpreting binary-looking records inside the directory as executable
/// call heads. It deliberately does not lift any D9 names from the data.
pub fn parse_mixed_exact_domain_guard_reference_source(
    path: &str,
    source: &str,
) -> Result<Vec<Expr>, LanguageError> {
    if path != "knowledge/guard-reference.lisp" {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "Guard reference data reader is restricted to knowledge/guard-reference.lisp",
            Span::default(),
        ));
    }
    parse_mixed_pinned_d8_io(source)
}

/// Exact D3/D4 call heads are intentionally present in this single
/// deterministic filesystem regression fixture. The fixture uses the
/// Lisp-derived ЛІХТАР syntax for LET; it must not ask the runtime to
/// guess function identities from numbers in arbitrary user programs.
/// W8 bootstrap wrappers remain compatibility syntax; quoted data is opaque.
pub fn parse_mixed_exact_domain_fs_fixture_source(
    path: &str,
    source: &str,
) -> Result<Vec<Expr>, LanguageError> {
    if path != "tests/fixtures/lisp-fs-conformance.lisp" {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "filesystem fixture exact-width reader requires its pinned fixture path",
            Span::default(),
        ));
    }
    parse_mixed_source(source, true)
}

/// Parse only the language-owned UTF-8 module through the exact-domain reader.
/// D9 heads are materialized only on this pinned path; execution still requires
/// a concrete callable mechanism previously attached to that exact identity.
fn lift_pinned_utf8_d9_strings(
    source: &str,
    expression: Expr,
    depth: u32,
) -> Result<Expr, LanguageError> {
    if depth > MAX_STRUCTURE_DEPTH {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "pinned UTF-8 D9 string path exceeds structure depth",
            expression.span,
        ));
    }
    let Expr { kind, span } = expression;
    let ExprKind::List(items) = kind else {
        return Ok(Expr { kind, span });
    };
    if items.is_empty()
        || is_exact_quote(&items[0])
        || source_spelling(source, &items[0]) == Some("'")
    {
        return Ok(Expr {
            kind: ExprKind::List(items),
            span,
        });
    }
    let mut lifted = items.to_vec();
    if source_spelling(source, &items[0]) == Some("рядок-додати") {
        let word = parse_binary_source_words("110011110")?[0].word;
        lifted[0] = Expr {
            kind: ExprKind::DomainIdentity(DomainIdentity::from_source_word(word)),
            span: items[0].span,
        };
    }
    let skip_binding = is_legacy_w8_define_head(source, &items[0])
        || is_legacy_w8_lambda_head(source, &items[0])
        || is_legacy_w8_macro_head(source, &items[0])
        || is_exact_d4_binding_head(&items[0]);
    for (index, item) in lifted.iter_mut().enumerate().skip(1) {
        if skip_binding && index == 1 {
            continue;
        }
        *item = lift_pinned_utf8_d9_strings(source, item.clone(), depth + 1)?;
    }
    Ok(Expr {
        kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
        span,
    })
}

pub fn parse_mixed_exact_domain_utf8_source(
    path: &str,
    source: &str,
) -> Result<Vec<Expr>, LanguageError> {
    if path != "lib/utf8.lisp" {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "UTF-8 exact-domain reader is restricted to lib/utf8.lisp",
            Span::default(),
        ));
    }
    parse_mixed_source(source, true)?
        .into_iter()
        .map(|expr| lift_pinned_d8_io(source, expr, 0))
        .map(|expr| expr.and_then(|expr| lift_pinned_d9_language_calls(source, expr, 0)))
        .map(|expr| expr.and_then(|expr| lift_pinned_utf8_d9_strings(source, expr, 0)))
        .map(|expr| expr.and_then(|expr| expand_pinned_utf8_let_star(source, expr, 0)))
        .map(|expr| expr.and_then(qualify_pinned_utf8_numbers))
        .collect()
}

/// Expand the Lisp-owned LET/LET* forms used by the pinned UTF-8 module into
/// their established D4 lambda applications. This preserves the existing
/// binding semantics while avoiding runtime macro dispatch on source data.
fn expand_pinned_utf8_let_star(
    source: &str,
    expression: Expr,
    depth: u32,
) -> Result<Expr, LanguageError> {
    if depth > MAX_STRUCTURE_DEPTH {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "pinned UTF-8 source exceeds structure depth",
            expression.span,
        ));
    }
    let Expr { kind, span } = expression;
    let ExprKind::List(items) = kind else {
        return Ok(Expr { kind, span });
    };
    if items.is_empty() {
        return Ok(Expr {
            kind: ExprKind::List(items),
            span,
        });
    }

    if is_exact_quote(&items[0]) || source_spelling(source, &items[0]) == Some("'") {
        return Ok(Expr {
            kind: ExprKind::List(items),
            span,
        });
    }
    if matches!(
        source_spelling(source, &items[0]),
        Some("нехай-послідовно" | "нехай")
    ) {
        if items.len() != 3 {
            return Err(LanguageError::new(
                ErrorKind::Parse,
                "pinned UTF-8 sequential binding expects bindings and one body form",
                span,
            ));
        }
        let ExprKind::List(bindings) = &items[1].kind else {
            return Err(LanguageError::new(
                ErrorKind::Parse,
                "pinned UTF-8 sequential binding requires a proper binding list",
                items[1].span,
            ));
        };
        let lambda = crate::semantic_registry::exact_uk_callable_for_source_head("функція")
            .filter(|identity| identity.width() == 4)
            .ok_or_else(|| {
                LanguageError::new(
                    ErrorKind::Parse,
                    "pinned UTF-8 LET* expansion requires the admitted D4 lambda identity",
                    items[0].span,
                )
            })?;
        let mut body = expand_pinned_utf8_let_star(source, items[2].clone(), depth + 1)?;
        for binding in bindings.iter().rev() {
            let ExprKind::List(parts) = &binding.kind else {
                return Err(LanguageError::new(
                    ErrorKind::Parse,
                    "pinned UTF-8 sequential binding entry must be a two-item list",
                    binding.span,
                ));
            };
            if parts.len() != 2 || !matches!(parts[0].kind, ExprKind::Symbol(_)) {
                return Err(LanguageError::new(
                    ErrorKind::Parse,
                    "pinned UTF-8 sequential binding entry must contain a name and value",
                    binding.span,
                ));
            }
            let name = parts[0].clone();
            let value = expand_pinned_utf8_let_star(source, parts[1].clone(), depth + 1)?;
            let parameters = Expr {
                kind: ExprKind::List(Rc::from(vec![name].into_boxed_slice())),
                span: binding.span,
            };
            let lambda_form = Expr {
                kind: ExprKind::List(Rc::from(
                    vec![
                        Expr {
                            kind: ExprKind::DomainIdentity(lambda),
                            span: items[0].span,
                        },
                        parameters,
                        body,
                    ]
                    .into_boxed_slice(),
                )),
                span,
            };
            body = Expr {
                kind: ExprKind::List(Rc::from(vec![lambda_form, value].into_boxed_slice())),
                span,
            };
        }
        return Ok(body);
    }

    let mut lifted = items.to_vec();
    let skip_binding = is_legacy_w8_define_head(source, &items[0])
        || is_legacy_w8_lambda_head(source, &items[0])
        || is_legacy_w8_macro_head(source, &items[0])
        || is_exact_d4_binding_head(&items[0]);
    for (index, item) in lifted.iter_mut().enumerate().skip(1) {
        if skip_binding && index == 1 {
            continue;
        }
        *item = expand_pinned_utf8_let_star(source, item.clone(), depth + 1)?;
    }
    Ok(Expr {
        kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
        span,
    })
}

/// UTF-8's byte/scalar arithmetic is explicitly admitted on D24+. This
/// conversion is confined to the path-pinned UTF-8 source reader; ordinary
/// readers continue to produce unqualified compatibility numbers. Integer
/// decimal atoms here are the human source projection of exact D24 words.
fn qualify_pinned_utf8_numbers(expression: Expr) -> Result<Expr, LanguageError> {
    let Expr { kind, span } = expression;
    let kind = match kind {
        ExprKind::Number(value, Exactness::Exact)
            if value.is_finite()
                && value.fract() == 0.0
                && (-8_388_608.0..=8_388_607.0).contains(&value) =>
        {
            utf8_d24_integer(value as i64, span)?
        }
        ExprKind::Rational(value) if value.is_integer() => {
            let integer = value
                .as_precise_i64()
                .filter(|n| (-8_388_608..=8_388_607).contains(n))
                .ok_or_else(|| utf8_numeric_error(span))?;
            utf8_d24_integer(integer, span)?
        }
        ExprKind::Number(_, _) | ExprKind::Rational(_) => {
            return Err(utf8_numeric_error(span));
        }
        ExprKind::List(items) => ExprKind::List(Rc::from(
            items
                .iter()
                .cloned()
                .map(qualify_pinned_utf8_numbers)
                .collect::<Result<Vec<_>, _>>()?
                .into_boxed_slice(),
        )),
        ExprKind::Pair(head, tail) => ExprKind::Pair(
            Rc::new(qualify_pinned_utf8_numbers((*head).clone())?),
            Rc::new(qualify_pinned_utf8_numbers((*tail).clone())?),
        ),
        other => other,
    };
    Ok(Expr { kind, span })
}

fn utf8_d24_integer(value: i64, span: Span) -> Result<ExprKind, LanguageError> {
    let encoded = (value as u64) & 0x00ff_ffff;
    let bits = (0..24)
        .rev()
        .map(|shift| ((encoded >> shift) & 1) as u8)
        .collect::<Vec<_>>();
    let number = crate::BinaryNumber::from_numeric_domain_bits(24, &bits)
        .ok_or_else(|| utf8_numeric_error(span))?;
    Ok(ExprKind::BinaryNumber(number))
}

fn utf8_numeric_error(span: Span) -> LanguageError {
    LanguageError::new(
        ErrorKind::Parse,
        "pinned UTF-8 source requires exact integer values representable in signed D24",
        span,
    )
}

/// Parse only the language-owned filesystem text adapter. Like process/TCP,
/// this is a path-bound migration bridge, not general numeric-width inference.
pub fn parse_mixed_exact_domain_fs_source(
    path: &str,
    source: &str,
) -> Result<Vec<Expr>, LanguageError> {
    if path != "lib/fs.lisp" {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "filesystem exact-domain reader is restricted to lib/fs.lisp",
            Span::default(),
        ));
    }
    parse_mixed_source(source, true)?
        .into_iter()
        .map(|expr| lift_pinned_d9_language_calls(source, expr, 0))
        .collect()
}

/// Parse the process/TCP Lisp-owned adapters with exact current-domain call heads.
/// This exception is path-bound to these two source files; ordinary source must
/// never infer semantic width from short numeric-looking literals. QUOTE keeps
/// its payload opaque, and the approved paths do not alter language authority.
pub fn parse_mixed_exact_domain_process_tcp_source(
    path: &str,
    source: &str,
) -> Result<Vec<Expr>, LanguageError> {
    if !matches!(path, "lib/process.lisp" | "lib/tcp.lisp") {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "process/TCP exact-domain reader is restricted to lib/process.lisp or lib/tcp.lisp",
            Span::default(),
        ));
    }
    parse_mixed_source(source, true)
}

/// Parse only the language-owned time module with exact-width D3 call heads.
/// Its W8 DEFINE/LAMBDA wrappers remain bootstrap syntax; no general source
/// inference or W8-to-D8 promotion is authorized.
pub fn parse_mixed_exact_domain_time_source(
    path: &str,
    source: &str,
) -> Result<Vec<Expr>, LanguageError> {
    if path != "lib/time.lisp" {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "time-source exact-domain reader is restricted to lib/time.lisp",
            Span::default(),
        ));
    }
    parse_mixed_source(source, true)
}

/// Parse the one owner-approved Core4 source file using the mixed exact-width
/// reader. Core4's historical W8 DEFINE/LAMBDA/COND wrappers remain compatible
/// syntax, but executable D3-D6 heads inside their bodies are lifted to typed
/// DomainIdentity nodes before the FASL snapshot is generated.
///
/// This mode is deliberately path-bound to `lib/core4.lisp`. Ordinary Lisp
/// parsing and the public mixed-source bridge do not change; W8 QUOTE remains
/// opaque and numeric arguments remain Number values.
pub fn parse_mixed_exact_domain_core_source(
    path: &str,
    source: &str,
) -> Result<Vec<Expr>, LanguageError> {
    if path != "lib/core4.lisp" {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "Core4 exact-domain reader is restricted to lib/core4.lisp",
            Span::default(),
        ));
    }

    // Core4 is owner-pinned semantic source. Materialize only admitted D8
    // direct mechanisms and exact D9 residents here; ordinary source parsing
    // never gains width inference from this migration bridge.
    let parsed = parse_mixed_source(source, true)?
        .into_iter()
        .map(|expr| lift_pinned_d8_io(source, expr, 0))
        .collect::<Result<Vec<_>, _>>()?;
    // Цитовані українські імена залишаються даними: побітовий
    // адаптер макросів уже фізично вилучено з runtime.
    parsed
        .into_iter()
        .map(|expr| lift_pinned_d9_language_calls(source, expr, 0))
        .collect()
}

fn parse_mixed_source(
    source: &str,
    descend_legacy_machine_wrappers: bool,
) -> Result<Vec<Expr>, LanguageError> {
    let parsed = crate::parser::parse(source)?;
    // Project ordinary Ukrainian decimal leaves before callable heads become
    // DomainIdentity nodes, so D5 arithmetic trees can choose one exact width.
    // The projector preserves quote payloads and already typed domain data.
    let expressions =
        crate::source_projection::project_ukr_decimal_integer_literals(&parsed, source)?;
    // Call-head source spellings are NOT authoritative domain identities
    // when this very source declares the spelling as a DEFINE or LAMBDA
    // binding. Protect all such names across this source until the owner
    // lexical-slot resolver can prove their exact scopes. Conservatively
    // declining a projection is safer than silently calling a builtin.
    let mut bound_names = HashSet::new();
    for expression in &expressions {
        collect_source_bindings(
            source,
            expression,
            &mut bound_names,
            descend_legacy_machine_wrappers,
        );
    }
    let lifted = expressions
        .into_iter()
        .map(|expression| {
            lift_expression(
                source,
                expression,
                0,
                &bound_names,
                descend_legacy_machine_wrappers,
            )
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok(lifted)
}

fn binding_form(source: &str, head: &Expr) -> Option<u16> {
    let spelling = source_spelling(source, head)?;
    match spelling {
        "0010" => return Some(2),
        "0011" => return Some(3),
        _ => {}
    }
    let identity = crate::semantic_registry::exact_uk_callable_for_source_head(spelling)?;
    (identity.width() == 4)
        .then_some(identity.packed_bits())
        .filter(|bits| matches!(bits, 2 | 3))
}

fn is_source_quote(source: &str, head: &Expr) -> bool {
    // Apostrophe is lowered to exact D3:001 by the ordinary parser. Treat
    // quoted bindings as data while collecting names, not as live DEFINEs.
    if is_exact_quote(head) || source_spelling(source, head) == Some("'") {
        return true;
    }
    if source_spelling(source, head) == Some("001") {
        return true;
    }
    source_spelling(source, head)
        .and_then(crate::semantic_registry::exact_uk_callable_for_source_head)
        .is_some_and(|id| id.width() == 3 && id.packed_bits() == 1)
}

/// Source-language binder inventory, not an inference of runtime identity.
/// Ignore quoted records and ambiguous old exact-eight forms entirely.
fn collect_source_bindings(
    source: &str,
    expression: &Expr,
    names: &mut HashSet<String>,
    descend_legacy_machine_wrappers: bool,
) {
    let ExprKind::List(items) = &expression.kind else {
        return;
    };
    let Some(head) = items.first() else { return };
    if is_source_quote(source, head)
        || (is_opaque_legacy_w8_head(source, head)
            && (!descend_legacy_machine_wrappers || is_legacy_w8_quote_head(source, head)))
    {
        return;
    }
    if descend_legacy_machine_wrappers && is_legacy_w8_define_head(source, head) {
        if let Some(target) = items.get(1) {
            if matches!(&target.kind, ExprKind::Symbol(_)) {
                if let Some(name) = source_spelling(source, target) {
                    names.insert(name.to_owned());
                }
            }
        }
        for child in items.iter().skip(2) {
            collect_source_bindings(source, child, names, descend_legacy_machine_wrappers);
        }
        return;
    }
    if descend_legacy_machine_wrappers
        && (is_legacy_w8_lambda_head(source, head) || is_legacy_w8_macro_head(source, head))
    {
        // W8 lambda parameter lists are binding data, not call-head positions.
        for child in items.iter().skip(2) {
            collect_source_bindings(source, child, names, descend_legacy_machine_wrappers);
        }
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
        collect_source_bindings(source, head, names, descend_legacy_machine_wrappers);
    }
    for (index, child) in items.iter().enumerate().skip(1) {
        if binding.is_some() && index == 1 {
            continue;
        }
        collect_source_bindings(source, child, names, descend_legacy_machine_wrappers);
    }
}

fn lift_expression(
    source: &str,
    expression: Expr,
    depth: u32,
    bound_names: &HashSet<String>,
    descend_legacy_machine_wrappers: bool,
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

            // In the explicitly approved machine-source mode, keep the
            // historical W8 DEFINE/LAMBDA wrappers as syntax containers, but
            // descend only into their executable bodies. Their target names
            // and parameter lists remain data and are never width-lifted.
            // W8 QUOTE remains opaque in every mode so quoted (100 ...) data
            // is never projected to a callable D3 identity.
            if descend_legacy_machine_wrappers && is_legacy_w8_quote_head(source, &lifted[0]) {
                return Ok(Expr {
                    kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
                    span,
                });
            }
            if descend_legacy_machine_wrappers && is_legacy_w8_define_head(source, &lifted[0]) {
                for item in lifted.iter_mut().skip(2) {
                    *item = lift_expression(
                        source,
                        item.clone(),
                        depth + 1,
                        bound_names,
                        descend_legacy_machine_wrappers,
                    )?;
                }
                return Ok(Expr {
                    kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
                    span,
                });
            }
            if descend_legacy_machine_wrappers
                && (is_legacy_w8_lambda_head(source, &lifted[0])
                    || is_legacy_w8_macro_head(source, &lifted[0]))
            {
                for item in lifted.iter_mut().skip(2) {
                    *item = lift_expression(
                        source,
                        item.clone(),
                        depth + 1,
                        bound_names,
                        descend_legacy_machine_wrappers,
                    )?;
                }
                return Ok(Expr {
                    kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
                    span,
                });
            }
            if descend_legacy_machine_wrappers && is_legacy_w8_cond_head(source, &lifted[0]) {
                // W8 COND's clauses are DATA-shaped lists whose first element
                // is itself an executable test form. Treat that slot as code,
                // just like current D3 COND clauses, while preserving W8 COND
                // as the compatibility control form and preserving quote data.
                for clause in lifted.iter_mut().skip(1) {
                    *clause = lift_cond_clause(
                        source,
                        clause.clone(),
                        depth + 1,
                        bound_names,
                        descend_legacy_machine_wrappers,
                    )?;
                }
                return Ok(Expr {
                    kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
                    span,
                });
            }

            // A computed executable head is itself code, including ordinary
            // immediately-applied exact D4 LAMBDA ((0010 ...) argument).
            // Recursively lift that executable expression without turning
            // historical W8 wrappers into current D8: lift_expression keeps
            // such wrappers opaque outside the explicitly pinned machine mode.
            // Exact D3 QUOTE still protects its entire payload as data.
            if matches!(&lifted[0].kind, ExprKind::List(_)) {
                lifted[0] = lift_expression(
                    source,
                    lifted[0].clone(),
                    depth + 1,
                    bound_names,
                    descend_legacy_machine_wrappers,
                )?;
            } else {
                lifted[0] = lift_head(source, lifted[0].clone(), bound_names)?;
            }

            // Legacy W8 heads remain opaque in ordinary mixed source. The
            // machine-source mode descends only through non-QUOTE wrappers
            // under its explicit caller contract; it never infers current D8.
            if is_opaque_legacy_w8_head(source, &lifted[0]) && !descend_legacy_machine_wrappers {
                return Ok(Expr {
                    kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
                    span,
                });
            }

            // Exact D3 QUOTE keeps its argument as reader data. Apostrophe
            // sugar also stays data-owned without naming legacy byte identity.
            let quote_data = is_source_quote(source, &lifted[0])
                || is_exact_quote(&lifted[0])
                || source_spelling(source, &lifted[0]) == Some("'");

            if quote_data {
                // A canonical D4 negation head can occur as object-language
                // data inside a knowledge clause. Preserve its exact identity
                // through QUOTE; ordinary predicate names and macro templates
                // remain data and never acquire callability from their spelling.
                for item in lifted.iter_mut().skip(1) {
                    *item = lift_quoted_d4_identity_data(source, item.clone(), depth + 1)?;
                }
            } else {
                if is_exact_cond(&lifted[0]) {
                    for clause in lifted.iter_mut().skip(1) {
                        *clause = lift_cond_clause(
                            source,
                            clause.clone(),
                            depth + 1,
                            bound_names,
                            descend_legacy_machine_wrappers,
                        )?;
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
                        *item = lift_expression(
                            source,
                            item.clone(),
                            depth + 1,
                            bound_names,
                            descend_legacy_machine_wrappers,
                        )?;
                    }
                }
            }

            Ok(Expr {
                kind: ExprKind::List(Rc::from(lifted.into_boxed_slice())),
                span,
            })
        }
        ExprKind::Symbol(name) => {
            if let Some(identity) = crate::semantic_registry::d1_value_for_uk_surface(&name) {
                Ok(Expr {
                    kind: ExprKind::DomainIdentity(identity),
                    span,
                })
            } else {
                Ok(Expr {
                    kind: ExprKind::Symbol(name),
                    span,
                })
            }
        }
        other => Ok(Expr { kind: other, span }),
    }
}

// Recover an exact payload from the outer quote form. The mixed reader may
// attach a lossy Text7-local span to the payload node (e.g. D4:0100 rendered
// as "п-р"), so domain preservation must use the enclosing source bytes.
fn exact_quoted_d4_identity(source: &str, quote_span: Span) -> Option<DomainIdentity> {
    let form = source.get(quote_span.start..quote_span.end)?.trim();
    let payload = form
        .strip_prefix("(як-є")?
        .strip_suffix(')')?
        .trim();

    if payload == "хибне?" {
        return crate::semantic_registry::exact_uk_callable_for_source_head("хибне?")
            .filter(|identity| identity.width() == 4 && identity.packed_bits() == 0b0100);
    }
    if payload.len() != 4 || !payload.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
        return None;
    }
    let word = parse_binary_source_words(payload).ok()?.first()?.word;
    let identity = DomainIdentity::from_source_word(word);
    (identity.width() == 4).then_some(identity)
}

fn lift_quoted_d4_identity_data(
    source: &str,
    expression: Expr,
    depth: u32,
) -> Result<Expr, LanguageError> {
    if depth > MAX_STRUCTURE_DEPTH {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "quoted domain data exceeds structure depth",
            expression.span,
        ));
    }
    // A quoted, exact-width D4 coordinate is still its D4 identity.
    // Only this ratified NOT datum is lifted here; other bit widths and
    // coordinates remain data, so the quote reader cannot create callability.
    if source_spelling(source, &expression) == Some("0100") {
        let word = parse_binary_source_words("0100")?[0].word;
        let identity = DomainIdentity::from_source_word(word);
        if identity.width() == 4 && identity.packed_bits() == 0b0100 {
            return Ok(Expr {
                kind: ExprKind::DomainIdentity(identity),
                span: expression.span,
            });
        }
    }
    // Mixed parsing may materialize an unadmitted source spelling as a Text7
    // datum. Recover only the exact spelling owned by this source span, then
    // project the already-ratified D4 identity; never infer from rendered D7.
    if source_spelling(source, &expression) == Some("хибне?") {
        if let Some(identity) =
            crate::semantic_registry::exact_uk_callable_for_source_head("хибне?")
                .filter(|identity| identity.width() == 4 && identity.packed_bits() == 0b0100)
        {
            return Ok(Expr {
                kind: ExprKind::DomainIdentity(identity),
                span: expression.span,
            });
        }
    }
    let Expr { kind, span } = expression;
    match kind {
        ExprKind::List(items) => {
            let mut mapped = items
                .iter()
                .cloned()
                .map(|item| lift_quoted_d4_identity_data(source, item, depth + 1))
                .collect::<Result<Vec<_>, _>>()?;

            // Promote only the head of a quoted executable form. A symbol
            // with the same spelling in an argument position remains data.
            if let Some(head) = mapped.first_mut() {
                if let ExprKind::Symbol(name) = &head.kind {
                    let expected_bits = match name.as_ref() {
                        "хибне?" => Some(0b0100),
                        "визначити" => Some(0b0011),
                        // Macro expansion may emit executable D4 append from quoted data.
                        "приєднати" => Some(0b1111),
                        _ => None,
                    };
                    if let Some(expected_bits) = expected_bits {
                        let identity = crate::semantic_registry::exact_uk_callable_for_source_head(name)
                            .filter(|identity| identity.width() == 4 && identity.packed_bits() == expected_bits);
                        if let Some(identity) = identity {
                            head.kind = ExprKind::DomainIdentity(identity);
                        }
                    }
                }
            }

            Ok(Expr {
                kind: ExprKind::List(Rc::from(mapped.into_boxed_slice())),
                span,
            })
        }
        // The bare quoted D4 NOT identity is an object-language predicate
        // value used as a clause head by the knowledge reasoner. Preserve its
        // exact ratified identity as data; it is not dispatched until a later
        // SENS reasoning step consumes the clause. Syntax forms such as DEFINE
        // deliberately remain ordinary quoted data (see macro-code law).
        ExprKind::Symbol(name) if name.as_ref() == "хибне?" => {
            let identity = crate::semantic_registry::exact_uk_callable_for_source_head(&name)
                .filter(|identity| identity.width() == 4 && identity.packed_bits() == 0b0100);
            if let Some(identity) = identity {
                Ok(Expr {
                    kind: ExprKind::DomainIdentity(identity),
                    span,
                })
            } else {
                Ok(Expr {
                    kind: ExprKind::Symbol(name),
                    span,
                })
            }
        }
        // Other bare symbols in quote data remain data; spelling alone does
        // not authorize arbitrary callable identities.
        other => Ok(Expr { kind: other, span }),
    }
}

fn lift_head(
    source: &str,
    head: Expr,
    bound_names: &HashSet<String>,
) -> Result<Expr, LanguageError> {
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
            // Ordinary mixed source admits D3–D6 callable heads. D8 is a
            // narrower, explicit Ukrainian allowlist; D9/D10 stay path-pinned.
            let admitted_width = (3..=6).contains(&identity.width())
                || (identity.width() == 8 && admitted_d8_uk_bits(spelling).is_some());
            if admitted_width {
                return Ok(Expr {
                    kind: ExprKind::DomainIdentity(identity),
                    span: head.span,
                });
            }
        }
        // D8 I/O was already admitted by the same reader in pinned modules.
        // Apply its exact Ukrainian address in ordinary source as well:
        // binder names above win; quoted data never reaches lift_head.
        if let Some(bits) = admitted_d8_uk_bits(spelling) {
            let word = parse_binary_source_words(bits)?[0].word;
            return Ok(Expr {
                kind: ExprKind::DomainIdentity(DomainIdentity::from_source_word(word)),
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
    descend_legacy_machine_wrappers: bool,
) -> Result<Expr, LanguageError> {
    let Expr { kind, span } = clause;
    match kind {
        ExprKind::List(items) => {
            let mut lifted = items.to_vec();
            for item in &mut lifted {
                *item = lift_expression(
                    source,
                    item.clone(),
                    depth + 1,
                    bound_names,
                    descend_legacy_machine_wrappers,
                )?;
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

fn is_legacy_w8_quote_head(source: &str, head: &Expr) -> bool {
    source_spelling(source, head) == Some("00000001")
}

fn is_legacy_w8_define_head(source: &str, head: &Expr) -> bool {
    source_spelling(source, head) == Some("00001001")
}

fn is_legacy_w8_lambda_head(source: &str, head: &Expr) -> bool {
    source_spelling(source, head) == Some("00001000")
}

fn is_legacy_w8_macro_head(source: &str, head: &Expr) -> bool {
    source_spelling(source, head) == Some("00001010")
}

fn is_legacy_w8_cond_head(source: &str, head: &Expr) -> bool {
    source_spelling(source, head) == Some("00000111")
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
    fn quoted_macro_define_keeps_exact_d4_identity() {
        let expression = only(
            parse_mixed_exact_domain("(як-є (визначити журнал-знань значення))")
                .expect("quoted macro-generated DEFINE must preserve its exact D4 identity"),
        );
        let ExprKind::List(quote) = expression.kind else {
            panic!("QUOTE");
        };
        let ExprKind::List(data) = &quote[1].kind else {
            panic!("quoted macro data");
        };
        assert!(matches!(
            &data[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 4 && identity.packed_bits() == 0b0011
        ));
        assert!(matches!(
            &data[1].kind,
            ExprKind::Symbol(name) if name.as_ref() == "журнал-знань"
        ));
    }

    #[test]
    fn quoted_macro_define_argument_remains_plain_data() {
        let expression = only(
            parse_mixed_exact_domain("(як-є (список визначити))")
                .expect("quoted list data must parse"),
        );
        let ExprKind::List(quote) = expression.kind else {
            panic!("QUOTE");
        };
        let ExprKind::List(data) = &quote[1].kind else {
            panic!("quoted data");
        };
        assert!(matches!(
            &data[1].kind,
            ExprKind::Symbol(name) if name.as_ref() == "визначити"
        ));
    }

    #[test]
    fn translation_reader_preserves_quoted_d4_negation_and_unknown_data() {
        let quoted = only(
            parse_mixed_exact_domain_reasoning_source("lib/translation.lisp", "(як-є хибне?)")
                .expect("translation source quote"),
        );
        let ExprKind::List(form) = quoted.kind else {
            panic!("QUOTE form");
        };
        assert!(matches!(
            &form[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 3 && identity.packed_bits() == 0b001
        ));
        assert!(matches!(
            &form[1].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 4 && identity.packed_bits() == 0b0100
        ));

        // The same ratified D4 identity may arrive as its exact four-bit word.
        // Do not trust the child's lossy Text7 span ("п-р"); recover it from
        // the full quote expression and preserve exact domain identity.
        let binary = only(
            parse_mixed_exact_domain_reasoning_source("lib/translation.lisp", "(як-є 0100)")
                .expect("explicit D4 word inside quote"),
        );
        let ExprKind::List(binary_form) = binary.kind else {
            panic!("binary QUOTE form");
        };
        assert!(matches!(
            &binary_form[1].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 4 && identity.packed_bits() == 0b0100
        ));

        let unknown = only(
            parse_mixed_exact_domain_reasoning_source(
                "lib/translation.lisp",
                "(як-є непогоджена-функція)",
            )
            .expect("translation source quote with ordinary data"),
        );
        let ExprKind::List(form) = unknown.kind else {
            panic!("QUOTE form");
        };
        assert!(matches!(
            &form[1].kind,
            ExprKind::Symbol(name) if name.as_ref() == "непогоджена-функція"
        ));
    }

    #[test]
    fn quoted_standalone_knowledge_negation_keeps_exact_d4_identity() {
        let expression = only(
            parse_mixed_exact_domain("(як-є хибне?)")
                .expect("quoted D4 NOT symbol used as knowledge-clause head"),
        );
        let ExprKind::List(quote) = expression.kind else {
            panic!("QUOTE");
        };
        assert!(matches!(
            &quote[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 3 && identity.packed_bits() == 0b001
        ));
        assert!(matches!(
            &quote[1].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 4 && identity.packed_bits() == 0b0100
        ));
    }

    #[test]
    fn translation_reader_preserves_nested_quoted_d4_negation_and_unknown_data() {
        let nested = only(
            parse_mixed_exact_domain_reasoning_source(
                "lib/translation.lisp",
                "(список (як-є хибне?) (як-є непогоджена-функція))",
            )
            .expect("translation reader keeps nested quote data"),
        );
        let ExprKind::List(items) = nested.kind else {
            panic!("outer list");
        };
        let ExprKind::List(negation) = &items[1].kind else {
            panic!("quoted D4 negation");
        };
        assert!(matches!(
            &negation[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 3 && identity.packed_bits() == 0b001
        ));
        assert!(matches!(
            &negation[1].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 4 && identity.packed_bits() == 0b0100
        ));

        let ExprKind::List(unknown) = &items[2].kind else {
            panic!("quoted unknown data");
        };
        assert!(matches!(
            &unknown[1].kind,
            ExprKind::Symbol(name) if name.as_ref() == "непогоджена-функція"
        ));
    }

    #[test]
    fn pinned_reasoning_reader_preserves_quoted_d4_negation_and_unknown_data() {
        let quoted = only(
            parse_mixed_exact_domain_reasoning_source("lib/world.lisp", "(як-є хибне?)")
                .expect("pinned reasoning quote"),
        );
        let ExprKind::List(form) = quoted.kind else {
            panic!("QUOTE form");
        };
        assert!(matches!(
            &form[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 3 && identity.packed_bits() == 0b001
        ));
        assert!(matches!(
            &form[1].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 4 && identity.packed_bits() == 0b0100
        ));

        let unknown = only(
            parse_mixed_exact_domain_reasoning_source(
                "lib/world.lisp",
                "(як-є непогоджена-функція)",
            )
            .expect("pinned reasoning quote with ordinary data"),
        );
        let ExprKind::List(form) = unknown.kind else {
            panic!("QUOTE form");
        };
        assert!(matches!(
            &form[1].kind,
            ExprKind::Symbol(name) if name.as_ref() == "непогоджена-функція"
        ));
    }

    #[test]
    fn quoted_knowledge_negation_keeps_exact_d4_identity() {
        let expression = only(
            parse_mixed_exact_domain("(як-є (хибне? (human socrates)))")
                .expect("quoted object-language negation must preserve its ratified D4 word"),
        );
        let ExprKind::List(quote) = expression.kind else {
            panic!("QUOTE");
        };
        let ExprKind::List(clause) = &quote[1].kind else {
            panic!("quoted clause");
        };
        assert!(matches!(
            &clause[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 4 && identity.packed_bits() == 0b0100
        ));
        let ExprKind::List(goal) = &clause[1].kind else {
            panic!("goal data");
        };
        assert!(matches!(&goal[0].kind, ExprKind::Symbol(name) if name.as_ref() == "human"));
        assert!(matches!(&goal[1].kind, ExprKind::Symbol(name) if name.as_ref() == "socrates"));
    }

    #[test]
    fn quoted_macro_append_keeps_exact_d4_identity_and_arguments_as_data() {
        let expression = only(
            parse_mixed_exact_domain("(як-є (приєднати журнал-знань події))")
                .expect("quoted macro-generated append must parse"),
        );
        let ExprKind::List(quote) = expression.kind else {
            panic!("QUOTE");
        };
        let ExprKind::List(data) = &quote[1].kind else {
            panic!("quoted macro data");
        };
        assert!(matches!(
            &data[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 4 && identity.packed_bits() == 0b1111
        ));
        assert!(matches!(
            &data[1].kind,
            ExprKind::Symbol(name) if name.as_ref() == "журнал-знань"
        ));
        assert!(matches!(
            &data[2].kind,
            ExprKind::Symbol(name) if name.as_ref() == "події"
        ));
    }

    #[test]
    fn pinned_reader_lifts_only_the_ratified_lisp_owned_d9_advice_call() {
        let source = "(порадити-світ світ corpus клаузи)";
        let pinned = only(
            parse_mixed_exact_domain_reasoning_source("lib/world.lisp", source)
                .expect("the World reader admits its ratified D9 function"),
        );
        let ExprKind::List(pinned_parts) = pinned.kind else {
            panic!("pinned advice call");
        };
        assert!(matches!(
            &pinned_parts[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 9 && identity.packed_bits() == 0b111110111
        ));

        let ordinary = only(
            parse_mixed_exact_domain(source).expect("ordinary source remains parseable"),
        );
        let ExprKind::List(ordinary_parts) = ordinary.kind else {
            panic!("ordinary advice call");
        };
        assert!(
            !matches!(&ordinary_parts[0].kind, ExprKind::DomainIdentity(identity) if identity.width() == 9),
            "ordinary source must not infer a D9 call from its Ukrainian spelling"
        );
    }

    #[test]
    fn mixed_human_projection_reads_tak_and_ni_as_d1_values() {
        for (surface, bits) in [("ні", 0), ("так", 1)] {
            let parsed = only(
                parse_mixed_exact_domain(surface)
                    .expect("людська проєкція D1 має розбиратися як значення"),
            );
            assert!(
                matches!(
                    parsed.kind,
                    ExprKind::DomainIdentity(identity)
                        if identity.width() == 1 && identity.packed_bits() == bits
                ),
                "{surface} має лишитися значенням D1:{bits}"
            );
        }
    }

    #[test]
    fn ordinary_ukrainian_source_lifts_only_admitted_d8_io_heads() {
        for (surface, bits) in [
            ("код-символу", 0b11100000),
            ("текст-у-символ", 0b11101101),
            ("символ-у-текст", 0b11101110),
            ("значення-у-текст", 0b11110100),
        ] {
            let input = format!("({surface} (як-є а))");
            let expression = only(
                parse_mixed_exact_domain(&input)
                    .expect("ратифікований D8 I/O має мати єдину exact адресу"),
            );
            let ExprKind::List(parts) = expression.kind else {
                panic!("виклична форма");
            };
            assert!(
                matches!(
                    &parts[0].kind,
                    ExprKind::DomainIdentity(identity)
                        if identity.width() == 8 && identity.packed_bits() == bits
                ),
                "{surface}: людська назва не стає D7-зв'язуванням"
            );
        }

        // Quote payload is data; user DEFINE shadows even an admitted surface.
        let quoted = only(
            parse_mixed_exact_domain("(як-є (текст-у-символ а))")
                .expect("цитування не проектує викличні голови"),
        );
        let ExprKind::List(outer) = quoted.kind else {
            panic!("quote");
        };
        let ExprKind::List(inner) = &outer[1].kind else {
            panic!("quoted list");
        };
        assert!(matches!(&inner[0].kind, ExprKind::Symbol(name)
            if name.as_ref() == "текст-у-символ"));

        let input = "(визначити текст-у-символ (функція (а) а)) (текст-у-символ (як-є а))";
        let expressions =
            parse_mixed_exact_domain(input).expect("власна функція перекриває зовнішній виклик");
        let ExprKind::List(call) = &expressions[1].kind else {
            panic!("call");
        };
        assert!(matches!(&call[0].kind, ExprKind::Symbol(name)
            if name.as_ref() == "текст-у-символ"));

        let unadmitted = only(
            parse_mixed_exact_domain("(символ-за-кодом 65)")
                .expect("не допущений до цього читача D8 не змінюється від читання"),
        );
        let ExprKind::List(parts) = unadmitted.kind else {
            panic!("call");
        };
        assert!(matches!(&parts[0].kind, ExprKind::Symbol(name)
            if name.as_ref() == "символ-за-кодом"));
    }

    #[test]
    fn d1_values_are_not_shadowed_by_source_binding_inventory() {
        let source = "(визначити тестове-імя (функція (так) так)) так";
        let expressions = parse_mixed_exact_domain(source)
            .expect("D1 source values remain exact even beside a same-spelled binder");
        assert!(matches!(
            expressions.last().map(|expression| &expression.kind),
            Some(ExprKind::DomainIdentity(identity))
                if identity.width() == 1 && identity.packed_bits() == 1
        ));
    }

    #[test]
    fn core4_pinned_d9_ukrainian_mechanism_head_lifts_inside_its_wrapper() {
        let source = "(визначити рядок-порожній? (функція (текст) (рядок-порожній? текст)))";
        let expressions = parse_mixed_exact_domain_core_source("lib/core4.lisp", source)
            .expect("Core4's explicit D9 mechanism projection is admitted");
        let ExprKind::List(definition) = &expressions[0].kind else {
            panic!("definition");
        };
        assert!(
            matches!(&definition[1].kind, ExprKind::Symbol(name) if name.as_ref() == "рядок-порожній?"),
            "the definition target remains a surface binding"
        );
        let ExprKind::List(lambda) = &definition[2].kind else {
            panic!("lambda");
        };
        let ExprKind::List(body_call) = &lambda[2].kind else {
            panic!("body call");
        };
        assert!(
            matches!(
                &body_call[0].kind,
                ExprKind::DomainIdentity(identity)
                    if identity.width() == 9 && identity.packed_bits() == 0b110011100
            ),
            "the explicitly admitted D9 mechanism head must bypass its same-spelled wrapper"
        );

        for (head, source) in [
            ("string-empty?", "(string-empty? text)"),
            ("рядок-довжина", "(рядок-довжина text)"),
        ] {
            let parsed = only(
                parse_mixed_exact_domain_core_source("lib/core4.lisp", source)
                    .expect("non-admitted heads remain ordinary source"),
            );
            let ExprKind::List(call) = parsed.kind else {
                panic!("call");
            };
            assert!(
                matches!(&call[0].kind, ExprKind::Symbol(name) if name.as_ref() == head),
                "{head} must not be promoted by D9 residency or an English projection"
            );
        }
    }

    #[test]
    fn core4_pinned_ukrainian_d8_string_mechanism_heads_lift_exactly() {
        for (surface, bits) in [
            ("текст-у-символ", 0b11101101),
            ("символ-у-текст", 0b11101110),
            ("значення-у-текст", 0b11110100),
        ] {
            let source = format!("(визначити {surface} (функція (текст) ({surface} текст)))");
            let expressions = parse_mixed_exact_domain_core_source("lib/core4.lisp", &source)
                .expect("Core4 may use already-admitted D8 string mechanisms");
            let ExprKind::List(definition) = &expressions[0].kind else {
                panic!("definition");
            };
            assert!(
                matches!(&definition[1].kind, ExprKind::Symbol(name) if name.as_ref() == surface),
                "the definition target remains a surface binding"
            );
            let ExprKind::List(lambda) = &definition[2].kind else {
                panic!("lambda");
            };
            let ExprKind::List(body_call) = &lambda[2].kind else {
                panic!("body call");
            };
            assert!(
                matches!(
                    &body_call[0].kind,
                    ExprKind::DomainIdentity(identity)
                        if identity.width() == 8 && identity.packed_bits() == bits
                ),
                "{surface} must select only its exact D8 identity"
            );
        }
    }

    #[test]
    fn core4_pinned_source_lifts_ratified_d8_structural_equality() {
        let expression = only(
            parse_mixed_exact_domain_core_source(
                "lib/core4.lisp",
                "(однакові? (як-є (а)) (як-є (а)))",
            )
            .expect("Core4 structural equality is an explicitly admitted D8 mechanism"),
        );
        let ExprKind::List(call) = expression.kind else {
            panic!("structural equality call");
        };
        assert!(
            matches!(
                &call[0].kind,
                ExprKind::DomainIdentity(identity)
                    if identity.width() == 8 && identity.packed_bits() == 0b11110111
            ),
            "Core4 must preserve the exact D8 EQUAL identity"
        );
    }

    #[test]
    fn ordinary_ukrainian_source_lifts_ratified_d8_structural_equality() {
        let expression = only(
            parse_mixed_exact_domain("(однакові? (як-є (а)) (як-є (а)))")
                .expect("ratified D8 structural equality source"),
        );
        let ExprKind::List(call) = expression.kind else {
            panic!("structural equality call");
        };
        assert!(
            matches!(
                &call[0].kind,
                ExprKind::DomainIdentity(identity)
                    if identity.width() == 8 && identity.packed_bits() == 0b11110111
            ),
            "ordinary source must preserve the exact D8 EQUAL identity"
        );
    }

    #[test]
    fn clips_source_lifts_only_admitted_d8_symbol_to_string_and_never_quoted_payload() {
        let literal = "(11101110 (001 word))";
        let exact = only(
            parse_mixed_exact_domain_reasoning_source("lib/clips-import.lisp", literal)
                .expect("CLIPS is explicitly pinned for D8 mechanism heads"),
        );
        let ExprKind::List(call) = &exact.kind else {
            panic!("executable CLIPS call");
        };
        assert!(
            matches!(
                &call[0].kind,
                ExprKind::DomainIdentity(identity)
                    if identity.width() == 8 && identity.packed_bits() == 0b11101110
            ),
            "only path-pinned source gets the exact D8 identity"
        );

        let quoted = only(
            parse_mixed_exact_domain_reasoning_source(
                "lib/clips-import.lisp",
                "(001 (11101110 word))",
            )
            .expect("CLIPS quoted data parses"),
        );
        let ExprKind::List(quote) = &quoted.kind else {
            panic!("D3 quote");
        };
        let ExprKind::List(data) = &quote[1].kind else {
            panic!("quote list datum");
        };
        assert!(
            !matches!(&data[0].kind, ExprKind::DomainIdentity(_)),
            "quoted eight-bit-looking data never gains a callable D8 identity"
        );

        let unpinned = only(
            parse_mixed_exact_domain_reasoning_source("lib/unify.lisp", literal)
                .expect("other admitted source remains readable"),
        );
        let ExprKind::List(legacy) = &unpinned.kind else {
            panic!("unify source");
        };
        assert!(
            !matches!(&legacy[0].kind, ExprKind::DomainIdentity(_)),
            "same eight bits in another file do not authorize a D8 identity"
        );
    }

    #[test]
    fn apostrophe_d3_quote_does_not_introduce_executable_binders() {
        let forms = parse_mixed_exact_domain("'(визначити атом? ()) (атом? ())")
            .expect("apostrophe quoted data and D3 surface head");
        assert_eq!(forms.len(), 2);
        let ExprKind::List(items) = &forms[1].kind else {
            panic!("second form must remain an executable list");
        };
        assert!(matches!(
            &items[0].kind,
            ExprKind::DomainIdentity(identity)
                if identity.width() == 3 && identity.packed_bits() == 0b010
        ));
        let ExprKind::List(quoted) = &forms[0].kind else {
            panic!("apostrophe expands to D2 list");
        };
        assert!(is_exact_quote(&quoted[0]));
    }

    #[test]
    fn core4_ukr_macro_data_stays_opaque_while_executable_d3_is_exact() {
        // Ім'я D3 у цитаті — дані. У виконуваній позиції воно має
        // точну D3:110, без історичного восьмибітного підйому макроса.
        let source = "(визначити макро-дані (функція (умови) (як-є за-умовою))) \
                      (за-умовою ((атом? (як-є ())) так))";
        let expressions = parse_mixed_exact_domain_core_source("lib/core4.lisp", source)
            .expect("український Core4 reader");
        assert_eq!(expressions.len(), 2);
        let ExprKind::List(definition) = &expressions[0].kind else {
            panic!("D4 визначити");
        };
        let ExprKind::List(lambda) = &definition[2].kind else {
            panic!("D4 функція");
        };
        let ExprKind::List(quoted) = &lambda[2].kind else {
            panic!("D3 як-є");
        };
        assert!(
            matches!(
                &quoted[1].kind,
                ExprKind::Symbol(name) if name.as_ref() == "за-умовою"
            ),
            "цитоване ім'я не стає викличною координатою"
        );

        let ExprKind::List(call) = &expressions[1].kind else {
            panic!("D3 виклик");
        };
        assert!(
            matches!(
                &call[0].kind,
                ExprKind::DomainIdentity(identity)
                    if identity.width() == 3 && identity.packed_bits() == 0b110
            ),
            "виконувана голова має бути D3:110, а не історичним W8"
        );
        assert!(parse_mixed_exact_domain_core_source("lib/untrusted.lisp", source).is_err());
    }

    #[test]
    fn reasoning_source_is_path_bound_and_preserves_w8_macro_data() {
        let src = "(00001010 preserve (x) (110 ((010 x) (001 (101 x x)))))";
        for path in [
            "lib/world.lisp",
            "lib/forward.lisp",
            "lib/knowledge.lisp",
            "lib/unify.lisp",
            "lib/reason.lisp",
            "lib/persistent-map.lisp",
            "lib/content-store.lisp",
            "lib/lisp-fs.lisp",
        ] {
            let tree = parse_mixed_exact_domain_reasoning_source(path, src)
                .expect("one of three authorized reasoning source files");
            let ExprKind::List(parts) = &tree[0].kind else {
                panic!("macro");
            };
            let ExprKind::List(cond) = &parts[3].kind else {
                panic!("body");
            };
            assert!(matches!(&cond[0].kind, ExprKind::DomainIdentity(id)
                if id.width() == 3 && id.packed_bits() == 0b110));
        }
        for path in ["lib/core4.lisp", "lib/other.lisp", "../world.lisp"] {
            assert!(parse_mixed_exact_domain_reasoning_source(path, src).is_err());
        }
    }

    #[test]
    fn reasoning_reader_lifts_d9_heads_only_on_pinned_paths() {
        let src = "(0011 probe (0010 (a b s) (101010000 a b s)))";
        let parsed = parse_mixed_exact_domain_reasoning_source("lib/unify.lisp", src).unwrap();
        let ExprKind::List(defn) = &parsed[0].kind else {
            panic!("def");
        };
        let ExprKind::List(lambda) = &defn[2].kind else {
            panic!("lambda");
        };
        let ExprKind::List(call) = &lambda[2].kind else {
            panic!("call");
        };
        assert!(matches!(&call[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 9 && id.packed_bits() == 0b101010000));

        let ordinary = only(parse_mixed_exact_domain("(101010000 a b s)").unwrap());
        let ExprKind::List(call) = &ordinary.kind else {
            panic!("call");
        };
        assert!(!matches!(&call[0].kind, ExprKind::DomainIdentity(_)));

        let quoted = parse_mixed_exact_domain_reasoning_source(
            "lib/unify.lisp",
            "(0011 datum (0010 () (001 (101010000 a b s))))",
        )
        .unwrap();
        let ExprKind::List(defn) = &quoted[0].kind else {
            panic!("def");
        };
        let ExprKind::List(lambda) = &defn[2].kind else {
            panic!("lambda");
        };
        let ExprKind::List(quote) = &lambda[2].kind else {
            panic!("quote");
        };
        let ExprKind::List(data) = &quote[1].kind else {
            panic!("data");
        };
        assert!(!matches!(&data[0].kind, ExprKind::DomainIdentity(_)));
    }

    #[test]
    fn w8_macro_wrapper_lifts_only_executable_d3_body() {
        let source = "(00001010 m (value) (110 ((010 value) (001 (101 value value)))))";
        let parsed = parse_mixed_exact_domain_machine_source(
            "lib/machine/dispatch/macro-probe.lisp",
            source,
        )
        .expect("W8 macro bodies are executable while their binders remain data");
        let ExprKind::List(defmacro) = &parsed[0].kind else {
            panic!("macro");
        };
        assert!(
            !matches!(&defmacro[0].kind, ExprKind::DomainIdentity(_)),
            "an unratified eight-bit wrapper must not acquire a current domain identity"
        );
        let ExprKind::List(params) = &defmacro[2].kind else {
            panic!("macro parameter data");
        };
        assert!(matches!(&params[0].kind, ExprKind::Symbol(_)));
        let ExprKind::List(cond) = &defmacro[3].kind else {
            panic!("macro body");
        };
        assert!(matches!(&cond[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b110));
        let ExprKind::List(clause) = &cond[1].kind else {
            panic!("clause");
        };
        let ExprKind::List(test) = &clause[0].kind else {
            panic!("test");
        };
        assert!(matches!(&test[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b010));
        let ExprKind::List(quoted) = &clause[1].kind else {
            panic!("quoted data");
        };
        let ExprKind::List(data) = &quoted[1].kind else {
            panic!("data");
        };
        assert!(
            !matches!(&data[0].kind, ExprKind::DomainIdentity(_)),
            "macro templates inside QUOTE cannot become evaluated code"
        );
    }

    #[test]
    fn time_source_requires_owner_path_and_lifts_nested_d3_calls() {
        let fixture = "(00001001 t (00001000 (x) (110 ((010 x) (001 ())) ((101 x x) (001 1)))))";
        assert!(parse_mixed_exact_domain_time_source("lib/not-time.lisp", fixture).is_err());
        let parsed = parse_mixed_exact_domain_time_source("lib/time.lisp", fixture)
            .expect("time loader must lift exact calls inside W8 bootstrap wrappers");
        let ExprKind::List(defined) = &parsed[0].kind else {
            panic!("definition");
        };
        let ExprKind::List(lambda) = &defined[2].kind else {
            panic!("lambda");
        };
        let ExprKind::List(cond) = &lambda[2].kind else {
            panic!("cond");
        };
        assert!(matches!(&cond[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b110));
        let ExprKind::List(first_clause) = &cond[1].kind else {
            panic!("clause");
        };
        let ExprKind::List(atom) = &first_clause[0].kind else {
            panic!("atom");
        };
        assert!(matches!(&atom[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b010));
        let ExprKind::List(second_clause) = &cond[2].kind else {
            panic!("clause");
        };
        let ExprKind::List(eq) = &second_clause[0].kind else {
            panic!("eq");
        };
        assert!(matches!(&eq[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b101));
        let quoted = "(00001001 datum (00001000 (x) (00000001 (110 (010 x)))))";
        let parsed = parse_mixed_exact_domain_time_source("lib/time.lisp", quoted)
            .expect("legacy W8 QUOTE remains data");
        let ExprKind::List(root) = &parsed[0].kind else {
            panic!("define");
        };
        let ExprKind::List(lambda) = &root[2].kind else {
            panic!("lambda");
        };
        let ExprKind::List(quote) = &lambda[2].kind else {
            panic!("quote");
        };
        let ExprKind::List(data) = &quote[1].kind else {
            panic!("quoted list");
        };
        assert!(
            !matches!(&data[0].kind, ExprKind::DomainIdentity(_)),
            "quoted 110 must not become executable D3 COND"
        );
    }

    #[test]
    fn ukrainian_callable_heads_lower_to_exact_domain_without_rewriting_lisp() {
        let source = "(визначити хід (функція (x) (перше x)))";
        let parsed = only(parse_mixed_exact_domain(source).expect("ratified ук surface"));
        let ExprKind::List(defined) = parsed.kind else {
            panic!("definition");
        };
        assert!(matches!(&defined[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 4 && id.packed_bits() == 0b0011));
        // Owner-ratified binding targets are lexical DATA, not callable heads.
        assert!(!matches!(&defined[1].kind, ExprKind::DomainIdentity(_)));
        let ExprKind::List(lambda) = &defined[2].kind else {
            panic!("звʼязування");
        };
        assert!(matches!(&lambda[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 4 && id.packed_bits() == 0b0010));
        let ExprKind::List(body) = &lambda[2].kind else {
            panic!("lambda body");
        };
        assert!(matches!(&body[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 3 && id.packed_bits() == 0b100));

        let byte_source = "(0011 хід (0010 (x) (100 x)))";
        let exact = only(parse_mixed_exact_domain(byte_source).expect("exact source"));
        let ExprKind::List(encoded) = exact.kind else {
            panic!("exact definition");
        };
        let ExprKind::List(encoded_lambda) = &encoded[2].kind else {
            panic!("exact lambda");
        };
        assert_eq!(defined[0].kind, encoded[0].kind);
        assert_eq!(lambda[0].kind, encoded_lambda[0].kind);
        let ExprKind::List(encoded_body) = &encoded_lambda[2].kind else {
            panic!("exact body");
        };
        assert_eq!(body[0].kind, encoded_body[0].kind);
    }

    #[test]
    fn ukrainian_quote_data_and_binding_position_are_not_retyped() {
        let source = "(як-є (перше x))";
        let quoted = only(parse_mixed_exact_domain(source).expect("quoted data"));
        let ExprKind::List(outer) = quoted.kind else {
            panic!("цитування");
        };
        assert!(matches!(&outer[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 3 && id.packed_bits() == 0b001));
        let ExprKind::List(data) = &outer[1].kind else {
            panic!("quoted data");
        };
        assert!(!matches!(&data[0].kind, ExprKind::DomainIdentity(_)));

        let binder = only(
            parse_mixed_exact_domain("(визначити перше (функція (перше) (атом? перше)))")
                .expect("binder data"),
        );
        let ExprKind::List(definition) = binder.kind else {
            panic!("definition");
        };
        assert!(!matches!(&definition[1].kind, ExprKind::DomainIdentity(_)));
        let ExprKind::List(lambda) = &definition[2].kind else {
            panic!("звʼязування");
        };
        let ExprKind::List(parameters) = &lambda[1].kind else {
            panic!("parameters");
        };
        assert!(!matches!(&parameters[0].kind, ExprKind::DomainIdentity(_)));
        let ExprKind::List(call) = &lambda[2].kind else {
            panic!("call");
        };
        assert!(matches!(&call[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 3 && id.packed_bits() == 0b010));
    }

    #[test]
    fn unknown_english_and_legacy_heads_get_no_new_current_identity() {
        // Literal legacy-English negative input is DATA, not executable Rust
        // or SENS. Keep its rejection test while avoiding false language-debt.
        let legacy_english_case =
            include_str!("../../../tests/fixtures/unknown-english-head.txt").trim();
        for source in [
            legacy_english_case,
            "(CONS x y)",
            "(00000101 x)",
            "(невідоме x)",
        ] {
            let expr = only(parse_mixed_exact_domain(source).expect("bounded mixed syntax"));
            let ExprKind::List(items) = expr.kind else {
                panic!("список");
            };
            assert!(
                !matches!(&items[0].kind, ExprKind::DomainIdentity(_)),
                "{source} must not become a ratified current domain from spelling"
            );
        }
    }

    #[test]
    fn local_callable_shadows_ratified_uk_surface_in_lambda_body() {
        let forms = parse_mixed_exact_domain("(функція (перше) (перше x))")
            .expect("local shadowing remains valid source");
        let ExprKind::List(lambda) = &forms[0].kind else {
            panic!("звʼязування");
        };
        assert!(matches!(&lambda[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 4 && id.packed_bits() == 0b0010));
        let ExprKind::List(body) = &lambda[2].kind else {
            panic!("body");
        };
        assert!(
            matches!(&body[0].kind, ExprKind::Symbol(name)
            if &**name == "перше"),
            "shadowed head must NOT become D3 CAR"
        );
    }

    #[test]
    fn globally_defined_callable_shadows_builtin_even_before_its_definition() {
        let forms =
            parse_mixed_exact_domain("(перше x) (визначити перше (функція (x) x)) (перше y)")
                .expect("whole source binding inventory");
        assert_eq!(forms.len(), 3);
        for index in [0, 2] {
            let ExprKind::List(call) = &forms[index].kind else {
                panic!("call");
            };
            assert!(
                matches!(&call[0].kind, ExprKind::Symbol(name)
                if &**name == "перше"),
                "user callable wins over ratified built-in"
            );
        }
    }

    #[test]
    fn quoted_definition_is_data_and_does_not_shadow_builtin() {
        let forms = parse_mixed_exact_domain("(як-є (визначити перше (функція (x) x))) (перше x)")
            .expect("quote remains data");
        let ExprKind::List(call) = &forms[1].kind else {
            panic!("call");
        };
        assert!(
            matches!(&call[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b100),
            "quoted pseudo-definition must not bind source"
        );
    }

    #[test]
    fn nested_local_shadowed_callable_is_not_promoted_inside_cond_clause() {
        let parsed =
            parse_mixed_exact_domain("(функція (перше) (за-умовою ((атом? x) (перше x))))")
                .expect("nested clause");
        let ExprKind::List(lambda) = &parsed[0].kind else {
            panic!("звʼязування");
        };
        let ExprKind::List(cond) = &lambda[2].kind else {
            panic!("умова");
        };
        let ExprKind::List(clause) = &cond[1].kind else {
            panic!("clause");
        };
        let ExprKind::List(body) = &clause[1].kind else {
            panic!("branch");
        };
        assert!(
            matches!(&body[0].kind, ExprKind::Symbol(name)
            if &**name == "перше"),
            "local binding is not D3 CAR even in COND"
        );
    }

    #[test]
    fn mixed_lambda_preserves_symbol_binder_and_exact_d3_d4_heads() {
        let expression = only(parse_mixed_exact_domain("(0010 (x) (100 x))").expect("mixed parse"));

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
        let parsed = parse_mixed_exact_domain("(0011 f (0010 (x) (010 x)))\n(f (001 a))")
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
            parse_mixed_exact_domain("(110 ((101 x 0) (01010 x 1)) ((101 0 0) 0))")
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
        let expression = only(parse_mixed_exact_domain("(0010 (x) 100)").expect("mixed parse"));
        let ExprKind::List(items) = expression.kind else {
            panic!("expected list");
        };
        assert!(
            matches!(&items[2].kind, ExprKind::BinaryNumber(number) if number.numeric_domain_width() == Some(24) && number.bits() == "1100100"),
            "ordinary decimal data is an exact D24+ value"
        );
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
    fn exact8_head_stays_opaque_to_current_domain_identity() {
        let expression = only(parse_mixed_exact_domain("(00000001 x)").expect("mixed parse"));
        let ExprKind::List(items) = expression.kind else {
            panic!("expected list");
        };
        assert!(!matches!(&items[0].kind, ExprKind::DomainIdentity(_)));
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
        let current = parse_mixed_exact_domain("(001110 x)").expect("ratified D6 mechanism source");
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
        assert!(!matches!(&outer[0].kind, ExprKind::DomainIdentity(_)));
        let ExprKind::List(quoted) = &outer[1].kind else {
            panic!("expected quoted list data");
        };
        assert!(
            matches!(
                &quoted[0].kind,
                ExprKind::Number(value, _) if *value == 100.0
            ),
            "quoted source must not become a D3 executable identity"
        );

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
            parse_mixed_exact_domain("(0010 ((100 x)) (011 x))").expect("exact D4 lambda parse"),
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

        let defined =
            only(parse_mixed_exact_domain("(0011 (100 x) (011 x))").expect("D4 define parse"));
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
        let parsed = parse_mixed_exact_domain("(local-f (100 x))").expect("mixed ordinary call");
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
    fn d4_append_requires_exact_mixed_head_not_decimal_number() {
        let source = "(1111 (001 (a)) (001 (b)))";
        let ordinary = crate::parser::parse(source).expect("звичайне читання");
        let ExprKind::List(ordinary_items) = &ordinary[0].kind else {
            panic!("очікується структура виклику");
        };
        assert!(
            matches!(
                &ordinary_items[0].kind,
                ExprKind::Number(_, _) | ExprKind::Rational(_)
            ),
            "звичайний Lisp-читач не надає числу D4-ідентичності"
        );

        let mixed = parse_mixed_exact_domain(source).expect("точний змішаний читач");
        let ExprKind::List(mixed_items) = &mixed[0].kind else {
            panic!("очікується структура D4-виклику");
        };
        assert!(
            matches!(
                &mixed_items[0].kind,
                ExprKind::DomainIdentity(id)
                    if id.width() == 4 && id.packed_bits() == 0b1111
            ),
            "тільки типізований D4:1111 є власником APPEND"
        );

        let mut session = crate::Session::default();
        let result = crate::eval::eval_parsed_expressions(&mixed, &mut session)
            .expect("ратифікований APPEND має об'єднати правильні списки");
        assert_eq!(result.value.to_string(), "(a b)");

        let invalid = parse_mixed_exact_domain("(1111 42)").expect("структурно допустиме джерело");
        let error = crate::eval::eval_parsed_expressions(&invalid, &mut session)
            .expect_err("APPEND не приймає числовий аргумент як список");
        assert!(error
            .message
            .contains("D4:1111 APPEND requires proper lists"));
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
    fn machine_source_mode_has_no_unquoted_numeric_d3_car_heads_in_x86_libraries() {
        fn walk(source: &str, expression: &Expr, quoted: bool, path: &str, hits: &mut Vec<String>) {
            let ExprKind::List(items) = &expression.kind else {
                return;
            };
            if items.is_empty() {
                return;
            }

            let head_spelling = source_spelling(source, &items[0]);
            let quote_head = matches!(head_spelling, Some("00000001" | "001" | "як-є"));
            if quoted || quote_head {
                return;
            }

            if matches!(&items[0].kind, ExprKind::Number(value, _) if *value == 100.0)
                || matches!(&items[0].kind, ExprKind::BinaryNumber(number) if number.numeric_domain_width() == Some(24) && number.bits() == "1100100")
            {
                let start = expression.span.start;
                let end = expression.span.end;
                let line = source[..start.min(source.len())].matches('\n').count() + 1;
                let snippet_end = end.min(start.saturating_add(100)).min(source.len());
                hits.push(format!(
                    "{path}:line={line}:span={start}..{end}:{}",
                    source[start.min(source.len())..snippet_end].replace('\n', " ")
                ));
            }

            // A list used as a clause's first item is itself executable; walk
            // it as well. Quoted subtrees were returned above and stay data.
            for child in items.iter() {
                walk(source, child, false, path, hits);
            }
        }

        let files = [
            (
                "lib/machine/effects/u64.lisp",
                include_str!("../../../lib/machine/effects/u64.lisp"),
            ),
            (
                "lib/machine/lowering/semantic-effects.lisp",
                include_str!("../../../lib/machine/lowering/semantic-effects.lisp"),
            ),
            (
                "lib/machine/encoding/x86-64.lisp",
                include_str!("../../../lib/machine/encoding/x86-64.lisp"),
            ),
            (
                "lib/machine/operands/x86-64.lisp",
                include_str!("../../../lib/machine/operands/x86-64.lisp"),
            ),
            (
                "lib/machine/admission/x86-64.lisp",
                include_str!("../../../lib/machine/admission/x86-64.lisp"),
            ),
            (
                "lib/machine/atoms/x86-64.lisp",
                include_str!("../../../lib/machine/atoms/x86-64.lisp"),
            ),
            (
                "lib/machine/projection/x86-64.lisp",
                include_str!("../../../lib/machine/projection/x86-64.lisp"),
            ),
            (
                "lib/machine/layout/pair-x86-64.lisp",
                include_str!("../../../lib/machine/layout/pair-x86-64.lisp"),
            ),
            (
                "lib/machine/lowering/semantic-x86-64.lisp",
                include_str!("../../../lib/machine/lowering/semantic-x86-64.lisp"),
            ),
            (
                "lib/machine/capability-axis.lisp",
                include_str!("../../../lib/machine/capability-axis.lisp"),
            ),
            (
                "lib/machine/profile/current-domain-x86-64.lisp",
                include_str!("../../../lib/machine/profile/current-domain-x86-64.lisp"),
            ),
            (
                "lib/machine/authority-boundary.lisp",
                include_str!("../../../lib/machine/authority-boundary.lisp"),
            ),
        ];

        let mut hits = Vec::new();
        for (path, source) in files {
            let expressions = parse_mixed_exact_domain_machine_source(path, source)
                .expect("approved machine source parses");
            for expression in &expressions {
                walk(source, expression, false, path, &mut hits);
            }
        }

        assert!(
            hits.is_empty(),
            "numeric 100 remains in executable head position after machine-source lifting:\n{}",
            hits.iter().take(30).cloned().collect::<Vec<_>>().join("\n")
        );
    }

    #[test]
    fn core4_reader_lifts_d4_not_inside_w8_cond_but_keeps_quoted_data() {
        let source =
            "(00001001 probe (00001000 (x) (00000111 ((0100 x) 0) ((00000001 (0100 x)) 0))))";

        let ordinary = only(parse_mixed_exact_domain(source).expect("ordinary mixed source"));
        let ExprKind::List(ordinary_def) = &ordinary.kind else {
            panic!("definition");
        };
        let ExprKind::List(ordinary_lambda) = &ordinary_def[2].kind else {
            panic!("lambda");
        };
        let ExprKind::List(ordinary_cond) = &ordinary_lambda[2].kind else {
            panic!("COND");
        };
        let ExprKind::List(ordinary_clause) = &ordinary_cond[1].kind else {
            panic!("clause");
        };
        let ExprKind::List(ordinary_test) = &ordinary_clause[0].kind else {
            panic!("test");
        };
        assert!(matches!(&ordinary_test[0].kind, ExprKind::BinaryNumber(number) if number.numeric_domain_width() == Some(24) && number.bits() == "1100100"),
            "ordinary reader remains backward-compatible and keeps 0100 numeric inside opaque W8 wrappers");

        let mixed = only(
            parse_mixed_exact_domain_core_source("lib/core4.lisp", source)
                .expect("approved Core4 reader"),
        );
        let ExprKind::List(def) = &mixed.kind else {
            panic!("definition");
        };
        let ExprKind::List(lambda) = &def[2].kind else {
            panic!("lambda");
        };
        let ExprKind::List(cond) = &lambda[2].kind else {
            panic!("COND");
        };
        let ExprKind::List(clause) = &cond[1].kind else {
            panic!("clause");
        };
        let ExprKind::List(test) = &clause[0].kind else {
            panic!("test");
        };
        assert!(
            matches!(&test[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 4 && id.packed_bits() == 0b0100),
            "Core4's executable 0100 head is typed D4:0100 NOT, not Number(100)"
        );

        let ExprKind::List(quoted_clause) = &cond[2].kind else {
            panic!("quoted clause");
        };
        let ExprKind::List(quote_form) = &quoted_clause[0].kind else {
            panic!("quote form");
        };
        assert!(
            !matches!(&quote_form[0].kind, ExprKind::DomainIdentity(_)),
            "unratified eight-bit quote spelling stays opaque, not a current identity"
        );
        let ExprKind::List(quoted_data) = &quote_form[1].kind else {
            panic!("quoted data");
        };
        assert!(
            matches!(
                &quoted_data[0].kind,
                ExprKind::BinaryNumber(number)
                    if number.numeric_domain_width() == Some(24)
                        && number.bits() == "1100100"
            ),
            "0100 under W8 QUOTE remains exact D24 data and is not promoted to a callable identity"
        );

        let wrong_path = parse_mixed_exact_domain_core_source("lib/core.lisp", source)
            .expect_err("Core4 exact-width lifting must not apply to another source file");
        assert_eq!(wrong_path.kind, ErrorKind::Parse);
    }

    #[test]
    fn core4_source_has_no_numeric_0100_in_executable_call_head_positions() {
        fn walk(source: &str, expression: &Expr, hits: &mut Vec<String>) {
            let ExprKind::List(items) = &expression.kind else {
                return;
            };
            let Some(head) = items.first() else {
                return;
            };
            let spelling = source_spelling(source, head);
            if spelling == Some("00000001") {
                return; // W8 QUOTE owns its entire payload as data.
            }
            if spelling == Some("0100")
                && (matches!(&head.kind, ExprKind::Number(value, _) if *value == 100.0)
                    || matches!(&head.kind, ExprKind::BinaryNumber(number) if number.numeric_domain_width() == Some(24) && number.bits() == "1100100"))
            {
                let start = expression.span.start;
                let end = expression.span.end;
                let line = source[..start.min(source.len())].matches('\n').count() + 1;
                hits.push(format!(
                    "line={line} span={start}..{end} form={:?}",
                    source[start.min(source.len())..end.min(source.len())].replace('\n', " ")
                ));
            }
            for child in items.iter() {
                walk(source, child, hits);
            }
        }

        let source = include_str!("../../../lib/core4.lisp");
        let expressions = parse_mixed_exact_domain_core_source("lib/core4.lisp", source)
            .expect("owner-approved Core4 source parses in exact-domain mode");
        let mut hits = Vec::new();
        for expression in &expressions {
            walk(source, expression, &mut hits);
        }
        assert!(
            hits.is_empty(),
            "Core4 still has an unlifted numeric 0100 call head:\\n{}",
            hits.iter()
                .take(30)
                .cloned()
                .collect::<Vec<_>>()
                .join("\\n")
        );
    }

    #[test]
    fn machine_source_mode_lifts_executable_forms_inside_w8_cond_clause_tests() {
        let source =
            "(00001001 probe (00001000 (x) (00000111 ((100 x) 0) ((00000001 (100 x)) 0))))";

        let ordinary = only(parse_mixed_exact_domain(source).expect("ordinary mixed source"));
        let ExprKind::List(ordinary_def) = &ordinary.kind else {
            panic!("definition");
        };
        let ExprKind::List(ordinary_lambda) = &ordinary_def[2].kind else {
            panic!("lambda");
        };
        let ExprKind::List(ordinary_cond) = &ordinary_lambda[2].kind else {
            panic!("COND");
        };
        let ExprKind::List(ordinary_clause) = &ordinary_cond[1].kind else {
            panic!("clause");
        };
        let ExprKind::List(ordinary_test) = &ordinary_clause[0].kind else {
            panic!("test");
        };
        assert!(
            matches!(&ordinary_test[0].kind, ExprKind::BinaryNumber(number) if number.numeric_domain_width() == Some(24) && number.bits() == "1100100"),
            "the ordinary mixed reader leaves legacy wrappers opaque"
        );

        let machine = only(
            parse_mixed_exact_domain_machine_source("lib/machine/probe.lisp", source)
                .expect("machine-only mixed source"),
        );
        let ExprKind::List(def) = &machine.kind else {
            panic!("definition");
        };
        let ExprKind::List(lambda) = &def[2].kind else {
            panic!("lambda");
        };
        let ExprKind::List(cond) = &lambda[2].kind else {
            panic!("COND");
        };
        let ExprKind::List(clause) = &cond[1].kind else {
            panic!("clause");
        };
        let ExprKind::List(test) = &clause[0].kind else {
            panic!("test");
        };
        assert!(
            matches!(&test[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b100),
            "W8 COND's first clause item is executable code and must be exact D3 CAR"
        );

        let ExprKind::List(quoted_clause) = &cond[2].kind else {
            panic!("quoted clause");
        };
        let ExprKind::List(quoted_test) = &quoted_clause[0].kind else {
            panic!("quoted test");
        };
        assert!(
            !matches!(&quoted_test[0].kind, ExprKind::DomainIdentity(_)),
            "unratified quote spelling stays opaque, not a current identity"
        );
        let ExprKind::List(quoted_data) = &quoted_test[1].kind else {
            panic!("quoted data");
        };
        assert!(
            matches!(&quoted_data[0].kind, ExprKind::Number(value, _) if *value == 100.0),
            "quoted data must not be lifted as executable code"
        );
    }

    #[test]
    fn machine_source_mode_descends_w8_function_bodies_but_preserves_quote_and_number_data() {
        fn definition_body(expression: &Expr) -> &Expr {
            let ExprKind::List(definition) = &expression.kind else {
                panic!("definition");
            };
            let ExprKind::List(lambda) = &definition[2].kind else {
                panic!("legacy lambda wrapper");
            };
            &lambda[2]
        }

        let executable = "(00001001 probe (00001000 (x) (100 x)))";
        let ordinary = only(parse_mixed_exact_domain(executable).expect("ordinary mixed parse"));
        let ExprKind::List(ordinary_call) = &definition_body(&ordinary).kind else {
            panic!("ordinary executable body");
        };
        assert!(
            matches!(&ordinary_call[0].kind, ExprKind::BinaryNumber(number) if number.numeric_domain_width() == Some(24) && number.bits() == "1100100"),
            "ordinary bridge keeps legacy W8 containers opaque"
        );

        let machine = only(
            parse_mixed_exact_domain_machine_source("lib/machine/test-probe.lisp", executable)
                .expect("approved machine-source mixed parse"),
        );
        let ExprKind::List(machine_call) = &definition_body(&machine).kind else {
            panic!("machine executable body");
        };
        assert!(
            matches!(
                &machine_call[0].kind,
                ExprKind::DomainIdentity(identity)
                    if identity.width() == 3 && identity.packed_bits() == 0b100
            ),
            "only an executable 3-bit head inside the approved wrapper is lifted"
        );

        let quoted_source = "(00001001 probe (00001000 (x) (00000001 (100 x))))";
        let quoted = only(
            parse_mixed_exact_domain_machine_source("lib/machine/test-probe.lisp", quoted_source)
                .expect("machine source with historical quote"),
        );
        let ExprKind::List(quote_form) = &definition_body(&quoted).kind else {
            panic!("quote form");
        };
        assert!(
            !matches!(&quote_form[0].kind, ExprKind::DomainIdentity(_)),
            "unratified quote spelling stays opaque and keeps its payload as data"
        );
        let ExprKind::List(payload) = &quote_form[1].kind else {
            panic!("quote payload");
        };
        assert!(
            matches!(&payload[0].kind, ExprKind::Number(value, _) if *value == 100.0),
            "quoted 100 remains a number, never a callable D3 head"
        );

        let number_data_source = "(00001001 probe (00001000 (x) (ordinary-list 100 x)))";
        let number_data = only(
            parse_mixed_exact_domain_machine_source(
                "lib/machine/test-probe.lisp",
                number_data_source,
            )
            .expect("machine source numeric data"),
        );
        let ExprKind::List(data_call) = &definition_body(&number_data).kind else {
            panic!("data call");
        };
        assert!(
            matches!(&data_call[1].kind, ExprKind::BinaryNumber(number) if number.numeric_domain_width() == Some(24) && number.bits() == "1100100"),
            "non-head decimal data remains unchanged"
        );
    }

    #[test]
    fn machine_reader_lifts_only_admitted_d8_io_and_preserves_quoted_data() {
        let source = "(0011 wire (0010 (value) (11110100 value)))";
        let parsed = only(
            parse_mixed_exact_domain_machine_source("lib/machine/tests/d8-wire.lisp", source)
                .expect("trusted machine-source reader"),
        );
        let ExprKind::List(definition) = &parsed.kind else {
            panic!("DEFINE");
        };
        let ExprKind::List(lambda) = &definition[2].kind else {
            panic!("LAMBDA");
        };
        let ExprKind::List(call) = &lambda[2].kind else {
            panic!("call");
        };
        assert!(
            matches!(
                &call[0].kind, ExprKind::DomainIdentity(id)
                    if id.width() == 8 && id.packed_bits() == 0b11110100
            ),
            "trusted machine D8 WRITE-TO-STRING must carry exact identity"
        );

        let ordinary = only(parse_mixed_exact_domain("(11110100 2)").expect("ordinary reader"));
        let ExprKind::List(ordinary_call) = &ordinary.kind else {
            panic!("ordinary call");
        };
        assert!(
            !matches!(&ordinary_call[0].kind, ExprKind::DomainIdentity(_)),
            "ordinary source never infers D8 from eight bits"
        );

        let quoted = only(
            parse_mixed_exact_domain_machine_source(
                "lib/machine/tests/d8-wire.lisp",
                "(001 (11110100 2))",
            )
            .expect("quoted data"),
        );
        let ExprKind::List(quote) = &quoted.kind else {
            panic!("QUOTE");
        };
        let ExprKind::List(payload) = &quote[1].kind else {
            panic!("quoted payload");
        };
        assert!(
            !matches!(&payload[0].kind, ExprKind::DomainIdentity(_)),
            "quoted D8-shaped data must never become callable"
        );

        let other = only(
            parse_mixed_exact_domain_machine_source(
                "lib/machine/tests/d8-wire.lisp",
                "(11110000 2)",
            )
            .expect("other W8 call head"),
        );
        let ExprKind::List(other_call) = &other.kind else {
            panic!("other call");
        };
        assert!(
            !matches!(&other_call[0].kind, ExprKind::DomainIdentity(_)),
            "no general D8 callability expansion"
        );
    }

    #[test]
    fn machine_admission_lifts_only_four_pinned_d9_string_heads() {
        let cases = [
            ("110011100", "(110011100 text)"),          // string-empty?
            ("110011101", "(110011101 text)"),          // string-rest
            ("110101010", "(110101010 \"#q2:\" text)"), // string-prefix?
            ("110101011", "(110101011 text)"),          // string-first
        ];
        for (word, call_source) in cases {
            let source = format!("(0011 probe (0010 (text) {call_source}))");
            let parsed = only(
                parse_mixed_exact_domain_machine_source(
                    "lib/machine/admission/x86-64.lisp",
                    &source,
                )
                .expect("pinned machine-admission D9 string head"),
            );
            let ExprKind::List(definition) = &parsed.kind else {
                panic!("DEFINE");
            };
            let ExprKind::List(lambda) = &definition[2].kind else {
                panic!("LAMBDA");
            };
            let ExprKind::List(call) = &lambda[2].kind else {
                panic!("call");
            };
            assert!(
                matches!(
                    &call[0].kind, ExprKind::DomainIdentity(id)
                        if id.width() == 9 && id.packed_bits() == u16::from_str_radix(word, 2).unwrap()
                ),
                "ratified D9 head {word} must retain its exact width"
            );
        }

        let source = "(0011 probe (0010 (text) (110101010 \"#q2:\" text)))";
        let encoding_path = only(
            parse_mixed_exact_domain_machine_source("lib/machine/encoding/x86-64.lisp", source)
                .expect("encoding's exact wire reader admits the same bounded D9 string heads"),
        );
        let ExprKind::List(definition) = &encoding_path.kind else {
            panic!("DEFINE");
        };
        let ExprKind::List(lambda) = &definition[2].kind else {
            panic!("LAMBDA");
        };
        let ExprKind::List(call) = &lambda[2].kind else {
            panic!("call");
        };
        assert!(
            matches!(&call[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 9 && id.packed_bits() == 0b110101010),
            "encoding can call only the exact D9 prefix mechanism for canonical wire validation"
        );

        let other_machine_path = only(
            parse_mixed_exact_domain_machine_source(
                "lib/machine/lowering/semantic-x86-64.lisp",
                source,
            )
            .expect("unrelated trusted machine source remains D9-closed"),
        );
        let ExprKind::List(definition) = &other_machine_path.kind else {
            panic!("DEFINE");
        };
        let ExprKind::List(lambda) = &definition[2].kind else {
            panic!("LAMBDA");
        };
        let ExprKind::List(call) = &lambda[2].kind else {
            panic!("call");
        };
        assert!(
            !matches!(&call[0].kind, ExprKind::DomainIdentity(id) if id.width() == 9),
            "D9 callability must not leak to other machine files"
        );

        let quoted_source = "(001 (110101010 \"#q2:\" text))";
        let quoted = only(
            parse_mixed_exact_domain_machine_source(
                "lib/machine/admission/x86-64.lisp",
                quoted_source,
            )
            .expect("quoted D9-looking datum remains opaque"),
        );
        let ExprKind::List(quote) = &quoted.kind else {
            panic!("QUOTE");
        };
        let ExprKind::List(payload) = &quote[1].kind else {
            panic!("quoted payload");
        };
        assert!(
            !matches!(&payload[0].kind, ExprKind::DomainIdentity(id) if id.width() == 9),
            "quoted data must never gain D9 callability"
        );
    }

    #[test]
    fn ordinary_mixed_reader_executes_immediately_applied_exact_d4_lambda() {
        let source = "((0010 (x) (101 (100 x) (001 alpha))) (001 (alpha beta)))";
        let forms = parse_mixed_exact_domain(source).expect("current D4 Lambda application");
        assert_eq!(forms.len(), 1);
        let ExprKind::List(call) = &forms[0].kind else {
            panic!("outer application");
        };
        let ExprKind::List(lambda) = &call[0].kind else {
            panic!("computed lambda");
        };
        assert!(
            matches!(&lambda[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 4 && id.packed_bits() == 0b0010),
            "D4:0010 must retain its width in a computed executable head"
        );
        let ExprKind::List(eq) = &lambda[2].kind else {
            panic!("lambda body");
        };
        assert!(matches!(&eq[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b101));
        let mut session = crate::Session::default();
        let evaluated = crate::eval_parsed_expressions(&forms, &mut session)
            .expect("SENS must execute its current D4 lambda and D3 EQ");
        assert_eq!(
            evaluated.value.as_predicate_bit(),
            Some(true),
            "SENS D3 EQ returns its own exact D1:YES verdict"
        );

        let quoted = only(
            parse_mixed_exact_domain("((0010 (x) (001 (100 x))) (001 (a b)))")
                .expect("quote remains data inside computed lambda"),
        );
        let ExprKind::List(outer) = quoted.kind else {
            panic!("outer application");
        };
        let ExprKind::List(inner_lambda) = &outer[0].kind else {
            panic!("computed lambda");
        };
        let ExprKind::List(quote) = &inner_lambda[2].kind else {
            panic!("D3 QUOTE");
        };
        assert!(is_exact_quote(&quote[0]));
        let ExprKind::List(data) = &quote[1].kind else {
            panic!("quoted data");
        };
        assert!(
            !matches!(&data[0].kind, ExprKind::DomainIdentity(_)),
            "W3-looking word inside quoted data cannot become callable"
        );
    }

    #[test]
    fn machine_source_mode_lifts_an_immediately_applied_lambda_head() {
        let source = "((00001000 (x) (100 x)) 7)";

        // The ordinary mixed reader leaves the legacy lambda wrapper opaque.
        let ordinary = only(parse_mixed_exact_domain(source).expect("ordinary parse"));
        let ExprKind::List(ordinary_call) = &ordinary.kind else {
            panic!("outer application");
        };
        let ExprKind::List(ordinary_lambda) = &ordinary_call[0].kind else {
            panic!("lambda head");
        };
        let ExprKind::List(ordinary_body) = &ordinary_lambda[2].kind else {
            panic!("lambda body");
        };
        assert!(
            matches!(&ordinary_body[0].kind, ExprKind::BinaryNumber(number) if number.numeric_domain_width() == Some(24) && number.bits() == "1100100"),
            "ordinary mixed source must not opt into machine-source lifting"
        );

        let machine = only(
            parse_mixed_exact_domain_machine_source("lib/machine/test-probe.lisp", source)
                .expect("approved machine-source parse"),
        );
        let ExprKind::List(call) = &machine.kind else {
            panic!("outer application");
        };
        let ExprKind::List(lambda) = &call[0].kind else {
            panic!("lambda head");
        };
        let ExprKind::List(body) = &lambda[2].kind else {
            panic!("lambda body");
        };
        assert!(
            matches!(&body[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b100),
            "nested executable CAR must be an exact D3 identity"
        );
        assert!(
            matches!(&call[1].kind, ExprKind::BinaryNumber(number) if number.numeric_domain_width() == Some(24) && number.bits() == "111"),
            "numeric call arguments remain data"
        );
    }

    #[test]
    fn process_tcp_reader_is_path_bound_and_preserves_quoted_data() {
        let source = "(0011 probe (0010 (x) (101 (100 x) (001 x))))";
        for path in ["lib/process.lisp", "lib/tcp.lisp"] {
            let parsed = only(
                parse_mixed_exact_domain_process_tcp_source(path, source)
                    .expect("approved process/TCP reader"),
            );
            let ExprKind::List(definition) = &parsed.kind else {
                panic!("definition");
            };
            let ExprKind::List(lambda) = &definition[2].kind else {
                panic!("lambda");
            };
            let ExprKind::List(call) = &lambda[2].kind else {
                panic!("body call");
            };
            assert!(
                matches!(
                    &call[0].kind,
                    ExprKind::DomainIdentity(identity)
                        if identity.width() == 3 && identity.packed_bits() == 0b101
                ),
                "exact D3 EQ call head in approved process/TCP source must be typed"
            );
        }

        let quoted_source = "(0011 probe (0010 (x) (001 (101 x))))";
        let quoted = only(
            parse_mixed_exact_domain_process_tcp_source("lib/process.lisp", quoted_source)
                .expect("approved source with quote"),
        );
        let ExprKind::List(definition) = &quoted.kind else {
            panic!("definition");
        };
        let ExprKind::List(lambda) = &definition[2].kind else {
            panic!("lambda");
        };
        let ExprKind::List(quote_form) = &lambda[2].kind else {
            panic!("quoted body");
        };
        assert!(
            matches!(&quote_form[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b001),
            "D3 QUOTE remains an identity"
        );
        let ExprKind::List(payload) = &quote_form[1].kind else {
            panic!("quoted payload");
        };
        assert!(
            !matches!(&payload[0].kind, ExprKind::DomainIdentity(_)),
            "quoted numeric-looking payload must not become executable domain identity"
        );

        assert!(
            parse_mixed_exact_domain_process_tcp_source("lib/time.lisp", source).is_err(),
            "the process/TCP exception must not authorize a third source path"
        );
    }

    #[test]
    fn utf8_reader_materializes_current_short_and_d9_heads_without_touching_quotes() {
        let source =
            "(0011 probe (0010 (x) (110 ((010 x) (110011100 \"\")) ((010 ()) (110011101 x)))))";
        let parsed = parse_mixed_exact_domain_utf8_source("lib/utf8.lisp", source)
            .expect("pinned UTF8 source");
        let ExprKind::List(defn) = &parsed[0].kind else {
            panic!("DEFINE");
        };
        let ExprKind::List(lambda) = &defn[2].kind else {
            panic!("LAMBDA");
        };
        let ExprKind::List(cond) = &lambda[2].kind else {
            panic!("COND");
        };
        assert!(matches!(&cond[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 3 && id.packed_bits() == 0b110));
        let ExprKind::List(first_clause) = &cond[1].kind else {
            panic!("clause");
        };
        let ExprKind::List(d9_call) = &first_clause[1].kind else {
            panic!("D9 call");
        };
        assert!(matches!(&d9_call[0].kind, ExprKind::DomainIdentity(id)
            if id.width() == 9 && id.packed_bits() == 0b110011100));

        assert!(parse_mixed_exact_domain_utf8_source("lib/not-utf8.lisp", source).is_err());
    }

    #[test]
    fn core_macro_code_names_are_ordinary_quoted_ukrainian_data() {
        let source = "(як-є функція)";
        let exact =
            only(parse_mixed_exact_domain(source).expect("generic exact-domain source parse"));
        let ExprKind::List(quote) = &exact.kind else {
            panic!("QUOTE");
        };
        assert!(matches!(&quote[0].kind,
            ExprKind::DomainIdentity(id) if id.width() == 3 && id.packed_bits() == 0b001));
        assert!(matches!(&quote[1].kind,
            ExprKind::Symbol(name) if name.as_ref() == "функція"));
    }

    #[test]
    fn macro_code_templates_keep_ukrainian_names_as_data_until_expansion() {
        let source = "(як-є визначити) (як-є функція)";
        let parsed = parse_mixed_exact_domain(source)
            .expect("macro code templates use ordinary ratified Ukrainian source");
        assert_eq!(parsed.len(), 2);

        for (expression, expected) in parsed.iter().zip(["визначити", "функція"]) {
            let ExprKind::List(form) = &expression.kind else {
                panic!("QUOTE form");
            };
            assert!(
                matches!(
                    &form[0].kind,
                    ExprKind::DomainIdentity(identity)
                        if identity.width() == 3 && identity.packed_bits() == 0b001
                ),
                "code-data constructor must be the exact D3 QUOTE resident"
            );
            assert!(
                matches!(
                    &form[1].kind,
                    ExprKind::Symbol(name) if name.as_ref() == expected
                ),
                "{expected} is ordinary quoted source data until macro expansion"
            );
        }

        let macro_source = include_str!("../../../lib/macro.lisp");
        assert!(!macro_source.contains("(як-є 0010)"));
        assert!(!macro_source.contains("(як-є 0011)"));
    }

    #[test]
    fn process_tcp_reader_routes_d6_let_star_through_lisp_macro_and_keeps_quote_opaque() {
        let source = "(0011 probe (0010 (x) (001001 ((y 1)) y)))";
        let parsed = only(
            parse_mixed_exact_domain_process_tcp_source("lib/process.lisp", source)
                .expect("approved process/TCP D6 LET* source"),
        );
        let ExprKind::List(definition) = &parsed.kind else {
            panic!("DEFINE");
        };
        let ExprKind::List(lambda) = &definition[2].kind else {
            panic!("LAMBDA");
        };
        let ExprKind::List(let_star) = &lambda[2].kind else {
            panic!("LET* body");
        };
        assert!(
            matches!(&let_star[0].kind, ExprKind::DomainIdentity(identity)
                if identity.width() == 6 && identity.packed_bits() == 0b001001),
            "D6 LET* must remain its exact canonical identity until the loader binds its Lisp-owned macro code-slot"
        );

        let quoted_source = "(0011 probe (0010 (x) (001 (001001 ((y 1)) y))))";
        let quoted = only(
            parse_mixed_exact_domain_process_tcp_source("lib/process.lisp", quoted_source)
                .expect("quoted D6 LET* data"),
        );
        let ExprKind::List(quoted_definition) = &quoted.kind else {
            panic!("DEFINE");
        };
        let ExprKind::List(quoted_lambda) = &quoted_definition[2].kind else {
            panic!("LAMBDA");
        };
        let ExprKind::List(quote_form) = &quoted_lambda[2].kind else {
            panic!("QUOTE");
        };
        let ExprKind::List(payload) = &quote_form[1].kind else {
            panic!("quoted payload");
        };
        assert!(
            !matches!(&payload[0].kind, ExprKind::DomainIdentity(_)),
            "quoted D6-shaped spelling remains opaque data; no call-head projection runs beneath QUOTE"
        );
    }

    #[test]
    fn process_tcp_language_loaders_use_path_bound_reader() {
        let process_ast =
            parse_mixed_exact_domain_process_tcp_source("lib/process.lisp", crate::PROCESS_LIBRARY_SOURCE)
                .expect("actual process.lisp parses through its path-bound reader");
        let tcp_ast = parse_mixed_exact_domain_process_tcp_source("lib/tcp.lisp", crate::TCP_LIBRARY_SOURCE)
            .expect("actual tcp.lisp parses through its path-bound reader");
        assert!(!process_ast.is_empty() && !tcp_ast.is_empty());

        let mut session = crate::Session::default();
        crate::load_core_library(&mut session).expect("current Core bootstrap");
        crate::load_process_library(&mut session)
            .expect("process/TCP Lisp libraries must load via the path-bound exact-domain reader");
    }
}
