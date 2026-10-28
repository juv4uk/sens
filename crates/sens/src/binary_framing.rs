use crate::domain_numeric::{self, DomainNumericComposition};
use crate::BinaryNumber;
use crate::DomainIdentity;
use crate::Value;
use crate::{CoreDomainIdentity, Rational, Text7};
use std::fmt;

/// Host-side view of one self-describing SENS framing record.
///
/// This is a standalone framing/decoder mechanism, **not** the canonical
/// semantic payload representation. Canonical exact-width domain payloads are
/// packed continuously by `BitPacker` / `PackedBitstream`; any tag/type/width
/// bits used here are framing metadata and must be accounted separately.
///
/// The current semantic carrier admits D1-D9 identities. D10 remains an exact
/// mechanical coordinate in its own carrier and is not promoted here by width
/// or payload alone. The historical Function8 frame is compatibility-only.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum BinaryFrame {
    Space,
    Close,
    Open,
    Function(CoreDomainIdentity),
    Domain(DomainIdentity),
    Number(Rational),
    /// Canonical #3022 natural Number. The Rational frame remains compatibility-only.
    BinaryNumber(BinaryNumber),
    /// Transport-only signed/reduced rational composition of existing D24+ values.
    /// The subtype tag is framing metadata, not a SENS function opcode or T5 law.
    NumericComposition(DomainNumericComposition),
    Text(Text7),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum BinaryFrameError {
    NonBit {
        index: usize,
        value: u8,
    },
    UnexpectedEnd {
        index: usize,
    },
    LengthOverflow {
        index: usize,
    },
    ReservedExtension {
        index: usize,
    },
    UnsupportedDomainWidth {
        index: usize,
        width: usize,
    },
    NonCanonicalNumber {
        index: usize,
    },
    InvalidNumber {
        index: usize,
    },
    UnexpectedClose {
        index: usize,
    },
    UnclosedStructure {
        index: usize,
        depth: usize,
    },
    /// Індекс кадру, який не має права потрапляти до точнодоменної програми.
    LegacyFrameForbidden {
        index: usize,
    },
}

const CONTROL_SPACE: [u8; 2] = [0, 0];
const CONTROL_CLOSE: [u8; 2] = [0, 1];
const CONTROL_OPEN: [u8; 2] = [1, 0];
const CONTROL_ESCAPE: [u8; 2] = [1, 1];

const TYPE_FUNCTION: [u8; 2] = [0, 0];
const TYPE_NUMBER: [u8; 2] = [0, 1];
const TYPE_TEXT: [u8; 2] = [1, 0];
const TYPE_EXTENSION: [u8; 2] = [1, 1];

const EXT_DOMAIN: [u8; 2] = [0, 0];
const EXT_BINARY_NUMBER: [u8; 2] = [0, 1];
const EXT_WIDE_DOMAIN: [u8; 2] = [1, 0];
// Formerly reserved EXT=11: an additive, self-delimiting Core frame subtype.
const EXT_NUMERIC_COMPOSITION: [u8; 2] = [1, 1];

/// Encode one non-negative length as Elias-gamma(n+1).
///
/// Adding one gives zero a unique code while preserving an unbounded,
/// prefix-free length domain:
///
/// 0 -> 1
/// 1 -> 010
/// 2 -> 011
/// 3 -> 00100
fn encode_len_into(length: usize, out: &mut Vec<u8>) -> Result<(), BinaryFrameError> {
    let value = length
        .checked_add(1)
        .ok_or(BinaryFrameError::LengthOverflow { index: out.len() })?;
    let width = usize::BITS as usize - value.leading_zeros() as usize;

    out.extend(std::iter::repeat_n(0, width - 1));
    for shift in (0..width).rev() {
        out.push(((value >> shift) & 1) as u8);
    }
    Ok(())
}

