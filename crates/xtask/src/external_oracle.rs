//! Exact arithmetic AST projection for WSM-5's independent external oracle.
//!
//! This layer does not interpret arithmetic by spelling and does not evaluate
//! sens. It parses one source expression, resolves the operator through the
//! authoritative semantic registry, and projects the exact AST shape into a
//! Wolfram Language expression. Unsupported input fails closed with stable
//! codes instead of being approximated.
//!
//! ## Corpus loading
//!
//! `load_corpus()` reads the active `tests/fixtures/conformance.lisp` source.
//! The retired generated inventory is not consulted. An explicit `(id . \"F-…\")`
//! field preserves a published fixture identity; other rows receive deterministic
//! content-derived IDs for this external-oracle transport only.
//!
//! ## Export
//!
//! `export_fixture()` selects a single fixture by `F-…` id and produces a
//! versioned `external-oracle/1` request s-expression ready for an external
//! Wolfram Language host.

use sens::semantic_registry_export::admitted_core_domain_for_surface;
use sens::{Exactness, Expr, ExprKind};

// ── Public corpus types ───────────────────────────────────────────────────────

/// One fixture as read from the corpus pair.
#[derive(Debug, Clone)]
pub struct CorpusFixture {
    /// Explicit or content-derived F-… identifier for this fixture record.
    pub id: String,
    /// Source expression text from `conformance.lisp`.
    pub source: String,
    /// Expected output string, or `None` when the fixture expects an error.
    pub expected: Option<String>,
    /// True when `(axioms . (S1 …))` appears in the conformance line.
    pub is_s1: bool,
}

/// Load the current conformance corpus without relying on the retired inventory projection.
///
/// Rows are source records from `tests/fixtures/conformance.lisp`. Stable fixture
/// IDs are metadata, not semantics: use an explicit `(id . "F-…")` when a
/// published identity must be preserved; otherwise derive the ID from the exact
/// UTF-8 record bytes. Duplicate IDs fail closed rather than aliasing fixtures.
pub fn load_corpus(repo_root: &str) -> Result<Vec<CorpusFixture>, String> {
    let conformance_path = format!("{repo_root}/tests/fixtures/conformance.lisp");
    let conformance_text = std::fs::read_to_string(&conformance_path)
        .map_err(|e| format!("cannot read {conformance_path}: {e}"))?;

    let mut fixtures = Vec::new();
    let mut seen_ids = std::collections::BTreeSet::new();

    for line in conformance_text.lines() {
        let record = line.trim();
        if !record.starts_with("((expr . ") {
            continue;
        }

        let source = parse_field(record, "expr")
            .ok_or_else(|| format!("conformance line missing (expr . \"...\") field: {record}"))?;
        let expected = parse_field(record, "expected");
        let is_s1 = record.contains("(axioms . (S1") || record.contains("(axioms S1");
        let id = parse_field(record, "id").unwrap_or_else(|| content_fixture_id(record));

        if !seen_ids.insert(id.clone()) {
            return Err(format!("duplicate fixture id {id} in {conformance_path}"));
        }

        fixtures.push(CorpusFixture {
            id,
            source,
            expected,
            is_s1,
        });
    }

    Ok(fixtures)
}

fn content_fixture_id(record: &str) -> String {
    let digest = sens::sha256_source(record.as_bytes());
    let short_hex: String = digest[..8]
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect();
    format!("F-{short_hex}")
}

