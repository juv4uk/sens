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
        .map(|expr| lift_pinned_d8_io(source, expr, 0, false))
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

fn lift_pinned_d8_io(
    source: &str,
    expression: Expr,
    depth: u32,
    preserve_legacy_w8_quote: bool,
) -> Result<Expr, LanguageError> {
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
    if preserve_legacy_w8_quote && is_legacy_w8_quote_head(source, &lifted[0]) {
        return Ok(Expr { kind: ExprKind::List(items), span });
    }
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
        lifted[0] = lift_pinned_d8_io(source, lifted[0].clone(), depth + 1, preserve_legacy_w8_quote)?;
    }

    let skip_binding_slot = is_legacy_w8_define_head(source, &items[0])
        || is_legacy_w8_lambda_head(source, &items[0])
        || is_legacy_w8_macro_head(source, &items[0])
        || is_exact_d4_binding_head(&items[0]);

    for (index, item) in lifted.iter_mut().enumerate().skip(1) {
        if skip_binding_slot && index == 1 {
            continue;
        }
        *item = lift_pinned_d8_io(source, item.clone(), depth + 1, preserve_legacy_w8_quote)?;
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
        .map(|expr| lift_pinned_d8_io(source, expr, 0, false))
        .collect()
}

/// Migrate only explicitly pinned sources. W8 syntax containers remain
/// compatible while approved exact D9 mechanisms are lifted from their
/// Ukrainian projection. D9 residency alone never grants callability.
fn lift_pinned_d9_language_calls(
    source: &str,
    expression: Expr,
    depth: u32,
    preserve_legacy_w8_quote: bool,
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
    const UKRAINIAN_D9_LISP_CALLS: [&str; 4] = [
        "повідомити-знання",
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
    if preserve_legacy_w8_quote && is_legacy_w8_quote_head(source, &lifted[0]) {
        return Ok(Expr { kind: ExprKind::List(items), span });
    }
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
        lifted[0] = lift_pinned_d9_language_calls(source, lifted[0].clone(), depth + 1, preserve_legacy_w8_quote)?;
    }

    let skip_binding = is_legacy_w8_define_head(source, &items[0])
        || is_legacy_w8_lambda_head(source, &items[0])
        || is_legacy_w8_macro_head(source, &items[0])
        || is_exact_d4_binding_head(&items[0]);
    for (index, item) in lifted.iter_mut().enumerate().skip(1) {
        if skip_binding && index == 1 {
            continue;
        }
        *item = lift_pinned_d9_language_calls(source, item.clone(), depth + 1, preserve_legacy_w8_quote)?;
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
    } else if path == "lib/translation.lisp" {
        let bindings = translation_reasoning_dependency_bindings()?;
        parse_mixed_source_with_external_bindings(source, true, &bindings)?
    } else {
        parse_mixed_source(source, true)?
    };
    base.into_iter()
        .map(|expr| lift_pinned_d9_language_calls(source, expr, 0, false))
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
        .map(|expr| lift_pinned_d8_io(source, expr, 0, false))
        .map(|expr| expr.and_then(|expr| lift_pinned_d9_language_calls(source, expr, 0, false)))
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
        .map(|expr| lift_pinned_d9_language_calls(source, expr, 0, false))
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
        .map(|expr| проєктувати_цитовані_числа_core4(source, expr, 0))
        .collect::<Result<Vec<_>, _>>()?
        .into_iter()
        .map(|expr| lift_pinned_d8_io(source, expr, 0, true))
        .collect::<Result<Vec<_>, _>>()?;
    // Цитовані українські імена залишаються даними: побітовий
    // адаптер макросів уже фізично вилучено з runtime.
    parsed
        .into_iter()
        .map(|expr| lift_pinned_d9_language_calls(source, expr, 0, true))
        .collect()
}

fn parse_mixed_source(
    source: &str,
    descend_legacy_machine_wrappers: bool,
) -> Result<Vec<Expr>, LanguageError> {
    parse_mixed_source_with_external_bindings(source, descend_legacy_machine_wrappers, &HashSet::new())
}

