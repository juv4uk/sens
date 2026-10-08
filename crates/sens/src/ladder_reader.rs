//! Дослідний рідер голих бітів: перевіряє домени від D1 до D9.
//! Це не затверджений .sens: повертає неоднозначність, не вигадує роздільників.

use crate::{parse_binary_source_words, parse_canonical_binary, BinarySourceWord, PackedBitstream};

#[derive(Debug, Eq, PartialEq)]
pub enum LadderReaderProbe {
    Unique(Vec<BinarySourceWord>),
    Ambiguous { first: Vec<BinarySourceWord>, second: Vec<BinarySourceWord> },
    NoParse,
    SearchLimit,
}

const MAX_PROBE_BITS: usize = 128;
const MAX_SEARCH_NODES: usize = 50_000;

struct ProbeState<'f, F: FnMut(&[crate::Expr]) -> bool> {
    visited: usize,
    exceeded: bool,
    solutions: Vec<Vec<BinarySourceWord>>,
    admits: &'f mut F,
}

impl<F: FnMut(&[crate::Expr]) -> bool> ProbeState<'_, F> {
    fn walk<'a>(&mut self, raw: &'a str, offset: usize, depth: usize, words: &mut Vec<&'a str>) {
        if self.exceeded || self.solutions.len() >= 2 { return; }
        self.visited += 1;
        if self.visited > MAX_SEARCH_NODES {
            self.exceeded = true;
            return;
        }
        if offset == raw.len() {
            // Справжній SENS reader перевіряє синтаксис, НЕ виконання.
            if depth != 0 { return; }
            let projection = words.join(" ");
            if let Ok(ast) = parse_canonical_binary(&projection) {
                // Очікувана семантична роль приходить ЗОВНІ,
                // від мови/оракула; Rust не визначає її самовільно.
                if (self.admits)(&ast) {
                    if let Ok(tokens) = parse_binary_source_words(&projection) {
                        self.solutions.push(tokens.into_iter().map(|t| t.word).collect());
                    }
                }
            }
            return;
        }
        // Драбина знизу догори: від D1 до D9 без першого-жадібного вибору.
        for width in 1..=9 {
            if offset + width > raw.len() { break; }
            let word = &raw[offset..offset + width];
            let next_depth = if width == 2 {
                match word {
                    "10" => depth + 1,
                    "01" if depth > 0 => depth - 1,
                    "01" | "11" if depth == 0 => continue,
                    _ => depth,
                }
            } else { depth };
            words.push(word);
            self.walk(raw, offset + width, next_depth, words);
            words.pop();
            if self.exceeded || self.solutions.len() >= 2 { return; }
        }
    }
}

/// Пробує ширини D1…D9 і синтаксис SENS. Два допустимих розбори —
/// відхилення, не вибір першого; жодних транспортних тегів.
/// PackedBitstream зберігає довжину payload в пам'яті, не EOS файла.
/// Number D24+ та runtime-арність тут поки не включені.
pub fn probe_binary_ladder(packed: &PackedBitstream) -> LadderReaderProbe {
    probe_binary_ladder_with_context(packed, |_| true)
}

/// Додаткове правило допустимості надає власний SENS-контекст.
/// Наприклад, очікування порожнього списку усуває D1/D2-суперечність
/// для 000. Відхилені варіанти не перетворюються в нові ідентичності.
pub fn probe_binary_ladder_with_context(
    packed: &PackedBitstream,
    mut admits: impl FnMut(&[crate::Expr]) -> bool,
) -> LadderReaderProbe {
    let count = packed.bit_len();
    if count == 0 { return LadderReaderProbe::NoParse; }
    if count > MAX_PROBE_BITS { return LadderReaderProbe::SearchLimit; }
    let bits: String = (0..count).map(|pos| {
        let byte = packed.bytes()[pos / 8];
        if byte & (1 << (7 - pos % 8)) == 0 { '0' } else { '1' }
    }).collect();
    let mut state = ProbeState {
        visited: 0, exceeded: false, solutions: Vec::new(), admits: &mut admits,
    };
    state.walk(&bits, 0, 0, &mut Vec::new());
    if state.exceeded { return LadderReaderProbe::SearchLimit; }
    match state.solutions.len() {
        0 => LadderReaderProbe::NoParse,
        1 => LadderReaderProbe::Unique(state.solutions.pop().expect("one candidate")),
        _ => LadderReaderProbe::Ambiguous {
            first: state.solutions.remove(0),
            second: state.solutions.remove(0),
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{pack_binary_source_tokens, parse_binary_source_words};
    fn probe(s: &str) -> LadderReaderProbe {
        let tokens = parse_binary_source_words(s).unwrap();
        probe_binary_ladder(&pack_binary_source_tokens(&tokens))
    }

    #[test]
    fn one_bit_d1_is_uniquely_identified() {
        match probe("1") {
            LadderReaderProbe::Unique(words) => {
                assert_eq!(words.len(), 1);
                assert_eq!((words[0].width(), words[0].packed_bits()), (1, 1));
            }
            other => panic!("D1 expected, got {other:?}"),
        }
    }

    #[test]
    fn d1_d2_and_d3_collide_even_when_canonical_reader_accepts_both() {
        assert!(crate::parse_canonical_binary("0 00").is_ok());
        assert!(crate::parse_canonical_binary("000").is_ok());
        assert!(matches!(probe("000"), LadderReaderProbe::Ambiguous { .. }));
        assert_eq!(probe("0 00"), probe("000"));
    }

    #[test]
    fn cannot_greedily_decode_quote_by_starting_at_d1() {
        assert!(matches!(
            probe("10 001 00 000 01"),
            LadderReaderProbe::Ambiguous { .. }
        ));
    }

    #[test]
    fn language_context_can_disambiguate_d3_empty_without_any_extra_bits() {
        let words = parse_binary_source_words("000").unwrap();
        let payload = pack_binary_source_tokens(&words);
        assert!(matches!(probe_binary_ladder(&payload), LadderReaderProbe::Ambiguous { .. }));
        let resolved = probe_binary_ladder_with_context(&payload, |expressions| {
            expressions.len() == 1
                && matches!(
                    expressions[0].kind,
                    crate::ExprKind::List(ref items) if items.is_empty()
                )
        });
        match resolved {
            LadderReaderProbe::Unique(words) => {
                assert_eq!(words.len(), 1);
                assert_eq!((words[0].width(), words[0].packed_bits()), (3, 0));
            }
            other => panic!("D3 empty expected by language context, got {other:?}"),
        }
    }

    #[test]
    fn no_empty_and_no_false_certainty_beyond_search_limit() {
        assert_eq!(probe_binary_ladder(&crate::BitPacker::new().finish()),
                   LadderReaderProbe::NoParse);
        assert_eq!(probe("1 ".repeat(129).trim()),
                   LadderReaderProbe::SearchLimit);
    }

    #[test]
    fn different_word_partitions_collapse_in_naked_packer() {
        let a = parse_binary_source_words("0 00").unwrap();
        let b = parse_binary_source_words("000").unwrap();
        assert!(pack_binary_source_tokens(&a) == pack_binary_source_tokens(&b));
        assert_ne!(a.iter().map(|x| x.word).collect::<Vec<_>>(),
                   b.iter().map(|x| x.word).collect::<Vec<_>>());
    }
}
