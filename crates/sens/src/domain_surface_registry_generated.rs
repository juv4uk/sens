// GENERATED — DO NOT EDIT BY HAND.
// Authority: lib/surface/domain-registry.lisp
// Generator: scripts/generate-rust-domain-registry.lisp
// No legacy Function8/Sens8 byte is present in this projection.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) struct DomainSurface {
    pub(super) namespace: &'static str,
    pub(super) name: &'static str,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) struct DomainSurfaceRow {
    pub(super) width: u8,
    pub(super) bits: u8,
    pub(super) surfaces: &'static [DomainSurface],
}

pub(super) const DOMAIN_SURFACE_ROWS: &[DomainSurfaceRow] = &[
    DomainSurfaceRow { width: 3, bits: 0b001, surfaces: &[DomainSurface { namespace: "en", name: "quote" }, DomainSurface { namespace: "ук", name: "як-є" }, DomainSurface { namespace: "укр", name: "як-є" }, DomainSurface { namespace: "sa", name: "svarūpa" }, DomainSurface { namespace: "sym", name: "'" }, ] },
    DomainSurfaceRow { width: 3, bits: 0b010, surfaces: &[DomainSurface { namespace: "en", name: "atom?" }, DomainSurface { namespace: "ук", name: "атом?" }, DomainSurface { namespace: "укр", name: "атом?" }, DomainSurface { namespace: "sa", name: "aṇu" }, DomainSurface { namespace: "sym", name: ".?" }, ] },
    DomainSurfaceRow { width: 3, bits: 0b011, surfaces: &[DomainSurface { namespace: "en", name: "cond" }, DomainSurface { namespace: "ук", name: "за-умовою" }, DomainSurface { namespace: "укр", name: "за-умовою" }, DomainSurface { namespace: "sa", name: "anukrama" }, DomainSurface { namespace: "sym", name: "?:" }, ] },
    DomainSurfaceRow { width: 3, bits: 0b100, surfaces: &[DomainSurface { namespace: "en", name: "cons" }, DomainSurface { namespace: "ук", name: "сполучити" }, DomainSurface { namespace: "укр", name: "сполучити" }, DomainSurface { namespace: "sa", name: "saṃyuj" }, ] },
    DomainSurfaceRow { width: 3, bits: 0b101, surfaces: &[DomainSurface { namespace: "en", name: "car" }, DomainSurface { namespace: "ук", name: "перше" }, DomainSurface { namespace: "укр", name: "перше" }, DomainSurface { namespace: "sa", name: "ādi" }, DomainSurface { namespace: "sym", name: ":п" }, ] },
    DomainSurfaceRow { width: 3, bits: 0b110, surfaces: &[DomainSurface { namespace: "en", name: "cdr" }, DomainSurface { namespace: "ук", name: "решта" }, DomainSurface { namespace: "укр", name: "решта" }, DomainSurface { namespace: "sa", name: "śeṣa" }, DomainSurface { namespace: "sym", name: ":р" }, ] },
    DomainSurfaceRow { width: 3, bits: 0b111, surfaces: &[DomainSurface { namespace: "en", name: "eq?" }, DomainSurface { namespace: "ук", name: "тотожне?" }, DomainSurface { namespace: "укр", name: "тотожне?" }, DomainSurface { namespace: "sa", name: "abheda" }, DomainSurface { namespace: "sym", name: "=?" }, ] },
    DomainSurfaceRow { width: 4, bits: 0b0010, surfaces: &[DomainSurface { namespace: "en", name: "lambda" }, DomainSurface { namespace: "ук", name: "функція" }, DomainSurface { namespace: "укр", name: "функція" }, ] },
    DomainSurfaceRow { width: 4, bits: 0b0011, surfaces: &[DomainSurface { namespace: "en", name: "define" }, DomainSurface { namespace: "ук", name: "визначити" }, DomainSurface { namespace: "укр", name: "визначити" }, ] },
    DomainSurfaceRow { width: 4, bits: 0b0011, surfaces: &[DomainSurface { namespace: "en", name: "def" }, ] },
    DomainSurfaceRow { width: 4, bits: 0b1010, surfaces: &[DomainSurface { namespace: "en", name: "caar" }, DomainSurface { namespace: "укр", name: "перше-від-першого" }, ] },
    DomainSurfaceRow { width: 4, bits: 0b1011, surfaces: &[DomainSurface { namespace: "en", name: "cadr" }, DomainSurface { namespace: "укр", name: "перше-від-решти" }, ] },
    DomainSurfaceRow { width: 4, bits: 0b1101, surfaces: &[DomainSurface { namespace: "en", name: "cddr" }, DomainSurface { namespace: "укр", name: "решта-від-решти" }, ] },
];