fn append_binary_digits(text: &str, out: &mut Vec<u8>) {
    for byte in text.bytes() {
        match byte {
            b'0' => out.push(0),
            b'1' => out.push(1),
            _ => unreachable!("binary part contains only sign + 0/1"),
        }
    }
}

fn append_fixed_bits(value: u8, width: usize, out: &mut Vec<u8>) {
    for shift in (0..width).rev() {
        out.push((value >> shift) & 1);
    }
}

fn append_fixed_bits_u16(value: u16, width: usize, out: &mut Vec<u8>) {
    for shift in (0..width).rev() {
        out.push(((value >> shift) & 1) as u8);
    }
}

pub fn encode_binary_frame(frame: &BinaryFrame) -> Result<Vec<u8>, BinaryFrameError> {
    let mut out = Vec::new();

    match frame {
        BinaryFrame::Space => out.extend_from_slice(&CONTROL_SPACE),
        BinaryFrame::Close => out.extend_from_slice(&CONTROL_CLOSE),
        BinaryFrame::Open => out.extend_from_slice(&CONTROL_OPEN),
        BinaryFrame::Function(_) => {
            // A historical unqualified W8 function frame is not an exact domain.
            return Err(BinaryFrameError::LegacyFrameForbidden { index: out.len() });
        }
        BinaryFrame::Domain(identity) => {
            out.extend_from_slice(&CONTROL_ESCAPE);
            out.extend_from_slice(&TYPE_EXTENSION);

            if identity.width() <= 8 {
                // Preserve the established D1-D8 wire byte-for-byte.
                out.extend_from_slice(&EXT_DOMAIN);
                append_fixed_bits((identity.width() - 1) as u8, 3, &mut out);
                append_fixed_bits(identity.packed_bits() as u8, identity.width(), &mut out);
            } else {
                // W9 cannot be represented by the legacy 3-bit (width-1) tag.
                // Use the explicit wide-domain extension with a prefix-free
                // width field instead of wrapping/truncating the width.
                out.extend_from_slice(&EXT_WIDE_DOMAIN);
                encode_len_into(identity.width(), &mut out)?;
                append_fixed_bits_u16(identity.packed_bits(), identity.width(), &mut out);
            }
        }
        BinaryFrame::BinaryNumber(number) => {
            out.extend_from_slice(&CONTROL_ESCAPE);
            out.extend_from_slice(&TYPE_EXTENSION);
            out.extend_from_slice(&EXT_BINARY_NUMBER);
            match number.numeric_domain_width() {
                None => {
                    // Historical normalized/UNQUALIFIED natural Number framing:
                    // preserve the exact old bytes for all existing values.
                    encode_len_into(number.width(), &mut out)?;
                    out.extend_from_slice(number.as_bits());
                }
                Some(domain_width) => {
                    // The old gamma0(count=0) was invalid. It is now a
                    // disjoint mechanical subtype marker for a Dn-qualified
                    // number. The domain width is explicitly encoded; raw
                    // payload length or its leading bits never infer Dn.
                    // [frame extension][gamma0(0)][gamma0(Dn width)][Dn bits]
                    encode_len_into(0, &mut out)?;
                    encode_len_into(domain_width, &mut out)?;
                    let exact = number
                        .exact_numeric_domain_bits()
                        .ok_or(BinaryFrameError::InvalidNumber { index: 0 })?;
                    if exact.len() != domain_width {
                        return Err(BinaryFrameError::InvalidNumber { index: 0 });
                    }
                    out.extend_from_slice(&exact);
                }
            }
        }
        BinaryFrame::NumericComposition(value) => {
            out.extend_from_slice(&CONTROL_ESCAPE);
            out.extend_from_slice(&TYPE_EXTENSION);
            out.extend_from_slice(&EXT_NUMERIC_COMPOSITION);
            let width = value.domain_width();
            if !BinaryNumber::is_numeric_domain_width(width) {
                return Err(BinaryFrameError::UnsupportedDomainWidth { index: 0, width });
            }
            let (negative, numerator, denominator) = value.as_parts();
            // Shape: EXT=11; gamma0(Dn width); is_ratio; is_negative;
            // exact n-bit numerator; if ratio, exact n-bit denominator.
            // The sign is never stolen from the n-bit magnitude.
            encode_len_into(width, &mut out)?;
            out.push(u8::from(denominator.is_some()));
            out.push(u8::from(negative));
            let word = numerator
                .exact_numeric_domain_bits()
                .ok_or(BinaryFrameError::InvalidNumber { index: 0 })?;
            if word.len() != width || word.iter().all(|&v| v == 0) {
                return Err(BinaryFrameError::NonCanonicalNumber { index: 0 });
            }
            out.extend(word);
            if let Some(d) = denominator {
                let denominator_word = d
                    .exact_numeric_domain_bits()
                    .ok_or(BinaryFrameError::InvalidNumber { index: 0 })?;
                if denominator_word.len() != width {
                    return Err(BinaryFrameError::InvalidNumber { index: 0 });
                }
                out.extend(denominator_word);
            } else if !negative {
                return Err(BinaryFrameError::NonCanonicalNumber { index: 0 });
            }
            // Replay constructor against the actual operands. For negative
            // integers the denominator is the exact Dn(1), not the magnitude.
            let mut one_word = vec![0u8; width];
            one_word[width - 1] = 1;
            let unit = BinaryNumber::from_numeric_domain_bits(width, &one_word)
                .ok_or(BinaryFrameError::InvalidNumber { index: 0 })?;
            let canonical =
                domain_numeric::canonical_parts(negative, numerator, denominator.unwrap_or(&unit));
            if canonical != Some(Value::NumericComposition(value.clone())) {
                return Err(BinaryFrameError::NonCanonicalNumber { index: 0 });
            }
        }
        BinaryFrame::Text(text) => {
            out.extend_from_slice(&CONTROL_ESCAPE);
            out.extend_from_slice(&TYPE_TEXT);
            encode_len_into(text.len(), &mut out)?;
            for &cell in text.cells() {
                append_fixed_bits(cell, 7, &mut out);
            }
        }
        BinaryFrame::Number(number) => {
            out.extend_from_slice(&CONTROL_ESCAPE);
            out.extend_from_slice(&TYPE_NUMBER);

            let (numerator, denominator) = number.binary_parts();
            let (negative, magnitude) = match numerator.strip_prefix('-') {
                Some(magnitude) => (true, magnitude),
                None => (false, numerator.as_str()),
            };
            let numerator_bits = if magnitude == "0" { "" } else { magnitude };

            out.push(u8::from(negative));
            encode_len_into(numerator_bits.len(), &mut out)?;
            append_binary_digits(numerator_bits, &mut out);

            encode_len_into(denominator.len(), &mut out)?;
            append_binary_digits(&denominator, &mut out);
        }
    }

    Ok(out)
}

