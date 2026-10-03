//! #2646 HUMAN-WIRE-ARQ-1 — block framing, CRC and retry policy for a
//! human-keyed binary stream. LAYER: MECHANISM (#2552). Not semantic DOMAIN.
//!
//! Framing is transport only: it is never racanā2 and never semantic identity
//! (#2490). The semantic payload is an opaque bit string and is never touched.
//!
//! Variants compared on the same payload:
//!   A  whole message: len16 | payload | crc16
//!   B  fixed blocks : [idx8 last1 len9 | payload | crc16] ...   (no sync)
//!   C  sync + blocks: [SYNC8 | idx8 last1 len9 | payload | crc16] ... + resync scan
//!   D  C + Hamming(7,4) over each block body (sync stays uncoded) + CRC
//!
//! Zero external dependencies.

use std::collections::BTreeMap;

pub type Bits = Vec<u8>;

pub const IDX_BITS: usize = 8;
pub const FLAG_BITS: usize = 1;
pub const LEN_BITS: usize = 9;
pub const HDR_BITS: usize = IDX_BITS + FLAG_BITS + LEN_BITS;
pub const CRC_BITS: usize = 16;
pub const A_LEN_BITS: usize = 16;
pub const SYNC: [u8; 8] = [1, 1, 0, 1, 0, 0, 1, 1];
pub const MAX_BLOCKS: usize = 1 << IDX_BITS;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Variant {
    A,
    B,
    C,
    D,
}

impl Variant {
    pub const ALL: [Variant; 4] = [Variant::A, Variant::B, Variant::C, Variant::D];
    pub fn name(self) -> &'static str {
        match self {
            Variant::A => "A-whole-crc",
            Variant::B => "B-blocks-crc",
            Variant::C => "C-sync-blocks-crc",
            Variant::D => "D-sync-blocks-hamming-crc",
        }
    }
}

// ---------------------------------------------------------------- bit utils

pub fn push_uint(bits: &mut Bits, val: usize, width: usize) {
    for i in (0..width).rev() {
        bits.push(((val >> i) & 1) as u8);
    }
}

pub fn read_uint(bits: &[u8], pos: usize, width: usize) -> usize {
    let mut v = 0usize;
    for i in 0..width {
        v = (v << 1) | bits[pos + i] as usize;
    }
    v
}

/// CRC-16/CCITT (poly 0x1021, init 0xFFFF) computed bit-by-bit, so payloads
/// need not be byte aligned. It DETECTS; it does not correct.
pub fn crc16(bits: &[u8]) -> u16 {
    let mut crc: u16 = 0xFFFF;
    for &b in bits {
        let top = ((crc >> 15) & 1) as u8;
        crc <<= 1;
        if top ^ (b & 1) == 1 {
            crc ^= 0x1021;
        }
    }
    crc
}

// ------------------------------------------------------------------ hamming

/// Hamming(7,4): positions 1..7, parity at 1,2,4. Corrects one flip per word.
pub fn hamming_encode_nibble(d: [u8; 4]) -> [u8; 7] {
    let (d1, d2, d3, d4) = (d[0], d[1], d[2], d[3]);
    let c1 = d1 ^ d2 ^ d4;
    let c2 = d1 ^ d3 ^ d4;
    let c4 = d2 ^ d3 ^ d4;
    [c1, c2, d1, c4, d2, d3, d4]
}

/// Returns (nibble, corrected?).
pub fn hamming_decode_word(w: &[u8]) -> ([u8; 4], bool) {
    let mut c = [w[0], w[1], w[2], w[3], w[4], w[5], w[6]];
    let s1 = c[0] ^ c[2] ^ c[4] ^ c[6];
    let s2 = c[1] ^ c[2] ^ c[5] ^ c[6];
    let s4 = c[3] ^ c[4] ^ c[5] ^ c[6];
    let syn = (s1 + 2 * s2 + 4 * s4) as usize;
    let fixed = syn != 0;
    if fixed {
        c[syn - 1] ^= 1;
    }
    ([c[2], c[4], c[5], c[6]], fixed)
}

fn hamming_encode(raw: &[u8]) -> Bits {
    let mut padded = raw.to_vec();
    let pad = (4 - padded.len() % 4) % 4;
    // fixed by the format (a function of len), not payload-ambiguous
    padded.extend(std::iter::repeat_n(0u8, pad));
    let mut out = Vec::with_capacity(padded.len() / 4 * 7);
    for ch in padded.chunks(4) {
        out.extend_from_slice(&hamming_encode_nibble([ch[0], ch[1], ch[2], ch[3]]));
    }
    out
}

