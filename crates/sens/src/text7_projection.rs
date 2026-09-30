use crate::Text7;
use std::fmt;

use crate::text7_projection_generated as generated;

/// Human layout used only to project spelling to/from canonical Text7 cells.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Text7Layout {
    Uk,
    SaSlp1,
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
}

pub const TEXT7_UPSTREAM_REVISION: &str = generated::UPC7_SOURCE_REVISION;
pub const TEXT7_TABLE_SHA256: &str = generated::UPC7_TABLE_SHA256;
pub const TEXT7_LAYOUT_SHA256: &str = generated::UPC7_LAYOUT_SHA256;

type Candidate = (&'static str, Option<&'static [u8]>);

fn projection(layout: Text7Layout) -> (&'static [Candidate], &'static [Option<&'static str>; 128]) {
    match layout {
        Text7Layout::Uk => (generated::UK_ENCODE, &generated::UK_RENDER),
        Text7Layout::SaSlp1 => (generated::SA_SLP1_ENCODE, &generated::SA_SLP1_RENDER),
    }
}

/// Lower one human spelling through a selected pinned UPC-7 layout.
///
/// Candidate order is generated longest-first from upstream. A source alias
/// may therefore expand to several cells, while canonical Text identity is
/// only the resulting cell stream.
pub fn encode_text7(text: &str, layout: Text7Layout) -> Result<Text7, Text7ProjectionError> {
    let (candidates, _) = projection(layout);
    let mut cells = Vec::new();
    let mut byte_offset = 0usize;

    while byte_offset < text.len() {
        let rest = &text[byte_offset..];
        let Some((spelling, projected)) = candidates
            .iter()
            .find(|(spelling, _)| rest.starts_with(*spelling))
        else {
            return Err(Text7ProjectionError::UnknownSpelling {
                layout,
                byte_offset,
            });
        };

        let Some(projected) = projected else {
            return Err(Text7ProjectionError::UnassignedSpelling {
                layout,
                byte_offset,
                spelling,
            });
        };

        cells.extend_from_slice(projected);
        byte_offset += spelling.len();
    }

    Ok(Text7::from_cells(cells)
        .expect("generated UPC-7 projection must contain only seven-bit cells"))
}

/// Render canonical Text7 through one human layout.
///
/// A layout is allowed to be partial. Missing renderings fail instead of
/// inventing a near-equivalent spelling.
pub fn render_text7(text: &Text7, layout: Text7Layout) -> Result<String, Text7ProjectionError> {
    let (_, render) = projection(layout);
    let mut out = String::new();

    for (index, &cell) in text.cells().iter().enumerate() {
        let Some(spelling) = render[cell as usize] else {
            return Err(Text7ProjectionError::UnrenderableCell {
                layout,
                index,
                cell,
            });
        };
        out.push_str(spelling);
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
