use crate::{Rational, Sens8, Text7};
use crate::DomainIdentity;
use std::fmt;

/// Host-side view of one canonical SENS binary frame.
///
/// The enum is a decoder mechanism only. Its variants do not create a new
/// language ontology. Exact domain identity has its own tagged frame; the
/// historical Function8 frame is compatibility-only and never aliases Core.D8.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum BinaryFrame {
    Space,
    Close,
    Open,
    Function(Sens8),
    Domain(DomainIdentity),
    Number(Rational),
    Text(Text7),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum BinaryFrameError {
    NonBit { index: usize, value: u8 },
    UnexpectedEnd { index: usize },
    LengthOverflow { index: usize },
    ReservedExtension { index: usize },
    NonCanonicalNumber { index: usize },
    InvalidNumber { index: usize },
    UnexpectedClose { index: usize },
    UnclosedStructure { index: usize, depth: usize },
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

pub fn encode_binary_frame(frame: &BinaryFrame) -> Result<Vec<u8>, BinaryFrameError> {
    let mut out = Vec::new();

    match frame {
        BinaryFrame::Space => out.extend_from_slice(&CONTROL_SPACE),
        BinaryFrame::Close => out.extend_from_slice(&CONTROL_CLOSE),
        BinaryFrame::Open => out.extend_from_slice(&CONTROL_OPEN),
        BinaryFrame::Function(sens) => {
            out.extend_from_slice(&CONTROL_ESCAPE);
            out.extend_from_slice(&TYPE_FUNCTION);
            append_fixed_bits(sens.packed_byte(), 8, &mut out);
        }
        BinaryFrame::Domain(identity) => {
            out.extend_from_slice(&CONTROL_ESCAPE);
            out.extend_from_slice(&TYPE_EXTENSION);
            out.extend_from_slice(&EXT_DOMAIN);
            append_fixed_bits((identity.width() - 1) as u8, 3, &mut out);
            append_fixed_bits(identity.packed_bits(), identity.width(), &mut out);
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

pub fn encode_binary_program(frames: &[BinaryFrame]) -> Result<Vec<u8>, BinaryFrameError> {
    let mut out = Vec::new();
    let mut depth = 0usize;

    for frame in frames {
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
        out.extend(encode_binary_frame(frame)?);
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
                TYPE_FUNCTION => {
                    let packed = reader.read_fixed_u8(8)?;
                    Ok(BinaryFrame::Function(Sens8::from_packed_byte(packed)))
                }
                TYPE_NUMBER => decode_number(reader, frame_start),
                TYPE_TEXT => decode_text(reader),
                TYPE_EXTENSION => {
                    let e0 = reader.read_bit()?;
                    let e1 = reader.read_bit()?;
                    match [e0, e1] {
                        EXT_DOMAIN => decode_domain_identity(reader),
                        _ => Err(BinaryFrameError::ReservedExtension { index: type_start }),
                    }
                },
                _ => unreachable!("read_bit returns only 0 or 1"),
            }
        }
        _ => unreachable!("read_bit returns only 0 or 1"),
    }
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
            Self::NonCanonicalNumber { index } => {
                write!(f, "non-canonical exact Number frame begins at bit {index}")
            }
            Self::InvalidNumber { index } => {
                write!(f, "invalid exact Number frame begins at bit {index}")
            }
            Self::UnexpectedClose { index } => {
                write!(f, "canonical Control2 program closes unopened structure at bit {index}")
            }
            Self::UnclosedStructure { index, depth } => {
                write!(
                    f,
                    "canonical Control2 program ends at bit {index} with {depth} unclosed structure(s)"
                )
            }
        }
    }
}

impl std::error::Error for BinaryFrameError {}

#[cfg(test)]
mod tests {
    use super::*;

    fn bits(text: &str) -> Vec<u8> {
        text.bytes().map(|b| b - b'0').collect()
    }

