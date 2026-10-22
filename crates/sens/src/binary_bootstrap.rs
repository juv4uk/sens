//! Bootstrap-бібліотеки надходять у бекенд тільки точними доменними словами.
//! Фізичний Т5М відновлює pinned Zig під час збірки; Lisp-джерела тут немає.

use crate::{ErrorKind, ExactDomainWord, LanguageError, PhysicalT5Program, Span};

include!(concat!(env!("OUT_DIR"), "/binary_bootstrap_words.rs"));

pub(super) fn macro_program() -> Result<PhysicalT5Program, LanguageError> {
    program(MACRO_BOOTSTRAP_WORDS)
}

pub(super) fn core3_program() -> Result<PhysicalT5Program, LanguageError> {
    program(CORE3_BOOTSTRAP_WORDS)
}

pub(super) fn time_program() -> Result<PhysicalT5Program, LanguageError> {
    program(TIME_BOOTSTRAP_WORDS)
}

fn program(restored: &[(usize, &[u8])]) -> Result<PhysicalT5Program, LanguageError> {
    let words = restored
        .iter()
        .map(|&(width, bits)| {
            ExactDomainWord::from_physical_width_bits(width, bits).map_err(|error| {
                LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("Zig T5M bootstrap word rejected: {error}"),
                    Span { start: 0, end: 0 },
                )
            })
        })
        .collect::<Result<Vec<_>, _>>()?;
    PhysicalT5Program::from_exact_domain_words_owned(words)
}
