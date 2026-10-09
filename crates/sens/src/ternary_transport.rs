//! Дослідний трійковий ТРАНСПОРТ двійкових слів SENS.
//!
//! Це не трійкова семантика: D1..D9 залишаються двійковими.
//! Транспортні цифри 0/1 відтворюють біт, 2 відділяє слова.
//! Упаковано п'ять тритів в один фізичний байт (3^5=243).
//! Фізичний EOF дає сам файл: окремий 22 не потрібний.
//! Завершальна неповна п'ятірка доповнюється лише тритами 2,
//! яких має бути 0..4; довший хвіст відхиляється.
//! Жодного D7-пробілу чи нового D10-резидента тут немає.
//! Number D24+ ще не допускається до цього механічного носія.

use crate::{parse_binary_source_words, parse_canonical_binary, BinarySourceWord};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TernaryTransportError {
    EmptyProgram,
    InvalidBinaryProjection,
    InvalidProgramSyntax,
    InvalidPhysicalByte,
    EmptyDomainWord,
    UnsupportedDomainWidth,
    InvalidTail,
    NoncanonicalEncoding,
    TransportTooLarge,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TernaryTransportAccounting {
    pub word_count: usize,
    pub semantic_bits: usize,
    pub separating_trits: usize,
    pub encoded_trits: usize,
    pub tail_trits: usize,
    pub physical_bytes: usize,
    pub physical_bits: usize,
}

const TRITS_PER_BYTE: usize = 5;
const MAX_FILE_BYTES: usize = 4 * 1024 * 1024;

/// Структурно зв'язані доменні слова віддані вже наявним типом.
/// Транспорт не змінює їхню двійкову ідентичність.
pub fn encode_ternary_words(
    words: &[BinarySourceWord],
) -> Result<Vec<u8>, TernaryTransportError> {
    if words.is_empty() {
        return Err(TernaryTransportError::EmptyProgram);
    }
    let mut trits = Vec::new();
    for (position, word) in words.iter().copied().enumerate() {
        if position != 0 {
            trits.push(2);
        }
        let width = word.width();
        if !(1..=9).contains(&width) {
            return Err(TernaryTransportError::UnsupportedDomainWidth);
        }
        let value = word.packed_bits();
        for shift in (0..width).rev() {
            trits.push(((value >> shift) & 1) as u8);
        }
    }
    // У файлі EOF вже відомий з його фізичної довжини.
    // Роздільник 2 пишеться ВИКЛЮЧНО між двома словами.
    // Трити 2 в кінці — тільки байтовий padding (0..4 шт.).
    while trits.len() % TRITS_PER_BYTE != 0 {
        trits.push(2);
    }
    let byte_len = trits.len() / TRITS_PER_BYTE;
    if byte_len > MAX_FILE_BYTES {
        return Err(TernaryTransportError::TransportTooLarge);
    }
    let mut encoded = Vec::with_capacity(byte_len);
    let (chunks, remainder) = trits.as_chunks::<TRITS_PER_BYTE>();
    debug_assert!(remainder.is_empty(), "T5 encoding pads to whole five-trit bytes");
    for five in chunks {
        let value = five.iter().fold(0u16, |n, d| n * 3 + u16::from(*d));
        // Кожна п'ятірка дає рівно діапазон 0..=242.
        encoded.push(value as u8);
    }
    Ok(encoded)
}

/// Читає ФІЗИЧНІ байти, відновлює трити, розбиває на слова
/// лише за цифрою 2, а потім отримує точні типи D1..D9.
/// Доказом безпомилковості носія є канонічний повторний encode.
pub fn decode_ternary_words(
    data: &[u8],
) -> Result<Vec<BinarySourceWord>, TernaryTransportError> {
    if data.is_empty() {
        return Err(TernaryTransportError::EmptyProgram);
    }
    if data.len() > MAX_FILE_BYTES {
        return Err(TernaryTransportError::TransportTooLarge);
    }
    let mut trits = Vec::with_capacity(data.len() * TRITS_PER_BYTE);
    for byte in data.iter().copied() {
        if byte >= 243 {
            return Err(TernaryTransportError::InvalidPhysicalByte);
        }
        let mut value = byte;
        let mut digits = [0u8; TRITS_PER_BYTE];
        for digit in digits.iter_mut().rev() {
            *digit = value % 3;
            value /= 3;
        }
        trits.extend_from_slice(&digits);
    }
    // Не слід шукати EOS=22: межу файла вже дає кількість байтів.
    // Після останнього слова може бути тільки 0..4 trit-2 як padding.
    // У самих словах допустимі лише 0 та 1, тому фізичний хвіст
    // однозначно відділяється від останнього слова.
    let tail = trits.iter().rev().take_while(|digit| **digit == 2).count();
    if tail >= TRITS_PER_BYTE {
        return Err(TernaryTransportError::InvalidTail);
    }
    trits.truncate(trits.len() - tail);
    if trits.is_empty() {
        return Err(TernaryTransportError::EmptyDomainWord);
    }

    let mut parts = Vec::<String>::new();
    let mut current = String::new();
    for digit in trits {
        match digit {
            0 | 1 => {
                current.push(char::from(b'0' + digit));
                if current.len() > 9 {
                    return Err(TernaryTransportError::UnsupportedDomainWidth);
                }
            }
            2 => {
                if current.is_empty() {
                    return Err(TernaryTransportError::EmptyDomainWord);
                }
                parts.push(std::mem::take(&mut current));
            }
            _ => unreachable!(),
        }
    }
    if current.is_empty() {
        return Err(TernaryTransportError::EmptyDomainWord);
    }
    parts.push(current);
    let visible = parts.join(" ");
    let tokens = parse_binary_source_words(&visible)
        .map_err(|_| TernaryTransportError::UnsupportedDomainWidth)?;
    let words: Vec<_> = tokens.into_iter().map(|token| token.word).collect();
    // Зайвий байт, неоднозначний або неканонічний хвіст — відмова.
    if encode_ternary_words(&words)? != data {
        return Err(TernaryTransportError::NoncanonicalEncoding);
    }
    Ok(words)
}

/// Вертикальний вигляд — тільки для людини, newline не є
/// тритом і не записується в сам .sens файл.
pub fn render_ternary_words_vertical(words: &[BinarySourceWord]) -> String {
    words.iter().map(|word| format!("{word}\n")).collect()
}

/// Звичайне людське представлення фізичного .sens: транспортний трит 2
/// перетворюється тільки на пробіл МІЖ словами. Кінцевий
/// padding ніколи не потрапляє у відкритий для людини текст.
/// Це НЕ фізичний вміст файла: не записувати цей рядок у .sens.
pub fn render_ternary_words_spaced(words: &[BinarySourceWord]) -> String {
    words.iter().map(ToString::to_string).collect::<Vec<_>>().join(" ")
}

/// Відкрити .sens у вигляді вихідних двійкових слів, розділених
/// одним ASCII пробілом. Декодер спершу перевіряє канонічний T5
/// та синтаксичні закони D2. Не відображати жодної транспортної '2'.
pub fn open_ternary_program(data: &[u8]) -> Result<String, TernaryTransportError> {
    let words = decode_ternary_program(data)?;
    Ok(render_ternary_words_spaced(&words))
}

/// Поки що адаптер приймає видиму точну двійкову проєкцію D1..D9,
/// а не довільні історичні чи українські Lisp-імена.
pub fn encode_binary_projection_ternary(
    projection: &str,
) -> Result<Vec<u8>, TernaryTransportError> {
    let words = parse_binary_source_words(projection)
        .map_err(|_| TernaryTransportError::InvalidBinaryProjection)?;
    if words.is_empty() {
        return Err(TernaryTransportError::EmptyProgram);
    }
    parse_canonical_binary(projection)
        .map_err(|_| TernaryTransportError::InvalidProgramSyntax)?;
    encode_ternary_words(&words.iter().map(|word| word.word).collect::<Vec<_>>())
}

/// Формально валідує повноту D2-структури через наявний
/// рідер SENS, а не вигадує ще один парсер у transport.
pub fn decode_ternary_program(
    data: &[u8],
) -> Result<Vec<BinarySourceWord>, TernaryTransportError> {
    let words = decode_ternary_words(data)?;
    let projection = render_ternary_words_vertical(&words);
    parse_canonical_binary(&projection)
        .map_err(|_| TernaryTransportError::InvalidProgramSyntax)?;
    Ok(words)
}

/// Вартість носія, включно з фізичним заповненням, але БЕЗ EOS.
/// Трити і біти — різні одиниці; физичні байти враховано окремо.
pub fn ternary_transport_accounting(
    words: &[BinarySourceWord],
) -> Result<TernaryTransportAccounting, TernaryTransportError> {
    let data = encode_ternary_words(words)?;
    let semantic_bits = words.iter().map(|word| word.width()).sum::<usize>();
    let separating_trits = words.len() - 1;
    let encoded_trits = semantic_bits + separating_trits;
    let tail_trits = data.len() * TRITS_PER_BYTE - encoded_trits;
    Ok(TernaryTransportAccounting {
        word_count: words.len(),
        semantic_bits,
        separating_trits,
        encoded_trits,
        tail_trits,
        physical_bytes: data.len(),
        physical_bits: data.len() * 8,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn words(source: &str) -> Vec<BinarySourceWord> {
        parse_binary_source_words(source).unwrap()
            .into_iter().map(|token| token.word).collect()
    }

    #[test]
    fn five_binary_words_survive_without_file_whitespace() {
        let source = "10 001 00 000 01";
        let original = words(source);
        let binary = encode_binary_projection_ternary(source).unwrap();
        assert_eq!(binary.len(), 4);
        assert_eq!(decode_ternary_program(&binary).unwrap(), original);
        assert_eq!(render_ternary_words_vertical(&original),
                   "10\n001\n00\n000\n01\n");
        let measure = ternary_transport_accounting(&original).unwrap();
        assert_eq!(measure.semantic_bits, 12);
        assert_eq!(measure.separating_trits, 4);
        assert_eq!(measure.encoded_trits, 16);
        assert_eq!(measure.tail_trits, 4);
        assert_eq!(measure.physical_bits, 32);
    }

    #[test]
    fn opening_binary_sens_shows_only_spaces_not_transport_twos() {
        let original = "10 001 00 000 01";
        let binary = encode_binary_projection_ternary(original).unwrap();
        assert_eq!(binary, [0x63, 0x89, 0x06, 0xa1]);
        let visible = open_ternary_program(&binary).unwrap();
        assert_eq!(visible, original);
        assert_eq!(visible.bytes().filter(|c| *c == b' ').count(), 4);
        assert!(!visible.contains('2'));
        assert!(!visible.contains('\n'));
        // View is a projection, physical SENS remains nontext packed bytes.
        assert_ne!(visible.as_bytes(), binary);
        assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), binary);
    }

    #[test]
    fn opening_never_renders_padding_or_d7_space_as_a_separator_token() {
        let source = "10 001 00 1100000 01";
        let encoded = encode_binary_projection_ternary(source).unwrap();
        assert_eq!(open_ternary_program(&encoded).unwrap(), source);
        assert_eq!(render_ternary_words_spaced(&[]), "");
        let changed = [243u8]; // impossible packed 5-trit value
        assert_eq!(
            open_ternary_program(&changed),
            Err(TernaryTransportError::InvalidPhysicalByte)
        );
    }

    #[test]
    fn identical_naked_payload_no_longer_loses_domain_boundaries() {
        let a = words("0 00");
        let b = words("000");
        let encoded_a = encode_ternary_words(&a).unwrap();
        let encoded_b = encode_ternary_words(&b).unwrap();
        assert_ne!(encoded_a, encoded_b);
        assert_eq!(decode_ternary_words(&encoded_a).unwrap(), a);
        assert_eq!(decode_ternary_words(&encoded_b).unwrap(), b);
    }

    #[test]
    fn exhaustive_single_word_roundtrip_d1_to_d9() {
        for width in 1..=9 {
            for value in 0..(1usize << width) {
                let sample = format!("{value:0width$b}");
                let original = words(&sample);
                let physical = encode_ternary_words(&original).unwrap();
                assert_eq!(decode_ternary_words(&physical).unwrap(), original);
            }
        }
    }

    #[test]
    fn d7_sign_space_is_payload_not_transport_separator() {
        let original = words("1100000 101 1100000");
        let physical = encode_ternary_words(&original).unwrap();
        assert_eq!(decode_ternary_words(&physical).unwrap(), original);
    }

    #[test]
    fn file_eof_and_padding_are_canonical_without_22() {
        let original = words("1");
        let physical = encode_ternary_words(&original).unwrap();
        assert_eq!(decode_ternary_words(&physical).unwrap(), original);
        // Голий single-word теж має кінець: EOF файла, не закривальна дужка.
        assert_eq!(physical.len(), 1);
        let mut extra = physical.clone();
        extra.push(242); // п'ять зайвих тритів 2 — не канонічний padding
        assert_eq!(decode_ternary_words(&extra),
                   Err(TernaryTransportError::InvalidTail));
        assert_eq!(decode_ternary_words(&[243]),
                   Err(TernaryTransportError::InvalidPhysicalByte));
        assert_eq!(decode_ternary_words(&[242]),
                   Err(TernaryTransportError::InvalidTail));
        // Старий EOF=22 не дозволено приймати як новий canonical wire,
        // якщо він створює зайвий фізичний байт.
        let closed = words("10 01");
        assert_eq!(encode_ternary_words(&closed).unwrap(), [0x64]);
        assert_eq!(decode_ternary_words(&[0x64, 0xf2]),
                   Err(TernaryTransportError::InvalidTail));
    }

    #[test]
    fn bracket_close_is_not_required_by_physical_eof() {
        for source in ["000", "1", "10 01", "10 001 01",
                       "10 001 01 10 000 01"] {
            let original = words(source);
            let encoded = encode_ternary_words(&original).unwrap();
            assert_eq!(decode_ternary_words(&encoded).unwrap(), original, "{source}");
            assert_eq!(decode_ternary_program(&encoded).unwrap(), original, "{source}");
        }
        // Крайній випадок: код у 5 тритів, padding відсутній.
        let single_exact = words("00000");
        let physical = encode_ternary_words(&single_exact).unwrap();
        assert_eq!(physical.len(), 1);
        assert_eq!(decode_ternary_words(&physical).unwrap(), single_exact);
    }

    #[test]
    fn no_eos_saves_byte_for_short_parenthesized_forms() {
        for (source, expected_bytes) in [
            ("10 01", 1usize),
            ("10 001 01", 2usize),
        ] {
            let original = words(source);
            let physical = encode_ternary_words(&original).unwrap();
            assert_eq!(physical.len(), expected_bytes);
            assert_eq!(decode_ternary_program(&physical).unwrap(), original);
        }
    }

    #[test]
    fn reject_unclosed_grammar_and_unratified_word_width() {
        assert_eq!(encode_binary_projection_ternary("10 001"),
                   Err(TernaryTransportError::InvalidProgramSyntax));
        assert_eq!(encode_binary_projection_ternary("0000000000"),
                   Err(TernaryTransportError::InvalidBinaryProjection));
        assert_eq!(encode_binary_projection_ternary(""),
                   Err(TernaryTransportError::EmptyProgram));
    }

    #[test]
    fn mixed_width_words_and_nested_form_roundtrip() {
        let source = "10 001 00 10 000 01 01";
        let binary = encode_binary_projection_ternary(source).unwrap();
        assert_eq!(decode_ternary_program(&binary).unwrap(), words(source));
        for w in 1..=9 {
            let short = "1".repeat(w);
            let input = words(&format!("10 {short} 01"));
            let bytes = encode_ternary_words(&input).unwrap();
            assert_eq!(decode_ternary_words(&bytes).unwrap(), input);
        }
    }

    #[test]
    fn every_possible_terminal_padding_length_is_canonical() {
        let mut seen = [false; 5];
        // A single exact-width word of each length 1..9 exercises all
        // possible byte remainders. No D2 CLOSE and no EOS are needed.
        for width in 1usize..=9 {
            let source = "1".repeat(width);
            let original = words(&source);
            let physical = encode_ternary_words(&original).unwrap();
            let account = ternary_transport_accounting(&original).unwrap();
            assert_eq!(account.encoded_trits, width);
            assert!(account.tail_trits < 5);
            seen[account.tail_trits] = true;
            assert_eq!(decode_ternary_words(&physical).unwrap(), original);
        }
        assert!(seen.iter().all(|value| *value));
    }

    #[test]
    fn explicit_double_separator_is_not_an_eof_marker() {
        let original = words("10 01");
        let canonical = encode_ternary_words(&original).unwrap();
        assert_eq!(canonical, [0x64]); // 10201, exactly 5 trits.
        // A second block of pure padding cannot be mistaken for EOF.
        assert_eq!(decode_ternary_words(&[0x64, 0xf2]),
                   Err(TernaryTransportError::InvalidTail));
        // T5 separator between two words continues to preserve exact widths.
        let a = words("0 00");
        let b = words("000");
        assert_ne!(encode_ternary_words(&a).unwrap(), encode_ternary_words(&b).unwrap());
    }

    #[test]
    fn trailing_padding_must_not_become_a_program_word() {
        let original = words("10 001 00 000 01");
        let binary = encode_ternary_words(&original).unwrap();
        let mut mutated = binary.clone();
        *mutated.last_mut().unwrap() -= 1;
        assert!(decode_ternary_words(&mutated).is_err());
    }
}
