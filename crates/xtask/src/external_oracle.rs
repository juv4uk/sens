//! Exact arithmetic AST projection for WSM-5's independent external oracle.
//!
//! This layer does not interpret arithmetic by spelling and does not evaluate
//! my-lisp. It parses one source expression, resolves the operator through the
//! authoritative semantic registry, and projects the exact AST shape into a
//! Wolfram Language expression. Unsupported input fails closed with stable
//! codes instead of being approximated.
//!
//! ## Corpus loading
//!
//! `load_corpus()` reads `tests/fixtures/conformance.my` and
//! `tests/fixtures/inventory.my` positionally (same as `scripts/oracle-batch.wsm`):
//! both files must have the same fixture count; they are walked in lockstep.
//!
//! ## Export
//!
//! `export_fixture()` selects a single fixture by `F-…` id and produces a
//! versioned `external-oracle/1` request s-expression ready for an external
//! Wolfram Language host.

use my_lisp::semantic_registry_export::semantic_id_for_admitted_surface;
use my_lisp::{Exactness, Expr, ExprKind};

// ── Public corpus types ───────────────────────────────────────────────────────

/// One fixture as read from the corpus pair.
#[derive(Debug, Clone)]
pub struct CorpusFixture {
    /// Stable F-… identifier from `inventory.my`.
    pub id: String,
    /// Source expression text from `conformance.my`.
    pub source: String,
    /// Expected output string, or `None` when the fixture expects an error.
    pub expected: Option<String>,
    /// True when `(axioms . (S1 …))` appears in the conformance line.
    pub is_s1: bool,
}

/// Load and pair conformance.my + inventory.my.
///
/// Both files are read from `repo_root/tests/fixtures/`.  Returns an error
/// string if the files cannot be read, are malformed, or have different counts.
pub fn load_corpus(repo_root: &str) -> Result<Vec<CorpusFixture>, String> {
    let conformance_path = format!("{repo_root}/tests/fixtures/conformance.lisp");
    let inventory_path = format!("{repo_root}/tests/fixtures/inventory.lisp");

    let conformance_text = std::fs::read_to_string(&conformance_path)
        .map_err(|e| format!("cannot read {conformance_path}: {e}"))?;
    let inventory_text = std::fs::read_to_string(&inventory_path)
        .map_err(|e| format!("cannot read {inventory_path}: {e}"))?;

    // Collect top-level forms from each file (one fixture per form).
    let conformance_lines: Vec<&str> = conformance_text
        .lines()
        .filter(|l| {
            let t = l.trim();
            t.starts_with("((expr . ") || t.starts_with("((expr . \"")
        })
        .collect();

    let inventory_lines: Vec<&str> = inventory_text
        .lines()
        .filter(|l| l.trim().starts_with("(fixture "))
        .collect();

    if conformance_lines.len() != inventory_lines.len() {
        return Err(format!(
            "corpus/inventory count mismatch: conformance has {} fixtures, inventory has {}",
            conformance_lines.len(),
            inventory_lines.len()
        ));
    }

    let mut fixtures = Vec::with_capacity(conformance_lines.len());
    for (c_line, i_line) in conformance_lines.iter().zip(inventory_lines.iter()) {
        let source = parse_field(c_line, "expr")
            .ok_or_else(|| format!("conformance line missing (expr . \"...\") field: {c_line}"))?;
        let expected = parse_field(c_line, "expected");
        let is_s1 = c_line.contains("(axioms . (S1") || c_line.contains("(axioms S1");
        let id = parse_id_field(i_line)
            .ok_or_else(|| format!("inventory line missing (id . \"...\") field: {i_line}"))?;

        fixtures.push(CorpusFixture {
            id,
            source,
            expected,
            is_s1,
        });
    }

    Ok(fixtures)
}

fn parse_field(line: &str, field: &str) -> Option<String> {
    let marker = format!("({field} . \"");
    let start = line.find(&marker)? + marker.len();
    let rest = &line[start..];
    // Find the closing `"` that is not preceded by `\`
    let mut end = 0;
    let chars: Vec<char> = rest.chars().collect();
    let mut i = 0;
    while i < chars.len() {
        if chars[i] == '\\' {
            i += 2;
            continue;
        }
        if chars[i] == '"' {
            end = i;
            break;
        }
        i += 1;
    }
    Some(rest[..end].replace("\\\"", "\""))
}

fn parse_id_field(line: &str) -> Option<String> {
    // inventory format: (fixture (id . "F-...") ...)
    parse_field(line, "id")
}

// ── Export ────────────────────────────────────────────────────────────────────

