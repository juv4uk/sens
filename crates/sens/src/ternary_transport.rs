//! Дослідний трійковий ТРАНСПОРТ двійкових слів SENS.
//!
//! Це не трійкова семантика: D1..D9 залишаються двійковими.
//! Транспортні цифри 0/1 відтворюють біт, 2 відділяє слова.
//! Упаковано п'ять тритів в один фізичний байт (3^5=243).
//! Подвійна 2 наприкінці є експериментальним EOS; хвіст
//! добивається лише транспортними 2 та перевіряється канонічно.
//! Жодного D7-пробілу чи нового D10-резидента тут немає.
//! Number D24+ ще не допускається до цього механічного носія.

use crate::{parse_binary_source_words, parse_canonical_binary, BinarySourceWord};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TernaryTransportError {
    EmptyProgram,
    InvalidBinaryProjection,
    InvalidProgramSyntax,
    InvalidPhysicalByte,
    MissingEnd,
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
    pub eos_trits: usize,
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
    // EOS — дві послідовні транспортні 2; звичайний
    // роздільник завжди одиночний і стоїть МІЖ двійковими словами.
    trits.extend_from_slice(&[2, 2]);
    while trits.len() % TRITS_PER_BYTE != 0 {
        trits.push(2);
    }
    let byte_len = trits.len() / TRITS_PER_BYTE;
    if byte_len > MAX_FILE_BYTES {
        return Err(TernaryTransportError::TransportTooLarge);
    }
    let mut encoded = Vec::with_capacity(byte_len);
    for five in trits.chunks_exact(TRITS_PER_BYTE) {
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
    let mut parts = Vec::<String>::new();
    let mut current = String::new();
    let mut offset = 0;
    while offset < trits.len() {
        let digit = trits[offset];
        match digit {
            0 | 1 => {
                current.push(char::from(b'0' + digit));
                if current.len() > 9 {
                    return Err(TernaryTransportError::UnsupportedDomainWidth);
                }
                offset += 1;
            }
            2 => {
                if current.is_empty() {
                    return Err(TernaryTransportError::EmptyDomainWord);
                }
                if offset + 1 >= trits.len() {
                    return Err(TernaryTransportError::MissingEnd);
                }
                parts.push(std::mem::take(&mut current));
                if trits[offset + 1] == 2 {
                    offset += 2;
                    // Не дозволяти додатковий байт після EOS:
                    // лише <5 тритів 2 як останній фізичний хвіст.
                    if trits.len() - offset >= TRITS_PER_BYTE
                        || trits[offset..].iter().any(|d| *d != 2)
                    {
                        return Err(TernaryTransportError::InvalidTail);
                    }
                    let visible = parts.join(" ");
                    let tokens = parse_binary_source_words(&visible)
                        .map_err(|_| TernaryTransportError::UnsupportedDomainWidth)?;
                    let words: Vec<_> = tokens.into_iter().map(|token| token.word).collect();
                    let reconstructed = encode_ternary_words(&words)?;
                    if reconstructed != data {
                        return Err(TernaryTransportError::NoncanonicalEncoding);
                    }
                    return Ok(words);
                }
                offset += 1;
            }
            _ => unreachable!(),
        }
    }
    Err(TernaryTransportError::MissingEnd)
}

/// Вертикальний вигляд — тільки для людини, newline не є
/// тритом і не записується в сам .sens файл.
pub fn render_ternary_words_vertical(words: &[BinarySourceWord]) -> String {
    words.iter().map(|word| format!("{word}\n")).collect()
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

/// Вартість носія, включно з EOS і фінальним заповненням.
/// Трити і біти — різні одиниці; физичні байти враховано окремо.
pub fn ternary_transport_accounting(
    words: &[BinarySourceWord],
) -> Result<TernaryTransportAccounting, TernaryTransportError> {
    let data = encode_ternary_words(words)?;
    let semantic_bits = words.iter().map(|word| word.width()).sum::<usize>();
    let separating_trits = words.len() - 1;
    let eos_trits = 2;
    let encoded_trits = semantic_bits + separating_trits + eos_trits;
    let tail_trits = data.len() * TRITS_PER_BYTE - encoded_trits;
    Ok(TernaryTransportAccounting {
        word_count: words.len(),
        semantic_bits,
        separating_trits,
        eos_trits,
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
        assert_eq!(measure.eos_trits, 2);
        assert_eq!(measure.encoded_trits, 18);
        assert_eq!(measure.tail_trits, 2);
        assert_eq!(measure.physical_bits, 32);
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
    fn explicit_terminator_and_tail_are_canonical() {
        let original = words("1");
        let physical = encode_ternary_words(&original).unwrap();
        assert_eq!(decode_ternary_words(&physical).unwrap(), original);
        let mut extra = physical.clone();
        extra.push(242); // trailing physical byte, навіть якщо це п'ять 2
        assert_eq!(decode_ternary_words(&extra),
                   Err(TernaryTransportError::InvalidTail));
        assert_eq!(decode_ternary_words(&[243]),
                   Err(TernaryTransportError::InvalidPhysicalByte));
        assert_eq!(decode_ternary_words(&[242]),
                   Err(TernaryTransportError::EmptyDomainWord));
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
    fn trailing_padding_must_not_become_a_program_word() {
        let original = words("10 001 00 000 01");
        let binary = encode_ternary_words(&original).unwrap();
        let mut mutated = binary.clone();
        *mutated.last_mut().unwrap() -= 1;
        assert_eq!(decode_ternary_words(&mutated),
                   Err(TernaryTransportError::InvalidTail));
    }
}
