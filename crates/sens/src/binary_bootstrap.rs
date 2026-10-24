//! Bootstrap-бібліотеки надходять у бекенд тільки точними доменними словами.
//! Фізичний Т5М відновлює pinned Zig під час збірки; Lisp-джерела тут немає.

use crate::{
    DomainD10, DomainIdentity, ErrorKind, ExactDomainWord, LanguageError, PhysicalT5Program, Span,
};

// Точні коди вже визначених функцій lib/domains/d10.lisp. Це лише ключі
// перевірки встановлення бібліотек: вони не визначають значення чи викличність.
pub(super) const TIME_DEFINITION: DomainIdentity = DomainIdentity::D10(
    DomainD10::new(0b1010111110).expect("точна Д10 координата часової бібліотеки"),
);
pub(super) const UTF8_DEFINITION: DomainIdentity = DomainIdentity::D10(
    DomainD10::new(0b0010111011).expect("точна Д10 координата бібліотеки кодування"),
);

include!(concat!(env!("OUT_DIR"), "/binary_bootstrap_words.rs"));

pub(super) fn macro_program() -> Result<PhysicalT5Program, LanguageError> {
    program(MACRO_BOOTSTRAP_WORDS)
}

pub(super) fn core3_program() -> Result<PhysicalT5Program, LanguageError> {
    program(CORE3_BOOTSTRAP_WORDS)
}

pub(super) fn compiler_nucleus_program() -> Result<PhysicalT5Program, LanguageError> {
    program(COMPILER_NUCLEUS_BOOTSTRAP_WORDS)
}

pub(super) fn with_core4_program<T>(
    action: impl FnOnce(&PhysicalT5Program) -> T,
) -> Result<T, LanguageError> {
    thread_local! {
        static PROGRAM: std::cell::OnceCell<Result<PhysicalT5Program, LanguageError>> =
            const { std::cell::OnceCell::new() };
    }
    PROGRAM.with(
        |slot| match slot.get_or_init(|| program(CORE4_BOOTSTRAP_WORDS)) {
            Ok(program) => Ok(action(program)),
            Err(error) => Err(error.clone()),
        },
    )
}

pub(super) fn time_program() -> Result<PhysicalT5Program, LanguageError> {
    program(TIME_BOOTSTRAP_WORDS)
}

pub(super) fn utf8_program() -> Result<PhysicalT5Program, LanguageError> {
    program(UTF8_BOOTSTRAP_WORDS)
}

pub(super) fn process_program() -> Result<PhysicalT5Program, LanguageError> {
    program(PROCESS_BOOTSTRAP_WORDS)
}

pub(super) fn tcp_program() -> Result<PhysicalT5Program, LanguageError> {
    program(TCP_BOOTSTRAP_WORDS)
}

pub(super) fn fs_program() -> Result<PhysicalT5Program, LanguageError> {
    program(FS_BOOTSTRAP_WORDS)
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