/// The outcome of attempting to build an external-oracle export request.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExportOutcome {
    /// Ready to send to an external Wolfram Language host.
    Request {
        fixture_id: String,
        source_digest: String,
        query: String,
        expected: String,
    },
    /// This fixture cannot be projected for a declared reason.
    Unsupported {
        fixture_id: String,
        code: &'static str,
    },
}

/// Build an `external-oracle/1` export request for a single fixture.
///
/// Selects the fixture by `fixture_id` from the loaded corpus.  Only fixtures
/// that:
/// - have `(expected …)` (not an error fixture),
/// - are marked `S1`,
/// - contain only exact numeric literals and supported arithmetic semantic IDs,
/// - are a single top-level expression without effects, bindings, or host ops
///
/// will produce `ExportOutcome::Request`.  Everything else is
/// `ExportOutcome::Unsupported` with a stable code.
pub fn export_fixture(corpus: &[CorpusFixture], fixture_id: &str) -> ExportOutcome {
    let Some(fixture) = corpus.iter().find(|f| f.id == fixture_id) else {
        return ExportOutcome::Unsupported {
            fixture_id: fixture_id.to_string(),
            code: "external-oracle/fixture-not-found",
        };
    };

    let Some(ref expected) = fixture.expected else {
        return ExportOutcome::Unsupported {
            fixture_id: fixture_id.to_string(),
            code: "external-oracle/error-fixture",
        };
    };

    if !fixture.is_s1 {
        return ExportOutcome::Unsupported {
            fixture_id: fixture_id.to_string(),
            code: "external-oracle/not-s1",
        };
    }

    // Attempt to translate the source expression.
    match translate_source(&fixture.source) {
        Ok(query) => {
            let source_digest = sha256_hex(fixture.source.as_bytes());
            ExportOutcome::Request {
                fixture_id: fixture_id.to_string(),
                source_digest,
                query,
                expected: expected.clone(),
            }
        }
        Err(Unsupported { code }) => ExportOutcome::Unsupported {
            fixture_id: fixture_id.to_string(),
            code,
        },
    }
}

/// Render an `ExportOutcome::Request` as an `external-oracle/1` s-expression.
pub fn render_request(outcome: &ExportOutcome, contract_revision: (u32, u32)) -> String {
    match outcome {
        ExportOutcome::Request {
            fixture_id,
            source_digest,
            query,
            expected,
        } => {
            let (major, minor) = contract_revision;
            format!(
                "(external-oracle-request\n\
                 \x20 (protocol . external-oracle/1)\n\
                 \x20 (fixture-id . \"{fixture_id}\")\n\
                 \x20 (source-digest . \"{source_digest}\")\n\
                 \x20 (contract-revision . ({major} {minor}))\n\
                 \x20 (oracle . wolfram-language)\n\
                 \x20 (query . \"{query}\")\n\
                 \x20 (expected . \"{expected}\"))"
            )
        }
        ExportOutcome::Unsupported { fixture_id, code } => {
            format!(
                "(external-oracle-request\n\
                 \x20 (protocol . external-oracle/1)\n\
                 \x20 (fixture-id . \"{fixture_id}\")\n\
                 \x20 (outcome . unsupported)\n\
                 \x20 (code . \"{code}\"))"
            )
        }
    }
}

// ── Verify ────────────────────────────────────────────────────────────────────

/// The outcome of verifying an external oracle response against the corpus.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum VerifyOutcome {
    Pass,
    Mismatch { expected: String, actual: String },
    ProtocolError { reason: String },
}

/// Verify a raw `actual` result string against a corpus fixture's `expected`.
///
/// Performs exact canonical string comparison only — no decimal approximation.
pub fn verify_response(corpus: &[CorpusFixture], fixture_id: &str, actual: &str) -> VerifyOutcome {
    let Some(fixture) = corpus.iter().find(|f| f.id == fixture_id) else {
        return VerifyOutcome::ProtocolError {
            reason: format!("fixture {fixture_id} not found in corpus"),
        };
    };
    let Some(ref expected) = fixture.expected else {
        return VerifyOutcome::ProtocolError {
            reason: format!("fixture {fixture_id} is an error fixture, not verifiable by value"),
        };
    };
    if actual.trim() == expected.trim() {
        VerifyOutcome::Pass
    } else {
        VerifyOutcome::Mismatch {
            expected: expected.clone(),
            actual: actual.to_string(),
        }
    }
}

// ── Minimal SHA-256 hex (no external crate) ───────────────────────────────────

