// GENERATED — DO NOT EDIT BY HAND.
// Authority: knowledge/domain-surface-registry.lisp
// Generator: scripts/generate-rust-domain-registry.lisp
// No historical flat-byte semantic identity is present in this projection.

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
    DomainSurfaceRow { width: 0b11, bits: 0b001, surfaces: &[DomainSurface { namespace: "ук", name: "як-є" }, DomainSurface { namespace: "укр", name: "як-є" }, DomainSurface { namespace: "sa", name: "svarūpa" }, DomainSurface { namespace: "sym", name: "'" }, ] },
    DomainSurfaceRow { width: 0b11, bits: 0b010, surfaces: &[DomainSurface { namespace: "ук", name: "атом?" }, DomainSurface { namespace: "укр", name: "атом?" }, DomainSurface { namespace: "sa", name: "aṇu" }, DomainSurface { namespace: "sym", name: ".?" }, ] },
    DomainSurfaceRow { width: 0b11, bits: 0b011, surfaces: &[DomainSurface { namespace: "ук", name: "за-умовою" }, DomainSurface { namespace: "укр", name: "за-умовою" }, DomainSurface { namespace: "sa", name: "anukrama" }, DomainSurface { namespace: "sym", name: "?:" }, ] },
    DomainSurfaceRow { width: 0b11, bits: 0b100, surfaces: &[DomainSurface { namespace: "ук", name: "сполучити" }, DomainSurface { namespace: "укр", name: "сполучити" }, DomainSurface { namespace: "sa", name: "saṃyuj" }, ] },
    DomainSurfaceRow { width: 0b11, bits: 0b101, surfaces: &[DomainSurface { namespace: "ук", name: "перше" }, DomainSurface { namespace: "укр", name: "перше" }, DomainSurface { namespace: "sa", name: "ādi" }, DomainSurface { namespace: "sym", name: ":п" }, ] },
    DomainSurfaceRow { width: 0b11, bits: 0b110, surfaces: &[DomainSurface { namespace: "ук", name: "решта" }, DomainSurface { namespace: "укр", name: "решта" }, DomainSurface { namespace: "sa", name: "śeṣa" }, DomainSurface { namespace: "sym", name: ":р" }, ] },
    DomainSurfaceRow { width: 0b11, bits: 0b111, surfaces: &[DomainSurface { namespace: "ук", name: "тотожне?" }, DomainSurface { namespace: "укр", name: "тотожне?" }, DomainSurface { namespace: "sa", name: "abheda" }, DomainSurface { namespace: "sym", name: "=?" }, ] },
];