// ------------------------------------------------------------------- frames

fn block_raw(idx: usize, last: bool, payload: &[u8]) -> Bits {
    let mut raw = Vec::with_capacity(HDR_BITS + payload.len() + CRC_BITS);
    push_uint(&mut raw, idx, IDX_BITS);
    push_uint(&mut raw, last as usize, FLAG_BITS);
    push_uint(&mut raw, payload.len(), LEN_BITS);
    raw.extend_from_slice(payload);
    let crc = crc16(&raw);
    push_uint(&mut raw, crc as usize, CRC_BITS);
    raw
}

/// raw = header | payload | crc. Length must be self-consistent.
fn check_raw(raw: &[u8]) -> Option<(usize, bool, Bits)> {
    if raw.len() < HDR_BITS + CRC_BITS {
        return None;
    }
    let idx = read_uint(raw, 0, IDX_BITS);
    let last = read_uint(raw, IDX_BITS, FLAG_BITS) == 1;
    let len = read_uint(raw, IDX_BITS + FLAG_BITS, LEN_BITS);
    if HDR_BITS + len + CRC_BITS != raw.len() {
        return None;
    }
    let body = HDR_BITS + len;
    let crc = read_uint(raw, body, CRC_BITS) as u16;
    if crc16(&raw[..body]) != crc {
        return None;
    }
    Some((idx, last, raw[HDR_BITS..body].to_vec()))
}

pub type Chunk<'a> = (usize, bool, &'a [u8]);

pub fn split(payload: &[u8], k: usize) -> Result<Vec<Chunk<'_>>, String> {
    if k == 0 || k >= (1 << LEN_BITS) {
        return Err(format!("block size {k} outside 1..{}", (1 << LEN_BITS) - 1));
    }
    if payload.is_empty() {
        return Ok(vec![(0, true, &payload[..0])]);
    }
    let chunks: Vec<&[u8]> = payload.chunks(k).collect();
    if chunks.len() > MAX_BLOCKS {
        return Err(format!("{} blocks exceed {} index space", chunks.len(), MAX_BLOCKS));
    }
    let n = chunks.len();
    Ok(chunks.into_iter().enumerate().map(|(i, c)| (i, i + 1 == n, c)).collect())
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct Accounting {
    pub semantic_payload_bits: usize,
    pub sync_bits: usize,
    pub block_index_bits: usize,
    pub length_bits: usize, // length + last-flag
    pub crc_bits: usize,
    pub fec_bits: usize, // Hamming parity + format-fixed pad
    pub total_wire_bits: usize,
    pub blocks: usize,
}

impl Accounting {
    pub fn goodput(&self) -> f64 {
        if self.total_wire_bits == 0 {
            0.0
        } else {
            self.semantic_payload_bits as f64 / self.total_wire_bits as f64
        }
    }
}

pub fn encode_a(payload: &[u8]) -> Result<(Bits, Accounting), String> {
    if payload.len() >= (1 << A_LEN_BITS) {
        return Err("payload too long for variant A".into());
    }
    let mut bits = Vec::new();
    push_uint(&mut bits, payload.len(), A_LEN_BITS);
    bits.extend_from_slice(payload);
    let crc = crc16(&bits);
    push_uint(&mut bits, crc as usize, CRC_BITS);
    let acc = Accounting {
        semantic_payload_bits: payload.len(),
        length_bits: A_LEN_BITS,
        crc_bits: CRC_BITS,
        total_wire_bits: bits.len(),
        blocks: 1,
        ..Default::default()
    };
    Ok((bits, acc))
}

