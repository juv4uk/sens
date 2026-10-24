//! Проєкція української клавіатурної поверхні у точні D7:W7 слова.
//!
//! Цей модуль належить SENS і не пакує фізичний T5M. Zig може прийняти
//! повернуті exact-width слова та виконати лише транспортне кодування.

use crate::{semantic_registry, BinarySourceWord, Bit7};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum D7ProjectionError {
    EmptyText,
    UnassignedKeyboardGlyph { byte_offset: usize },
    NonD7Word,
    UnrenderableD7Cell,
    AmbiguousText,
}

fn keyboard_d7_words(source: &str) -> Result<Vec<BinarySourceWord>, D7ProjectionError> {
    if source.is_empty() {
        return Err(D7ProjectionError::EmptyText);
    }
    source
        .char_indices()
        .map(|(offset, ch)| {
            let mut utf8 = [0u8; 4];
            let glyph = ch.encode_utf8(&mut utf8);
            let cell = semantic_registry::d7_uk_keyboard_cell(glyph).ok_or(
                D7ProjectionError::UnassignedKeyboardGlyph {
                    byte_offset: offset,
                },
            )?;
            Ok(BinarySourceWord::W7(
                Bit7::new(cell).expect("D7 table is exactly W7"),
            ))
        })
        .collect()
}

/// Відображає тільки ратифіковані українські клавіатурні знаки у точні W7.
/// Фізичне T5M-кодування тут не виконується.
pub fn encode_d7_uk_words(source: &str) -> Result<Vec<BinarySourceWord>, D7ProjectionError> {
    keyboard_d7_words(source)
}

/// Відображає лише точні W7-слова; D2-слова не стають текстом чи пунктуацією.
pub fn decode_d7_uk_words(words: &[BinarySourceWord]) -> Result<String, D7ProjectionError> {
    let mut text = String::new();
    for word in words {
        let BinarySourceWord::W7(cell) = word else {
            return Err(D7ProjectionError::NonD7Word);
        };
        let glyph = semantic_registry::d7_uk_keyboard_glyph(cell.packed_bits())
            .ok_or(D7ProjectionError::UnrenderableD7Cell)?;
        text.push_str(glyph);
    }
    if keyboard_d7_words(&text)?.as_slice() != words {
        return Err(D7ProjectionError::AmbiguousText);
    }
    Ok(text)
}
