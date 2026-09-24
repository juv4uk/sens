use crate::value::{NumericBuffer, Rational};
use crate::Sid8;
use std::{cell::Cell, fmt, ops::Deref, rc::Rc};

/// Byte range in the original UTF-8 source.
/// Diapazon baitiv u pochatkovomu teksti UTF-8.
/// Bytebereich im ursprünglichen UTF-8-Quelltext.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Span {
    pub start: usize,
    pub end: usize,
}

#[derive(Clone, Debug, PartialEq)]
pub struct Expr {
    pub kind: ExprKind,
    pub span: Span,
}


/// Proper-list reader/executable structure.
///
/// `resolved_head_sid` is deliberately not semantic data and is excluded
/// from equality, debug output and FASL serialization. It is a one-way
/// mechanical cache populated only after the evaluator has proved that this
/// executable list head denotes an immutable language identity.
///
/// The source spelling remains in `items` for diagnostics/source fidelity;
/// execution may stop consulting it once `resolved_head_sid` is present.
/// See issue #1320 for the one-way surface -> SID execution invariant.
pub struct ExprList {
    items: Rc<[Expr]>,
    resolved_head_sid: Cell<Option<Sid8>>,
}

impl ExprList {
    pub(crate) fn resolved_head_sid(&self) -> Option<Sid8> {
        self.resolved_head_sid.get()
    }

    pub(crate) fn cache_resolved_head_sid(&self, sid: Sid8) {
        match self.resolved_head_sid.get() {
            Some(existing) => {
                debug_assert_eq!(
                    existing, sid,
                    "one executable list must never resolve to two SID identities"
                );
            }
            None => self.resolved_head_sid.set(Some(sid)),
        }
    }
}

impl Clone for ExprList {
    fn clone(&self) -> Self {
        Self {
            items: self.items.clone(),
            resolved_head_sid: Cell::new(self.resolved_head_sid.get()),
        }
    }
}

impl PartialEq for ExprList {
    fn eq(&self, other: &Self) -> bool {
        self.items == other.items
    }
}

impl fmt::Debug for ExprList {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.debug_tuple("ExprList").field(&self.items).finish()
    }
}

impl Deref for ExprList {
    type Target = [Expr];

    fn deref(&self) -> &Self::Target {
        &self.items
    }
}

impl AsRef<[Expr]> for ExprList {
    fn as_ref(&self) -> &[Expr] {
        &self.items
    }
}

impl From<Vec<Expr>> for ExprList {
    fn from(items: Vec<Expr>) -> Self {
        Self {
            items: items.into(),
            resolved_head_sid: Cell::new(None),
        }
    }
}

impl From<Box<[Expr]>> for ExprList {
    fn from(items: Box<[Expr]>) -> Self {
        Self {
            items: items.into(),
            resolved_head_sid: Cell::new(None),
        }
    }
}

impl From<Rc<[Expr]>> for ExprList {
    fn from(items: Rc<[Expr]>) -> Self {
        Self {
            items,
            resolved_head_sid: Cell::new(None),
        }
    }
}

/// Whether a numeric value is a precise quantity or a floating-point
/// approximation — a property of the value itself (PLAN.md item 10, Path A),
/// not of how it happens to print. Set once at the reader (every literal is
/// exact by default — integers, `n/d` rationals, and finite decimal/scientific
/// literals like `0.5` or `1e-3` all read as exact values per axiom S1) and
/// propagated by arithmetic's promotion rule (`Exact ⊕ Exact → Exact`, anything
/// touching `Inexact` → `Inexact`), never re-guessed from a result's shape.
/// `Inexact` values currently only arise from explicit runtime sources (e.g.
/// wall-clock timing), not from literal syntax; the future `(float ...)`
/// operation is the intended explicit way to opt into them.
/// Chy ye chyslove znachennia tochnoiu velychynoiu, chy nablyzhenniam iz plavaiuchoiu
/// komoiu — vlastyvist samoho znachennia (PLAN.md, punkt 10, shliakh A), ne
/// toho, yak vono drukuietsia. Vstanovliuietsia odyn raz u readeri (kozhen
/// literal tochnyi za zamovchuvanniam — tsili, `n/d`-ratsionalni ta skinchenni
/// desiatkovi/eksponentsiini literaly na kshtalt `0.5` chy `1e-3` chytaiutsia
/// yak tochni znachennia za aksiomoiu S1) i poshyriuietsia pravylom promotion v
/// aryfmetytsi (`Exact ⊕ Exact → Exact`, bud-yakyi dotyk do `Inexact` →
/// `Inexact`), nikoly ne vhaduietsia zanovo z formy rezultatu. Znachennia
/// `Inexact` nyni vynykaiut lyshe z yavnykh dzherel u chasi vykonannia
/// (napryklad, pomir chasu), ne z syntaksysu literala; maibutnia operatsiia
/// `(float ...)` — ye zatverdzhenyi sposib svidomoho perekhodu v ne-toche.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Exactness {
    Exact,
    Inexact,
}