/// Encode a message (or only the listed block indices — selective retry).
pub fn encode(
    variant: Variant,
    payload: &[u8],
    k: usize,
    only: Option<&[usize]>,
) -> Result<(Bits, Accounting), String> {
    if variant == Variant::A {
        return encode_a(payload);
    }
    let mut bits = Vec::new();
    let mut acc = Accounting::default();
    for (idx, last, chunk) in split(payload, k)? {
        if let Some(sel) = only {
            if !sel.contains(&idx) {
                continue;
            }
        }
        let raw = block_raw(idx, last, chunk);
        acc.blocks += 1;
        acc.semantic_payload_bits += chunk.len();
        acc.block_index_bits += IDX_BITS;
        acc.length_bits += FLAG_BITS + LEN_BITS;
        acc.crc_bits += CRC_BITS;
        match variant {
            Variant::B => bits.extend_from_slice(&raw),
            Variant::C => {
                acc.sync_bits += SYNC.len();
                bits.extend_from_slice(&SYNC);
                bits.extend_from_slice(&raw);
            }
            Variant::D => {
                acc.sync_bits += SYNC.len();
                bits.extend_from_slice(&SYNC);
                let enc = hamming_encode(&raw);
                acc.fec_bits += enc.len() - raw.len();
                bits.extend_from_slice(&enc);
            }
            Variant::A => unreachable!(),
        }
    }
    acc.total_wire_bits = bits.len();
    debug_assert_eq!(
        acc.total_wire_bits,
        acc.semantic_payload_bits
            + acc.sync_bits
            + acc.block_index_bits
            + acc.length_bits
            + acc.crc_bits
            + acc.fec_bits
    );
    Ok((bits, acc))
}

// ------------------------------------------------------------------ decoder

#[derive(Clone, Debug, Default)]
pub struct Decoded {
    pub blocks: BTreeMap<usize, Bits>,
    pub last_index: Option<usize>,
    pub conflicts: usize,
    pub duplicates: usize,
    pub corrected_bits: usize,
    pub rejected_candidates: usize,
    /// (wire offset of frame start, block index) for every accepted frame.
    pub accepted: Vec<(usize, usize)>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AssembleError {
    MissingBlocks(Vec<usize>),
    NoLastBlock,
    Conflict(usize),
}

impl Decoded {
    fn accept(&mut self, off: usize, idx: usize, last: bool, payload: Bits) {
        match self.blocks.get(&idx) {
            Some(p) if *p == payload => self.duplicates += 1,
            Some(_) => self.conflicts += 1,
            None => {
                self.blocks.insert(idx, payload);
            }
        }
        if last {
            match self.last_index {
                Some(l) if l != idx => self.conflicts += 1,
                _ => self.last_index = Some(idx),
            }
        }
        self.accepted.push((off, idx));
    }