/// Strict additive Core numeric Value framing; a physical-T5 .sens decoder
/// is a distinct authority and MUST NOT interpret these records as its words.
pub fn encode_numeric_value_frame(value: &Value) -> Result<Vec<u8>, BinaryFrameError> {
    match value {
        Value::BinaryNumber(n) if n.numeric_domain_width().is_some() => {
            encode_binary_frame(&BinaryFrame::BinaryNumber(n.clone()))
        }
        Value::NumericComposition(c) => {
            encode_binary_frame(&BinaryFrame::NumericComposition(c.clone()))
        }
        _ => Err(BinaryFrameError::InvalidNumber { index: 0 }),
    }
}

/// Reconstruct exact Dn-qualified natural/negative/reduced-rational Value.
/// Reject every other frame rather than losing a domain or normalizing away
/// a noncanonical wire representation.
pub fn decode_numeric_value_frame(bits: &[u8]) -> Result<(Value, usize), BinaryFrameError> {
    let (frame, consumed) = decode_binary_frame(bits)?;
    let value = match frame {
        BinaryFrame::BinaryNumber(n) if n.numeric_domain_width().is_some() => {
            Value::BinaryNumber(n)
        }
        BinaryFrame::NumericComposition(c) => Value::NumericComposition(c),
        _ => return Err(BinaryFrameError::InvalidNumber { index: 0 }),
    };
    Ok((value, consumed))
}