    fn number(numerator: &str, denominator: &str) -> Rational {
        Rational::from_binary_wire_parts(numerator, denominator).unwrap()
    }

    #[test]
    fn gamma_plus_one_lengths_are_prefix_free_and_unbounded_in_shape() {
        let cases = [
            (0usize, "1"),
            (1, "010"),
            (2, "011"),
            (3, "00100"),
            (7, "0001000"),
            (8, "0001001"),
            (63, "0000001000000"),
        ];

        for (length, expected) in cases {
            let mut encoded = Vec::new();
            encode_len_into(length, &mut encoded).unwrap();
            assert_eq!(encoded, bits(expected), "length {length}");

            let mut reader = BitReader::new(&encoded);
            assert_eq!(reader.read_len().unwrap(), length);
            assert_eq!(reader.position(), encoded.len());
        }
    }

    #[test]
    fn all_d1_d8_domain_widths_round_trip_without_function8_aliasing() {
        let identities = [
            crate::BinarySourceWord::W1(crate::Bit1::new(1).unwrap()).domain_identity(),
            crate::BinarySourceWord::W2(crate::Bit2::new(1).unwrap()).domain_identity(),
            crate::BinarySourceWord::W3(crate::Bit3::new(1).unwrap()).domain_identity(),
            crate::BinarySourceWord::W4(crate::Bit4::new(1).unwrap()).domain_identity(),
            crate::BinarySourceWord::W5(crate::Bit5::new(1).unwrap()).domain_identity(),
            crate::BinarySourceWord::W6(crate::Bit6::new(1).unwrap()).domain_identity(),
            crate::BinarySourceWord::W7(crate::Bit7::new(1).unwrap()).domain_identity(),
            crate::BinarySourceWord::W8(crate::Bit8::new(1).unwrap()).domain_identity(),
        ];

        for identity in identities {
            let frame = BinaryFrame::Domain(identity);
            let encoded = encode_binary_frame(&frame).unwrap();
            assert_eq!(&encoded[..6], &[1, 1, 1, 1, 0, 0]);
            let (decoded, consumed) = decode_binary_frame(&encoded).unwrap();
            assert_eq!(decoded, frame);
            assert_eq!(consumed, encoded.len());
        }

        let d8 = BinaryFrame::Domain(
            crate::BinarySourceWord::W8(crate::Bit8::new(1).unwrap()).domain_identity(),
        );
        let d8_encoded = encode_binary_frame(&d8).unwrap();
        assert_eq!(&d8_encoded[..6], &[1, 1, 1, 1, 0, 0]);
        // The existing compatibility Function8 witness below uses 1100.
        // Domain identity therefore has a disjoint frame tag without creating
        // any new exact-domain -> legacy identity dependency.
        assert_ne!(&d8_encoded[..4], &[1, 1, 0, 0]);
    }

    #[test]
    fn all_function8_values_round_trip_exactly() {
        for packed in 0u16..=255 {
            let frame = BinaryFrame::Function(Sens8::from_packed_byte(packed as u8));
            let encoded = encode_binary_frame(&frame).unwrap();
            assert_eq!(&encoded[..4], &[1, 1, 0, 0]);
            assert_eq!(encoded.len(), 12);

            let (decoded, consumed) = decode_binary_frame(&encoded).unwrap();
            assert_eq!(decoded, frame);
            assert_eq!(consumed, encoded.len());
        }
    }

    #[test]
    fn exact_numbers_round_trip_without_textual_tags() {
        for value in [
            number("0", "1"),
            number("1", "1"),
            number("-1", "1"),
            number("101010", "1"),
            number("1", "10"),
            number("-101", "100"),
            number("10000000000000000", "11"),
        ] {
            let frame = BinaryFrame::Number(value);
            let encoded = encode_binary_frame(&frame).unwrap();
            assert_eq!(&encoded[..4], &[1, 1, 0, 1]);
            let (decoded, consumed) = decode_binary_frame(&encoded).unwrap();
            assert_eq!(decoded, frame);
            assert_eq!(consumed, encoded.len());
        }
    }

