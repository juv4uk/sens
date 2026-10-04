//! Поточні людські surface-проєкції над exact DomainIdentity.
//!
//! Словник живе у machine-readable таблиці
//! lib/surface/current-domain-surfaces.tsv і генерується в
//! human_surface_generated.rs. Цей модуль виконує лише exact-domain
//! проєкцію; історичні SID8/SENS8/Function8 тут не створюються.

use crate::human_surface_generated::{CurrentHumanSurfaceRow, CURRENT_HUMAN_SURFACES};
use crate::{Bija3, Bit3, CoreDomainIdentity};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SurfaceLanguage {
    English,
    Ukrainian,
    Sanskrit,
}

fn identity_from_row(row: &CurrentHumanSurfaceRow) -> Option<CoreDomainIdentity> {
    match row.width {
        3 => {
            let word = Bit3::new(row.bits).ok()?;
            Some(CoreDomainIdentity::D3(Bija3::from_word(word)))
        }
        _ => None,
    }
}

/// Розв'язати current human spelling безпосередньо в exact Core identity.
///
/// Невідоме spelling лишається нерозв'язаним, щоб звичайні lexical
/// identifiers ішли своїм звичайним шляхом.
pub fn resolve_human_surface(name: &str) -> Option<CoreDomainIdentity> {
    CURRENT_HUMAN_SURFACES
        .iter()
        .find(|row| row.en == name || row.uk == name || row.sa == name)
        .and_then(identity_from_row)
}

/// Відобразити exact Core identity в одну з current human surfaces.
///
/// Таблиця вже domain-qualified. Додаткові D4-D8 рядки можна додавати до
/// source-table лише разом із відповідним exact-domain конструктором у
/// identity_from_row.
pub fn render_human_surface(
    language: SurfaceLanguage,
    identity: CoreDomainIdentity,
) -> Option<&'static str> {
    let width = identity.width() as u8;
    let bits = identity.packed_bits();
    CURRENT_HUMAN_SURFACES
        .iter()
        .find(|row| row.width == width && row.bits == bits)
        .map(|row| match language {
            SurfaceLanguage::English => row.en,
            SurfaceLanguage::Ukrainian => row.uk,
            SurfaceLanguage::Sanskrit => row.sa,
        })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeSet;

    #[test]
    fn generated_current_rows_resolve_to_one_exact_identity_per_language() {
        for row in CURRENT_HUMAN_SURFACES {
            let expected = identity_from_row(row).expect("current row has an admitted Core domain");
            let en = resolve_human_surface(row.en).expect("EN spelling resolves");
            let uk = resolve_human_surface(row.uk).expect("UK spelling resolves");
            let sa = resolve_human_surface(row.sa).expect("SA spelling resolves");
            assert_eq!(en, expected);
            assert_eq!(uk, expected);
            assert_eq!(sa, expected);
            assert_eq!(expected.width(), row.width as usize);
            assert_eq!(expected.packed_bits(), row.bits);
        }
    }

    #[test]
    fn exact_identity_round_trips_through_every_current_surface() {
        for row in CURRENT_HUMAN_SURFACES {
            let identity = identity_from_row(row).expect("current row has an admitted Core domain");
            for language in [
                SurfaceLanguage::English,
                SurfaceLanguage::Ukrainian,
                SurfaceLanguage::Sanskrit,
            ] {
                let spelling =
                    render_human_surface(language, identity).expect("current spelling renders");
                assert_eq!(resolve_human_surface(spelling), Some(identity));
            }
        }
    }

    #[test]
    fn generated_table_is_collision_free_and_unknowns_fail_closed() {
        let mut seen = BTreeSet::new();
        for row in CURRENT_HUMAN_SURFACES {
            for spelling in [row.en, row.uk, row.sa] {
                assert!(seen.insert(spelling), "duplicate current surface spelling: {spelling}");
            }
        }
        assert_eq!(resolve_human_surface("невідоме"), None);
        assert_eq!(resolve_human_surface("unknown"), None);
        // Старий donor не стає current-native alias без окремої admission.
        assert_eq!(resolve_human_surface("krama"), None);
    }
}