/// Dense physical-byte storage of the already-admitted framed Dn numeric
/// value. Reuses the existing PackedBitstream MSB-first packer, without a
/// new transport grammar, magic header, semantic opcode or .sens/T5 claim.
/// The pair (bytes, exact meaningful bit length) is required to reconstruct
/// the record; raw bytes alone must not guess a numeric domain/last bit.
pub fn encode_packed_numeric_value(
    value: &Value,
) -> Result<crate::PackedBitstream, BinaryFrameError> {
    let bits = encode_numeric_value_frame(value)?;
    let mut packer = crate::BitPacker::new();
    for bit in bits {
        let word = crate::Bit1::new(bit).ok_or(BinaryFrameError::InvalidNumber { index: 0 })?;
        packer.push(word);
    }
    Ok(packer.finish())
}

/// Recover from existing byte+meaningful-bit-length container, validate one
/// complete canonical frame and refuse appended/trailing meaningful bits.
pub fn decode_packed_numeric_value(
    packed: &crate::PackedBitstream,
) -> Result<Value, BinaryFrameError> {
    let bits = (0..packed.bit_len())
        .map(|index| (packed.bytes()[index / 8] >> (7 - index % 8)) & 1)
        .collect::<Vec<_>>();
    let (value, consumed) = decode_numeric_value_frame(&bits)?;
    if consumed != bits.len() {
        return Err(BinaryFrameError::NonCanonicalNumber { index: consumed });
    }
    if encode_numeric_value_frame(&value)? != bits {
        return Err(BinaryFrameError::NonCanonicalNumber { index: 0 });
    }
    Ok(value)
}

/// Суворий транспортний маршрут для нових програм: ніякої прихованої
/// восьмибітної функції, раціонального літерала чи числа без D24+.
/// Це лише перевірка КАДРІВ; `Domain(D8)` означає дані з точною шириною,
/// а не автоматичний допуск відповідного механізму до виконання.
impl BinaryFrame {
    fn check_exact_program(frames: &[Self]) -> Result<(), BinaryFrameError> {
        for (index, frame) in frames.iter().enumerate() {
            match frame {
                Self::Function(_) | Self::Number(_) => {
                    return Err(BinaryFrameError::LegacyFrameForbidden { index });
                }
                Self::BinaryNumber(number) if number.numeric_domain_width().is_none() => {
                    return Err(BinaryFrameError::LegacyFrameForbidden { index });
                }
                _ => {}
            }
        }
        Ok(())
    }

    /// Записати точнодоменну програму, не змінюючи існуючого бітового формату.
    pub fn encode_exact_domain_program(frames: &[Self]) -> Result<Vec<u8>, BinaryFrameError> {
        Self::check_exact_program(frames)?;
        encode_binary_program(frames)
    }

    /// Прочитати точнодоменну програму без підвищення історичного W8 до D8.
    /// Помилка містить індекс кадру, а не позицію біта.
    pub fn decode_exact_domain_program(bits: &[u8]) -> Result<Vec<Self>, BinaryFrameError> {
        let frames = decode_binary_program(bits)?;
        Self::check_exact_program(&frames)?;
        Ok(frames)
    }
}

