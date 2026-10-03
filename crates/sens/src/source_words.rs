//! Canonical visible-binary source boundary for SENS .lisp files.
//!
//! This module owns source token shape only. It deliberately does not assign
//! D1-D6 meaning; semantic wrappers consume these exact-width words later.

use crate::{
    Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8, ErrorKind, LanguageError, Span,
};
use std::fmt;

/// Canonical SENS source extension. The extension identifies the language;
/// exact-width binary words carry program meaning.
pub const CANONICAL_SOURCE_EXTENSION: &str = ".lisp";

/// One already-bounded visible-binary source word.
///
/// Width is preserved in the variant, so equal packed numeric values from
/// different source widths remain distinct: 1 != 01 != 001.
#[derive(Clone, Copy, Eq, PartialEq)]
pub enum BinarySourceWord {
    W1(Bit1),
    W2(Bit2),
    W3(Bit3),
    W4(Bit4),
    W5(Bit5),
    W6(Bit6),
    W7(Bit7),
    W8(Bit8),
}

impl BinarySourceWord {
    pub const fn width(self) -> usize {
        match self {
            Self::W1(_) => 1,
            Self::W2(_) => 2,
            Self::W3(_) => 3,
            Self::W4(_) => 4,
            Self::W5(_) => 5,
            Self::W6(_) => 6,
            Self::W7(_) => 7,
            Self::W8(_) => 8,
        }
    }

    /// Mechanical payload only. Width must remain attached to the enum value.
    pub const fn packed_bits(self) -> u8 {
        match self {
            Self::W1(word) => word.packed_bits(),
            Self::W2(word) => word.packed_bits(),
            Self::W3(word) => word.packed_bits(),
            Self::W4(word) => word.packed_bits(),
            Self::W5(word) => word.packed_bits(),
            Self::W6(word) => word.packed_bits(),
            Self::W7(word) => word.packed_bits(),
            Self::W8(word) => word.packed_bits(),
        }
    }

    /// Lift an exact one-bit source word into the typed D1 carrier.
    ///
    /// This assigns no bit orientation: NO/YES remains language-owned.
    pub const fn d1(self) -> Option<crate::PredicateBit> {
        match self {
            Self::W1(word) => Some(crate::PredicateBit::from_word(word)),
            _ => None,
        }
    }

    /// Lift an exact two-bit source word into the typed D2 carrier.
    ///
    /// Structural roles remain language-owned; width is the only fact here.
    pub const fn d2(self) -> Option<crate::Racana2> {
        match self {
            Self::W2(word) => Some(crate::Racana2::from_word(word)),
            _ => None,
        }
    }

    /// Lift an exact three-bit source word into the typed D3 carrier.
    ///
    /// Primitive roles remain language-owned; no legacy Function8 mapping is
    /// performed at this boundary.
    pub const fn d3(self) -> Option<crate::Bija3> {
        match self {
            Self::W3(word) => Some(crate::Bija3::from_word(word)),
            _ => None,
        }
    }


    /// Lift an exact four-bit source word into the typed Core.D4 carrier.
    ///
    /// Occupancy and operation meaning remain owned by the D4 contract.
    pub const fn d4(self) -> Option<crate::CoreD4> {
        match self {
            Self::W4(word) => Some(crate::CoreD4::from_word(word)),
            _ => None,
        }
    }

    /// Lift an exact five-bit source word into the typed Core.D5 carrier.
    pub const fn d5(self) -> Option<crate::CoreD5> {
        match self {
            Self::W5(word) => Some(crate::CoreD5::from_word(word)),
            _ => None,
        }
    }

    /// Lift an exact six-bit source word into the typed Core.D6 carrier.
    pub const fn d6(self) -> Option<crate::CoreD6> {
        match self {
            Self::W6(word) => Some(crate::CoreD6::from_word(word)),
            _ => None,
        }
    }


    /// Lift an already-width-qualified Core source word into canonical
    /// domain identity without numeric inference or zero-padding.
    ///
    /// D1/D2 are outside Core identity, while D7/D8 do not gain Core identity
    /// merely from width. Only W3..W6 are admitted.
    pub const fn core_identity(self) -> Option<crate::CoreDomainIdentity> {
        match self {
            Self::W3(word) => Some(crate::CoreDomainIdentity::D3(crate::Bija3::from_word(word))),
            Self::W4(word) => Some(crate::CoreDomainIdentity::D4(crate::CoreD4::from_word(word))),
            Self::W5(word) => Some(crate::CoreDomainIdentity::D5(crate::CoreD5::from_word(word))),
            Self::W6(word) => Some(crate::CoreDomainIdentity::D6(crate::CoreD6::from_word(word))),
            Self::W1(_) | Self::W2(_) | Self::W7(_) | Self::W8(_) => None,
        }
    }
}