/// A tiny self-contained SHA-256 implementation so xtask stays dependency-free.
/// Only used for source-digest provenance, never for cryptographic security.
fn sha256_hex(data: &[u8]) -> String {
    // Round constants (first 32 bits of cube roots of first 64 primes)
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];
    // Initial hash values
    let mut h: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
        0x5be0cd19,
    ];
    // Pre-processing: add padding
    let bit_len = (data.len() as u64).wrapping_mul(8);
    let mut msg = data.to_vec();
    msg.push(0x80);
    while (msg.len() % 64) != 56 {
        msg.push(0x00);
    }
    msg.extend_from_slice(&bit_len.to_be_bytes());

    // Process each 512-bit chunk
    for chunk in msg.chunks(64) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            w[i] = u32::from_be_bytes(chunk[i * 4..i * 4 + 4].try_into().unwrap());
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }
        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh] = h;
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }
        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }
    h.iter()
        .map(|v| format!("{v:08x}"))
        .collect::<Vec<_>>()
        .join("")
}

// ── Internal AST translation (same logic as original, now non-test) ───────────

#[derive(Debug, Clone, PartialEq, Eq)]
struct Unsupported {
    code: &'static str,
}

impl Unsupported {
    const fn new(code: &'static str) -> Self {
        Self { code }
    }
}

fn translate_source(source: &str) -> Result<String, Unsupported> {
    let expressions =
        my_lisp::parse(source).map_err(|_| Unsupported::new("external-oracle/parse"))?;
    if expressions.len() != 1 {
        return Err(Unsupported::new("external-oracle/top-level-arity"));
    }
    translate_expr(&expressions[0])
}

fn translate_expr(expr: &Expr) -> Result<String, Unsupported> {
    match &expr.kind {
        ExprKind::Number(_number, Exactness::Inexact) => {
            Err(Unsupported::new("external-oracle/inexact-number"))
        }
        ExprKind::Number(number, Exactness::Exact) => {
            if number.is_finite()
                && number.fract() == 0.0
                && number.abs() <= 9_007_199_254_740_992.0
            {
                Ok(format!("{}", *number as i64))
            } else {
                Err(Unsupported::new(
                    "external-oracle/exact-number-representation",
                ))
            }
        }
        ExprKind::Rational(rational) => Ok(rational.to_string()),
        ExprKind::String(_) => Err(Unsupported::new("external-oracle/string")),
        ExprKind::Pair(_, _) => Err(Unsupported::new("external-oracle/pair")),
        ExprKind::NumericBuffer(_) => Err(Unsupported::new("external-oracle/numeric-buffer")),
        ExprKind::Symbol(_) => Err(Unsupported::new("external-oracle/bare-symbol")),
        ExprKind::List(items) => translate_call(items),
    }
}