pub fn encode_binary_program(frames: &[BinaryFrame]) -> Result<Vec<u8>, BinaryFrameError> {
    let mut out = Vec::new();
    let mut depth = 0usize;

    for (frame_index, frame) in frames.iter().enumerate() {
        match frame {
            BinaryFrame::Open => depth += 1,
            BinaryFrame::Close => {
                if depth == 0 {
                    return Err(BinaryFrameError::UnexpectedClose { index: out.len() });
                }
                depth -= 1;
            }
            _ => {}
        }
        let encoded = encode_binary_frame(frame).map_err(|error| match error {
            // This diagnostic is defined in frame coordinates by
            // BinaryFrameError, not as a local bit offset within one record.
            BinaryFrameError::LegacyFrameForbidden { .. } => {
                BinaryFrameError::LegacyFrameForbidden { index: frame_index }
            }
            other => other,
        })?;
        out.extend(encoded);
    }

    if depth != 0 {
        return Err(BinaryFrameError::UnclosedStructure {
            index: out.len(),
            depth,
        });
    }

    Ok(out)
}

pub fn decode_binary_frame(bits: &[u8]) -> Result<(BinaryFrame, usize), BinaryFrameError> {
    let mut reader = BitReader::new(bits);
    let frame = decode_frame_from(&mut reader)?;
    Ok((frame, reader.position()))
}

pub fn decode_binary_program(bits: &[u8]) -> Result<Vec<BinaryFrame>, BinaryFrameError> {
    let mut reader = BitReader::new(bits);
    let mut frames = Vec::new();
    let mut depth = 0usize;

    while reader.position() < bits.len() {
        let frame_start = reader.position();
        let frame = decode_frame_from(&mut reader)?;
        match frame {
            BinaryFrame::Open => depth += 1,
            BinaryFrame::Close => {
                if depth == 0 {
                    return Err(BinaryFrameError::UnexpectedClose { index: frame_start });
                }
                depth -= 1;
            }
            _ => {}
        }
        frames.push(frame);
    }

    if depth != 0 {
        return Err(BinaryFrameError::UnclosedStructure {
            index: reader.position(),
            depth,
        });
    }

    Ok(frames)
}

fn decode_frame_from(reader: &mut BitReader<'_>) -> Result<BinaryFrame, BinaryFrameError> {
    let frame_start = reader.position();
    let first = reader.read_bit()?;
    let second = reader.read_bit()?;

    match [first, second] {
        CONTROL_SPACE => Ok(BinaryFrame::Space),
        CONTROL_CLOSE => Ok(BinaryFrame::Close),
        CONTROL_OPEN => Ok(BinaryFrame::Open),
        CONTROL_ESCAPE => {
            let type_start = reader.position();
            let t0 = reader.read_bit()?;
            let t1 = reader.read_bit()?;
            match [t0, t1] {
                TYPE_FUNCTION => Err(BinaryFrameError::LegacyFrameForbidden { index: frame_start }),
                TYPE_NUMBER => decode_number(reader, frame_start),
                TYPE_TEXT => decode_text(reader),
                TYPE_EXTENSION => {
                    let e0 = reader.read_bit()?;
                    let e1 = reader.read_bit()?;
                    match [e0, e1] {
                        EXT_DOMAIN => decode_domain_identity(reader),
                        EXT_BINARY_NUMBER => decode_binary_number(reader, frame_start),
                        EXT_WIDE_DOMAIN => decode_wide_domain_identity(reader, frame_start),
                        EXT_NUMERIC_COMPOSITION => decode_numeric_composition(reader, frame_start),
                        _ => Err(BinaryFrameError::ReservedExtension { index: type_start }),
                    }
                }
                _ => unreachable!("read_bit returns only 0 or 1"),
            }
        }
        _ => unreachable!("read_bit returns only 0 or 1"),
    }
}