#[derive(Clone, Debug, PartialEq)]
pub enum ExprKind {
    Number(f64, Exactness),
    Rational(Rational),
    NumericBuffer(NumericBuffer),
    Sid(Sid8),
    String(Rc<str>),
    Symbol(Rc<str>),
    List(ExprList),
    /// A reader-level dotted pair, `(a . b)` — distinct from `List` because a
    /// proper list is nil-terminated and an improper one isn't. Only ever
    /// produced by a literal `.` between exactly two sub-expressions inside
    /// parentheses; never appears as executable code (only inside `quote`,
    /// or wherever a reader/`read`-style caller asks for data).
    /// Dotted-para na rivni readera, `(a . b)` — okremo vid `List`, bo
    /// pravylnyi spysok nil-terminovanyi, a nepravylnyi — ni. Ziavliaietsia
    /// lyshe cherez literalnu `.` mizh rivno dvoma pid-vyrazamy vseredyni
    /// duzhok; nikoly ne ziavliaietsia yak vykonuvanyi kod (lyshe vseredyni
    /// `quote`, chy de zavhodno, de vyklykach chytaie tse yak dani cherez `read`).
    /// Ein Reader-level Dotted Pair, `(a . b)` — getrennt von `List`, weil
    /// eine korrekte Liste nil-terminiert ist, eine unkorrekte nicht. Wird
    /// nur durch einen literalen `.` zwischen genau zwei Teilausdrücken
    /// innerhalb von Klammern erzeugt; erscheint nie als ausführbarer Code
    /// (nur innerhalb von `quote`, oder wo ein Aufrufer es über `read` als
    /// Daten liest).
    Pair(Rc<Expr>, Rc<Expr>),
}

/// Shared nesting cap for every recursive structure walk over reader
/// output: the parser itself, `quote`d-data conversion (`quoted`) and
/// value→expr lowering (`value_to_expr`). Mirrors the JSON decoder's
/// defense; past this the language fails named instead of overflowing
/// the native stack and killing the host process.
// Keep a safety margin below the native test-thread stack ceiling. The old
// 1024 value sat on that ceiling and could overflow before returning its named
// error when an additive Expr variant changed compiler frame layout.
pub(crate) const MAX_STRUCTURE_DEPTH: u32 = 768;

/// FASL snapshot encoding — parse-output cache (OPT-CORE-MY-AST-SNAPSHOT).
/// Deterministic, versioned; decode returns None on ANY inconsistency so
/// callers fall back to text parsing (never a wrong program).
pub(crate) mod fasl {
    use super::{Exactness, Expr, ExprKind};
    use crate::value::Rational;
    use std::rc::Rc;

    pub const FASL_FORMAT_VERSION: u32 = 3;

    const TAG_NUMBER: u8 = 1;
    const TAG_RATIONAL: u8 = 2;
    const TAG_STRING: u8 = 3;
    const TAG_SYMBOL: u8 = 4;
    const TAG_LIST: u8 = 5;
    const TAG_PAIR: u8 = 6;
    const TAG_BINARY: u8 = 7;

    fn put_u32(out: &mut Vec<u8>, v: u32) {
        out.extend_from_slice(&v.to_le_bytes());
    }

    fn put_str(out: &mut Vec<u8>, s: &str) {
        put_u32(out, s.len() as u32);
        out.extend_from_slice(s.as_bytes());
    }

    fn get_u32(bytes: &[u8], pos: &mut usize) -> Option<u32> {
        let slice = bytes.get(*pos..*pos + 4)?;
        *pos += 4;
        Some(u32::from_le_bytes(slice.try_into().ok()?))
    }

