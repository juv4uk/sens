//! Research-only measurement adapter: real D3 domain owner occupancy mechanism.
//! The underlying SENS API, not an English opcode or a second semantic table,
//! decides occupancy. The adapter grants no callability or domain law.

use sens::domain_ladder::DomainCoordinate;
use std::hint::black_box;

/// Exact-domain D3 owner lookup, measured as a batch to avoid timer granularity.
/// Its work is constant across instrumentation and wall-time lanes.
#[inline(never)]
pub fn scan_d3_owner_residency(iterations: usize) -> usize {
    let mut residents = 0usize;
    for i in 0..iterations {
        let bits = black_box((i & 7) as u16);
        let coordinate = DomainCoordinate::new(black_box(3), bits)
            .expect("valid 3-bit domain coordinate");
        residents += usize::from(black_box(coordinate.owner_residency()) == Some(true));
    }
    black_box(residents)
}

/// Strong preflight on every exact D3 slot; this is a mechanism assertion,
/// not an independent language-semantic oracle.
pub fn verify_d3_owner_projection() {
    let expected: [bool; 8] = [false, true, true, true, true, true, true, true];
    for (bits, is_resident) in expected.into_iter().enumerate() {
        let coordinate = DomainCoordinate::new(3, bits as u16).unwrap();
        assert_eq!(coordinate.owner_residency(), Some(is_resident));
    }
    assert_eq!(scan_d3_owner_residency(1_024), 896);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_d3_mechanism_still_obeys_owner_map() {
        verify_d3_owner_projection();
    }
}
