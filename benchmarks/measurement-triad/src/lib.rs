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