    pub fn assemble(&self) -> Result<Bits, AssembleError> {
        if self.conflicts > 0 {
            return Err(AssembleError::Conflict(self.conflicts));
        }
        let last = self.last_index.ok_or(AssembleError::NoLastBlock)?;
        if self.blocks.keys().any(|&i| i > last) {
            return Err(AssembleError::Conflict(1));
        }
        let missing: Vec<usize> = (0..=last).filter(|i| !self.blocks.contains_key(i)).collect();
        if !missing.is_empty() {
            return Err(AssembleError::MissingBlocks(missing));
        }
        let mut out = Vec::new();
        for i in 0..=last {
            out.extend_from_slice(&self.blocks[&i]);
        }
        Ok(out)
    }
}

fn decode_a(bits: &[u8]) -> Decoded {
    let mut d = Decoded::default();
    if bits.len() < A_LEN_BITS + CRC_BITS {
        d.rejected_candidates += 1;
        return d;
    }
    let len = read_uint(bits, 0, A_LEN_BITS);
    if A_LEN_BITS + len + CRC_BITS != bits.len() {
        d.rejected_candidates += 1; // truncation / insertion / deletion: fail closed
        return d;
    }
    let body = A_LEN_BITS + len;
    if crc16(&bits[..body]) as usize != read_uint(bits, body, CRC_BITS) {
        d.rejected_candidates += 1;
        return d;
    }
    d.accept(0, 0, true, bits[A_LEN_BITS..body].to_vec());
    d
}

/// Naive fixed-offset receiver: no sync, so after one insertion/deletion every
/// later block is misaligned.
fn decode_b(bits: &[u8], k: usize) -> Decoded {
    let mut d = Decoded::default();
    let mut pos = 0;
    while pos + HDR_BITS + CRC_BITS <= bits.len() {
        let len = read_uint(bits, pos + IDX_BITS + FLAG_BITS, LEN_BITS);
        if len > k {
            d.rejected_candidates += 1;
            break; // cannot know where the next block starts
        }
        let blen = HDR_BITS + len + CRC_BITS;
        if pos + blen > bits.len() {
            d.rejected_candidates += 1; // truncated block
            break;
        }
        match check_raw(&bits[pos..pos + blen]) {
            Some((idx, last, p)) => d.accept(pos, idx, last, p),
            None => d.rejected_candidates += 1,
        }
        pos += blen;
    }
    d
}

fn parse_plain(bits: &[u8], p: usize, k: usize) -> Option<(usize, usize, bool, Bits, usize)> {
    if p + HDR_BITS + CRC_BITS > bits.len() {
        return None;
    }
    let len = read_uint(bits, p + IDX_BITS + FLAG_BITS, LEN_BITS);
    if len > k {
        return None;
    }
    let blen = HDR_BITS + len + CRC_BITS;
    if p + blen > bits.len() {
        return None;
    }
    check_raw(&bits[p..p + blen]).map(|(i, l, pl)| (blen, i, l, pl, 0))
}

fn decode_words(bits: &[u8], p: usize, nwords: usize) -> (Bits, usize) {
    let mut out = Vec::with_capacity(nwords * 4);
    let mut fixes = 0;
    for w in 0..nwords {
        let (nib, fixed) = hamming_decode_word(&bits[p + 7 * w..p + 7 * w + 7]);
        out.extend_from_slice(&nib);
        fixes += fixed as usize;
    }
    (out, fixes)
}

fn parse_fec(bits: &[u8], p: usize, k: usize) -> Option<(usize, usize, bool, Bits, usize)> {
    let hdr_words = HDR_BITS.div_ceil(4);
    if p + 7 * hdr_words > bits.len() {
        return None;
    }
    let (hdr, _) = decode_words(bits, p, hdr_words);
    let len = read_uint(&hdr, IDX_BITS + FLAG_BITS, LEN_BITS);
    if len > k {
        return None;
    }
    let raw_len = HDR_BITS + len + CRC_BITS;
    let nwords = raw_len.div_ceil(4);
    if p + 7 * nwords > bits.len() {
        return None;
    }
    let (mut raw, fixes) = decode_words(bits, p, nwords);
    raw.truncate(raw_len);
    check_raw(&raw).map(|(i, l, pl)| (7 * nwords, i, l, pl, fixes))
}

/// Sync-scanning receiver. Every candidate is validated by CRC, so payload bits
/// that happen to equal SYNC can never silently become a block (fail closed).
fn decode_scan(bits: &[u8], k: usize, fec: bool) -> Decoded {
    let mut d = Decoded::default();
    let mut pos = 0;
    while pos + SYNC.len() <= bits.len() {
        if bits[pos..pos + SYNC.len()] != SYNC {
            pos += 1;
            continue;
        }
        let p = pos + SYNC.len();
        let parsed = if fec { parse_fec(bits, p, k) } else { parse_plain(bits, p, k) };
        match parsed {
            Some((consumed, idx, last, payload, fixes)) => {
                d.corrected_bits += fixes;
                d.accept(pos, idx, last, payload);
                pos = p + consumed;
            }
            None => {
                d.rejected_candidates += 1;
                pos += 1;
            }
        }
    }
    d
}

pub fn decode(variant: Variant, bits: &[u8], k: usize) -> Decoded {
    match variant {
        Variant::A => decode_a(bits),
        Variant::B => decode_b(bits, k),
        Variant::C => decode_scan(bits, k, false),
        Variant::D => decode_scan(bits, k, true),
    }
}

// ------------------------------------------------------------------ channel

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Fault {
    Flip(usize),
    Insert(usize, u8),
    Delete(usize),
    Burst(usize, usize),
}

pub fn apply_fault(bits: &[u8], f: Fault) -> Bits {
    let mut out = bits.to_vec();
    match f {
        Fault::Flip(p) => {
            if p < out.len() {
                out[p] ^= 1;
            }
        }
        Fault::Insert(p, b) => out.insert(p.min(out.len()), b & 1),
        Fault::Delete(p) => {
            if p < out.len() {
                out.remove(p);
            }
        }
        Fault::Burst(p, l) => {
            for i in p..(p + l).min(out.len()) {
                out[i] ^= 1;
            }
        }
    }
    out
}

// -------------------------------------------------------------- retry (ARQ)

#[derive(Clone, Debug)]
pub struct RetryReport {
    pub success: bool,
    pub rounds: usize,
    pub first_wire_bits: usize,
    pub retry_bits: usize,
    pub missing_after_first: usize,
    pub corrected_bits: usize,
}

/// Fault hits only the first transmission; retries are clean. The sender
/// retransmits only the missing blocks (A: the whole message, by definition).
pub fn simulate_retry(variant: Variant, payload: &[u8], k: usize, fault: Fault) -> RetryReport {
    let (first, acc) = encode(variant, payload, k, None).expect("encode");
    let total_blocks = acc.blocks;
    let mut rx = Decoded::default();
    let mut rep = RetryReport {
        success: false,
        rounds: 1,
        first_wire_bits: acc.total_wire_bits,
        retry_bits: 0,
        missing_after_first: 0,
        corrected_bits: 0,
    };
    let mut stream = apply_fault(&first, fault);
    let mut round = 1;
    loop {
        let d = decode(variant, &stream, k);
        rep.corrected_bits += d.corrected_bits;
        rx.conflicts += d.conflicts;
        for (idx, p) in &d.blocks {
            let last = d.last_index == Some(*idx);
            rx.accept(0, *idx, last, p.clone());
        }
        match rx.assemble() {
            Ok(m) => {
                rep.success = m == payload;
                break;
            }
            Err(e) => {
                let want: Vec<usize> = match e {
                    AssembleError::MissingBlocks(m) => m,
                    // extent unknown: receiver reports what it holds; sender resends
                    // the gaps below the highest seen index plus the unseen tail.
                    AssembleError::NoLastBlock => match rx.blocks.keys().next_back().copied() {
                        Some(max) => (0..total_blocks)
                            .filter(|i| *i > max || !rx.blocks.contains_key(i))
                            .collect(),
                        None => (0..total_blocks).collect(),
                    },
                    // conflicting data: nothing received can be trusted, resend all
                    AssembleError::Conflict(_) => {
                        rx = Decoded::default();
                        (0..total_blocks).collect()
                    }
                };
                if round == 1 {
                    rep.missing_after_first = want.len();
                }
                if round >= 4 {
                    break;
                }
                let (s, a) = encode(variant, payload, k, Some(&want)).expect("encode");
                rep.retry_bits += a.total_wire_bits;
                stream = s;
                round += 1;
                rep.rounds = round;
            }
        }
    }
    rep
}

// ------------------------------------------------------------ determinism

pub struct Lcg(pub u64);

impl Lcg {
    pub fn next_u64(&mut self) -> u64 {
        self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        self.0 >> 33
    }
    pub fn below(&mut self, n: usize) -> usize {
        (self.next_u64() as usize) % n.max(1)
    }
}

pub fn pseudo_payload(n: usize, seed: u64) -> Bits {
    let mut g = Lcg(seed);
    (0..n).map(|_| (g.next_u64() & 1) as u8).collect()
}

/// Random multi-flip / burst / insertion / deletion corruption. Returns
/// (undetected, trials): `undetected` = assemble() succeeded with WRONG data.
pub fn undetected_trials(variant: Variant, payload: &[u8], k: usize, trials: usize, seed: u64) -> (usize, usize) {
    let (wire, _) = encode(variant, payload, k, None).expect("encode");
    let mut g = Lcg(seed);
    let mut undetected = 0;
    for _ in 0..trials {
        let mut s = wire.clone();
        match g.below(4) {
            0 => {
                for _ in 0..(2 + g.below(4)) {
                    s = apply_fault(&s, Fault::Flip(g.below(s.len())));
                }
            }
            1 => s = apply_fault(&s, Fault::Burst(g.below(s.len()), 2 + g.below(19))),
            2 => s = apply_fault(&s, Fault::Insert(g.below(s.len() + 1), (g.next_u64() & 1) as u8)),
            _ => s = apply_fault(&s, Fault::Delete(g.below(s.len()))),
        }
        if let Ok(m) = decode(variant, &s, k).assemble() {
            if m != payload {
                undetected += 1;
            }
        }
    }
    (undetected, trials)
}

#[cfg(test)]
mod tests {
    use super::*;

