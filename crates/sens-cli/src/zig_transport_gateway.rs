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
