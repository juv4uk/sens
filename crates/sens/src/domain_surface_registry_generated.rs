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
    pub(super) source_routable: bool,
    pub(super) surfaces: &'static [DomainSurfaceName],
}

pub(super) const DOMAIN_SURFACE_ROWS: &[DomainSurfaceRow] = &[
    DomainSurfaceRow { width: 1, bits: 0b0, source_routable: false, surfaces: &[DomainSurfaceName { namespace: "en", name: "no" }, DomainSurfaceName { namespace: "uk", name: "ні" }, DomainSurfaceName { namespace: "sa", name: "na" }] },
    DomainSurfaceRow { width: 1, bits: 0b1, source_routable: false, surfaces: &[DomainSurfaceName { namespace: "en", name: "yes" }, DomainSurfaceName { namespace: "uk", name: "так" }, DomainSurfaceName { namespace: "sa", name: "ām" }] },
    DomainSurfaceRow { width: 2, bits: 0b00, source_routable: false, surfaces: &[DomainSurfaceName { namespace: "en", name: "separator" }, DomainSurfaceName { namespace: "uk", name: "пропуск" }, DomainSurfaceName { namespace: "sa", name: "antarāla" }] },
    DomainSurfaceRow { width: 2, bits: 0b01, source_routable: false, surfaces: &[DomainSurfaceName { namespace: "en", name: "close" }, DomainSurfaceName { namespace: "uk", name: "закрити" }, DomainSurfaceName { namespace: "sa", name: "samāpana" }] },
    DomainSurfaceRow { width: 2, bits: 0b10, source_routable: false, surfaces: &[DomainSurfaceName { namespace: "en", name: "open" }, DomainSurfaceName { namespace: "uk", name: "відкрити" }, DomainSurfaceName { namespace: "sa", name: "udghāṭana" }] },
    DomainSurfaceRow { width: 2, bits: 0b11, source_routable: false, surfaces: &[DomainSurfaceName { namespace: "en", name: "dot" }, DomainSurfaceName { namespace: "uk", name: "крапка" }, DomainSurfaceName { namespace: "sa", name: "bindu" }] },
    DomainSurfaceRow { width: 3, bits: 0b000, source_routable: false, surfaces: &[DomainSurfaceName { namespace: "en", name: "empty" }, DomainSurfaceName { namespace: "uk", name: "порожнє" }, DomainSurfaceName { namespace: "sa", name: "śūnya" }] },
    DomainSurfaceRow { width: 3, bits: 0b001, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "quote" }, DomainSurfaceName { namespace: "uk", name: "як-є" }, DomainSurfaceName { namespace: "sa", name: "svarūpa" }] },
    DomainSurfaceRow { width: 3, bits: 0b010, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "atom" }, DomainSurfaceName { namespace: "uk", name: "атом?" }, DomainSurfaceName { namespace: "sa", name: "aṇu?" }] },
    DomainSurfaceRow { width: 3, bits: 0b011, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "cdr" }, DomainSurfaceName { namespace: "uk", name: "решта" }, DomainSurfaceName { namespace: "sa", name: "śeṣa" }] },
    DomainSurfaceRow { width: 3, bits: 0b100, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "car" }, DomainSurfaceName { namespace: "uk", name: "перше" }, DomainSurfaceName { namespace: "sa", name: "ādi" }] },
    DomainSurfaceRow { width: 3, bits: 0b101, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "eq" }, DomainSurfaceName { namespace: "uk", name: "тотожне?" }, DomainSurfaceName { namespace: "sa", name: "abheda?" }] },
    DomainSurfaceRow { width: 3, bits: 0b110, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "cond" }, DomainSurfaceName { namespace: "uk", name: "за-умовою" }, DomainSurfaceName { namespace: "sa", name: "krama" }] },
    DomainSurfaceRow { width: 3, bits: 0b111, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "cons" }, DomainSurfaceName { namespace: "uk", name: "сполучити" }, DomainSurfaceName { namespace: "sa", name: "saṃyuj" }] },
    DomainSurfaceRow { width: 4, bits: 0b0000, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "apply" }, DomainSurfaceName { namespace: "uk", name: "застосувати" }, DomainSurfaceName { namespace: "sa", name: "prayoga" }] },
    DomainSurfaceRow { width: 4, bits: 0b0001, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "eval" }, DomainSurfaceName { namespace: "uk", name: "обчислити" }, DomainSurfaceName { namespace: "sa", name: "vicāraṇa" }] },
    DomainSurfaceRow { width: 4, bits: 0b0010, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "lambda" }, DomainSurfaceName { namespace: "uk", name: "функція" }, DomainSurfaceName { namespace: "sa", name: "phalana" }] },
    DomainSurfaceRow { width: 4, bits: 0b0011, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "define" }, DomainSurfaceName { namespace: "uk", name: "визначити" }, DomainSurfaceName { namespace: "sa", name: "nirvacana" }] },
    DomainSurfaceRow { width: 4, bits: 0b0100, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "not" }, DomainSurfaceName { namespace: "uk", name: "не" }, DomainSurfaceName { namespace: "sa", name: "niṣedha" }] },
    DomainSurfaceRow { width: 4, bits: 0b0101, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "null" }, DomainSurfaceName { namespace: "uk", name: "порожнє?" }, DomainSurfaceName { namespace: "sa", name: "śūnya?" }] },
    DomainSurfaceRow { width: 4, bits: 0b0110, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "cdar" }, DomainSurfaceName { namespace: "uk", name: "решта-від-першого" }, DomainSurfaceName { namespace: "sa", name: "śeṣa-ādi" }] },
    DomainSurfaceRow { width: 4, bits: 0b0111, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "cddr" }, DomainSurfaceName { namespace: "uk", name: "решта-від-решти" }, DomainSurfaceName { namespace: "sa", name: "śeṣa-śeṣa" }] },
    DomainSurfaceRow { width: 4, bits: 0b1000, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "caar" }, DomainSurfaceName { namespace: "uk", name: "перше-від-першого" }, DomainSurfaceName { namespace: "sa", name: "ādi-ādi" }] },
    DomainSurfaceRow { width: 4, bits: 0b1001, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "cadr" }, DomainSurfaceName { namespace: "uk", name: "перше-від-решти" }, DomainSurfaceName { namespace: "sa", name: "ādi-śeṣa" }] },
    DomainSurfaceRow { width: 4, bits: 0b1010, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "lookup" }, DomainSurfaceName { namespace: "uk", name: "знайти" }, DomainSurfaceName { namespace: "sa", name: "anveṣaṇa" }] },
    DomainSurfaceRow { width: 4, bits: 0b1011, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "bind" }, DomainSurfaceName { namespace: "uk", name: "зв'язати" }, DomainSurfaceName { namespace: "sa", name: "bandha" }] },
    DomainSurfaceRow { width: 4, bits: 0b1100, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "evcon" }, DomainSurfaceName { namespace: "uk", name: "обчислити-умови" }, DomainSurfaceName { namespace: "sa", name: "krama-vicāraṇa" }] },
    DomainSurfaceRow { width: 4, bits: 0b1101, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "evlis" }, DomainSurfaceName { namespace: "uk", name: "обчислити-список" }, DomainSurfaceName { namespace: "sa", name: "śreṇī-vicāraṇa" }] },
    DomainSurfaceRow { width: 4, bits: 0b1110, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "list" }, DomainSurfaceName { namespace: "uk", name: "список" }, DomainSurfaceName { namespace: "sa", name: "śreṇī" }] },
    DomainSurfaceRow { width: 4, bits: 0b1111, source_routable: true, surfaces: &[DomainSurfaceName { namespace: "en", name: "append" }, DomainSurfaceName { namespace: "uk", name: "приєднати" }, DomainSurfaceName { namespace: "sa", name: "saṅkalana" }] },
];
