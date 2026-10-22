//! Research-only composition of the Rust reference T5M codec and exact-word
//! SENS admission. Production ingress is owned by the Zig corridor.

use sens::{decode_ternary_words, PhysicalT5Program};

pub fn program(physical: &[u8]) -> std::io::Result<PhysicalT5Program> {
    let words = decode_ternary_words(physical)
        .map_err(|error| std::io::Error::other(format!("T5M reference decode: {error:?}")))?;
    PhysicalT5Program::from_exact_words(&words)
        .map_err(|error| std::io::Error::other(format!("SENS exact-word admission: {error:?}")))
}