    #[test]
    fn text7_round_trips_empty_and_full_width_cells() {
        for cells in [vec![], vec![0], vec![0, 1, 127], vec![92, 93, 94, 95]] {
            let frame = BinaryFrame::Text(Text7::from_cells(cells).unwrap());
            let encoded = encode_binary_frame(&frame).unwrap();
            assert_eq!(&encoded[..4], &[1, 1, 1, 0]);

            let (decoded, consumed) = decode_binary_frame(&encoded).unwrap();
            assert_eq!(decoded, frame);
            assert_eq!(consumed, encoded.len());
        }
    }

    #[test]
    fn control2_stream_keeps_real_space_and_nested_structure() {
        let frames = vec![
            BinaryFrame::Open,
            BinaryFrame::Function(crate::sens!(00001100)),
            BinaryFrame::Space,
            BinaryFrame::Number(number("10", "1")),
            BinaryFrame::Space,
            BinaryFrame::Number(number("11", "1")),
            BinaryFrame::Close,
        ];

        let encoded = encode_binary_program(&frames).unwrap();
        assert_eq!(&encoded[..2], &[1, 0]);
        assert!(encoded.windows(2).any(|pair| pair == [0, 0]));
        assert_eq!(decode_binary_program(&encoded).unwrap(), frames);
    }

    #[test]
    fn canonical_program_rejects_unbalanced_control2_structure() {
        assert!(matches!(
            encode_binary_program(&[BinaryFrame::Close]),
            Err(BinaryFrameError::UnexpectedClose { index: 0 })
        ));
        assert!(matches!(
            decode_binary_program(&[0, 1]),
            Err(BinaryFrameError::UnexpectedClose { index: 0 })
        ));

        let open_only = encode_binary_frame(&BinaryFrame::Open).unwrap();
        assert!(matches!(
            decode_binary_program(&open_only),
            Err(BinaryFrameError::UnclosedStructure { depth: 1, .. })
        ));
        assert!(matches!(
            encode_binary_program(&[BinaryFrame::Open]),
            Err(BinaryFrameError::UnclosedStructure { depth: 1, .. })
        ));
    }

    #[test]
    fn malformed_or_noncanonical_payloads_fail_closed() {
        assert!(matches!(
            decode_binary_frame(&[1, 1, 1, 1]),
            Err(BinaryFrameError::ReservedExtension { .. })
        ));
        assert!(matches!(
            decode_binary_frame(&[1, 1, 0, 0, 0, 0, 0, 0]),
            Err(BinaryFrameError::UnexpectedEnd { .. })
        ));
        assert!(matches!(
            decode_binary_frame(&[2, 0]),
            Err(BinaryFrameError::NonBit { index: 0, value: 2 })
        ));

        // Number: negative zero is forbidden.
        let negative_zero = bits("11011011011");
        assert!(matches!(
            decode_binary_frame(&negative_zero),
            Err(BinaryFrameError::NonCanonicalNumber { .. })
                | Err(BinaryFrameError::UnexpectedEnd { .. })
        ));

        // Number: 2/2 is mathematically one but not canonical reduced input.
        let non_reduced = {
            let mut raw = Vec::new();
            raw.extend_from_slice(&[1, 1, 0, 1]); // escape + Number
            raw.push(0); // positive
            encode_len_into(2, &mut raw).unwrap();
            raw.extend_from_slice(&[1, 0]); // numerator 2
            encode_len_into(2, &mut raw).unwrap();
            raw.extend_from_slice(&[1, 0]); // denominator 2
            raw
        };
        assert!(matches!(
            decode_binary_frame(&non_reduced),
            Err(BinaryFrameError::NonCanonicalNumber { .. })
        ));
    }
}
