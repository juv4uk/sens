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
    En,
    EnIpa,
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
    (glyph.is_whitespace() && glyph != ' ') || matches!(glyph, '(' | ')')
}

#[inline]
fn d2_shadow_cell(cell: u8) -> bool {
    matches!(cell, 0b1100001 | 0b1100010 | 0b1100011 | 0b1100100)
}

fn text_layout_name(layout: Text7Layout) -> Option<&'static str> {
    match layout {
        Text7Layout::SaSlp1 => Some("slp1"),
        Text7Layout::SaIast => Some("iast"),
        Text7Layout::SaDeva => Some("deva"),
        Text7Layout::En => Some("en"),
        Text7Layout::EnIpa => Some("en-ipa"),
        Text7Layout::Uk => None,
    }
}

/// Encode Unicode text data as existing exact W7 D7 cells.
/// Space and period are TEXT when inside a Text7 record; external D2
/// grammatical tokens keep their OWN 2-bit parsing context.
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
                let spelling = text_layout_name(layout).expect("non-Ukrainian text surface");
                let (length, cell) =
                    crate::semantic_registry::d7_text_surface_longest_prefix(rest, spelling)
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
            _ => crate::semantic_registry::d7_text_surface_glyph(
                cell, text_layout_name(layout).expect("non-Ukrainian text surface")
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
    fn ukrainian_keyboard_and_uppercase_are_exact_d7_words() {
        let lower = encode_text7("кіт", Text7Layout::Uk).unwrap();
        assert_eq!(lower.cells(), &[0x00, 0x44, 0x0f]);
        assert_eq!(render_text7(&lower, Text7Layout::Uk).unwrap(), "кіт");

        let title = encode_text7("Кіт", Text7Layout::Uk).unwrap();
        assert_eq!(title.cells(), &[0x22, 0x00, 0x44, 0x0f]);
        assert_eq!(render_text7(&title, Text7Layout::Uk).unwrap(), "Кіт");

        // These Ukrainian keys have no distinct ratified D7 resident yet.
        // Never silently collapse them into another sequence of sound cells.
        for missing in ["я", "щ", "є", "ї", "ю"] {
            assert!(matches!(encode_text7(missing, Text7Layout::Uk),
                Err(Text7ProjectionError::UnknownSpelling { .. })));
        }
    }

    #[test]
    fn ukrainian_digraph_uses_two_keyboard_symbols_not_old_sound_alias() {
        let lower = encode_text7("дж", Text7Layout::Uk).unwrap();
        assert_eq!(lower.cells(), &[0x11, 0x25]);
        assert_eq!(render_text7(&lower, Text7Layout::Uk).unwrap(), "дж");
        let title = encode_text7("Дж", Text7Layout::Uk).unwrap();
        assert_eq!(title.cells(), &[0x22, 0x11, 0x25]);
        assert_ne!(lower, title);
        let upper = encode_text7("ДЖ", Text7Layout::Uk).unwrap();
        assert_eq!(upper.cells(), &[0x22, 0x11, 0x22, 0x25]);
    }

    #[test]
    fn context_keeps_space_period_as_text_not_d2_syntax() {
        for punctuation in ["\t", "\n", "(", ")"] {
            assert!(matches!(encode_text7(punctuation, Text7Layout::Uk),
                Err(Text7ProjectionError::UnknownSpelling { .. })));
        }
        for cell in [0x61, 0x62, 0x63, 0x64] {
            let text = Text7::from_cells(vec![cell]).unwrap();
            assert!(render_text7(&text, Text7Layout::Uk).is_err());
        }
        for layout in [Text7Layout::Uk, Text7Layout::SaIast,
                       Text7Layout::SaDeva, Text7Layout::En, Text7Layout::EnIpa] {
            let words = encode_text7(" .", layout).unwrap();
            assert_eq!(words.cells(), &[0x60, 0x7a]);
            assert_eq!(render_text7(&words, layout).unwrap(), " .");
        }
        let slp1 = encode_text7(".", Text7Layout::SaSlp1).unwrap();
        assert_eq!(slp1.cells(), &[0x6b]); // danda, not ASCII period
        assert_ne!(slp1.cells(), &[0x7a]);
    }

    #[test]
    fn english_and_ipa_are_explicit_sound_projections_not_english_orthography() {
        for (roman, ipa, cell) in [("b", "b", 0x16), ("g", "ɡ", 0x02),
                                   ("m", "m", 0x18), ("y", "j", 0x26),
                                   ("k", "k", 0x00), ("p", "p", 0x14)] {
            assert_eq!(encode_text7(roman, Text7Layout::En).unwrap().cells(), &[cell]);
            assert_eq!(encode_text7(ipa, Text7Layout::EnIpa).unwrap().cells(), &[cell]);
        }
        assert_eq!(encode_text7("ŋ", Text7Layout::EnIpa).unwrap().cells(), &[0x04]);
        for false_friend in ["th", "θ", "ð", "ə"] {
            assert!(encode_text7(false_friend, Text7Layout::En).is_err());
            assert!(encode_text7(false_friend, Text7Layout::EnIpa).is_err());
        }
        let english = encode_text7("b. m", Text7Layout::En).unwrap();
        assert_eq!(english.cells(), &[0x16, 0x7a, 0x60, 0x18]);
        assert_eq!(render_text7(&english, Text7Layout::En).unwrap(), "b. m");
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
