//! Shared mechanical Zig transport FFI for SENS host binaries.
//! Rust buffers/statuses are NOT SENS domain identity, law, or truth.
//! Zig validates/repackages physical bytes; only SENS owns semantic admission.
//! Caller-owned pointers, no host structs crossing the CLI's T5 boundary.

unsafe extern "C" {
    fn sens_zig_codec_abi_version() -> u32;
    fn sens_zig_t5_validate(input: *const u8, len: usize) -> i32;
    fn sens_zig_t5_repack(
        input: *const u8, len: usize, output: *mut u8, capacity: usize
    ) -> isize;
    fn sens_zig_t5_encode_dense(
        packed_bits: *const u8, exact_bit_len: usize,
        widths: *const u8, word_count: usize,
        output: *mut u8, capacity: usize,
    ) -> isize;
    fn sens_zig_t5_decode_dense(
        input: *const u8, len: usize,
        output_bits: *mut u8, bit_bytes_capacity: usize,
        output_widths: *mut u8, word_capacity: usize,
        meaningful_bits: *mut usize, word_count: *mut usize,
    ) -> i32;
    fn sens_zig_f3c_pack(
        input: *const u8, len: usize, output: *mut u8, capacity: usize
    ) -> isize;
    fn sens_zig_f3c_unpack(
        input: *const u8, len: usize, output: *mut u8, capacity: usize
    ) -> isize;
}

fn version() -> Result<(), String> {
    // SAFETY: zero-argument pure function from a statically linked Zig library.
    if unsafe { sens_zig_codec_abi_version() } != 1 {
        return Err("Zig codec C ABI version mismatch".into());
    }
    Ok(())
}

pub fn validate_t5(bytes: &[u8]) -> Result<(), String> {
    version()?;
    // SAFETY: the borrowed byte slice lives through the synchronous call.
    if unsafe { sens_zig_t5_validate(bytes.as_ptr(), bytes.len()) } != 0 {
        return Err("Zig physical T5 rejected; no SENS execution".into());
    }
    Ok(())
}

/// Zig decodes ONLY physical T5; SENS still owns the D2 reader and
/// all executable semantics. Return canonical dense bits + word-widths.
/// Two-phase ABI refuses malformed T5 before any Rust SENS evaluation.
pub fn decode_dense_t5(bytes: &[u8]) -> Result<(sens::PackedBitstream, Vec<usize>), String> {
    version()?;
    let mut bit_len = 0usize;
    let mut word_count = 0usize;
    let mut no_bits: [u8; 0] = [];
    let mut no_widths: [u8; 0] = [];
    // SAFETY: query call has zero output capacities; Zig only writes the
    // two stack-owned length variables and never dereferences output buffers.
    let query = unsafe {
        sens_zig_t5_decode_dense(
            bytes.as_ptr(), bytes.len(),
            no_bits.as_mut_ptr(), 0,
            no_widths.as_mut_ptr(), 0,
            &mut bit_len, &mut word_count,
        )
    };
    if query != -2 || bit_len == 0 || word_count == 0 {
        return Err(format!("Zig T5 physical decode rejected: transport_status={query}"));
    }
    let bit_bytes = bit_len.checked_add(7).ok_or("Zig T5 bit length overflow")? / 8;
    let mut packed = vec![0u8; bit_bytes];
    let mut widths = vec![0u8; word_count];
    let mut verified_bit_len = 0usize;
    let mut verified_word_count = 0usize;
    // SAFETY: caller-owned buffers remain allocated throughout this
    // synchronous call; Zig validates all capacities before any write.
    let actual = unsafe {
        sens_zig_t5_decode_dense(
            bytes.as_ptr(), bytes.len(),
            packed.as_mut_ptr(), packed.len(),
            widths.as_mut_ptr(), widths.len(),
            &mut verified_bit_len, &mut verified_word_count,
        )
    };
    if actual != 0 || verified_bit_len != bit_len || verified_word_count != word_count {
        return Err(format!(
            "Zig T5 physical decode changed under identical input: status={actual}"
        ));
    }
    let packed = sens::PackedBitstream::from_parts(packed, bit_len)
        .ok_or("Zig returned noncanonical dense physical bits")?;
    // No Rust domain/token enum crosses ABI: SENS's own packed-word reader
    // will interpret these exact widths and preserve identity.
    let widths = widths.into_iter().map(usize::from).collect();
    Ok((packed, widths))
}

