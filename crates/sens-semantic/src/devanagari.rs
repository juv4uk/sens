//! SLP1 ⟷ Devanāgarī transliteration — Sanskrit migration Phase 2
//! (docs/sanskrit-semantic-migration.md §7, §10:
//! `render_atom(atom_id, DisplayMode::Devanagari)` should be
//! architecturally supported even before it's wired into an IDE).
//!
//! Unlike SLP1⟷IAST (`transliteration.rs`), Devanāgarī is an abugida:
//! consonant letters carry an inherent /a/ unless followed by a vowel
//! sign (mātrā) or suppressed by a virāma (्). That makes this a small
//! state machine over "is there a consonant pending its vowel", not a
//! flat character-for-character table — the two directions share no
//! code with Phase 1's table-driven approach, by necessity, not
//! inconsistency.
//!
//! Scope: the same core phoneme inventory as Phase 1 (spec §22's list),
//! no conjunct consonants beyond what a bare virāma expresses, no
//! Vedic accents. A word ending in a bare consonant (no following vowel)
//! correctly gets a trailing virāma (e.g. SLP1 `sat` -> `सत्`), matching
//! standard Devanāgarī orthography.

const VIRAMA: char = '्';
const ANUSVARA: char = 'ं';
const VISARGA: char = 'ः';
const AVAGRAHA: char = 'ऽ';

/// `(SLP1 vowel, independent form, dependent mātrā — empty for inherent /a/)`.
const VOWELS: &[(char, char, Option<char>)] = &[
    ('a', 'अ', None),
    ('A', 'आ', Some('ा')),
    ('i', 'इ', Some('ि')),
    ('I', 'ई', Some('ी')),
    ('u', 'उ', Some('ु')),
    ('U', 'ऊ', Some('ू')),
    ('f', 'ऋ', Some('ृ')),
    ('F', 'ॠ', Some('ॄ')),
    ('x', 'ऌ', Some('ॢ')),
    ('X', 'ॡ', Some('ॣ')),
    ('e', 'ए', Some('े')),
    ('E', 'ऐ', Some('ै')),
    ('o', 'ओ', Some('ो')),
    ('O', 'औ', Some('ौ')),
];

/// `(SLP1 consonant, Devanāgarī base glyph, carries inherent /a/)`.
const CONSONANTS: &[(char, char)] = &[
    ('k', 'क'),
    ('K', 'ख'),
    ('g', 'ग'),
    ('G', 'घ'),
    ('N', 'ङ'),
    ('c', 'च'),
    ('C', 'छ'),
    ('j', 'ज'),
    ('J', 'झ'),
    ('Y', 'ञ'),
    ('w', 'ट'),
    ('W', 'ठ'),
    ('q', 'ड'),
    ('Q', 'ढ'),
    ('R', 'ण'),
    ('t', 'त'),
    ('T', 'थ'),
    ('d', 'द'),
    ('D', 'ध'),
    ('n', 'न'),
    ('p', 'प'),
    ('P', 'फ'),
    ('b', 'ब'),
    ('B', 'भ'),
    ('m', 'म'),
    ('y', 'य'),
    ('r', 'र'),
    ('l', 'ल'),
    ('v', 'व'),
    ('S', 'श'),
    ('z', 'ष'),
    ('s', 'स'),
    ('h', 'ह'),
];

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DevanagariError {
    UnknownSlp1Char(char),
    UnknownDevanagariChar(char),
    Empty,
}

impl std::fmt::Display for DevanagariError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DevanagariError::UnknownSlp1Char(c) => write!(
                f,
                "unknown SLP1 character `{c}` (same core inventory as transliteration.rs)"
            ),
            DevanagariError::UnknownDevanagariChar(c) => {
                write!(f, "unrecognized Devanāgarī character `{c}`")
            }
            DevanagariError::Empty => write!(f, "empty input is not a valid phoneme sequence"),
        }
    }
}

impl std::error::Error for DevanagariError {}

fn consonant_glyph(c: char) -> Option<char> {
    CONSONANTS.iter().find(|(s, _)| *s == c).map(|(_, g)| *g)
}
fn vowel_forms(c: char) -> Option<(char, Option<char>)> {
    VOWELS
        .iter()
        .find(|(s, _, _)| *s == c)
        .map(|(_, ind, matra)| (*ind, *matra))
}

pub fn slp1_to_devanagari(slp1: &str) -> Result<String, DevanagariError> {
    if slp1.is_empty() {
        return Err(DevanagariError::Empty);
    }
    let mut out = String::with_capacity(slp1.len() * 2);
    let mut pending_consonant = false;

    for c in slp1.chars() {
        if let Some(glyph) = consonant_glyph(c) {
            if pending_consonant {
                out.push(VIRAMA);
            }
            out.push(glyph);
            pending_consonant = true;
        } else if let Some((independent, matra)) = vowel_forms(c) {
            if pending_consonant {
                if let Some(m) = matra {
                    out.push(m);
                }
                // else: inherent /a/, nothing to add
            } else {
                out.push(independent);
            }
            pending_consonant = false;
        } else if c == 'M' {
            out.push(ANUSVARA);
            pending_consonant = false;
        } else if c == 'H' {
            out.push(VISARGA);
            pending_consonant = false;
        } else if c == '\'' {
            if pending_consonant {
                out.push(VIRAMA);
            }
            out.push(AVAGRAHA);
            pending_consonant = false;
        } else {
            return Err(DevanagariError::UnknownSlp1Char(c));
        }
    }
    if pending_consonant {
        out.push(VIRAMA);
    }
    Ok(out)
}

pub fn devanagari_to_slp1(deva: &str) -> Result<String, DevanagariError> {
    if deva.is_empty() {
        return Err(DevanagariError::Empty);
    }
    let chars: Vec<char> = deva.chars().collect();
    let mut out = String::new();
    let mut i = 0;
    while i < chars.len() {
        let c = chars[i];
        if let Some((slp1, _)) = CONSONANTS.iter().find(|(_, g)| *g == c) {
            out.push(*slp1);
            let next = chars.get(i + 1).copied();
            if next == Some(VIRAMA) {
                i += 2;
                continue;
            }
            if let Some(matra_slp1) = next.and_then(|n| {
                VOWELS
                    .iter()
                    .find(|(_, _, m)| *m == Some(n))
                    .map(|(s, _, _)| *s)
            }) {
                out.push(matra_slp1);
                i += 2;
                continue;
            }
            out.push('a'); // inherent vowel, nothing followed
            i += 1;
            continue;
        }
        if let Some((slp1, _, _)) = VOWELS.iter().find(|(_, ind, _)| *ind == c) {
            out.push(*slp1);
            i += 1;
            continue;
        }
        if c == ANUSVARA {
            out.push('M');
        } else if c == VISARGA {
            out.push('H');
        } else if c == AVAGRAHA {
            out.push('\'');
        } else {
            return Err(DevanagariError::UnknownDevanagariChar(c));
        }
        i += 1;
    }
    Ok(out)
}

