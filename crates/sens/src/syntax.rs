use crate::value::{NumericBuffer, Rational};
use crate::CoreDomainIdentity;
use crate::Sens8;
use std::rc::Rc;

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
    /// Legacy exact-eight compatibility identity. New canonical Core identity
    /// uses `DomainIdentity`; this variant remains for historical parser,
    /// FASL/wire, and backend paths during #2817 migration.
    Sid(Sens8),
    /// Canonical domain-qualified Core identity. Width/domain is part of
    /// identity; equal packed payloads in D3/D4/D5/D6 do not collapse.
    DomainIdentity(CoreDomainIdentity),
    String(Rc<str>),
    Symbol(Rc<str>),
    List(Rc<[Expr]>),
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
    /// Виклик функції СЕНС: функція займає рівно 1 байт (`Sens8`), без
    /// тексту імені. Створюється лише `eval::lower` після розбору — з голови
    /// `(00000010 x)` або з написання, яке неможливо перевизначити
    /// (`atom`, `атом?`, `aṇu` ...), тож усі написання однієї функції
    /// дають один і той самий вузол. Парсер цей варіант не породжує.
    /// SENS call: the function slot is exactly one byte (`Sens8`), no name
    /// text. Produced only by `eval::lower` after parsing.
    Call(Sens8, Rc<[Expr]>),
    /// Canonical lowered call head. Construction of this node does not itself
    /// grant callability: lowering/routing may create it only after the
    /// corresponding domain law admits the identity as callable.
    DomainCall(CoreDomainIdentity, Rc<[Expr]>),
    /// Параметр замикання за числовими координатами: слот `index` кадру
    /// виклику на `depth` кадрів вище. Імені тут немає навмисно (#1697,
    /// контракт 10.0 `locals-are-slots-not-names`): виконання залежить лише від
    /// координат; людські імена лишаються в `Closure::slot_names` як
    /// налагоджувальні метадані. Створює лише розв'язувач тіла `lambda`
    /// (`eval::closures`); парсер його не породжує. fasl і wire записують
    /// саме координати.
    /// A closure parameter by numeric lexical coordinates only; the human name
    /// lives in the closure's debug metadata, never in the node.
    Local { depth: u32, index: u32 },
}

