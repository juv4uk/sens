use crate::Text7;
use std::fmt;

use crate::text7_projection_generated as generated;

/// Human layout used only to project spelling to/from canonical Text7 cells.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Text7Layout {
    Uk,
    SaSlp1,
    SaIast,
    SaDeva,
}

/// Fail-closed boundary error. No failed human spelling becomes Text7 identity.
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
    AmbiguousGlyphSequence { layout: Text7Layout },
}

pub const TEXT7_UPSTREAM_REVISION: &str = generated::UPC7_SOURCE_REVISION;
pub const TEXT7_TABLE_SHA256: &str = generated::UPC7_TABLE_SHA256;
pub const TEXT7_LAYOUT_SHA256: &str = generated::UPC7_LAYOUT_SHA256;

/// Old donor pins are retained as *historical evidence only*. Active
/// Text7 projections below use the ratified #3572 D7 coordinates.
#[inline]
fn d2_owned_glyph(glyph: char) -> bool {
    glyph.is_whitespace() || matches!(glyph, '(' | ')' | '.')
}

#[inline]
fn d2_shadow_cell(cell: u8) -> bool {
    matches!(cell, 0b1100000 | 0b1100001 | 0b1100010 |
                   0b1100011 | 0b1100100 | 0b1111010)
}

fn sanskrit_layout(layout: Text7Layout) -> Option<&'static str> {
    match layout {
        Text7Layout::SaSlp1 => Some("slp1"),
        Text7Layout::SaIast => Some("iast"),
        Text7Layout::SaDeva => Some("deva"),
        Text7Layout::Uk => None,
    }
}

/// Encode Ukrainian keyboard symbols or an explicitly selected Sanskrit
/// projection into exactly seven-bit D7 cells. No D2 punctuation in D7.
pub fn encode_text7(text: &str, layout: Text7Layout) -> Result<Text7, Text7ProjectionError> {
    let mut cells: Vec<u8> = Vec::new();
    let mut at = 0usize;
    while at < text.len() {
        let rest = &text[at..];
        let current = rest.chars().next().expect("nonempty rest");
        if d2_owned_glyph(current) {
            return Err(Text7ProjectionError::UnknownSpelling {
                layout, byte_offset: at,
            });
        }

        match layout {
            Text7Layout::Uk => {
                let lower: String = current.to_lowercase().collect();
                let glyph = if current.is_uppercase() {
                    lower.as_str()
                } else {
                    &rest[..current.len_utf8()]
                };
                let cell = crate::semantic_registry::d7_uk_keyboard_cell(glyph)
                    .ok_or(Text7ProjectionError::UnknownSpelling {
                        layout, byte_offset: at,
                    })?;
                if current.is_uppercase() {
                    cells.push(0b0100010); // owner-ratified D7 uppercase-next
                }
                cells.push(cell);
                at += current.len_utf8();
            }
            _ => {
                let spelling = sanskrit_layout(layout).expect("Sanskrit branch");
                let (length, cell) =
                    crate::semantic_registry::d7_sanskrit_longest_prefix(rest, spelling)
                    .ok_or(Text7ProjectionError::UnknownSpelling {
                        layout, byte_offset: at,
                    })?;
                if d2_shadow_cell(cell) {
                    return Err(Text7ProjectionError::UnknownSpelling {
                        layout, byte_offset: at,
                    });
                }
                cells.push(cell);
                at += length;
            }
        }
    }

    Ok(Text7::from_cells(cells).expect("ratified D7 cells fit seven bits"))
}

/// Render Unicode presentation of exact Sound/Text cells, NOT a D2 program.
/// Any absent glyph or ambiguous cell boundary is an error.
pub fn render_text7(text: &Text7, layout: Text7Layout) -> Result<String, Text7ProjectionError> {
    let mut out = String::new();
    let cells = text.cells();
    let mut index = 0usize;
    while index < cells.len() {
        let mut cell = cells[index];
        let uppercase = layout == Text7Layout::Uk && cell == 0b0100010;
        if uppercase {
            index += 1;
            let Some(&next) = cells.get(index) else {
                return Err(Text7ProjectionError::UnrenderableCell {
                    layout, index: index - 1, cell,
                });
            };
            cell = next;
        }
        if d2_shadow_cell(cell) {
            return Err(Text7ProjectionError::UnrenderableCell {
                layout, index, cell,
            });
        }
        let glyph = match layout {
            Text7Layout::Uk => crate::semantic_registry::d7_uk_keyboard_glyph(cell),
            _ => crate::semantic_registry::d7_sanskrit_glyph(
                cell, sanskrit_layout(layout).expect("Sanskrit branch")
            ),
        }.ok_or(Text7ProjectionError::UnrenderableCell {
            layout, index, cell,
        })?;
        if glyph.chars().any(d2_owned_glyph) {
            return Err(Text7ProjectionError::UnrenderableCell {
                layout, index, cell,
            });
        }
        if uppercase {
            if glyph.chars().count() != 1 || !glyph.chars().all(char::is_lowercase) {
                return Err(Text7ProjectionError::UnrenderableCell {
                    layout, index, cell,
                });
            }
            out.extend(glyph.chars().flat_map(char::to_uppercase));
        } else {
            out.push_str(glyph);
        }
        index += 1;
    }
    if encode_text7(&out, layout)?.cells() != cells {
        return Err(Text7ProjectionError::AmbiguousGlyphSequence { layout });
    }
    Ok(out)
}