fn decode_numeric_composition(
    reader: &mut BitReader<'_>,
    frame_start: usize,
) -> Result<BinaryFrame, BinaryFrameError> {
    let width = reader.read_len()?;
    if !BinaryNumber::is_numeric_domain_width(width) {
        return Err(BinaryFrameError::UnsupportedDomainWidth {
            index: frame_start,
            width,
        });
    }
    // All numeric component words are exactly width bits and the tag is
    // self-delimiting; rejecting truncation before allocation is mandatory.
    let ratio = reader.read_bit()? == 1;
    let negative = reader.read_bit()? == 1;
    if !ratio && !negative {
        return Err(BinaryFrameError::NonCanonicalNumber { index: frame_start });
    }
    let n = reader.read_bit_string(width)?;
    let n = n.bytes().map(|v| v - b'0').collect::<Vec<_>>();
    let numerator = BinaryNumber::from_numeric_domain_bits(width, &n)
        .ok_or(BinaryFrameError::InvalidNumber { index: frame_start })?;
    let denominator = if ratio {
        let d = reader.read_bit_string(width)?;
        let d = d.bytes().map(|v| v - b'0').collect::<Vec<_>>();
        BinaryNumber::from_numeric_domain_bits(width, &d)
            .ok_or(BinaryFrameError::InvalidNumber { index: frame_start })?
    } else {
        let mut one = vec![0; width];
        one[width - 1] = 1;
        BinaryNumber::from_numeric_domain_bits(width, &one)
            .ok_or(BinaryFrameError::InvalidNumber { index: frame_start })?
    };
    let canonical = domain_numeric::canonical_parts(negative, &numerator, &denominator)
        .ok_or(BinaryFrameError::InvalidNumber { index: frame_start })?;
    match &canonical {
        Value::NumericComposition(c) => {
            if c.domain_width() != width
                || c.as_parts().2.is_some() != ratio
                || c.as_parts().1 != &numerator
                || c.as_parts().2.is_some_and(|d| d != &denominator)
            {
                return Err(BinaryFrameError::NonCanonicalNumber { index: frame_start });
            }
            Ok(BinaryFrame::NumericComposition(c.clone()))
        }
        _ => Err(BinaryFrameError::NonCanonicalNumber { index: frame_start }),
    }
}

fn decode_wide_domain_identity(
    reader: &mut BitReader<'_>,
    frame_start: usize,
) -> Result<BinaryFrame, BinaryFrameError> {
    let width = reader.read_len()?;
    if width != 9 {
        return Err(BinaryFrameError::UnsupportedDomainWidth {
            index: frame_start,
            width,
        });
    }

    let payload = reader.read_fixed_u16(width)?;
    let word = crate::Bit9::new(payload).ok_or(BinaryFrameError::UnsupportedDomainWidth {
        index: frame_start,
        width,
    })?;

    Ok(BinaryFrame::Domain(
        crate::BinarySourceWord::W9(word).domain_identity(),
    ))
}

fn decode_binary_number(
    reader: &mut BitReader<'_>,
    frame_start: usize,
) -> Result<BinaryFrame, BinaryFrameError> {
    let count = reader.read_len()?;
    if count == 0 {
        // A zero *legacy* magnitude length was previously prohibited.
        // Reuse that unassigned subcase, not a D2 syntactic control code,
        // for an explicit D24/D48/... domain width and full-width word.
        let domain_width = reader.read_len()?;
        if !BinaryNumber::is_numeric_domain_width(domain_width) {
            return Err(BinaryFrameError::UnsupportedDomainWidth {
                index: frame_start,
                width: domain_width,
            });
        }
        // Read only after validating width: avoids allocating for arbitrary
        // attacker-supplied lengths not belonging to the numeric ladder.
        let bits = reader.read_bit_string(domain_width)?;
        let word = bits
            .bytes()
            .map(|c| if c == b'1' { 1 } else { 0 })
            .collect::<Vec<_>>();
        let number = BinaryNumber::from_numeric_domain_bits(domain_width, &word)
            .ok_or(BinaryFrameError::InvalidNumber { index: frame_start })?;
        return Ok(BinaryFrame::BinaryNumber(number));
    }
    let bits = reader.read_bit_string(count)?;
    if bits.len() > 1 && bits.starts_with('0') {
        return Err(BinaryFrameError::NonCanonicalNumber { index: frame_start });
    }
    let number = BinaryNumber::parse(&bits)
        .map_err(|_| BinaryFrameError::InvalidNumber { index: frame_start })?;
    Ok(BinaryFrame::BinaryNumber(number))
}