    fn get_str<'a>(bytes: &'a [u8], pos: &mut usize) -> Option<&'a str> {
        let len = get_u32(bytes, pos)? as usize;
        let slice = bytes.get(*pos..*pos + len)?;
        *pos += len;
        std::str::from_utf8(slice).ok()
    }

    pub(crate) fn encode_expr(expr: &Expr, out: &mut Vec<u8>) {
        match &expr.kind {
            ExprKind::Number(f, exactness) => {
                out.push(TAG_NUMBER);
                out.extend_from_slice(&f.to_le_bytes());
                out.push(matches!(exactness, Exactness::Inexact) as u8);
            }
            ExprKind::Rational(rational) => {
                out.push(TAG_RATIONAL);
                rational.write_fasl(out);
            }
            ExprKind::Sid(sid) => {
                out.push(TAG_BINARY);
                out.push(sid.packed_byte());
            }
            ExprKind::String(value) => {
                out.push(TAG_STRING);
                put_str(out, value);
            }
            ExprKind::Symbol(symbol) => {
                out.push(TAG_SYMBOL);
                put_str(out, symbol);
            }
            ExprKind::List(items) => {
                out.push(TAG_LIST);
                put_u32(out, items.len() as u32);
                for item in items.iter() {
                    encode_expr(item, out);
                }
            }
            ExprKind::Pair(head, tail) => {
                out.push(TAG_PAIR);
                encode_expr(head, out);
                encode_expr(tail, out);
            }
            // Runtime-constructed buffers are not source syntax; a program
            // containing one cannot come from lib/*.my text, so snapshots
            // refuse them and callers fall back to parsing.
            ExprKind::NumericBuffer(_) => {
                unreachable!("NumericBuffer is runtime-only, never parsed")
            }
        }
    }

    fn decode_expr(bytes: &[u8], pos: &mut usize) -> Option<Expr> {
        let tag = *bytes.get(*pos)?;
        *pos += 1;
        let kind = match tag {
            TAG_NUMBER => {
                let bits = bytes.get(*pos..*pos + 8)?;
                *pos += 8;
                let exact = match bytes.get(*pos)? {
                    0 => Exactness::Exact,
                    1 => Exactness::Inexact,
                    _ => return None,
                };
                *pos += 1;
                ExprKind::Number(f64::from_le_bytes(bits.try_into().ok()?), exact)
            }
            TAG_RATIONAL => ExprKind::Rational(Rational::read_fasl(bytes, pos)?),
            TAG_BINARY => {
                let value = *bytes.get(*pos)?;
                *pos += 1;
                ExprKind::Sid(crate::Sid8::from_packed_byte(value))
            }
            TAG_STRING => ExprKind::String(get_str(bytes, pos)?.into()),
            TAG_SYMBOL => ExprKind::Symbol(get_str(bytes, pos)?.into()),
            TAG_LIST => {
                let count = get_u32(bytes, pos)? as usize;
                let mut items = Vec::with_capacity(count.min(1 << 22));
                for _ in 0..count {
                    items.push(decode_expr(bytes, pos)?);
                }
                ExprKind::List(items.into())
            }
            TAG_PAIR => {
                let head = decode_expr(bytes, pos)?;
                let tail = decode_expr(bytes, pos)?;
                ExprKind::Pair(Rc::new(head), Rc::new(tail))
            }
            _ => return None,
        };
        // Spans are debug metadata only; the snapshot records position zero.
        Some(Expr {
            kind,
            span: crate::Span { start: 0, end: 0 },
        })
    }

    /// Header: magic + format version + payload length. Source-hash is the
    /// CALLER's invalidation contract and is stored/checked outside.
    pub fn encode_program(expressions: &[Expr], source_hash: &[u8; 32]) -> Vec<u8> {
        let mut payload = Vec::new();
        put_u32(&mut payload, FASL_FORMAT_VERSION);
        payload.extend_from_slice(source_hash);
        put_u32(&mut payload, expressions.len() as u32);
        for expr in expressions {
            encode_expr(expr, &mut payload);
        }
        let mut out = b"MYF1".to_vec();
        put_u32(&mut out, payload.len() as u32);
        out.extend_from_slice(&payload);
        out
    }

    pub fn decode_program(bytes: &[u8]) -> Option<(Vec<Expr>, [u8; 32])> {
        if bytes.get(0..4)? != b"MYF1" {
            return None;
        }
        // Layout: magic | payload_len | version | source_hash | count | exprs
        let mut pos = 4;
        let payload_len = get_u32(bytes, &mut pos)? as usize;
        if bytes.len() != pos + payload_len {
            return None;
        }
        if get_u32(bytes, &mut pos)? != FASL_FORMAT_VERSION {
            return None;
        }
        let source_hash: [u8; 32] = bytes.get(pos..pos + 32)?.try_into().ok()?;
        pos += 32;
        let count = get_u32(bytes, &mut pos)? as usize;
        let mut out = Vec::with_capacity(count.min(1 << 16));
        for _ in 0..count {
            out.push(decode_expr(bytes, &mut pos)?);
        }
        if pos != 8 + payload_len {
            return None;
        }
        Some((out, source_hash))
    }
}