    const K: usize = 32;

    fn payload() -> Bits {
        pseudo_payload(272, 0x5E55)
    }

    #[test]
    fn clean_roundtrip_all_variants() {
        let p = payload();
        for v in Variant::ALL {
            let (w, acc) = encode(v, &p, K, None).unwrap();
            assert_eq!(acc.total_wire_bits, w.len());
            assert_eq!(acc.semantic_payload_bits, p.len());
            assert_eq!(decode(v, &w, K).assemble().unwrap(), p, "{}", v.name());
        }
    }

    #[test]
    fn empty_and_exact_multiple_payloads_have_no_padding_ambiguity() {
        for n in [0usize, 1, 31, 32, 33, 64, 272] {
            let p = pseudo_payload(n, n as u64 + 7);
            for v in Variant::ALL {
                let (w, _) = encode(v, &p, K, None).unwrap();
                assert_eq!(decode(v, &w, K).assemble().unwrap(), p, "{} n={n}", v.name());
            }
        }
    }

    #[test]
    fn single_bit_flip_never_yields_wrong_data() {
        let p = payload();
        for v in Variant::ALL {
            let (w, _) = encode(v, &p, K, None).unwrap();
            for pos in 0..w.len() {
                let s = apply_fault(&w, Fault::Flip(pos));
                if let Ok(m) = decode(v, &s, K).assemble() {
                    assert_eq!(m, p, "{} flip@{pos} accepted wrong data", v.name());
                }
            }
        }
    }