impl From<crate::PredicateBit> for BinarySourceWord {
    fn from(value: crate::PredicateBit) -> Self {
        Self::W1(value.word())
    }
}

impl From<crate::Racana2> for BinarySourceWord {
    fn from(value: crate::Racana2) -> Self {
        Self::W2(value.word())
    }
}

impl From<crate::Bija3> for BinarySourceWord {
    fn from(value: crate::Bija3) -> Self {
        Self::W3(value.word())
    }
}


impl From<crate::CoreD4> for BinarySourceWord {
    fn from(value: crate::CoreD4) -> Self {
        Self::W4(value.word())
    }
}

impl From<crate::CoreD5> for BinarySourceWord {
    fn from(value: crate::CoreD5) -> Self {
        Self::W5(value.word())
    }
}

impl From<crate::CoreD6> for BinarySourceWord {
    fn from(value: crate::CoreD6) -> Self {
        Self::W6(value.word())
    }
}

impl fmt::Display for BinarySourceWord {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{:0width$b}",
            self.packed_bits(),
            width = self.width()
        )
    }
}

impl fmt::Debug for BinarySourceWord {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "BinarySourceWord<{}>({self})", self.width())
    }
}

/// One canonical binary word together with its exact byte span in UTF-8 source.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct BinarySourceToken {
    pub word: BinarySourceWord,
    pub span: Span,
}

/// Tokenize canonical visible-binary SENS source.
///
/// Whitespace separates words. Semicolon starts a comment through end-of-line.
/// Every non-comment token must contain only 0/1 and have width 1..=8.
/// This function performs no semantic lookup and no human-name fallback.
pub fn parse_binary_source_words(source: &str) -> Result<Vec<BinarySourceToken>, LanguageError> {
    let bytes = source.as_bytes();
    let mut cursor = 0usize;
    let mut tokens = Vec::new();

    while cursor < bytes.len() {
        match bytes[cursor] {
            b if b.is_ascii_whitespace() => cursor += 1,
            b';' => {
                while cursor < bytes.len() && bytes[cursor] != b'\n' {
                    cursor += 1;
                }
            }
            _ => {
                let start = cursor;
                while cursor < bytes.len()
                    && !bytes[cursor].is_ascii_whitespace()
                    && bytes[cursor] != b';'
                {
                    cursor += 1;
                }
                let token = &source[start..cursor];
                let word = parse_word(token).ok_or_else(|| {
                    let message = if token.len() > 8
                        && token.bytes().all(|byte| matches!(byte, b'0' | b'1'))
                    {
                        "canonical SENS source word exceeds bounded 8-bit carrier"
                    } else {
                        "canonical SENS source accepts only exact-width binary words"
                    };
                    LanguageError::new(
                        ErrorKind::Parse,
                        message,
                        Span { start, end: cursor },
                    )
                })?;
                tokens.push(BinarySourceToken {
                    word,
                    span: Span { start, end: cursor },
                });
            }
        }
    }

    Ok(tokens)
}