#[cfg(test)]
mod fasl_tests {
    use super::fasl::{decode_program, encode_program};
    use super::ExprKind;
    use crate::parser::parse;
    use crate::sha256_source;

    const SAMPLE: &str = r#"
(def rat-loop
  (lambda (n acc)
    (cond ((= n 0) acc)
          (t (rat-loop (- n 1) (+ acc (/ (* n n) (+ (* n 3) 1))))))))
(print (/ 1 3))
(print 0.25)
(print -42/7777)
(print "рядок з кирилицею")
(quote (a b . c))
"#;

    #[test]
    fn fasl_round_trip_is_byte_identical_and_hash_bound() {
        let source_hash = sha256_source(SAMPLE.as_bytes());
        let expressions = parse(SAMPLE).expect("parse sample");
        let encoded = encode_program(&expressions, &source_hash);

        let (decoded, decoded_hash) = decode_program(&encoded).expect("decode should succeed");
        assert_eq!(decoded_hash, source_hash, "embedded hash must survive");

        // Structural equality: re-encoding the decode output must be
        // byte-identical to the original encoding.
        let re_encoded = encode_program(&decoded, &source_hash);
        assert_eq!(re_encoded, encoded);
    }

    #[test]
    fn resolved_head_cache_is_not_ast_identity_or_fasl_data() {
        const SOURCE: &str = "(car (quote (1 2)))";
        let source_hash = sha256_source(SOURCE.as_bytes());
        let expressions = parse(SOURCE).expect("source parses");
        let structurally_equal = expressions.clone();
        let before = encode_program(&expressions, &source_hash);

        let ExprKind::List(items) = &expressions[0].kind else {
            panic!("expected executable list");
        };
        items.cache_resolved_head_sid(crate::sid!(00000101));

        assert_eq!(
            expressions, structurally_equal,
            "mechanical resolved-head cache must not change AST identity"
        );
        assert_eq!(
            encode_program(&expressions, &source_hash),
            before,
            "FASL must serialize source structure, never runtime resolution cache"
        );
    }

    #[test]
    fn fasl_preserves_large_exact_integer_past_f64_boundary() {
        const SOURCE: &str = "9007199254740993";
        let source_hash = sha256_source(SOURCE.as_bytes());
        let expressions = parse(SOURCE).expect("large exact integer parses");
        assert!(matches!(expressions[0].kind, ExprKind::Rational(_)));

        let encoded = encode_program(&expressions, &source_hash);
        let (decoded, decoded_hash) =
            decode_program(&encoded).expect("large exact integer FASL decodes");
        assert_eq!(decoded_hash, source_hash);

        let ExprKind::Rational(rational) = &decoded[0].kind else {
            panic!("2^53 + 1 must remain Rational across FASL");
        };
        assert_eq!(rational.to_string(), SOURCE);
        assert_eq!(encode_program(&decoded, &source_hash), encoded);
    }

    #[test]
    fn fasl_rejects_tampered_hash_so_callers_fall_back() {
        let source_hash = sha256_source(SAMPLE.as_bytes());
        let expressions = parse(SAMPLE).expect("parse sample");
        let mut encoded = encode_program(&expressions, &source_hash);
        // flip one hash byte in the header region (offset 8..40)
        let hpos = 12; // magic4 + ver4 + hash starts at 8? layout: magic(4)+len(4)+ver(4)+hash32
        encoded[hpos] ^= 0xFF;
        let other = sha256_source(b"different source");
        let _ = other;
        // decode still succeeds structurally; the CALLER compares hashes and
        // falls back — so here we only assert the hash came back tampered.
        let (_, decoded_hash) = decode_program(&encoded).expect("structural decode");
        assert_ne!(decoded_hash, source_hash);
    }

    #[test]
    fn fasl_rejects_garbage() {
        assert!(decode_program(b"not a fasl at all").is_none());
        assert!(decode_program(&[]).is_none());
    }
}