fn decode_domain_identity(reader: &mut BitReader<'_>) -> Result<BinaryFrame, BinaryFrameError> {
    let width = usize::from(reader.read_fixed_u8(3)?) + 1;
    let payload = reader.read_fixed_u8(width)?;
    let source = match width {
        1 => crate::BinarySourceWord::W1(crate::Bit1::new(payload).unwrap()),
        2 => crate::BinarySourceWord::W2(crate::Bit2::new(payload).unwrap()),
        3 => crate::BinarySourceWord::W3(crate::Bit3::new(payload).unwrap()),
        4 => crate::BinarySourceWord::W4(crate::Bit4::new(payload).unwrap()),
        5 => crate::BinarySourceWord::W5(crate::Bit5::new(payload).unwrap()),
        6 => crate::BinarySourceWord::W6(crate::Bit6::new(payload).unwrap()),
        7 => crate::BinarySourceWord::W7(crate::Bit7::new(payload).unwrap()),
        8 => crate::BinarySourceWord::W8(crate::Bit8::new(payload).unwrap()),
        _ => unreachable!("three-bit width tag + 1 is always 1..=8"),
    };
    Ok(BinaryFrame::Domain(source.domain_identity()))
}

fn decode_text(reader: &mut BitReader<'_>) -> Result<BinaryFrame, BinaryFrameError> {
    let count = reader.read_len()?;
    let needed = count
        .checked_mul(7)
        .ok_or(BinaryFrameError::LengthOverflow {
            index: reader.position(),
        })?;
    if reader.remaining() < needed {
        return Err(BinaryFrameError::UnexpectedEnd {
            index: reader.position(),
        });
    }

    let mut cells = Vec::with_capacity(count);
    for _ in 0..count {
        cells.push(reader.read_fixed_u8(7)?);
    }

    Ok(BinaryFrame::Text(Text7::from_cells(cells).expect(
        "seven-bit decoder cannot create an invalid Text7 cell",
    )))
}

fn decode_number(
    reader: &mut BitReader<'_>,
    frame_start: usize,
) -> Result<BinaryFrame, BinaryFrameError> {
    let negative = reader.read_bit()? == 1;

    let numerator_len = reader.read_len()?;
    let numerator_bits = reader.read_bit_string(numerator_len)?;
    if numerator_len == 0 {
        if negative {
            return Err(BinaryFrameError::NonCanonicalNumber { index: frame_start });
        }
    } else if !numerator_bits.starts_with('1') {
        return Err(BinaryFrameError::NonCanonicalNumber { index: frame_start });
    }

    let denominator_len = reader.read_len()?;
    if denominator_len == 0 {
        return Err(BinaryFrameError::NonCanonicalNumber { index: frame_start });
    }
    let denominator_bits = reader.read_bit_string(denominator_len)?;
    if !denominator_bits.starts_with('1') {
        return Err(BinaryFrameError::NonCanonicalNumber { index: frame_start });
    }

    let numerator = if numerator_len == 0 {
        "0".to_string()
    } else if negative {
        format!("-{numerator_bits}")
    } else {
        numerator_bits
    };

    let value = Rational::from_binary_wire_parts(&numerator, &denominator_bits)
        .ok_or(BinaryFrameError::InvalidNumber { index: frame_start })?;

    let (canonical_numerator, canonical_denominator) = value.binary_parts();
    if canonical_numerator != numerator || canonical_denominator != denominator_bits {
        return Err(BinaryFrameError::NonCanonicalNumber { index: frame_start });
    }

    Ok(BinaryFrame::Number(value))
}

struct BitReader<'a> {
    bits: &'a [u8],
    position: usize,
}