impl fmt::Display for Text7ProjectionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UnknownSpelling {
                layout,
                byte_offset,
            } => write!(
                f,
                "{layout:?} has no admitted Text7 spelling at source byte {byte_offset}"
            ),
            Self::UnassignedSpelling {
                layout,
                byte_offset,
                spelling,
            } => write!(
                f,
                "{layout:?} spelling {spelling:?} at source byte {byte_offset} has no admitted Text7 cells"
            ),
            Self::UnrenderableCell {
                layout,
                index,
                cell,
            } => write!(
                f,
                "{layout:?} cannot render Text7 cell {cell:07b} at index {index}"
            ),
            Self::AmbiguousGlyphSequence { layout } => write!(f, "{layout:?} glyph concatenation loses D7 word boundaries"),
        }
    }
}

impl std::error::Error for Text7ProjectionError {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ukrainian_sequence_and_case_projection_preserve_identity() {
        let ya = encode_text7("я", Text7Layout::Uk).unwrap();
        assert_eq!(ya, encode_text7("йа", Text7Layout::Uk).unwrap());
        assert_eq!(ya, encode_text7("Я", Text7Layout::Uk).unwrap());

        let shcha = encode_text7("щ", Text7Layout::Uk).unwrap();
        assert_eq!(shcha, encode_text7("шч", Text7Layout::Uk).unwrap());
        assert_eq!(shcha, encode_text7("Щ", Text7Layout::Uk).unwrap());
    }

    #[test]
    fn ukrainian_affricate_longest_match_stays_one_cell() {
        let lower = encode_text7("дж", Text7Layout::Uk).unwrap();
        let title = encode_text7("Дж", Text7Layout::Uk).unwrap();
        let upper = encode_text7("ДЖ", Text7Layout::Uk).unwrap();

        assert_eq!(lower.cells(), &[0x3f]);
        assert_eq!(lower, title);
        assert_eq!(lower, upper);
    }

    #[test]
    fn slp1_case_remains_phonologically_distinct() {
        let lower = encode_text7("k", Text7Layout::SaSlp1).unwrap();
        let upper = encode_text7("K", Text7Layout::SaSlp1).unwrap();

        assert_ne!(lower, upper);
        assert_eq!(lower.cells(), &[0x00]);
        assert_eq!(upper.cells(), &[0x01]);
    }

    #[test]
    fn switching_human_layout_does_not_change_code_stream() {
        let uk = encode_text7("к", Text7Layout::Uk).unwrap();
        let rendered = render_text7(&uk, Text7Layout::SaSlp1).unwrap();
        let sa = encode_text7(&rendered, Text7Layout::SaSlp1).unwrap();

        assert_eq!(rendered, "k");
        assert_eq!(uk, sa);
    }

    #[test]
    fn sanskrit_slp1_iast_and_devanagari_share_text7_identity() {
        let slp1 = encode_text7("K", Text7Layout::SaSlp1).unwrap();
        let iast = encode_text7("kh", Text7Layout::SaIast).unwrap();
        let deva = encode_text7("ख", Text7Layout::SaDeva).unwrap();

        assert_eq!(slp1.cells(), &[0x01]);
        assert_eq!(slp1, iast);
        assert_eq!(slp1, deva);
        assert_eq!(render_text7(&slp1, Text7Layout::SaIast).unwrap(), "kh");
        assert_eq!(render_text7(&slp1, Text7Layout::SaDeva).unwrap(), "ख");
    }

    #[test]
    fn unknown_input_and_unrenderable_cells_fail_closed() {
        assert!(matches!(
            encode_text7("A", Text7Layout::Uk),
            Err(Text7ProjectionError::UnknownSpelling { .. })
        ));

        let sanskrit_only = Text7::from_cells(vec![0x01]).unwrap();
        assert!(matches!(
            render_text7(&sanskrit_only, Text7Layout::Uk),
            Err(Text7ProjectionError::UnrenderableCell {
                index: 0,
                cell: 0x01,
                ..
            })
        ));
    }
}
