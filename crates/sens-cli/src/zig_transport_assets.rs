//! Opaque checked-in byte assets exposed by the ROOT Zig transport module.
//! Not part of the nine canonical transport_abi.zig ABI-v2 codec functions.
//! Rust does not embed or interpret either SENS source; ownership stays Zig.
//! Root exports are implemented in zig_transport_root.zig, built via build.rs.
unsafe extern "C" {
    pub(super) fn sens_zig_linter_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_contract_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_sanskrit_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_ukr_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_uk_bytes_copy(output: *mut u8, capacity: usize) -> isize;
}
