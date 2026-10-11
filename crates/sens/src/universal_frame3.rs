//! Універсальна Рамка-3: перший перевірюваний Rust-зріз нового формату.
//!
//! Не залежить від T5, F3/F4 або їхнього декодера. Точні значення D1–D9
//! зберігаються як BinarySourceWord; структуру перевіряє канонічний D2 reader.
//! Доведений byte-optimum стосується ЛИШЕ двох режимів: dense/raw та repeat.
//! Інші режими потребують окремого доказу перед production cutover.
//!
//! Формат v1: magic [S,3,1] | ULEB(number of exact words) |
//! [tag | ULEB(words in block) | body]* | CRC32(all preceding bytes).
//! Тег 0: два 4-бітові exact width на байт, потім щільно упаковані біти.
//! Тег 1: один exact width і один packed word, повторений N разів.
//! Сума блокових N дорівнює оголошеній кількості слів.
//! CRC32 виявляє випадкові пошкодження, але НЕ є криптографічним MAC.

use crate::{
    parse_canonical_word_sequence, BinarySourceWord,
    Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8, Bit9,
};

const MAGIC: [u8; 3] = [b'S', b'3', 1];
const RAW: u8 = 0;
const REPEAT: u8 = 1;
const MAX_WORDS: usize = 4096;
const MAX_BLOCK_WORDS: usize = 128;
const MAX_FILE_BYTES: usize = 1 << 20;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Frame3Error {
    TooLarge,
    BadVersion,
    Truncated,
    Malformed,
    NonCanonical,
    Integrity,
    InvalidD2,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Mode { Raw, Repeat }

#[derive(Clone, Copy, Debug)]
struct Step {
    bytes: usize,
    end: usize,
    mode: Mode,
}

fn varint_len(mut n: usize) -> usize {
    let mut bytes = 1;
    while n >= 128 { n >>= 7; bytes += 1; }
    bytes
}

fn put_varint(mut n: usize, out: &mut Vec<u8>) {
    while n >= 128 {
        out.push(((n & 0x7f) as u8) | 0x80);
        n >>= 7;
    }
    out.push(n as u8);
}

fn get_varint(input: &[u8], pos: &mut usize) -> Result<usize, Frame3Error> {
    let start = *pos;
    let mut n = 0u64;
    for step in 0..5 {
        let byte = *input.get(*pos).ok_or(Frame3Error::Truncated)?;
        *pos += 1;
        n |= u64::from(byte & 0x7f) << (7 * step);
        if byte & 0x80 == 0 {
            let value = usize::try_from(n).map_err(|_| Frame3Error::TooLarge)?;
            if *pos - start != varint_len(value) {
                return Err(Frame3Error::NonCanonical);
            }
            return Ok(value);
        }
    }
    Err(Frame3Error::Malformed)
}

fn physical_crc32(bytes: &[u8]) -> u32 {
    let mut crc = !0u32;
    for &byte in bytes {
        crc ^= u32::from(byte);
        for _ in 0..8 {
            crc = (crc >> 1) ^ (0xedb88320u32 & (0u32.wrapping_sub(crc & 1)));
        }
    }
    !crc
}

fn new_word(width: usize, bits: u16) -> Result<BinarySourceWord, Frame3Error> {
    // Лише фізичне відновлення уже відомої ширини, без таблиці семантики.
    if !(1..=9).contains(&width) || bits >= (1 << width) {
        return Err(Frame3Error::Malformed);
    }
    let small = bits as u8;
    let word = match width {
        1 => Bit1::new(small).map(BinarySourceWord::W1),
        2 => Bit2::new(small).map(BinarySourceWord::W2),
        3 => Bit3::new(small).map(BinarySourceWord::W3),
        4 => Bit4::new(small).map(BinarySourceWord::W4),
        5 => Bit5::new(small).map(BinarySourceWord::W5),
        6 => Bit6::new(small).map(BinarySourceWord::W6),
        7 => Bit7::new(small).map(BinarySourceWord::W7),
        8 => Bit8::new(small).map(BinarySourceWord::W8),
        9 => Bit9::new(bits).map(BinarySourceWord::W9),
        _ => None,
    };
    word.ok_or(Frame3Error::Malformed)
}

fn bits_to_bytes(words: &[BinarySourceWord]) -> Vec<u8> {
    let nbits: usize = words.iter().map(|w| w.width()).sum();
    let mut bytes = vec![0u8; nbits.div_ceil(8)];
    let mut cursor = 0usize;
    for &word in words {
        for shift in (0..word.width()).rev() {
            if (word.packed_bits() >> shift) & 1 == 1 {
                bytes[cursor / 8] |= 1 << (7 - cursor % 8);
            }
            cursor += 1;
        }
    }
    bytes
}

fn bytes_to_words(
    widths: &[usize],
    bytes: &[u8],
) -> Result<Vec<BinarySourceWord>, Frame3Error> {
    let nbits: usize = widths.iter().sum();
    if bytes.len() != nbits.div_ceil(8) { return Err(Frame3Error::Malformed); }
    if nbits % 8 != 0 && !bytes.is_empty() {
        let mask = (1u8 << (8 - nbits % 8)) - 1;
        if bytes[bytes.len() - 1] & mask != 0 { return Err(Frame3Error::NonCanonical); }
    }
    let mut offset = 0usize;
    let mut words = Vec::with_capacity(widths.len());
    for &width in widths {
        if !(1..=9).contains(&width) { return Err(Frame3Error::Malformed); }
        let mut value = 0u16;
        for _ in 0..width {
            value = (value << 1) | u16::from(
                (bytes[offset / 8] >> (7 - offset % 8)) & 1
            );
            offset += 1;
        }
        words.push(new_word(width, value)?);
    }
    Ok(words)
}

fn choose_plan(words: &[BinarySourceWord]) -> Vec<Step> {
    // Повний DP за всіма межами 1..128 слів і двома допустимими режимами.
    // Постійні magic/count/checksum теж входять у фізичний підсумок.
    let n = words.len();
    let mut dp = vec![Step { bytes: usize::MAX, end: n, mode: Mode::Raw }; n + 1];
    dp[n].bytes = 0;
    for i in (0..n).rev() {
        let mut bits = 0usize;
        let mut all_equal = true;
        for j in i + 1..=n.min(i + MAX_BLOCK_WORDS) {
            let word = words[j - 1];
            bits += word.width();
            all_equal &= word == words[i];
            let count = j - i;
            let raw_cost = 1 + varint_len(count) + count.div_ceil(2) + bits.div_ceil(8);
            let mut winner = (raw_cost, Mode::Raw);
            if all_equal {
                let repeat_cost = 1 + varint_len(count) + 1 + word.width().div_ceil(8);
                if repeat_cost < raw_cost { winner = (repeat_cost, Mode::Repeat); }
            }
            let total = winner.0 + dp[j].bytes;
            let old = dp[i];
            // При рівності перевага raw, потім довшому сегменту.
            let earlier = (winner.1 as u8, usize::MAX - j);
            let existing = (old.mode as u8, usize::MAX - old.end);
            if total < old.bytes || (total == old.bytes && earlier < existing) {
                dp[i] = Step { bytes: total, end: j, mode: winner.1 };
            }
        }
    }
    dp
}

pub fn encode(words: &[BinarySourceWord]) -> Result<Vec<u8>, Frame3Error> {
    if words.len() > MAX_WORDS { return Err(Frame3Error::TooLarge); }
    parse_canonical_word_sequence(words).map_err(|_| Frame3Error::InvalidD2)?;
    let dp = choose_plan(words);
    let mut result = Vec::with_capacity(3 + varint_len(words.len()) + dp[0].bytes + 4);
    result.extend_from_slice(&MAGIC);
    put_varint(words.len(), &mut result);
    let mut i = 0usize;
    while i < words.len() {
        let step = dp[i];
        let chunk = &words[i..step.end];
        result.push(match step.mode { Mode::Raw => RAW, Mode::Repeat => REPEAT });
        put_varint(chunk.len(), &mut result);
        match step.mode {
            Mode::Raw => {
                for pair in chunk.chunks(2) {
                    let left = pair[0].width() as u8;
                    let right = pair.get(1).map_or(0, |word| word.width() as u8);
                    result.push((left << 4) | right);
                }
                result.extend_from_slice(&bits_to_bytes(chunk));
            }
            Mode::Repeat => {
                result.push(chunk[0].width() as u8);
                result.extend_from_slice(&bits_to_bytes(&chunk[..1]));
            }
        }
        i = step.end;
    }
    let crc = physical_crc32(&result);
    result.extend_from_slice(&crc.to_be_bytes());
    if result.len() > MAX_FILE_BYTES { return Err(Frame3Error::TooLarge); }
    Ok(result)
}

pub fn decode(bytes: &[u8]) -> Result<Vec<BinarySourceWord>, Frame3Error> {
    if bytes.len() > MAX_FILE_BYTES { return Err(Frame3Error::TooLarge); }
    if bytes.len() < MAGIC.len() + 1 + 4 { return Err(Frame3Error::Truncated); }
    if bytes[..3] != MAGIC { return Err(Frame3Error::BadVersion); }
    let cutoff = bytes.len() - 4;
    let expected = u32::from_be_bytes(bytes[cutoff..].try_into()
        .map_err(|_| Frame3Error::Truncated)?);
    if physical_crc32(&bytes[..cutoff]) != expected {
        return Err(Frame3Error::Integrity);
    }
    let mut pos = 3usize;
    let target = get_varint(&bytes[..cutoff], &mut pos)?;
    if target > MAX_WORDS { return Err(Frame3Error::TooLarge); }
    let mut words = Vec::with_capacity(target);
    while words.len() < target {
        let mode = *bytes.get(pos).ok_or(Frame3Error::Truncated)?;
        pos += 1;
        let count = get_varint(&bytes[..cutoff], &mut pos)?;
        if count == 0 || count > MAX_BLOCK_WORDS || count > target - words.len() {
            return Err(Frame3Error::Malformed);
        }
        let widths = if mode == RAW {
            let map_bytes = count.div_ceil(2);
            let finish = pos.checked_add(map_bytes).ok_or(Frame3Error::Malformed)?;
            if finish > cutoff { return Err(Frame3Error::Truncated); }
            let mut list = Vec::with_capacity(count);
            for &byte in &bytes[pos..finish] {
                list.push((byte >> 4) as usize);
                list.push((byte & 15) as usize);
            }
            if count % 2 != 0 && list[count] != 0 {
                return Err(Frame3Error::NonCanonical);
            }
            list.truncate(count);
            pos = finish;
            list
        } else if mode == REPEAT {
            let width = *bytes.get(pos).ok_or(Frame3Error::Truncated)? as usize;
            pos += 1;
            vec![width]
        } else {
            return Err(Frame3Error::Malformed);
        };
        if widths.iter().any(|&w| !(1..=9).contains(&w)) {
            return Err(Frame3Error::Malformed);
        }
        let nbits: usize = widths.iter().sum();
        let end = pos.checked_add(nbits.div_ceil(8)).ok_or(Frame3Error::Malformed)?;
        if end > cutoff { return Err(Frame3Error::Truncated); }
        let restored = bytes_to_words(&widths, &bytes[pos..end])?;
        pos = end;
        if mode == REPEAT {
            words.resize(words.len() + count, restored[0]);
        } else {
            words.extend(restored);
        }
    }
    if pos != cutoff { return Err(Frame3Error::NonCanonical); }
    parse_canonical_word_sequence(&words).map_err(|_| Frame3Error::InvalidD2)?;
    // Відхиляємо всі alias: альтернативні режими, блоки, padding, varint.
    if encode(&words)?.as_slice() != bytes { return Err(Frame3Error::NonCanonical); }
    Ok(words)
}

/// Bounded incremental accumulator: chunks may end at any byte boundary.
/// Validation and D2-parse run at finish; this is NOT a streaming AST parser.
#[derive(Default)]
pub struct Frame3Decoder {
    buffer: Vec<u8>,
    failed: bool,
}

impl Frame3Decoder {
    pub fn new() -> Self { Self::default() }

    pub fn push(&mut self, chunk: &[u8]) -> Result<(), Frame3Error> {
        if self.failed { return Err(Frame3Error::TooLarge); }
        if chunk.len() > MAX_FILE_BYTES.saturating_sub(self.buffer.len()) {
            // Помилка необоротна: finish не прийме попередній валідний префікс.
            self.failed = true;
            return Err(Frame3Error::TooLarge);
        }
        self.buffer.extend_from_slice(chunk);
        Ok(())
    }

    pub fn finish(self) -> Result<Vec<BinarySourceWord>, Frame3Error> {
        if self.failed { return Err(Frame3Error::TooLarge); }
        decode(&self.buffer)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parse_binary_source_words;

    fn source(s: &str) -> Vec<BinarySourceWord> {
        parse_binary_source_words(s).unwrap().into_iter().map(|t| t.word).collect()
    }

    fn roundtrip(s: &str) {
        let words = source(s);
        let encoded = encode(&words).unwrap();
        assert_eq!(decode(&encoded).unwrap(), words);
        assert_eq!(encode(&decode(&encoded).unwrap()).unwrap(), encoded);
        for size in [1, 2, 3, 7, 64] {
            let mut reader = Frame3Decoder::new();
            for chunk in encoded.chunks(size) { reader.push(chunk).unwrap(); }
            assert_eq!(reader.finish().unwrap(), words);
        }
        for end in 0..encoded.len() {
            assert!(decode(&encoded[..end]).is_err(), "truncation at {end}");
        }
        let mut added = encoded.clone();
        added.push(0);
        assert!(decode(&added).is_err());
    }

    #[test]
    fn exact_widths_and_multiple_roots() {
        for sample in [
            "", "0", "1", "10 01", "10 001 01",
            "10 000000001 01", "10 111111111 01",
            "10 01 10 01",
            "10 0 01 10 1 01",
        ] {
            roundtrip(sample);
        }
        // D2:00 та D2:11 — структурні, НЕ окремі атоми.
        roundtrip("10 0 00 1 01");
        roundtrip("10 1 11 0 01");
        for width in [1, 3, 4, 5, 6, 7, 8, 9] {
            let word = "0".repeat(width);
            roundtrip(&word);
            let max = "1".repeat(width);
            roundtrip(&max);
        }
    }

    #[test]
    fn long_repeats_and_mixed_byte_blocks() {
        let mut text = String::from("10 ");
        for _ in 0..150 { text.push_str("000000001 "); }
        text.push_str("01");
        roundtrip(&text);
        let words = source(&text);
        let data = encode(&words).unwrap();
        assert!(data.contains(&REPEAT));
    }

    #[test]
    fn physical_overhead_and_corruption() {
        let bytes = encode(&source("10 001 01")).unwrap();
        assert_eq!(&bytes[..3], &MAGIC);
        assert_eq!(physical_crc32(&bytes[..bytes.len()-4]).to_be_bytes(),
            bytes[bytes.len()-4..]);
        for i in 0..bytes.len() {
            let mut damaged = bytes.clone();
            damaged[i] ^= 0x40;
            assert!(decode(&damaged).is_err(), "mutation at {i}");
        }
    }

    #[test]
    fn wrong_d2_rejected() {
        assert_eq!(encode(&source("01")), Err(Frame3Error::InvalidD2));
        assert_eq!(encode(&source("10")), Err(Frame3Error::InvalidD2));
        assert_eq!(decode(b"T5 not a universal frame"), Err(Frame3Error::BadVersion));
    }

    #[test]
    fn malformed_physical_aliases_rejected_even_with_matching_crc() {
        fn framed(mut payload: Vec<u8>) -> Vec<u8> {
            let crc = physical_crc32(&payload);
            payload.extend_from_slice(&crc.to_be_bytes());
            payload
        }
        // Той самий атом 0 у повторному режимі: неканонічний alias raw.
        let alias = framed(vec![b'S', b'3', 1, 1, REPEAT, 1, 1, 0]);
        assert_eq!(decode(&alias), Err(Frame3Error::NonCanonical));
        // Довжина 1, записана двома байтами, заборонена.
        let nonminimal = framed(vec![b'S', b'3', 1, 0x81, 0, RAW, 1, 0x10, 0]);
        assert_eq!(decode(&nonminimal), Err(Frame3Error::NonCanonical));
        // Додані padding bits є неканонічними, навіть із новим CRC.
        let padding = framed(vec![b'S', b'3', 1, 1, RAW, 1, 0x10, 1]);
        assert_eq!(decode(&padding), Err(Frame3Error::NonCanonical));
        // Exact-width D2 CLOSE не може бути самостійним верхнім виразом.
        let bad_d2 = framed(vec![b'S', b'3', 1, 1, RAW, 1, 0x20, 0x40]);
        assert_eq!(decode(&bad_d2), Err(Frame3Error::InvalidD2));
        let bad_tag = framed(vec![b'S', b'3', 1, 1, 0xff, 1, 0x10, 0]);
        assert_eq!(decode(&bad_tag), Err(Frame3Error::Malformed));
    }

    #[test]
    fn oversized_chunk_poisoned_stream() {
        let valid = encode(&source("0")).unwrap();
        let mut decoder = Frame3Decoder::new();
        decoder.push(&valid).unwrap();
        assert_eq!(decoder.push(&vec![0; MAX_FILE_BYTES]), Err(Frame3Error::TooLarge));
        assert_eq!(decoder.finish(), Err(Frame3Error::TooLarge));
    }

    #[test]
    fn dp_matches_independent_bounded_enumeration() {
        fn brute(words: &[BinarySourceWord]) -> usize {
            if words.is_empty() { return 0; }
            let mut best = usize::MAX;
            for n in 1..=words.len().min(MAX_BLOCK_WORDS) {
                let chunk = &words[..n];
                let bits: usize = chunk.iter().map(|w| w.width()).sum();
                let raw = 1 + varint_len(n) + n.div_ceil(2) + bits.div_ceil(8);
                best = best.min(raw + brute(&words[n..]));
                if chunk.iter().all(|w| *w == chunk[0]) {
                    let run = 1 + varint_len(n) + 1 + chunk[0].width().div_ceil(8);
                    best = best.min(run + brute(&words[n..]));
                }
            }
            best
        }
        for width in 1..=9 {
            for n in 0..=7 {
                let words = std::iter::repeat(new_word(width, 0).unwrap())
                    .take(n).collect::<Vec<_>>();
                assert_eq!(choose_plan(&words)[0].bytes, brute(&words));
            }
        }
    }
}