// Коробка для функції СЕНС — рівно 1 байт. Якщо це колись зміниться,
// збірка має впасти, а не мовчки розійтися з таблицею функцій.
const _: () = assert!(std::mem::size_of::<Sens8>() == 1);

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
    use crate::value::{NumericBuffer, Rational};
    use std::rc::Rc;
    use std::sync::Arc;

    pub const FASL_FORMAT_VERSION: u32 = 3;

    const TAG_NUMBER: u8 = 1;
    const TAG_RATIONAL: u8 = 2;
    const TAG_STRING: u8 = 3;
    const TAG_SYMBOL: u8 = 4;
    const TAG_LIST: u8 = 5;
    const TAG_PAIR: u8 = 6;
    const TAG_BINARY: u8 = 7;
    // Адитивні v3 tags: старі snapshots лишаються байт-в-байт незмінними,
    // а старий decoder fail-closed відхилить новий tag як невідомий.
    const TAG_I32_BUFFER: u8 = 8;
    const TAG_F32_BUFFER: u8 = 9;
    // #1697: числові координати локальної змінної; ім'я не записується.
    const TAG_LOCAL: u8 = 10;
    // #2840: domain-qualified Core identity, encoded as exact domain width
    // followed by its packed payload. Old decoders fail closed on this tag.
    const TAG_DOMAIN_IDENTITY: u8 = 11;

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

    fn put_domain_identity(out: &mut Vec<u8>, identity: crate::CoreDomainIdentity) {
        let tag = match identity {
            crate::CoreDomainIdentity::D1(_) => 1,
            crate::CoreDomainIdentity::D2(_) => 2,
            crate::CoreDomainIdentity::D3(_) => 3,
            crate::CoreDomainIdentity::D4(_) => 4,
            crate::CoreDomainIdentity::D5(_) => 5,
            crate::CoreDomainIdentity::D6(_) => 6,
            crate::CoreDomainIdentity::D7Sound(_) => 0x71,
            crate::CoreDomainIdentity::D7LocalOrdinal(_) => 0x72,
            crate::CoreDomainIdentity::D8(_) => 8,
        };
        out.push(tag);
        out.push(identity.packed_bits());
    }

    fn get_domain_identity(
        bytes: &[u8],
        pos: &mut usize,
    ) -> Option<crate::CoreDomainIdentity> {
        let domain = *bytes.get(*pos)?;
        let payload = *bytes.get(*pos + 1)?;
        *pos += 2;
        match domain {
            1 => Some(crate::PredicateBit::from_word(crate::Bit1::new(payload)?).into()),
            2 => Some(crate::Racana2::from_word(crate::Bit2::new(payload)?).into()),
            3 => Some(crate::Bija3::from_word(crate::Bit3::new(payload)?).into()),
            4 => Some(crate::CoreD4::from_word(crate::Bit4::new(payload)?).into()),
            5 => Some(crate::CoreD5::from_word(crate::Bit5::new(payload)?).into()),
            6 => Some(crate::CoreD6::from_word(crate::Bit6::new(payload)?).into()),
            0x71 => Some(crate::D7SoundCell::from_word(crate::Bit7::new(payload)?).into()),
            0x72 => Some(crate::D7LocalOrdinal::from_word(crate::Bit7::new(payload)?).into()),
            8 => Some(crate::CoreD8::from_word(crate::Bit8::new(payload)?).into()),
            _ => None,
        }
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
            ExprKind::DomainIdentity(identity) => {
                out.push(TAG_DOMAIN_IDENTITY);
                put_domain_identity(out, *identity);
            }
            ExprKind::String(value) => {
                out.push(TAG_STRING);
                put_str(out, value);
            }
            ExprKind::Symbol(symbol) => {
                out.push(TAG_SYMBOL);
                put_str(out, symbol);
            }
            ExprKind::Local { depth, index } => {
                out.push(TAG_LOCAL);
                put_u32(out, *depth);
                put_u32(out, *index);
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
            // Зведений виклик зберігається як список із 1-байтовою головою.
            ExprKind::Call(sid, arguments) => {
                out.push(TAG_LIST);
                put_u32(out, arguments.len() as u32 + 1);
                out.push(TAG_BINARY);
                out.push(sid.packed_byte());
                for argument in arguments.iter() {
                    encode_expr(argument, out);
                }
            }
            ExprKind::DomainCall(identity, arguments) => {
                out.push(TAG_LIST);
                put_u32(out, arguments.len() as u32 + 1);
                out.push(TAG_DOMAIN_IDENTITY);
                put_domain_identity(out, *identity);
                for argument in arguments.iter() {
                    encode_expr(argument, out);
                }
            }
            ExprKind::NumericBuffer(NumericBuffer::I32(values)) => {
                out.push(TAG_I32_BUFFER);
                put_u32(out, values.len() as u32);
                for value in values.iter() {
                    out.extend_from_slice(&value.to_le_bytes());
                }
            }
            ExprKind::NumericBuffer(NumericBuffer::F32(values)) => {
                out.push(TAG_F32_BUFFER);
                put_u32(out, values.len() as u32);
                for value in values.iter() {
                    out.extend_from_slice(&value.to_bits().to_le_bytes());
                }
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
                ExprKind::Sid(crate::Sens8::from_packed_byte(value))
            }
            TAG_DOMAIN_IDENTITY => ExprKind::DomainIdentity(get_domain_identity(bytes, pos)?),
            TAG_STRING => ExprKind::String(get_str(bytes, pos)?.into()),
            TAG_SYMBOL => ExprKind::Symbol(get_str(bytes, pos)?.into()),
            TAG_LOCAL => {
                let depth = get_u32(bytes, pos)?;
                let index = get_u32(bytes, pos)?;
                ExprKind::Local { depth, index }
            }
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
            TAG_I32_BUFFER => {
                let count = get_u32(bytes, pos)? as usize;
                let byte_len = count.checked_mul(std::mem::size_of::<i32>())?;
                let raw = bytes.get(*pos..pos.checked_add(byte_len)?)?;
                *pos += byte_len;
                let mut values = Vec::with_capacity(count.min(1 << 22));
                for chunk in raw.as_chunks::<4>().0 {
                    values.push(i32::from_le_bytes(*chunk));
                }
                ExprKind::NumericBuffer(NumericBuffer::I32(Arc::from(values)))
            }
            TAG_F32_BUFFER => {
                let count = get_u32(bytes, pos)? as usize;
                let byte_len = count.checked_mul(std::mem::size_of::<u32>())?;
                let raw = bytes.get(*pos..pos.checked_add(byte_len)?)?;
                *pos += byte_len;
                let mut values = Vec::with_capacity(count.min(1 << 22));
                for chunk in raw.as_chunks::<4>().0 {
                    let bits = u32::from_le_bytes(*chunk);
                    let value = f32::from_bits(bits);
                    if !value.is_finite() {
                        return None;
                    }
                    values.push(value);
                }
                ExprKind::NumericBuffer(NumericBuffer::F32(Arc::from(values)))
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

/// Компактний формат програм для обміну між агентами (SENS wire).
///
/// На відміну від fasl (кеш розбору ядра з хешем джерела), тут немає хешу й
/// фіксованих u32: малі цілі — 1 байт, список до 15 елементів — 1 байт
/// заголовка, довжини — varint, функція СЕНС — тег + 1 байт. Вхід вважається
/// недовіреним: глибина й розміри обмежені, будь-яка невідповідність — None.
pub(crate) mod wire {
    use super::{Exactness, Expr, ExprKind, MAX_STRUCTURE_DEPTH};
    use crate::value::Rational;
    use std::rc::Rc;

    const MAGIC: &[u8; 3] = b"SW\x01";
    const SMALL_INT_END: u8 = 0x40; // 0x00..0x3F — ціле 0..63
    const SHORT_LIST: u8 = 0x40; // 0x40..0x4F — список із 0..15 елементів
    const SHORT_LIST_END: u8 = 0x50;
    const TAG_LIST: u8 = 0x50;
    const TAG_BINARY: u8 = 0x51;
    const TAG_INTEGER: u8 = 0x52;
    const TAG_NUMBER: u8 = 0x53;
    const TAG_RATIONAL: u8 = 0x54;
    const TAG_STRING: u8 = 0x55;
    const TAG_SYMBOL: u8 = 0x56;
    const TAG_PAIR: u8 = 0x57;
    const TAG_LOCAL: u8 = 0x58;
    const TAG_DOMAIN_IDENTITY: u8 = 0x59;
    /// Точні цілі поза цим діапазоном ідуть як f64, щоб не втратити точність.
    const EXACT_INTEGER_LIMIT: f64 = 9_007_199_254_740_992.0;

    fn put_varint(out: &mut Vec<u8>, mut value: u64) {
        while value >= 0x80 {
            out.push((value as u8) | 0x80);
            value >>= 7;
        }
        out.push(value as u8);
    }

    fn get_varint(bytes: &[u8], pos: &mut usize) -> Option<u64> {
        let mut value = 0u64;
        for shift in (0..64).step_by(7) {
            let byte = *bytes.get(*pos)?;
            *pos += 1;
            value |= u64::from(byte & 0x7F) << shift;
            if byte < 0x80 {
                return Some(value);
            }
        }
        None
    }

    fn put_text(out: &mut Vec<u8>, tag: u8, text: &str) {
        out.push(tag);
        put_varint(out, text.len() as u64);
        out.extend_from_slice(text.as_bytes());
    }

    fn get_text<'a>(bytes: &'a [u8], pos: &mut usize) -> Option<&'a str> {
        let len = usize::try_from(get_varint(bytes, pos)?).ok()?;
        let slice = bytes.get(*pos..pos.checked_add(len)?)?;
        *pos += len;
        std::str::from_utf8(slice).ok()
    }

    fn put_domain_identity(out: &mut Vec<u8>, identity: crate::CoreDomainIdentity) {
        let tag = match identity {
            crate::CoreDomainIdentity::D1(_) => 1,
            crate::CoreDomainIdentity::D2(_) => 2,
            crate::CoreDomainIdentity::D3(_) => 3,
            crate::CoreDomainIdentity::D4(_) => 4,
            crate::CoreDomainIdentity::D5(_) => 5,
            crate::CoreDomainIdentity::D6(_) => 6,
            crate::CoreDomainIdentity::D7Sound(_) => 0x71,
            crate::CoreDomainIdentity::D7LocalOrdinal(_) => 0x72,
            crate::CoreDomainIdentity::D8(_) => 8,
        };
        out.push(tag);
        out.push(identity.packed_bits());
    }

    fn get_domain_identity(
        bytes: &[u8],
        pos: &mut usize,
    ) -> Option<crate::CoreDomainIdentity> {
        let domain = *bytes.get(*pos)?;
        let payload = *bytes.get(*pos + 1)?;
        *pos += 2;
        match domain {
            1 => Some(crate::PredicateBit::from_word(crate::Bit1::new(payload)?).into()),
            2 => Some(crate::Racana2::from_word(crate::Bit2::new(payload)?).into()),
            3 => Some(crate::Bija3::from_word(crate::Bit3::new(payload)?).into()),
            4 => Some(crate::CoreD4::from_word(crate::Bit4::new(payload)?).into()),
            5 => Some(crate::CoreD5::from_word(crate::Bit5::new(payload)?).into()),
            6 => Some(crate::CoreD6::from_word(crate::Bit6::new(payload)?).into()),
            0x71 => Some(crate::D7SoundCell::from_word(crate::Bit7::new(payload)?).into()),
            0x72 => Some(crate::D7LocalOrdinal::from_word(crate::Bit7::new(payload)?).into()),
            8 => Some(crate::CoreD8::from_word(crate::Bit8::new(payload)?).into()),
            _ => None,
        }
    }

    fn put_list_header(out: &mut Vec<u8>, count: usize) {
        if count < usize::from(SHORT_LIST_END - SHORT_LIST) {
            out.push(SHORT_LIST + count as u8);
        } else {
            out.push(TAG_LIST);
            put_varint(out, count as u64);
        }
    }

    /// Точне ціле, яке f64 зберігає без втрат (включно зі знаком нуля).
    fn exact_integer(value: f64, exactness: &Exactness) -> Option<i64> {
        if !matches!(exactness, Exactness::Exact) || value.abs() >= EXACT_INTEGER_LIMIT {
            return None;
        }
        let integer = value as i64;
        ((integer as f64).to_bits() == value.to_bits()).then_some(integer)
    }

    fn encode_expr(expr: &Expr, out: &mut Vec<u8>) {
        match &expr.kind {
            ExprKind::Number(value, exactness) => match exact_integer(*value, exactness) {
                Some(integer) if (0..i64::from(SMALL_INT_END)).contains(&integer) => {
                    out.push(integer as u8);
                }
                Some(integer) => {
                    out.push(TAG_INTEGER);
                    put_varint(out, ((integer << 1) ^ (integer >> 63)) as u64);
                }
                None => {
                    out.push(TAG_NUMBER);
                    out.extend_from_slice(&value.to_le_bytes());
                    out.push(matches!(exactness, Exactness::Inexact) as u8);
                }
            },
            ExprKind::Rational(rational) => {
                out.push(TAG_RATIONAL);
                rational.write_fasl(out);
            }
            ExprKind::Sid(sid) => {
                out.push(TAG_BINARY);
                out.push(sid.packed_byte());
            }
            ExprKind::DomainIdentity(identity) => {
                out.push(TAG_DOMAIN_IDENTITY);
                put_domain_identity(out, *identity);
            }
            ExprKind::String(value) => put_text(out, TAG_STRING, value),
            ExprKind::Symbol(symbol) => put_text(out, TAG_SYMBOL, symbol),
            ExprKind::Local { depth, index } => {
                out.push(TAG_LOCAL);
                put_varint(out, u64::from(*depth));
                put_varint(out, u64::from(*index));
            }
            ExprKind::List(items) => {
                put_list_header(out, items.len());
                for item in items.iter() {
                    encode_expr(item, out);
                }
            }
            ExprKind::Pair(head, tail) => {
                out.push(TAG_PAIR);
                encode_expr(head, out);
                encode_expr(tail, out);
            }
            ExprKind::Call(sid, arguments) => {
                put_list_header(out, arguments.len() + 1);
                out.push(TAG_BINARY);
                out.push(sid.packed_byte());
                for argument in arguments.iter() {
                    encode_expr(argument, out);
                }
            }
            ExprKind::DomainCall(identity, arguments) => {
                put_list_header(out, arguments.len() + 1);
                out.push(TAG_DOMAIN_IDENTITY);
                put_domain_identity(out, *identity);
                for argument in arguments.iter() {
                    encode_expr(argument, out);
                }
            }
            ExprKind::NumericBuffer(_) => {
                unreachable!("NumericBuffer is runtime-only, never parsed")
            }
        }
    }

    fn expr(kind: ExprKind) -> Expr {
        Expr {
            kind,
            span: crate::Span { start: 0, end: 0 },
        }
    }

    /// Незавершений контейнер на явному стеку декодера.
    enum Open {
        List { remaining: usize, items: Vec<Expr> },
        Pair { head: Option<Expr> },
    }

    /// Один вираз без рекурсії: вхід недовірений, тож глибина вкладеності не
    /// повинна залежати від розміру стеку потоку (debug-збірка, малий стек).
    /// Глибину все одно обмежено `MAX_STRUCTURE_DEPTH` — решта інтерпретатора
    /// обходить дерево рекурсивно.
    fn decode_expr(bytes: &[u8], pos: &mut usize) -> Option<Expr> {
        let mut stack: Vec<Open> = Vec::new();
        loop {
            let mut done = match decode_step(bytes, pos)? {
                Step::Value(kind) => expr(kind),
                Step::Open(open) => {
                    if stack.len() as u32 >= MAX_STRUCTURE_DEPTH {
                        return None;
                    }
                    match open {
                        Open::List { remaining: 0, .. } => expr(ExprKind::List(Rc::from([]))),
                        open => {
                            stack.push(open);
                            continue;
                        }
                    }
                }
            };
            // Готове значення піднімається вгору, закриваючи заповнені контейнери.
            loop {
                match stack.last_mut() {
                    None => return Some(done),
                    Some(Open::List { remaining, items }) => {
                        items.push(done);
                        *remaining -= 1;
                        if *remaining > 0 {
                            break;
                        }
                        let Some(Open::List { items, .. }) = stack.pop() else { unreachable!() };
                        done = expr(ExprKind::List(items.into()));
                    }
                    Some(Open::Pair { head }) => {
                        if head.is_none() {
                            *head = Some(done);
                            break;
                        }
                        let Some(Open::Pair { head: Some(head) }) = stack.pop() else { unreachable!() };
                        done = expr(ExprKind::Pair(Rc::new(head), Rc::new(done)));
                    }
                }
            }
        }
    }

    enum Step {
        Value(ExprKind),
        Open(Open),
    }

    fn open_list(bytes: &[u8], pos: usize, count: usize) -> Option<Step> {
        // Кожен елемент займає щонайменше 1 байт — більший лічильник брехливий.
        if count > bytes.len().saturating_sub(pos) {
            return None;
        }
        Some(Step::Open(Open::List {
            remaining: count,
            items: Vec::with_capacity(count),
        }))
    }

    fn decode_step(bytes: &[u8], pos: &mut usize) -> Option<Step> {
        let tag = *bytes.get(*pos)?;
        *pos += 1;
        let kind = match tag {
            0..SMALL_INT_END => ExprKind::Number(f64::from(tag), Exactness::Exact),
            SHORT_LIST..SHORT_LIST_END => {
                return open_list(bytes, *pos, usize::from(tag - SHORT_LIST));
            }
            TAG_LIST => {
                let count = usize::try_from(get_varint(bytes, pos)?).ok()?;
                return open_list(bytes, *pos, count);
            }
            TAG_PAIR => return Some(Step::Open(Open::Pair { head: None })),
            TAG_BINARY => {
                let value = *bytes.get(*pos)?;
                *pos += 1;
                ExprKind::Sid(crate::Sens8::from_packed_byte(value))
            }
            TAG_DOMAIN_IDENTITY => {
                ExprKind::DomainIdentity(get_domain_identity(bytes, pos)?)
            }
            TAG_LOCAL => {
                let depth = u32::try_from(get_varint(bytes, pos)?).ok()?;
                let index = u32::try_from(get_varint(bytes, pos)?).ok()?;
                ExprKind::Local { depth, index }
            }
            TAG_INTEGER => {
                let zigzag = get_varint(bytes, pos)?;
                let integer = ((zigzag >> 1) as i64) ^ -((zigzag & 1) as i64);
                if integer.unsigned_abs() as f64 >= EXACT_INTEGER_LIMIT {
                    return None;
                }
                ExprKind::Number(integer as f64, Exactness::Exact)
            }
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
            TAG_STRING => ExprKind::String(get_text(bytes, pos)?.into()),
            TAG_SYMBOL => ExprKind::Symbol(get_text(bytes, pos)?.into()),
            _ => return None,
        };
        Some(Step::Value(kind))
    }

    /// Магія `SW\x01` + varint кількість виразів + вирази.
    pub fn encode_program(expressions: &[Expr]) -> Vec<u8> {
        let mut out = MAGIC.to_vec();
        put_varint(&mut out, expressions.len() as u64);
        for expr in expressions {
            encode_expr(expr, &mut out);
        }
        out
    }

    pub fn decode_program(bytes: &[u8]) -> Option<Vec<Expr>> {
        if bytes.get(0..3)? != MAGIC {
            return None;
        }
        let mut pos = 3;
        let count = usize::try_from(get_varint(bytes, &mut pos)?).ok()?;
        if count > bytes.len() - pos {
            return None;
        }
        let mut out = Vec::with_capacity(count);
        for _ in 0..count {
            out.push(decode_expr(bytes, &mut pos)?);
        }
        (pos == bytes.len()).then_some(out)
    }
}

#[cfg(test)]
mod wire_tests {
    use super::wire::{decode_program, encode_program};
    use super::{fasl, Expr, ExprKind};
    use crate::parser::parse;

    const SAMPLE: &str = r#"
(00001011 f (00001000 (n) (00000111 ((00000011 n 0) 0) (t (00001100 n (f (00001101 n 1)))))))
(f 12)
(00000101 (00000110 (00000001 (64 85 24 38 36 75 1000000 -7 -0.0 0.25 9007199254740991))))
(00001111 1 3)
"рядок з кирилицею"
(00000001 (a b . c))
(00000001 (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17))
"#;

    #[test]
    fn wire_local_carries_numeric_coordinates_and_no_name() {
        // #1697: канонічний wire несе координати слота, а не людське ім'я.
        let local = |depth, index| Expr {
            kind: ExprKind::Local { depth, index },
            span: crate::Span { start: 0, end: 9 },
        };
        let encoded = encode_program(&[local(2, 3), local(0, 200)]);
        // магія(3) + кількість(1) + [тег + depth + index] * 2, усе varint
        assert_eq!(encoded.len(), 3 + 1 + (1 + 1 + 1) + (1 + 1 + 2));
        let decoded = decode_program(&encoded).expect("wire decodes local coordinates");
        assert_eq!(decoded[0].kind, ExprKind::Local { depth: 2, index: 3 });
        assert_eq!(decoded[1].kind, ExprKind::Local { depth: 0, index: 200 });
        assert_eq!(encode_program(&decoded), encoded);
    }

    #[test]
    fn wire_local_rejects_coordinates_wider_than_u32() {
        // depth = 2^32 як varint: 0x80 0x80 0x80 0x80 0x10
        assert!(decode_program(b"SW\x01\x01\x58\x80\x80\x80\x80\x10\x00").is_none());
    }

    #[test]
    fn fasl_local_carries_numeric_coordinates_and_no_name() {
        let local = Expr {
            kind: ExprKind::Local { depth: 1, index: 4 },
            span: crate::Span { start: 0, end: 0 },
        };
        let hash = [7u8; 32];
        let encoded = fasl::encode_program(&[local], &hash);
        let (decoded, decoded_hash) = fasl::decode_program(&encoded).expect("fasl decodes local");
        assert_eq!(decoded_hash, hash);
        assert_eq!(decoded[0].kind, ExprKind::Local { depth: 1, index: 4 });
        assert_eq!(fasl::encode_program(&decoded, &hash), encoded);
    }

    #[test]
    fn wire_round_trip_is_byte_identical() {
        let expressions = parse(SAMPLE).expect("sample parses");
        let encoded = encode_program(&expressions);
        let decoded = decode_program(&encoded).expect("wire decodes");
        assert_eq!(encode_program(&decoded), encoded);
        // Той самий вміст, що й через fasl — отже програма та сама.
        let hash = [0u8; 32];
        assert_eq!(fasl::encode_program(&decoded, &hash), fasl::encode_program(&expressions, &hash));
    }

    #[test]
    fn wire_is_smaller_than_fasl_and_text() {
        let source = "(00000101 (00000110 (00000110 (00000110 (00000001 (64 85 24 38 36 75))))))";
        let expressions = parse(source).expect("parses");
        let wire = encode_program(&expressions);
        let fasl = fasl::encode_program(&expressions, &[0u8; 32]);
        assert!(wire.len() < source.len(), "wire {} >= text {}", wire.len(), source.len());
        assert!(wire.len() * 4 < fasl.len(), "wire {} vs fasl {}", wire.len(), fasl.len());
    }

    #[test]
    fn wire_rejects_untrusted_garbage_without_panicking() {
        assert!(decode_program(b"").is_none());
        assert!(decode_program(b"not wire").is_none());
        // Брехливий лічильник, обрізаний varint, зайвий хвіст, надглибока вкладеність.
        assert!(decode_program(b"SW\x01\x01\x50\xff\xff\xff\xff\x0f").is_none());
        assert!(decode_program(b"SW\x01\x01\x52\xff").is_none());
        assert!(decode_program(b"SW\x01\x01\x05\x00").is_none());
        let mut deep = b"SW\x01\x01".to_vec();
        deep.extend(std::iter::repeat_n(0x41u8, 100_000));
        deep.push(0x00);
        assert!(decode_program(&deep).is_none());
        // Дозволена глибина декодується без рекурсії й без аварії.
        let mut nested = b"SW\x01\x01".to_vec();
        nested.extend(std::iter::repeat_n(0x41u8, 700));
        nested.push(0x07);
        let decoded = decode_program(&nested).expect("700 levels are within the limit");
        assert_eq!(encode_program(&decoded), nested);
        let expressions = parse(SAMPLE).expect("sample parses");
        let encoded = encode_program(&expressions);
        for cut in 0..encoded.len() {
            assert!(decode_program(&encoded[..cut]).is_none(), "prefix {cut} decoded");
        }
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
    fn fasl_transports_exact_sens_numeric_buffer_map_without_surface_names() {
        const SOURCE: &str =
            "(01011001 (00001000 (x) (00001100 x 1)) #i32(1 2 3))";
        let source_hash = sha256_source(SOURCE.as_bytes());
        let expressions = parse(SOURCE).expect("exact SENS numeric-buffer-map parses");
        let encoded = encode_program(&expressions, &source_hash);

        // FASL TAG_BINARY = 7; наступний байт є самою функцією СЕНС.
        assert!(
            encoded.windows(2).any(|bytes| bytes == [7, 0b01011001]),
            "numeric-buffer-map must travel as one exact SENS byte"
        );
        const FORBIDDEN_SURFACES: &[&[u8]] = &[
            &[110, 117, 109, 101, 114, 105, 99, 45, 98, 117, 102, 102, 101, 114, 45, 109, 97, 112],
            &[108, 97, 109, 98, 100, 97],
            &[105, 51, 50, 45, 98, 117, 102, 102, 101, 114],
        ];
        for forbidden in FORBIDDEN_SURFACES {
            assert!(
                !encoded.windows(forbidden.len()).any(|bytes| bytes == *forbidden),
                "людська назва просочилася в бінарний транспорт: {:?}",
                forbidden
            );
        }

        let (decoded, decoded_hash) =
            decode_program(&encoded).expect("typed-buffer FASL must decode");
        assert_eq!(decoded_hash, source_hash);
        assert_eq!(encode_program(&decoded, &source_hash), encoded);

        let ExprKind::List(outer) = &decoded[0].kind else {
            panic!("numeric-buffer-map program must stay a list");
        };
        assert!(matches!(
            &outer[0].kind,
            ExprKind::Sid(sid) if *sid == crate::sens!(01011001)
        ));
        let ExprKind::NumericBuffer(crate::NumericBuffer::I32(values)) = &outer[2].kind else {
            panic!("third argument must stay an i32 buffer");
        };
        assert_eq!(&**values, &[1, 2, 3]);
    }

    #[test]
    fn fasl_preserves_f32_buffer_bits_including_negative_zero() {
        const SOURCE: &str = "#f32(-0.0 0.1 3.0)";
        let source_hash = sha256_source(SOURCE.as_bytes());
        let expressions = parse(SOURCE).expect("f32 buffer parses");
        let encoded = encode_program(&expressions, &source_hash);
        let (decoded, _) = decode_program(&encoded).expect("f32 buffer FASL decodes");

        let ExprKind::NumericBuffer(crate::NumericBuffer::F32(values)) = &decoded[0].kind else {
            panic!("decoded expression must remain an f32 buffer");
        };
        assert_eq!(values[0].to_bits(), (-0.0f32).to_bits());
        assert_eq!(values[1].to_bits(), (0.1f32).to_bits());
        assert_eq!(values[2].to_bits(), 3.0f32.to_bits());
        assert_eq!(encode_program(&decoded, &source_hash), encoded);

        let mut tampered = encoded.clone();
        let start = tampered.len() - std::mem::size_of::<u32>();
        tampered[start..].copy_from_slice(&f32::INFINITY.to_bits().to_le_bytes());
        assert!(
            decode_program(&tampered).is_none(),
            "non-finite f32 payload must fail closed"
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
