//! Макробібліотека надходить у бекенд тільки точними доменними словами.
//! Фізичний Т5М відновлює pinned Zig під час збірки; Lisp-джерела тут немає.

use crate::{ErrorKind, ExactDomainWord, LanguageError, PhysicalT5Program, Span};

include!(concat!(env!("OUT_DIR"), "/macro_bootstrap_words.rs"));

pub(super) fn program() -> Result<PhysicalT5Program, LanguageError> {
    let words = MACRO_BOOTSTRAP_WORDS
        .iter()
        .map(|&(width, bits)| {
            ExactDomainWord::from_physical_width_bits(width, bits).map_err(|error| {
                LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("Zig T5M macro bootstrap word rejected: {error}"),
                    Span { start: 0, end: 0 },
                )
            })
        })
        .collect::<Result<Vec<_>, _>>()?;
    PhysicalT5Program::from_exact_domain_words_owned(words)
}
