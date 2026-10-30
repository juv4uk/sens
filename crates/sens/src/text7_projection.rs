//! Human text data through the current ratified D7 v2 keyboard coordinates.
//! A quoted function identity must resolve through the domain ladder first;
//! this projection is for text DATA only and never confers callability.

use crate::{d7_keyboard, Text7};
use std::fmt;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Text7Layout {
    Uk,
    SaSlp1,
    SaIast,
    SaDeva,
    En,
    EnIpa,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Text7ProjectionError {
    UnknownSpelling {
        layout: Text7Layout,
        byte_offset: usize,
    },
    UnassignedSpelling {
        layout: Text7Layout,
        byte_offset: usize,
        spelling: &'static str,
    },
    UnrenderableCell {
        layout: Text7Layout,
        index: usize,
        cell: u8,
    },
    AmbiguousGlyphSequence {
        layout: Text7Layout,
    },
}

/// Only the actual v2 keyboard surfaces are mappings. The former phonemic
/// SLP1, IAST and IPA aliases are never guessed from unrelated v2 coordinates.
fn current_mode(layout: Text7Layout) -> Option<d7_keyboard::D7Mode> {
    match layout {
        Text7Layout::Uk => Some(d7_keyboard::D7Mode::Uk),
        Text7Layout::SaDeva => Some(d7_keyboard::D7Mode::San),
        Text7Layout::En => Some(d7_keyboard::D7Mode::En),
        Text7Layout::SaSlp1 | Text7Layout::SaIast | Text7Layout::EnIpa => None,
    }
}

/// The selected text projection must be known before a W7 data stream is made.
/// D2 punctuation is structural only in the *source grammar*, not in a text value.
pub fn encode_text7(text: &str, layout: Text7Layout) -> Result<Text7, Text7ProjectionError> {
    let mode = current_mode(layout).ok_or(Text7ProjectionError::UnknownSpelling {
        layout,
        byte_offset: 0,
    })?;
    let words = d7_keyboard::encode(text, mode).map_err(|err| {
        let byte_offset = match err {
            d7_keyboard::D7CodecError::CharacterNotAdmitted(ch) => text
                .char_indices()
                .find(|(_, candidate)| *candidate == ch)
                .map(|(offset, _)| offset)
                .unwrap_or(0),
            _ => 0,
        };
        Text7ProjectionError::UnknownSpelling {
            layout,
            byte_offset,
        }
    })?;
    Text7::from_cells(words).map_err(|_| Text7ProjectionError::UnknownSpelling {
        layout,
        byte_offset: 0,
    })
}

pub fn render_text7(text: &Text7, layout: Text7Layout) -> Result<String, Text7ProjectionError> {
    // Human-only IAST display is generated from the same 128 exact W7 cells.
    // Digraphs and dependent vowel markers cannot be decoded as a single
    // scalar Sanskrit keyboard code: SaIast render does NOT grant encode.
    if layout == Text7Layout::SaIast {
        let mut out = String::new();
        for (index, &cell) in text.cells().iter().enumerate() {
            let word = crate::BinarySourceWord::W7(crate::Bit7::new(cell).ok_or(
                Text7ProjectionError::UnrenderableCell {
                    layout,
                    index,
                    cell,
                },
            )?);
            let identity = crate::DomainIdentity::from_source_word(word);
            let glyph = crate::semantic_registry::surface_for_domain_identity(identity, "sa")
                .ok_or(Text7ProjectionError::UnrenderableCell {
                    layout,
                    index,
                    cell,
                })?;
            out.push_str(glyph);
        }
        return Ok(out);
    }
    let mode = current_mode(layout).ok_or(Text7ProjectionError::UnknownSpelling {
        layout,
        byte_offset: 0,
    })?;
    d7_keyboard::decode(text.cells(), mode).map_err(|_| Text7ProjectionError::UnrenderableCell {
        layout,
        index: 0,
        cell: text.cells().first().copied().unwrap_or(0),
    })
}

impl fmt::Display for Text7ProjectionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UnknownSpelling {
                layout,
                byte_offset,
            } => write!(
                f,
                "{layout:?} has no current D7 v2 glyph at byte {byte_offset}"
            ),
            Self::UnassignedSpelling {
                layout,
                byte_offset,
                spelling,
            } => write!(
                f,
                "{layout:?} unsupported {spelling:?} at byte {byte_offset}"
            ),
            Self::UnrenderableCell {
                layout,
                index,
                cell,
            } => write!(
                f,
                "{layout:?} cannot display W7:{cell:07b} at index {index}"
            ),
            Self::AmbiguousGlyphSequence { layout } => {
                write!(f, "{layout:?} loses exact W7 cell boundaries")
            }
        }
    }
}
impl std::error::Error for Text7ProjectionError {}

#[cfg(test)]
mod tests {
    use super::{encode_text7, render_text7, Text7Layout};

    #[test]
    fn ukrainian_projection_encodes_glyphs_as_exact_w7_text_cells() {
        // UTF-8 "а" occupies two host bytes, but the ratified Ukrainian
        // projection maps that one glyph to the exact D7/W7 cell 1100110.
        // The following ASCII digit maps to its own cell; neither spelling
        // becomes a numeric value or a callable function identity here.
        let text = encode_text7("а1", Text7Layout::Uk).expect("admitted D7 text");

        assert_eq!(text.cells(), &[0b1100110, 0b0110001]);
        assert_eq!(text.to_canonical_wire_token(), "#t7:6631");
        assert_eq!(text.to_packed_w7().bit_len(), 14);
        assert_eq!(render_text7(&text, Text7Layout::Uk).unwrap(), "а1");
        assert_eq!(render_text7(&text, Text7Layout::En).unwrap(), "f1");
    }

    #[test]
    fn ukrainian_projection_rejects_glyphs_without_a_ratified_d7_cell() {
        assert!(encode_text7("ё", Text7Layout::Uk).is_err());
    }
}