/// Exact SENS-owned word bitstream plus explicit word-width schedule.
/// Zig creates T5 physical bytes; Rust enum/Word never crosses the C ABI.
/// A host usize here is an ABI transport length, never SENS domain identity.
pub fn encode_dense_t5(packed: &sens::PackedBitstream, widths: &[u8]) -> Result<Vec<u8>, String> {
    version()?;
    if widths.is_empty() || packed.bit_len() == 0 {
        return Err("empty SENS transport bitstream".into());
    }
    let trits = packed.bit_len().checked_add(widths.len() - 1)
        .ok_or("T5 trit count overflow")?;
    let cap = trits.checked_add(4).ok_or("T5 padding overflow")? / 5;
    let mut physical = vec![0u8; cap];
    // SAFETY: packed.bytes(), widths and physical are caller-owned and remain
    // alive for the duration of this call. Zig checks exact widths and bounds.
    let len = unsafe {
        sens_zig_t5_encode_dense(
            packed.bytes().as_ptr(), packed.bit_len(),
            widths.as_ptr(), widths.len(), physical.as_mut_ptr(), physical.len()
        )
    };
    if len < 0 || len as usize != physical.len() {
        return Err(format!(
            "Zig T5 exact-bit pack rejected: transport_status={len} expected_bytes={cap}"
        ));
    }
    Ok(physical)
}

/// Physical byte gateway only. The existing SENS-owned projection
/// supplies the admitted reference bytes; Rust must not translate them
/// into a host Word/enum ABI or interpret Zig status as SENS truth.
/// Zig independently decodes and re-encodes the bytes, fail-closed.
pub fn repack_t5(reference_bytes: &[u8]) -> Result<Vec<u8>, String> {
    version()?;
    let mut physical = vec![0u8; reference_bytes.len()];
    // SAFETY: both caller-owned buffers live throughout this synchronous
    // call, and Zig is bounded by the provided lengths/capacity.
    let len = unsafe {
        sens_zig_t5_repack(
            reference_bytes.as_ptr(), reference_bytes.len(),
            physical.as_mut_ptr(), physical.len()
        )
    };
    if len < 0 || len as usize != physical.len() {
        return Err(format!("Zig T5 physical gateway rejected: transport_status={len}"));
    }
    if physical != reference_bytes {
        return Err("Zig T5 repack mismatched authoritative physical input bytes".into());
    }
    Ok(physical)
}

pub fn encode_f3(t5: &[u8]) -> Result<Option<Vec<u8>>, String> {
    version()?;
    if t5.len() > 16 { return Ok(None); }
    let mut bytes = vec![0u8; 16];
    // SAFETY: Zig writes at most the provided capacity.
    let len = unsafe {
        sens_zig_f3c_pack(t5.as_ptr(), t5.len(), bytes.as_mut_ptr(), bytes.len())
    };
    if len == -3 { return Ok(None); } // not smaller: T5 remains production
    if len <= 0 { return Err(format!("Zig F3C pack rejected: code={len}")); }
    bytes.truncate(len as usize);
    if bytes.len() >= t5.len() { return Err("Zig F3C did not save bytes".into()); }
    Ok(Some(bytes))
}

pub fn decode_f3(carrier: &[u8]) -> Result<Vec<u8>, String> {
    version()?;
    let mut output = vec![0u8; 16];
    // SAFETY: caller owns valid input/output slices until call returns.
    let len = unsafe {
        sens_zig_f3c_unpack(
            carrier.as_ptr(), carrier.len(), output.as_mut_ptr(), output.len()
        )
    };
    if len <= 0 { return Err(format!("explicit Zig F3C rejected: code={len}")); }
    output.truncate(len as usize);
    // Zig first, then the existing SENS canonical parser/evaluator.
    validate_t5(&output)?;
    Ok(output)
}