fn parse_word(token: &str) -> Option<BinarySourceWord> {
    if token.is_empty() || token.len() > 8 {
        return None;
    }
    if !token.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
        return None;
    }

    let mut packed = 0u8;
    for byte in token.bytes() {
        packed = (packed << 1) | (byte - b'0');
    }

    Some(match token.len() {
        1 => BinarySourceWord::W1(Bit1::new(packed)?),
        2 => BinarySourceWord::W2(Bit2::new(packed)?),
        3 => BinarySourceWord::W3(Bit3::new(packed)?),
        4 => BinarySourceWord::W4(Bit4::new(packed)?),
        5 => BinarySourceWord::W5(Bit5::new(packed)?),
        6 => BinarySourceWord::W6(Bit6::new(packed)?),
        7 => BinarySourceWord::W7(Bit7::new(packed)?),
        8 => BinarySourceWord::W8(Bit8::new(packed)?),
        _ => return None,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_example_preserves_exact_word_boundaries() {
        let tokens = parse_binary_source_words("10 001 01").expect("canonical source");
        let widths: Vec<_> = tokens.iter().map(|token| token.word.width()).collect();
        let spellings: Vec<_> = tokens.iter().map(|token| token.word.to_string()).collect();

        assert_eq!(widths, vec![2, 3, 2]);
        assert_eq!(spellings, vec!["10", "001", "01"]);
        assert_eq!(tokens[0].span, Span { start: 0, end: 2 });
        assert_eq!(tokens[1].span, Span { start: 3, end: 6 });
        assert_eq!(tokens[2].span, Span { start: 7, end: 9 });
    }

    #[test]
    fn same_numeric_payload_at_different_widths_never_collapses() {
        let tokens = parse_binary_source_words("1 01 001 0001").unwrap();
        assert_eq!(
            tokens.iter().map(|t| t.word.width()).collect::<Vec<_>>(),
            [1, 2, 3, 4]
        );
        assert!(tokens.iter().all(|token| token.word.packed_bits() == 1));
        assert_ne!(tokens[0].word, tokens[1].word);
        assert_ne!(tokens[1].word, tokens[2].word);
        assert_ne!(tokens[2].word, tokens[3].word);
    }

    #[test]
    fn d1_through_d6_bridges_are_exact_and_lossless() {
        for raw in 0..=1 {
            let source = BinarySourceWord::W1(Bit1::new(raw).unwrap());
            assert_eq!(BinarySourceWord::from(source.d1().unwrap()), source);
            assert!(source.d2().is_none());
            assert!(source.d3().is_none());
            assert!(source.d4().is_none());
            assert!(source.d5().is_none());
            assert!(source.d6().is_none());
        }

        for raw in 0..=3 {
            let source = BinarySourceWord::W2(Bit2::new(raw).unwrap());
            assert_eq!(BinarySourceWord::from(source.d2().unwrap()), source);
            assert!(source.d1().is_none());
            assert!(source.d3().is_none());
            assert!(source.d4().is_none());
            assert!(source.d5().is_none());
            assert!(source.d6().is_none());
        }

        for raw in 0..=7 {
            let source = BinarySourceWord::W3(Bit3::new(raw).unwrap());
            assert_eq!(BinarySourceWord::from(source.d3().unwrap()), source);
            assert!(source.d1().is_none());
            assert!(source.d2().is_none());
            assert!(source.d4().is_none());
            assert!(source.d5().is_none());
            assert!(source.d6().is_none());
        }

        for raw in 0..=15 {
            let source = BinarySourceWord::W4(Bit4::new(raw).unwrap());
            assert_eq!(BinarySourceWord::from(source.d4().unwrap()), source);
            assert!(source.d1().is_none());
            assert!(source.d2().is_none());
            assert!(source.d3().is_none());
            assert!(source.d5().is_none());
            assert!(source.d6().is_none());
        }

        for raw in 0..=31 {
            let source = BinarySourceWord::W5(Bit5::new(raw).unwrap());
            assert_eq!(BinarySourceWord::from(source.d5().unwrap()), source);
            assert!(source.d1().is_none());
            assert!(source.d2().is_none());
            assert!(source.d3().is_none());
            assert!(source.d4().is_none());
            assert!(source.d6().is_none());
        }

        for raw in 0..=63 {
            let source = BinarySourceWord::W6(Bit6::new(raw).unwrap());
            assert_eq!(BinarySourceWord::from(source.d6().unwrap()), source);
            assert!(source.d1().is_none());
            assert!(source.d2().is_none());
            assert!(source.d3().is_none());
            assert!(source.d4().is_none());
            assert!(source.d5().is_none());
        }
    }

    #[test]
    fn d7_and_d8_do_not_gain_callable_domain_identity_by_width_alone() {
        for source in [
            BinarySourceWord::W7(Bit7::new(0).unwrap()),
            BinarySourceWord::W8(Bit8::new(0).unwrap()),
        ] {
            assert!(source.d1().is_none());
            assert!(source.d2().is_none());
            assert!(source.d3().is_none());
            assert!(source.d4().is_none());
            assert!(source.d5().is_none());
            assert!(source.d6().is_none());
        }
    }

    #[test]
    fn comments_and_whitespace_are_source_boundaries_only() {
        let tokens = parse_binary_source_words("10 ; open\n 001\t01 ; close\n").unwrap();
        assert_eq!(
            tokens
                .iter()
                .map(|token| token.word.to_string())
                .collect::<Vec<_>>(),
            ["10", "001", "01"]
        );
    }

    #[test]
    fn human_names_and_mixed_tokens_fail_closed() {
        for source in ["людина", "10x", "(10)", "01,"] {
            let error = parse_binary_source_words(source).expect_err(source);
            assert_eq!(error.kind, ErrorKind::Parse);
            assert!(error.message.contains("only exact-width binary words"));
        }
    }

    #[test]
    fn word_wider_than_bounded_carrier_fails_named() {
        let error = parse_binary_source_words("000000000").expect_err("nine bits must fail");
        assert_eq!(error.kind, ErrorKind::Parse);
        assert!(error.message.contains("exceeds bounded 8-bit carrier"));
        assert_eq!(error.span, Span { start: 0, end: 9 });
    }

    #[test]
    fn empty_and_comment_only_source_are_valid_empty_programs() {
        assert!(parse_binary_source_words("").unwrap().is_empty());
        assert!(parse_binary_source_words(" ; comment only\n").unwrap().is_empty());
    }
}
