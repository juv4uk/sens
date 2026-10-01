use std::{fmt, rc::Rc};

/// Canonical SENS text identity: an exact sequence of UPC-7 cells.
///
/// Each cell is logically seven bits wide (`0000000..1111111`). The host
/// stores one cell per `u8` only as a mechanism representation; the upper bit
/// is forbidden and never becomes part of Text identity.
///
/// Human Unicode spelling is deliberately absent from this type. Layout
/// selection and Unicode/UTF-8 decoding belong to the reader/boundary layer.
#[derive(Clone, Eq, Hash, PartialEq)]
pub struct Text7 {
    cells: Rc<[u8]>,
}

/// Failure to admit a host byte as one exact UPC-7 cell.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Text7CellError {
    index: usize,
    byte: u8,
}

impl Text7 {
    pub const LOGICAL_WIDTH: u8 = 7;
    pub const MAX_CELL: u8 = 0b0111_1111;

    /// Domain tag of the canonical machine transport token. The tag keeps a
    /// Text7 value distinct from Number (`#q2:`/`#b`), from a String spelling
    /// and from the bare eight-bit Function8 space.
    pub const WIRE_TAG: &'static str = "#t7:";

    /// Admit a sequence only when every mechanism byte is exactly one UPC-7
    /// cell. No masking or truncation is allowed: a set high bit is a named
    /// failure, never an implicit modulo-128 conversion.
    pub fn from_cells(cells: impl Into<Vec<u8>>) -> Result<Self, Text7CellError> {
        let cells = cells.into();
        if let Some((index, &byte)) = cells
            .iter()
            .enumerate()
            .find(|(_, byte)| **byte > Self::MAX_CELL)
        {
            return Err(Text7CellError { index, byte });
        }

        Ok(Self {
            cells: cells.into(),
        })
    }

    /// Canonical machine transport for one Text7 value.
    ///
    /// The token carries the exact UPC-7 cell stream: the domain tag followed
    /// by two lowercase hex digits per cell. It is deliberately not a human
    /// spelling — no Unicode, no UTF-8 and no selected layout appears in it —
    /// and `to_canonical_wire_string` must never fall back to human `render`
    /// for this domain.
    pub fn to_canonical_wire_token(&self) -> String {
        let mut token = String::with_capacity(Self::WIRE_TAG.len() + self.cells.len() * 2);
        token.push_str(Self::WIRE_TAG);
        for cell in self.cells.iter() {
            token.push(char::from_digit((cell >> 4) as u32, 16).expect("nibble is a hex digit"));
            token.push(char::from_digit((cell & 0x0F) as u32, 16).expect("nibble is a hex digit"));
        }
        token
    }

    /// Admit a canonical Text7 wire token back to its exact cell stream.
    ///
    /// Fails closed on every malformed shape: a missing tag, an odd digit
    /// count, a non-hex (or non-lowercase) digit, or a cell with the forbidden
    /// high bit set is a named error — never a masked, truncated or
    /// Unicode-transcoded value.
    pub fn from_canonical_wire_token(token: &str) -> Result<Self, Text7WireError> {
        let payload = token
            .strip_prefix(Self::WIRE_TAG)
            .ok_or(Text7WireError::MissingTag)?;
        if payload.len() % 2 != 0 {
            return Err(Text7WireError::OddLength {
                digits: payload.len(),
            });
        }

        let mut cells = Vec::with_capacity(payload.len() / 2);
        for (pair_index, pair) in payload.as_bytes().chunks(2).enumerate() {
            let high = hex_nibble(pair[0]).ok_or(Text7WireError::NonHexDigit {
                index: pair_index * 2,
                byte: pair[0],
            })?;
            let low = hex_nibble(pair[1]).ok_or(Text7WireError::NonHexDigit {
                index: pair_index * 2 + 1,
                byte: pair[1],
            })?;
            let byte = (high << 4) | low;
            if byte > Self::MAX_CELL {
                return Err(Text7WireError::CellOutOfRange {
                    index: pair_index,
                    byte,
                });
            }
            cells.push(byte);
        }

        Ok(Self {
            cells: cells.into(),
        })
    }