impl<'a> BitReader<'a> {
    fn new(bits: &'a [u8]) -> Self {
        Self { bits, position: 0 }
    }

    fn position(&self) -> usize {
        self.position
    }

    fn remaining(&self) -> usize {
        self.bits.len().saturating_sub(self.position)
    }

    fn read_bit(&mut self) -> Result<u8, BinaryFrameError> {
        let index = self.position;
        let Some(&value) = self.bits.get(index) else {
            return Err(BinaryFrameError::UnexpectedEnd { index });
        };
        if value > 1 {
            return Err(BinaryFrameError::NonBit { index, value });
        }
        self.position += 1;
        Ok(value)
    }

    fn read_fixed_u8(&mut self, width: usize) -> Result<u8, BinaryFrameError> {
        debug_assert!(width <= 8);
        let mut value = 0u8;
        for _ in 0..width {
            value = (value << 1) | self.read_bit()?;
        }
        Ok(value)
    }

    fn read_fixed_u16(&mut self, width: usize) -> Result<u16, BinaryFrameError> {
        debug_assert!(width <= 16);
        let mut value = 0u16;
        for _ in 0..width {
            value = (value << 1) | u16::from(self.read_bit()?);
        }
        Ok(value)
    }

    fn read_bit_string(&mut self, width: usize) -> Result<String, BinaryFrameError> {
        if self.remaining() < width {
            return Err(BinaryFrameError::UnexpectedEnd {
                index: self.position,
            });
        }
        let mut out = String::with_capacity(width);
        for _ in 0..width {
            out.push(if self.read_bit()? == 0 { '0' } else { '1' });
        }
        Ok(out)
    }

    fn read_len(&mut self) -> Result<usize, BinaryFrameError> {
        let start = self.position;
        let mut leading_zeroes = 0usize;

        loop {
            match self.read_bit()? {
                0 => {
                    leading_zeroes += 1;
                    if leading_zeroes >= usize::BITS as usize {
                        return Err(BinaryFrameError::LengthOverflow { index: start });
                    }
                }
                1 => break,
                _ => unreachable!(),
            }
        }

        let mut encoded = 1usize;
        for _ in 0..leading_zeroes {
            encoded = (encoded << 1) | self.read_bit()? as usize;
        }

        Ok(encoded - 1)
    }
}

impl fmt::Display for BinaryFrameError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NonBit { index, value } => {
                write!(
                    f,
                    "canonical binary stream has non-bit value {value} at {index}"
                )
            }
            Self::UnexpectedEnd { index } => {
                write!(
                    f,
                    "canonical binary stream ends unexpectedly at bit {index}"
                )
            }
            Self::LengthOverflow { index } => {
                write!(
                    f,
                    "canonical binary length overflows host index at bit {index}"
                )
            }
            Self::ReservedExtension { index } => {
                write!(
                    f,
                    "canonical Control2 extension 11 is reserved at bit {index}"
                )
            }
            Self::UnsupportedDomainWidth { index, width } => {
                write!(
                    f,
                    "canonical wide-domain frame at bit {index} does not admit width {width}"
                )
            }
            Self::NonCanonicalNumber { index } => {
                write!(f, "non-canonical exact Number frame begins at bit {index}")
            }
            Self::InvalidNumber { index } => {
                write!(f, "invalid exact Number frame begins at bit {index}")
            }
            Self::UnexpectedClose { index } => {
                write!(
                    f,
                    "canonical Control2 program closes unopened structure at bit {index}"
                )
            }
            Self::UnclosedStructure { index, depth } => {
                write!(
                    f,
                    "canonical Control2 program ends at bit {index} with {depth} unclosed structure(s)"
                )
            }
            Self::LegacyFrameForbidden { index } => {
                write!(
                    f,
                    "точнодоменна програма не допускає історичний кадр номер {index}"
                )
            }
        }
    }
}

impl std::error::Error for BinaryFrameError {}