/// Parse a source fragment with an explicit inventory of names already defined
/// by path-pinned libraries loaded into the same SENS session. This only
/// preserves those names as ordinary bound symbols; it does not admit new
/// callable domain identities or infer width from a word's spelling.
fn parse_mixed_source_with_external_bindings(
    source: &str,
    descend_legacy_machine_wrappers: bool,
    external_bound_names: &HashSet<String>,
) -> Result<Vec<Expr>, LanguageError> {
    let parsed = crate::parser::parse(source)?;
    // Project ordinary Ukrainian decimal leaves before callable heads become
    // DomainIdentity nodes, so D5 arithmetic trees can choose one exact width.
    // The projector preserves quote payloads and already typed domain data.
    let expressions =
        crate::source_projection::project_ukr_decimal_integer_literals(&parsed, source)?;
    // A path-pinned caller may supply only names from libraries it has already
    // loaded. Source-local definitions are still collected independently.
    // Conservatively declining a projection is safer than silently calling a builtin.
    let mut bound_names = external_bound_names.clone();
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

/// Collect only top-level Lisp-defined binding names from one already-approved
/// source file. Parameter/local names are intentionally excluded: this is an
/// inventory for a known library boundary, not global lexical scope.
fn collect_top_level_binding_names(source: &str) -> Result<HashSet<String>, LanguageError> {
    let parsed = crate::parser::parse(source)?;
    let mut names = HashSet::new();
    for expression in &parsed {
        let ExprKind::List(items) = &expression.kind else {
            continue;
        };
        if items.len() < 2 || binding_form(source, &items[0]) != Some(3) {
            continue;
        }
        // Binding position is authoritative within this already-pinned
        // library even when the mixed reader has projected its spelling to a
        // D7/D10 identity. Preserve the exact source name for external snippets;
        // this does not grant callability or infer any domain coordinate.
        if let Some(name) = source_spelling(source, &items[1]) {
            if !name.is_empty() {
                names.insert(name.to_owned());
            }
        }
    }
    Ok(names)
}

/// The translation-boundary tests and validator snippets execute after these
/// path-pinned reasoning libraries have been loaded. Preserve their Lisp-owned
/// helper names as symbols in external snippets; otherwise the reader tries to
/// project a multi-glyph D7 binding into a callable identity and correctly
/// refuses it. Names still need to exist in the active SENS environment.
fn translation_reasoning_dependency_bindings() -> Result<HashSet<String>, LanguageError> {
    const SOURCES: [&str; 8] = [
        include_str!("../../../lib/persistent-map.lisp"),
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
        include_str!("../../../lib/world.lisp"),
        include_str!("../../../lib/result-status.lisp"),
        include_str!("../../../lib/translation.lisp"),
    ];
    let mut names = HashSet::new();
    for library in SOURCES {
        names.extend(collect_top_level_binding_names(library)?);
    }
    Ok(names)
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
    // The Ukrainian spelling `як-є` is D3:001 QUOTE, but it is a syntax
    // form, not an ordinary callable source head. The callable-head index
    // intentionally omits some syntax identities, so resolve QUOTE through
    // the canonical surface registry before traversing its payload.
    if source_spelling(source, head) == Some("як-є") {
        return crate::semantic_registry::domain_identity_for_surface("як-є")
            .is_some_and(|identity| identity.width() == 3 && identity.packed_bits() == 0b001);
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
                // Дочірній span після змішаного підняття може бути локальним
                // поданням D7 (наприклад, D4:0100 відображається як «п-р»).
                // Повторно читаємо повну цитовану форму з її початкового
                // діапазону, щоб D4-ідентичність походила з вихідного написання,
                // а не відновлювалася з втратного відображення D7.
                let raw_quote = source.get(span.start..span.end);
                let raw_items = raw_quote.and_then(|form| {
                    let mut parsed = crate::parser::parse(form).ok()?;
                    if parsed.len() != 1 {
                        return None;
                    }
                    match parsed.remove(0).kind {
                        ExprKind::List(items) if items.len() == lifted.len() => Some((form, items)),
                        _ => None,
                    }
                });
                if let Some((raw_source, raw_items)) = raw_items {
                    for index in 1..lifted.len() {
                        lifted[index] = lift_quoted_d4_identity_data(
                            raw_source,
                            raw_items[index].clone(),
                            depth + 1,
                        )?;
                    }
                } else {
                    // Fail-closed сумісність, якщо точний діапазон не дає
                    // повторно розібрати одну повну цитовану форму.
                    for item in lifted.iter_mut().skip(1) {
                        *item = lift_quoted_d4_identity_data(source, item.clone(), depth + 1)?;
                    }
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
    // The world/knowledge macros quote this exact ratified D10 call as a
    // template head, then splice it into executable code. Preserve the D10
    // identity as data here so macro expansion can later call the admitted
    // target; do not project arbitrary quoted D7 names into callability.
    if source_spelling(source, &expression)
        == Some("перетворити-клаузи-на-події-повідомлення")
    {
        if let Some(identity) = crate::semantic_registry::d10_binding_identity_for_definition(
            "перетворити-клаузи-на-події-повідомлення",
        )
        .filter(|identity| identity.width() == 10 && identity.packed_bits() == 0b0010000001)
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

fn проєктувати_числові_дані_цитати(
    source: &str,
    expression: Expr,
    depth: u32,
) -> Result<Expr, LanguageError> {
    if depth > MAX_STRUCTURE_DEPTH {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "цитовані числові дані перевищують межу вкладеності",
            expression.span,
        ));
    }

    let Expr { kind, span } = expression;
    if matches!(&kind, ExprKind::Number(_, _)) {
        let token = source.get(span.start..span.end);
        let digits = token.map(|text| {
            text.strip_prefix('-')
                .or_else(|| text.strip_prefix('+'))
                .unwrap_or(text)
        });
        if digits.is_some_and(|digits| {
            !digits.is_empty() && digits.bytes().all(|byte| byte.is_ascii_digit())
        }) {
            let number = Expr { kind, span };
            let mut projected = crate::source_projection::project_ukr_decimal_integer_literals(
                std::slice::from_ref(&number),
                source,
            )?;
            if projected.len() == 1 {
                return Ok(projected.remove(0));
            }
            return Err(LanguageError::new(
                ErrorKind::Parse,
                "проєкція цитованого цілого числа має повернути одне значення",
                span,
            ));
        }
    }

    match kind {
        ExprKind::List(items) => {
            let projected = items
                .iter()
                .cloned()
                .map(|item| проєктувати_числові_дані_цитати(source, item, depth + 1))
                .collect::<Result<Vec<_>, _>>()?;
            Ok(Expr {
                kind: ExprKind::List(Rc::from(projected.into_boxed_slice())),
                span,
            })
        }
        ExprKind::Pair(car, cdr) => {
            let car = проєктувати_числові_дані_цитати(source, (*car).clone(), depth + 1)?;
            let cdr = проєктувати_числові_дані_цитати(source, (*cdr).clone(), depth + 1)?;
            Ok(Expr {
                kind: ExprKind::Pair(Rc::new(car), Rc::new(cdr)),
                span,
            })
        }
        other => Ok(Expr { kind: other, span }),
    }
}

fn проєктувати_цитовані_числа_core4(
    source: &str,
    expression: Expr,
    depth: u32,
) -> Result<Expr, LanguageError> {
    if depth > MAX_STRUCTURE_DEPTH {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "цитовані числа Core4 перевищують межу вкладеності",
            expression.span,
        ));
    }

    let Expr { kind, span } = expression;
    match kind {
        ExprKind::List(items) if !items.is_empty() => {
            let mut projected = items.to_vec();
            if is_legacy_w8_quote_head(source, &projected[0]) {
                for item in projected.iter_mut().skip(1) {
                    *item =
                        проєктувати_числові_дані_цитати(source, item.clone(), depth + 1)?;
                }
            } else {
                for item in &mut projected {
                    *item = проєктувати_цитовані_числа_core4(
                        source,
                        item.clone(),
                        depth + 1,
                    )?;
                }
            }
            Ok(Expr {
                kind: ExprKind::List(Rc::from(projected.into_boxed_slice())),
                span,
            })
        }
        ExprKind::List(items) => Ok(Expr {
            kind: ExprKind::List(items),
            span,
        }),
        ExprKind::Pair(car, cdr) => {
            let car = проєктувати_цитовані_числа_core4(source, (*car).clone(), depth + 1)?;
            let cdr = проєктувати_цитовані_числа_core4(source, (*cdr).clone(), depth + 1)?;
            Ok(Expr {
                kind: ExprKind::Pair(Rc::new(car), Rc::new(cdr)),
                span,
            })
        }
        other => Ok(Expr { kind: other, span }),
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