    #[test]
    fn selective_retry_recovers_every_single_flip() {
        let p = payload();
        for v in Variant::ALL {
            let (w, _) = encode(v, &p, K, None).unwrap();
            for pos in 0..w.len() {
                let r = simulate_retry(v, &p, K, Fault::Flip(pos));
                assert!(r.success, "{} flip@{pos}", v.name());
            }
        }
    }

    #[test]
    fn variant_a_retry_is_whole_message_but_c_costs_one_block() {
        let p = payload();
        let (wa, _) = encode(Variant::A, &p, K, None).unwrap();
        let ra = simulate_retry(Variant::A, &p, K, Fault::Flip(40));
        assert_eq!(ra.retry_bits, wa.len());
        // flip inside a payload bit of block 1 in C
        let rc = simulate_retry(Variant::C, &p, K, Fault::Flip(SYNC.len() + HDR_BITS + 3 + (SYNC.len() + HDR_BITS + K + CRC_BITS)));
        let (_, one) = encode(Variant::C, &p, K, Some(&[1])).unwrap();
        assert_eq!(rc.missing_after_first, 1);
        assert_eq!(rc.retry_bits, one.total_wire_bits);
        assert!(rc.retry_bits < ra.retry_bits);
    }

    #[test]
    fn hamming_corrects_single_flip_in_body_with_zero_retry() {
        let p = payload();
        let body_flip = SYNC.len() + 7 * 6 + 2; // inside block 0 body
        let r = simulate_retry(Variant::D, &p, K, Fault::Flip(body_flip));
        assert!(r.success);
        assert_eq!(r.retry_bits, 0);
        assert_eq!(r.corrected_bits, 1);
    }

    #[test]
    fn hamming_is_not_magic_sync_flip_still_costs_a_block() {
        let p = payload();
        let r = simulate_retry(Variant::D, &p, K, Fault::Flip(2)); // inside SYNC of block 0
        assert!(r.success);
        assert_eq!(r.missing_after_first, 1);
        assert!(r.retry_bits > 0);
    }

    #[test]
    fn deletion_cascades_without_sync_but_not_with_sync() {
        let p = payload();
        let pos = 3 * (HDR_BITS + K + CRC_BITS) + 20; // inside block 3 of B
        let rb = simulate_retry(Variant::B, &p, K, Fault::Delete(pos));
        let rc = simulate_retry(Variant::C, &p, K, Fault::Delete(pos + 3 * SYNC.len()));
        let rd = simulate_retry(Variant::D, &p, K, Fault::Delete(pos + 3 * SYNC.len()));
        assert!(rb.success && rc.success && rd.success);
        assert!(rb.missing_after_first > 1, "B should cascade, lost {}", rb.missing_after_first);
        assert_eq!(rc.missing_after_first, 1, "C should lose exactly one block");
        assert_eq!(rd.missing_after_first, 1, "D should lose exactly one block");
    }

    #[test]
    fn insertion_resynchronises_with_sync() {
        let p = payload();
        let off = 2 * (SYNC.len() + HDR_BITS + K + CRC_BITS) + 25;
        for bit in [0u8, 1] {
            let r = simulate_retry(Variant::C, &p, K, Fault::Insert(off, bit));
            assert!(r.success);
            assert_eq!(r.missing_after_first, 1);
        }
    }

    #[test]
    fn burst_errors_are_detected_and_recovered() {
        let p = payload();
        for v in Variant::ALL {
            for len in [2usize, 8, 16] {
                let r = simulate_retry(v, &p, K, Fault::Burst(50, len));
                assert!(r.success, "{} burst {len}", v.name());
            }
        }
    }