    /// Exact UPC-7 cell stream.
    ///
    /// The returned bytes are storage only; callers must not reinterpret them
    /// as SENS Numbers or widen Text identity beyond seven bits.
    pub fn cells(&self) -> &[u8] {
        &self.cells
    }

    pub fn len(&self) -> usize {
        self.cells.len()
    }

    pub fn is_empty(&self) -> bool {
        self.cells.is_empty()
    }
}

impl TryFrom<Vec<u8>> for Text7 {
    type Error = Text7CellError;

    fn try_from(cells: Vec<u8>) -> Result<Self, Self::Error> {
        Self::from_cells(cells)
    }
}

impl TryFrom<&[u8]> for Text7 {
    type Error = Text7CellError;

    fn try_from(cells: &[u8]) -> Result<Self, Self::Error> {
        Self::from_cells(cells.to_vec())
    }
}

impl Text7CellError {
    pub fn index(self) -> usize {
        self.index
    }

    /// Offending host storage byte. This is diagnostic mechanism data, not a
    /// Text7 identity.
    pub fn packed_byte(self) -> u8 {
        self.byte
    }
}

/// Failure to admit a canonical Text7 wire token. Every failure is named;
/// nothing here silently converts a malformed token into Text identity.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Text7WireError {
    /// The token does not carry the `#t7:` domain tag.
    MissingTag,
    /// The payload is not an even-length sequence of cell bytes.
    OddLength { digits: usize },
    /// A payload character is not a lowercase hex digit.
    NonHexDigit { index: usize, byte: u8 },
    /// A cell byte sets the forbidden high bit (`>= 128`).
    CellOutOfRange { index: usize, byte: u8 },
}

/// Only canonical lowercase hex is admitted; uppercase is a named failure so
/// one cell stream cannot gain two canonical spellings.
fn hex_nibble(byte: u8) -> Option<u8> {
    match byte {
        b'0'..=b'9' => Some(byte - b'0'),
        b'a'..=b'f' => Some(byte - b'a' + 10),
        _ => None,
    }
}

impl fmt::Display for Text7CellError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Text7 cell {} must fit exactly seven bits; got {:08b}",
            self.index, self.byte
        )
    }
}

impl std::error::Error for Text7CellError {}

impl fmt::Debug for Text7 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("Text7(")?;
        for (index, cell) in self.cells.iter().enumerate() {
            if index != 0 {
                f.write_str(" ")?;
            }
            write!(f, "{cell:07b}")?;
        }
        f.write_str(")")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn admits_only_exact_seven_bit_cells() {
        let text = Text7::from_cells(vec![0b0000000, 0b0000001, 0b1111111]).unwrap();

        assert_eq!(text.cells(), &[0, 1, 127]);
        assert_eq!(text.len(), 3);
        assert!(!text.is_empty());
        assert_eq!(format!("{text:?}"), "Text7(0000000 0000001 1111111)");
    }

    #[test]
    fn rejects_first_cell_with_a_high_bit_instead_of_masking_it() {
        let error = Text7::from_cells(vec![0b0000001, 0b10000000, 0b1111111]).unwrap_err();

        assert_eq!(error.index(), 1);
        assert_eq!(error.packed_byte(), 0b10000000);
        assert!(error.to_string().contains("10000000"));

        let max_error = Text7::from_cells(vec![0xff]).unwrap_err();
        assert_eq!(max_error.index(), 0);
        assert_eq!(max_error.packed_byte(), 0xff);
    }

    #[test]
    fn equality_is_exact_code_stream_equality() {
        let left = Text7::from_cells(vec![0b0000001, 0b0000010]).unwrap();
        let same = Text7::from_cells(vec![0b0000001, 0b0000010]).unwrap();
        let different = Text7::from_cells(vec![0b0000001, 0b0000011]).unwrap();

        assert_eq!(left, same);
        assert_ne!(left, different);
    }

    #[test]
    fn empty_text_is_a_valid_empty_code_stream() {
        let text = Text7::from_cells(Vec::new()).unwrap();

        assert!(text.is_empty());
        assert_eq!(text.cells(), &[]);
        assert_eq!(format!("{text:?}"), "Text7()");
    }
}
