//! SLP1 ⟷ IAST transliteration — Sanskrit migration Phase 1
//! (docs/sanskrit-semantic-migration.md §1, §22, §26, §27).
//!
//! SLP1 (Sanskrit Library Phonetic, basic scheme) is the canonical,
//! ASCII-only *storage* representation used everywhere in this language's
//! source and internal identifiers (spec §1: "SLP1 є ASCII-only"). IAST is
//! a *presentation-only* representation — never an internal identifier
//! (spec §1.3, §37: "НЕ використовувати IAST як internal identifier").
//!
//! Table verified 2026-08-12 against Wikipedia's SLP1 article
//! (<https://en.wikipedia.org/wiki/SLP1>), not reconstructed from memory
//! (spec §4, §22 explicitly forbid the latter). Scope is deliberately the
//! *core* phoneme inventory the spec's edge-case list calls for (§22:
//! vocalic ṛ, retroflex consonants, palatals, aspirates, anusvāra,
//! visarga, long vowels) plus the semivowels/sibilants needed for the
//! candidate dhātu/kāraka vocabulary in spec §4–§5. Deliberately NOT
//! mapped yet (extended/Vedic features, out of MVP scope per spec §12):
//! candrabindu (`~`), jihvāmūlīya (`Z`), upadhmānīya (`V`), the retroflex
//! lateral `L` (ळ), pluta/vedic-accent marks (`1`, `3`, `/`, `\`, `^`).
//! Feeding any of those in is a hard error, not a silent drop or
//! best-effort guess — spec §20 forbids silent fallback for unknown atoms.
//!
//! Unicode policy (spec §26): IAST strings produced and consumed here are
//! precomposed (NFC) Unicode — e.g. `ā` is U+0101, not `a` + a combining
//! macron (U+0304). This is the standard NFC form for every IAST
//! diacritic letter used below, so no normalization pass is needed as
//! long as callers don't hand-construct decomposed IAST text; that's an
//! explicit, documented simplification rather than an accidental gap.
//!
//! Performance note (spec §27): this module is for parser/IDE/diagnostic
//! use, not the runtime hot path — nothing here should be called per VM
//! instruction once later phases introduce interned semantic IDs.

/// `(SLP1 char, IAST spelling)` — the single source of truth both
/// directions are built from, so the two conversions can never drift
/// apart from each other.
const TABLE: &[(char, &str)] = &[
    // Vowels (short/long pairs + diphthongs)
    ('a', "a"),
    ('A', "ā"),
    ('i', "i"),
    ('I', "ī"),
    ('u', "u"),
    ('U', "ū"),
    ('e', "e"),
    ('E', "ai"),
    ('o', "o"),
    ('O', "au"),
    // Vocalic liquids
    ('f', "ṛ"),
    ('F', "ṝ"),
    ('x', "ḷ"),
    ('X', "ḹ"),
    // Anusvāra / visarga
    ('M', "ṃ"),
    ('H', "ḥ"),
    // Velars
    ('k', "k"),
    ('K', "kh"),
    ('g', "g"),
    ('G', "gh"),
    ('N', "ṅ"),
    // Palatals
    ('c', "c"),
    ('C', "ch"),
    ('j', "j"),
    ('J', "jh"),
    ('Y', "ñ"),
    // Retroflexes
    ('w', "ṭ"),
    ('W', "ṭh"),
    ('q', "ḍ"),
    ('Q', "ḍh"),
    ('R', "ṇ"),
    // Dentals
    ('t', "t"),
    ('T', "th"),
    ('d', "d"),
    ('D', "dh"),
    ('n', "n"),
    // Labials
    ('p', "p"),
    ('P', "ph"),
    ('b', "b"),
    ('B', "bh"),
    ('m', "m"),
    // Semivowels
    ('y', "y"),
    ('r', "r"),
    ('l', "l"),
    ('v', "v"),
    // Sibilants + h
    ('S', "ś"),
    ('z', "ṣ"),
    ('s', "s"),
    ('h', "h"),
    // Avagraha
    ('\'', "'"),
];

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TransliterationError {
    /// A character in an SLP1 token isn't in the mapped core inventory —
    /// either a typo, or a Vedic/extended feature not yet mapped (see the
    /// module doc for the explicit list of what's excluded from MVP).
    UnknownSlp1Char(char),
    /// A substring of an IAST token couldn't be matched against any known
    /// IAST spelling at that position.
    UnknownIastSegment(String),
    /// The input was empty — not meaningful as a phoneme sequence.
    Empty,
}

impl std::fmt::Display for TransliterationError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TransliterationError::UnknownSlp1Char(c) => {
                write!(f, "unknown SLP1 character `{c}` — not in the mapped core inventory (see semantic/transliteration.rs for what's excluded and why)")
            }
            TransliterationError::UnknownIastSegment(s) => {
                write!(f, "unrecognized IAST sequence starting at `{s}`")
            }
            TransliterationError::Empty => write!(f, "empty input is not a valid phoneme sequence"),
        }
    }
}

impl std::error::Error for TransliterationError {}

/// Converts a bare SLP1 atom (phonemes only — no whitespace, parens, or
/// surrounding source syntax; callers extract the token first) to its
/// canonical precomposed-Unicode IAST spelling.
pub fn slp1_to_iast(slp1: &str) -> Result<String, TransliterationError> {
    if slp1.is_empty() {
        return Err(TransliterationError::Empty);
    }
    let mut out = String::with_capacity(slp1.len() * 2);
    for c in slp1.chars() {
        match TABLE.iter().find(|(s, _)| *s == c) {
            Some((_, iast)) => out.push_str(iast),
            None => return Err(TransliterationError::UnknownSlp1Char(c)),
        }
    }
    Ok(out)
}

/// Converts an IAST spelling back to its canonical SLP1 atom, via greedy
/// longest-match: aspirated stops (`kh`, `gh`, `ch`, `jh`, `ṭh`, `ḍh`,
/// `th`, `dh`, `ph`, `bh`) and diphthongs (`ai`, `au`) are two characters
/// wide in IAST but one in SLP1, so every position tries a 2-character
/// match before falling back to 1.
pub fn iast_to_slp1(iast: &str) -> Result<String, TransliterationError> {
    if iast.is_empty() {
        return Err(TransliterationError::Empty);
    }
    let chars: Vec<char> = iast.chars().collect();
    let mut out = String::with_capacity(chars.len());
    let mut i = 0;
    while i < chars.len() {
        let mut matched = false;
        // Longest match first (max IAST spelling length in TABLE is 2).
        for len in (1..=2.min(chars.len() - i)).rev() {
            let candidate: String = chars[i..i + len].iter().collect();
            if let Some((slp1, _)) = TABLE.iter().find(|(_, iast)| *iast == candidate) {
                out.push(*slp1);
                i += len;
                matched = true;
                break;
            }
        }
        if !matched {
            let remainder: String = chars[i..].iter().take(8).collect();
            return Err(TransliterationError::UnknownIastSegment(remainder));
        }
    }
    Ok(out)
}