fn parse_field(line: &str, field: &str) -> Option<String> {
    let marker = format!("({field} . \"");
    let start = line.find(&marker)? + marker.len();
    let rest = &line[start..];
    // `char_indices` yields UTF-8 byte offsets, which are the offsets required
    // for slicing `str`; character counts panic on Ukrainian surface text.
    let mut end = None;
    let mut escaped = false;
    for (byte_index, ch) in rest.char_indices() {
        if escaped {
            escaped = false;
            continue;
        }
        if ch == '\\' {
            escaped = true;
        } else if ch == '"' {
            end = Some(byte_index);
            break;
        }
    }
    Some(rest[..end?].replace("\\\"", "\""))
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
    let expressions = sens::parse(source).map_err(|_| Unsupported::new("external-oracle/parse"))?;
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
        // BinaryNumber identity stays its exact normalized bits inside SENS.
        // The external Wolfram oracle receives only an exact decimal projection;
        // conversion is arbitrary-width and never passes through a host integer.
        ExprKind::BinaryNumber(number) => Ok(number.to_decimal_string()),
        ExprKind::Sid(sid) => Ok(sid.to_string()),
        ExprKind::DomainIdentity(_) => Err(Unsupported::new("external-oracle/domain-identity")),
        ExprKind::String(_) => Err(Unsupported::new("external-oracle/string")),
        ExprKind::Pair(_, _) => Err(Unsupported::new("external-oracle/pair")),
        ExprKind::NumericBuffer(_) => Err(Unsupported::new("external-oracle/numeric-buffer")),
        ExprKind::Symbol(_) => Err(Unsupported::new("external-oracle/bare-symbol")),
        ExprKind::List(items) => translate_call(items),
        // Парсер не породжує зведених викликів; сюди надходить лише parse().
        ExprKind::Call(_, _) => Err(Unsupported::new("external-oracle/lowered-call")),
        ExprKind::DomainCall(_, _) => Err(Unsupported::new("external-oracle/domain-lowered-call")),
        ExprKind::Local { .. } => Err(Unsupported::new("external-oracle/slot-local")),
    }
}

fn translate_call(items: &[Expr]) -> Result<String, Unsupported> {
    let Some((head, arguments)) = items.split_first() else {
        return Err(Unsupported::new("external-oracle/empty-list"));
    };
    let ExprKind::Symbol(surface) = &head.kind else {
        return Err(Unsupported::new("external-oracle/non-symbol-head"));
    };

    // `divmod` is a Core Lisp library closure, not a directly callable D9
    // resident. Keep that library operation distinct from D5 `частка` and
    // never infer D9 callability from residency.
    let is_core_divmod_library = surface.as_ref() == "divmod";
    let identity = admitted_core_domain_for_surface(surface);
    if identity.is_none() && !is_core_divmod_library {
        return Err(Unsupported::new("external-oracle/unknown-semantic-id"));
    }

    // External projection follows current callable identities from the domain
    // ladder. D5 `частка` is exact rational division; it is not integer
    // quotient-with-remainder. D8 `поділити` residency alone still does not
    // admit a direct callable route.
    let add = admitted_core_domain_for_surface("додати");
    let subtract = admitted_core_domain_for_surface("відняти");
    let multiply = admitted_core_domain_for_surface("помножити");
    let exact_divide = admitted_core_domain_for_surface("частка");

    let translated = arguments
        .iter()
        .map(translate_expr)
        .collect::<Result<Vec<_>, _>>()?;

    if is_core_divmod_library {
        match translated.as_slice() {
            [dividend, divisor] => Ok(format!(
                "{{Quotient[{dividend}, {divisor}], Mod[{dividend}, {divisor}]}}"
            )),
            _ => Err(Unsupported::new("external-oracle/arity")),
        }
    } else if identity == add {
        Ok(format!("Total[{{{}}}]", translated.join(", ")))
    } else if identity == subtract {
        match translated.as_slice() {
            [] => Err(Unsupported::new("external-oracle/arity")),
            [only] => Ok(format!("Minus[{only}]")),
            _ => Ok(format!("Fold[Subtract, {{{}}}]", translated.join(", "))),
        }
    } else if identity == multiply {
        Ok(format!("Times[{}]", translated.join(", ")))
    } else if identity == exact_divide {
        match translated.as_slice() {
            [] => Err(Unsupported::new("external-oracle/arity")),
            [only] => Ok(format!("Divide[1, {only}]")),
            [dividend, divisor] => Ok(format!("Divide[{dividend}, {divisor}]")),
            _ => Err(Unsupported::new("external-oracle/arity")),
        }
    } else {
        Err(Unsupported::new("external-oracle/unknown-semantic-id"))
    }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

