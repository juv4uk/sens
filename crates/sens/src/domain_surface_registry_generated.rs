// GENERATED — DO NOT EDIT BY HAND.
// Authority: lib/surface/domain-surfaces-d1-d4.lisp
// Checked by: scripts/check-domain-surfaces-d1-d4.py

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) struct DomainSurfaceName {
    pub(super) namespace: &'static str,
    pub(super) name: &'static str,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) struct DomainSurfaceRow {
    pub(super) width: u8,
    pub(super) bits: u8,
    pub(super) surfaces: &'static [DomainSurfaceName],
}

pub(super) const DOMAIN_SURFACE_ROWS: &[DomainSurfaceRow] = &[
    DomainSurfaceRow { width: 3, bits: 0b001, surfaces: &[DomainSurfaceName { namespace: "uk", name: "як-є" }, DomainSurfaceName { namespace: "sa", name: "svarūpa" }] },
    DomainSurfaceRow { width: 3, bits: 0b010, surfaces: &[DomainSurfaceName { namespace: "uk", name: "атом?" }, DomainSurfaceName { namespace: "sa", name: "aṇu?" }] },
    DomainSurfaceRow { width: 3, bits: 0b011, surfaces: &[DomainSurfaceName { namespace: "uk", name: "решта" }, DomainSurfaceName { namespace: "sa", name: "śeṣa" }] },
    DomainSurfaceRow { width: 3, bits: 0b100, surfaces: &[DomainSurfaceName { namespace: "uk", name: "перше" }, DomainSurfaceName { namespace: "sa", name: "ādi" }] },
    DomainSurfaceRow { width: 3, bits: 0b101, surfaces: &[DomainSurfaceName { namespace: "uk", name: "тотожне?" }, DomainSurfaceName { namespace: "sa", name: "abheda?" }] },
    DomainSurfaceRow { width: 3, bits: 0b110, surfaces: &[DomainSurfaceName { namespace: "uk", name: "за-умовою" }, DomainSurfaceName { namespace: "sa", name: "krama" }] },
    DomainSurfaceRow { width: 3, bits: 0b111, surfaces: &[DomainSurfaceName { namespace: "uk", name: "сполучити" }, DomainSurfaceName { namespace: "sa", name: "saṃyuj" }] },
    DomainSurfaceRow { width: 4, bits: 0b0000, surfaces: &[DomainSurfaceName { namespace: "uk", name: "застосувати" }, DomainSurfaceName { namespace: "sa", name: "prayoga" }] },
    DomainSurfaceRow { width: 4, bits: 0b0001, surfaces: &[DomainSurfaceName { namespace: "uk", name: "обчислити" }, DomainSurfaceName { namespace: "sa", name: "vicāraṇa" }] },
    DomainSurfaceRow { width: 4, bits: 0b0010, surfaces: &[DomainSurfaceName { namespace: "uk", name: "функція" }, DomainSurfaceName { namespace: "sa", name: "phalana" }] },
    DomainSurfaceRow { width: 4, bits: 0b0011, surfaces: &[DomainSurfaceName { namespace: "uk", name: "визначити" }, DomainSurfaceName { namespace: "sa", name: "nirvacana" }] },
    DomainSurfaceRow { width: 4, bits: 0b0100, surfaces: &[DomainSurfaceName { namespace: "uk", name: "не" }, DomainSurfaceName { namespace: "sa", name: "niṣedha" }] },
    DomainSurfaceRow { width: 4, bits: 0b0101, surfaces: &[DomainSurfaceName { namespace: "uk", name: "порожнє?" }, DomainSurfaceName { namespace: "sa", name: "śūnya?" }] },
    DomainSurfaceRow { width: 4, bits: 0b0110, surfaces: &[DomainSurfaceName { namespace: "uk", name: "решта-від-першого" }, DomainSurfaceName { namespace: "sa", name: "śeṣa-ādi" }] },
    DomainSurfaceRow { width: 4, bits: 0b0111, surfaces: &[DomainSurfaceName { namespace: "uk", name: "решта-від-решти" }, DomainSurfaceName { namespace: "sa", name: "śeṣa-śeṣa" }] },
    DomainSurfaceRow { width: 4, bits: 0b1000, surfaces: &[DomainSurfaceName { namespace: "uk", name: "перше-від-першого" }, DomainSurfaceName { namespace: "sa", name: "ādi-ādi" }] },
    DomainSurfaceRow { width: 4, bits: 0b1001, surfaces: &[DomainSurfaceName { namespace: "uk", name: "перше-від-решти" }, DomainSurfaceName { namespace: "sa", name: "ādi-śeṣa" }] },
    DomainSurfaceRow { width: 4, bits: 0b1010, surfaces: &[DomainSurfaceName { namespace: "uk", name: "знайти" }, DomainSurfaceName { namespace: "sa", name: "anveṣaṇa" }] },
    DomainSurfaceRow { width: 4, bits: 0b1011, surfaces: &[DomainSurfaceName { namespace: "uk", name: "зв'язати" }, DomainSurfaceName { namespace: "sa", name: "bandha" }] },
    DomainSurfaceRow { width: 4, bits: 0b1100, surfaces: &[DomainSurfaceName { namespace: "uk", name: "обчислити-умови" }, DomainSurfaceName { namespace: "sa", name: "krama-vicāraṇa" }] },
    DomainSurfaceRow { width: 4, bits: 0b1101, surfaces: &[DomainSurfaceName { namespace: "uk", name: "обчислити-список" }, DomainSurfaceName { namespace: "sa", name: "śreṇī-vicāraṇa" }] },
    DomainSurfaceRow { width: 4, bits: 0b1110, surfaces: &[DomainSurfaceName { namespace: "uk", name: "список" }, DomainSurfaceName { namespace: "sa", name: "śreṇī" }] },
    DomainSurfaceRow { width: 4, bits: 0b1111, surfaces: &[DomainSurfaceName { namespace: "uk", name: "приєднати" }, DomainSurfaceName { namespace: "sa", name: "saṅkalana" }] },
];