fn translate_call(items: &[Expr]) -> Result<String, Unsupported> {
    let Some((head, arguments)) = items.split_first() else {
        return Err(Unsupported::new("external-oracle/empty-list"));
    };
    let ExprKind::Symbol(surface) = &head.kind else {
        return Err(Unsupported::new("external-oracle/non-symbol-head"));
    };

    let semantic_id = semantic_id_for_admitted_surface(surface)
        .ok_or_else(|| Unsupported::new("external-oracle/unknown-semantic-id"))?;

    let translated = arguments
        .iter()
        .map(translate_expr)
        .collect::<Result<Vec<_>, _>>()?;

    match semantic_id {
        12 => Ok(format!("Total[{{{}}}]", translated.join(", "))),
        13 => match translated.as_slice() {
            [] => Err(Unsupported::new("external-oracle/arity")),
            [only] => Ok(format!("Minus[{only}]")),
            _ => Ok(format!("Fold[Subtract, {{{}}}]", translated.join(", "))),
        },
        14 => Ok(format!("Times[{}]", translated.join(", "))),
        15 => match translated.as_slice() {
            [] => Err(Unsupported::new("external-oracle/arity")),
            [only] => Ok(format!("Divide[1, {only}]")),
            _ => Ok(format!("Fold[Divide, {{{}}}]", translated.join(", "))),
        },
        _ => Err(Unsupported::new("external-oracle/unknown-semantic-id")),
    }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::{
        export_fixture, load_corpus, render_request, translate_expr, translate_source,
        verify_response, ExportOutcome, VerifyOutcome,
    };
    use my_lisp::semantic_registry_export::admitted_surfaces_for_semantic_id;
    use my_lisp::{Exactness, Expr, ExprKind, NumericBuffer, Span};
    use std::rc::Rc;

    // ── AST translation (regression tests) ───────────────────────────────────

    #[test]
    fn nary_division_preserves_left_fold() {
        assert_eq!(
            translate_source("(/ 5 6 8 7)").unwrap(),
            "Fold[Divide, {5, 6, 8, 7}]"
        );
    }

    #[test]
    fn nested_division_remains_structurally_distinct() {
        assert_eq!(
            translate_source("(/ (/ 5 6) (/ 8 7))").unwrap(),
            "Fold[Divide, {Fold[Divide, {5, 6}], Fold[Divide, {8, 7}]}]"
        );
    }

    #[test]
    fn addition_uses_total_and_exact_zero_identity() {
        assert_eq!(translate_source("(+ 1 2 3)").unwrap(), "Total[{1, 2, 3}]");
        assert_eq!(translate_source("(+)").unwrap(), "Total[{}]");
    }

    #[test]
    fn multiplication_uses_times_and_exact_one_identity() {
        assert_eq!(translate_source("(* 2 3 4)").unwrap(), "Times[2, 3, 4]");
        assert_eq!(translate_source("(*)").unwrap(), "Times[]");
    }

    #[test]
    fn unary_subtraction_and_reciprocal_are_explicit() {
        assert_eq!(translate_source("(- 3)").unwrap(), "Minus[3]");
        assert_eq!(translate_source("(/ 4)").unwrap(), "Divide[1, 4]");
    }

    #[test]
    fn all_admitted_arithmetic_surfaces_project_by_semantic_identity() {
        let cases = [
            (12, "Total[{8, 2}]"),
            (13, "Fold[Subtract, {8, 2}]"),
            (14, "Times[8, 2]"),
            (15, "Fold[Divide, {8, 2}]"),
        ];

        for (semantic_id, expected) in cases {
            let surfaces = admitted_surfaces_for_semantic_id(semantic_id);
            assert!(
                !surfaces.is_empty(),
                "semantic identity {semantic_id} must have admitted surfaces"
            );
            for surface in surfaces {
                let source = format!("({} 8 2)", surface.name);
                assert_eq!(
                    translate_source(&source).unwrap(),
                    expected,
                    "surface {} in namespace {} must project through semantic identity {}",
                    surface.name,
                    surface.namespace,
                    semantic_id
                );
            }
        }
    }

    #[test]
    fn source_must_contain_exactly_one_top_level_expression() {
        let error = translate_source("(+ 1 2) (* 3 4)").unwrap_err();
        assert_eq!(error.code, "external-oracle/top-level-arity");
    }

    #[test]
    fn unsupported_ast_kinds_fail_closed_with_stable_codes() {
        let span = Span::default();
        let exact_one = || Expr {
            kind: ExprKind::Number(1.0, Exactness::Exact),
            span,
        };

        let cases = [
            (
                Expr {
                    kind: ExprKind::Number(0.5, Exactness::Inexact),
                    span,
                },
                "external-oracle/inexact-number",
            ),
            (
                Expr {
                    kind: ExprKind::String(Rc::from("text")),
                    span,
                },
                "external-oracle/string",
            ),
            (
                Expr {
                    kind: ExprKind::Pair(Rc::new(exact_one()), Rc::new(exact_one())),
                    span,
                },
                "external-oracle/pair",
            ),
            (
                Expr {
                    kind: ExprKind::NumericBuffer(NumericBuffer::I32(vec![1].into())),
                    span,
                },
                "external-oracle/numeric-buffer",
            ),
            (
                Expr {
                    kind: ExprKind::Symbol(Rc::from("x")),
                    span,
                },
                "external-oracle/bare-symbol",
            ),
        ];

        for (expr, expected_code) in cases {
            let error = translate_expr(&expr).unwrap_err();
            assert_eq!(error.code, expected_code);
        }
    }

    #[test]
    fn unknown_operation_fails_closed_instead_of_guessing_by_spelling() {
        let error = translate_source("(mystery-op 1 2)").unwrap_err();
        assert_eq!(error.code, "external-oracle/unknown-semantic-id");
    }

    // ── Corpus loading ────────────────────────────────────────────────────────

    #[test]
    fn corpus_loads_and_target_fixture_is_present() {
        // repo root is two levels up from crates/xtask
        let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
        let corpus = load_corpus(repo_root).expect("corpus must load without error");
        assert!(!corpus.is_empty(), "corpus must not be empty");
        let target = corpus.iter().find(|f| f.id == "F-8bc31cae9e7e39b9");
        assert!(
            target.is_some(),
            "target fixture F-8bc31cae9e7e39b9 must be present"
        );
        let f = target.unwrap();
        assert_eq!(f.source.trim(), "(/ 5 6 8 7)");
        assert_eq!(f.expected.as_deref(), Some("5/336"));
        assert!(f.is_s1, "target fixture must be S1");
    }

    #[test]
    fn export_target_fixture_produces_correct_wolfram_query() {
        let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
        let corpus = load_corpus(repo_root).expect("corpus must load");
        let outcome = export_fixture(&corpus, "F-8bc31cae9e7e39b9");
        assert!(
            matches!(outcome, ExportOutcome::Request { ref query, .. } if query == "Fold[Divide, {5, 6, 8, 7}]"),
            "expected Fold[Divide, {{5, 6, 8, 7}}], got {outcome:?}"
        );
    }

    #[test]
    fn export_missing_fixture_is_unsupported() {
        let corpus = vec![];
        let outcome = export_fixture(&corpus, "F-nonexistent");
        assert_eq!(
            outcome,
            ExportOutcome::Unsupported {
                fixture_id: "F-nonexistent".into(),
                code: "external-oracle/fixture-not-found"
            }
        );
    }

    #[test]
    fn export_error_fixture_is_unsupported() {
        let corpus = vec![super::CorpusFixture {
            id: "F-error".into(),
            source: "(/ 1 0)".into(),
            expected: None, // error fixture
            is_s1: true,
        }];
        let outcome = export_fixture(&corpus, "F-error");
        assert_eq!(
            outcome,
            ExportOutcome::Unsupported {
                fixture_id: "F-error".into(),
                code: "external-oracle/error-fixture"
            }
        );
    }

    #[test]
    fn export_non_s1_fixture_is_unsupported() {
        let corpus = vec![super::CorpusFixture {
            id: "F-g2".into(),
            source: "(cons 1 2)".into(),
            expected: Some("(1 . 2)".into()),
            is_s1: false,
        }];
        let outcome = export_fixture(&corpus, "F-g2");
        assert_eq!(
            outcome,
            ExportOutcome::Unsupported {
                fixture_id: "F-g2".into(),
                code: "external-oracle/not-s1"
            }
        );
    }

    #[test]
    fn render_request_produces_well_formed_sexp() {
        let outcome = ExportOutcome::Request {
            fixture_id: "F-8bc31cae9e7e39b9".into(),
            source_digest: "abc123".into(),
            query: "Fold[Divide, {5, 6, 8, 7}]".into(),
            expected: "5/336".into(),
        };
        let rendered = render_request(&outcome, (6, 0));
        assert!(rendered.contains("(protocol . external-oracle/1)"));
        assert!(rendered.contains("(fixture-id . \"F-8bc31cae9e7e39b9\")"));
        assert!(rendered.contains("(oracle . wolfram-language)"));
        assert!(rendered.contains("Fold[Divide, {5, 6, 8, 7}]"));
        assert!(rendered.contains("5/336"));
    }

    // ── Verify ────────────────────────────────────────────────────────────────

    #[test]
    fn verify_pass_when_actual_matches_expected() {
        let corpus = vec![super::CorpusFixture {
            id: "F-test".into(),
            source: "(/ 5 6 8 7)".into(),
            expected: Some("5/336".into()),
            is_s1: true,
        }];
        assert_eq!(
            verify_response(&corpus, "F-test", "5/336"),
            VerifyOutcome::Pass
        );
    }

    #[test]
    fn verify_mismatch_when_actual_differs() {
        let corpus = vec![super::CorpusFixture {
            id: "F-test".into(),
            source: "(/ 5 6 8 7)".into(),
            expected: Some("5/336".into()),
            is_s1: true,
        }];
        assert_eq!(
            verify_response(&corpus, "F-test", "35/48"),
            VerifyOutcome::Mismatch {
                expected: "5/336".into(),
                actual: "35/48".into()
            }
        );
    }

    #[test]
    fn verify_mismatch_proves_two_trees_are_distinct() {
        // Core regression: (/ 5 6 8 7) and (/ (/ 5 6) (/ 8 7)) have DIFFERENT
        // expected values -- Wolfram returning 35/48 for the nested form is correct,
        // not a mismatch for that fixture.
        let corpus = vec![super::CorpusFixture {
            id: "F-nested".into(),
            source: "(/ (/ 5 6) (/ 8 7))".into(),
            expected: Some("35/48".into()),
            is_s1: true,
        }];
        assert_eq!(
            verify_response(&corpus, "F-nested", "35/48"),
            VerifyOutcome::Pass
        );
        // But 5/336 would be wrong for this tree
        assert!(matches!(
            verify_response(&corpus, "F-nested", "5/336"),
            VerifyOutcome::Mismatch { .. }
        ));
    }
}