    #[test]
    fn truncated_block_fails_closed() {
        let p = payload();
        for v in [Variant::B, Variant::C, Variant::D] {
            let (w, _) = encode(v, &p, K, None).unwrap();
            let cut = &w[..w.len() - 5];
            let d = decode(v, cut, K);
            assert!(d.assemble().is_err(), "{} accepted truncated stream", v.name());
        }
        let (w, _) = encode(Variant::A, &p, K, None).unwrap();
        assert!(decode(Variant::A, &w[..w.len() - 1], K).assemble().is_err());
    }

    #[test]
    fn repeated_and_omitted_block_index_are_detectable() {
        let p = payload();
        let (b0, _) = encode(Variant::C, &p, K, Some(&[0])).unwrap();
        let (b1, _) = encode(Variant::C, &p, K, Some(&[1])).unwrap();
        let (rest, _) = encode(Variant::C, &p, K, Some(&(2..9).collect::<Vec<_>>())).unwrap();
        // omitted block 1
        let mut s = b0.clone();
        s.extend_from_slice(&rest);
        assert_eq!(decode(Variant::C, &s, K).assemble(), Err(AssembleError::MissingBlocks(vec![1])));
        // repeated block 1 (identical): detected as duplicate, still assembles
        let mut s = b0.clone();
        s.extend_from_slice(&b1);
        s.extend_from_slice(&b1);
        s.extend_from_slice(&rest);
        let d = decode(Variant::C, &s, K);
        assert_eq!(d.duplicates, 1);
        assert_eq!(d.assemble().unwrap(), p);
        // conflicting index: same idx, different valid payload
        let other = pseudo_payload(272, 99);
        let (evil1, _) = encode(Variant::C, &other, K, Some(&[1])).unwrap();
        let mut s = b0;
        s.extend_from_slice(&b1);
        s.extend_from_slice(&evil1);
        s.extend_from_slice(&rest);
        let d = decode(Variant::C, &s, K);
        assert!(d.conflicts > 0);
        assert!(matches!(d.assemble(), Err(AssembleError::Conflict(_))));
    }

    #[test]
    fn payload_containing_sync_or_all_ones_is_never_an_unescaped_delimiter() {
        let mut p: Bits = Vec::new();
        while p.len() < 256 {
            p.extend_from_slice(&SYNC);
        }
        for payload in [p, vec![1u8; 200], vec![0u8; 200]] {
            for v in Variant::ALL {
                let (w, _) = encode(v, &payload, 16, None).unwrap();
                assert_eq!(decode(v, &w, 16).assemble().unwrap(), payload, "{}", v.name());
                if v == Variant::C || v == Variant::D {
                    let pos = 3 * (SYNC.len() + HDR_BITS + 16 + CRC_BITS) + 30;
                    let r = simulate_retry(v, &payload, 16, Fault::Delete(pos));
                    assert!(r.success, "{} lost data on sync-like payload", v.name());
                }
            }
        }
    }

    #[test]
    fn random_corruption_never_accepts_wrong_payload_in_bounded_trials() {
        let p = payload();
        for v in Variant::ALL {
            let (und, n) = undetected_trials(v, &p, K, 4000, 0xC0FFEE);
            assert!(und == 0, "{} accepted wrong data {und}/{n}", v.name());
        }
    }

    #[test]
    fn accounting_adds_up() {
        let p = payload();
        for v in Variant::ALL {
            let (w, a) = encode(v, &p, K, None).unwrap();
            let sum = a.semantic_payload_bits + a.sync_bits + a.block_index_bits + a.length_bits + a.crc_bits + a.fec_bits;
            assert_eq!(sum, w.len(), "{}", v.name());
            assert!(a.goodput() > 0.0 && a.goodput() < 1.0);
        }
    }

    #[test]
    fn crc_detects_every_single_flip_and_short_bursts() {
        let m = pseudo_payload(100, 3);
        let c = crc16(&m);
        for i in 0..m.len() {
            let mut x = m.clone();
            x[i] ^= 1;
            assert_ne!(crc16(&x), c);
        }
        for start in 0..(m.len() - 16) {
            let mut x = m.clone();
            for bit in x.iter_mut().skip(start).take(16) {
                *bit ^= 1;
            }
            assert_ne!(crc16(&x), c, "burst@{start}");
        }
    }
}
