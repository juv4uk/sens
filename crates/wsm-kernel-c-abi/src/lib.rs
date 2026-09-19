//! Semantic-neutral C ABI contract for the four-kernel experiment.
//!
//! This crate defines only mechanical calling conventions. It does not define
//! a shared semantic result type. Kernel payloads remain opaque bytes.

use core::ffi::{c_char, c_void};

pub const WSM_KERNEL_ABI_VERSION: u32 = 2;

#[repr(u32)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WsmKernelKind {
    CommonLisp = 1,
    Prolog = 2,
    Clips = 3,
    Datalog = 4,
}

#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct WsmByteSpan {
    pub ptr: *const u8,
    pub len: usize,
}

impl WsmByteSpan {
    pub const fn empty() -> Self {
        Self { ptr: core::ptr::null(), len: 0 }
    }
}

#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct WsmMutableByteSpan {
    pub ptr: *mut u8,
    pub len: usize,
}

impl WsmMutableByteSpan {
    pub const fn empty() -> Self {
        Self { ptr: core::ptr::null_mut(), len: 0 }
    }
}

#[repr(i32)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WsmStatus {
    Ok = 0,
    InvalidArgument = 1,
    NotRunning = 2,
    BufferTooSmall = 3,
    KernelFailure = 4,
}

pub type WsmStartFn = unsafe extern "C" fn(context: *mut c_void) -> WsmStatus;
pub type WsmStopFn = unsafe extern "C" fn(context: *mut c_void) -> WsmStatus;
#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct WsmKernelRequest {
    /// Opaque 8-bit semantic primitive identity owned by my-lisp.
    pub semantic_id: u8,
    pub payload: WsmByteSpan,
}

pub type WsmExchangeFn = unsafe extern "C" fn(
    context: *mut c_void,
    request: WsmKernelRequest,
    response: WsmMutableByteSpan,
    written: *mut usize,
) -> WsmStatus;
pub type WsmSnapshotFn = unsafe extern "C" fn(
    context: *mut c_void,
    response: WsmMutableByteSpan,
    written: *mut usize,
) -> WsmStatus;

#[repr(C)]
#[derive(Clone, Copy)]
pub struct WsmKernelVTable {
    pub abi_version: u32,
    pub kernel: WsmKernelKind,
    pub context: *mut c_void,
    pub start: Option<WsmStartFn>,
    pub exchange: Option<WsmExchangeFn>,
    pub snapshot: Option<WsmSnapshotFn>,
    pub stop: Option<WsmStopFn>,
}

impl WsmKernelVTable {
    pub const fn is_mechanically_complete(&self) -> bool {
        self.abi_version == WSM_KERNEL_ABI_VERSION
            && self.start.is_some()
            && self.exchange.is_some()
            && self.snapshot.is_some()
            && self.stop.is_some()
    }
}

#[no_mangle]
pub extern "C" fn wsm_kernel_abi_version() -> u32 {
    WSM_KERNEL_ABI_VERSION
}

#[no_mangle]
pub extern "C" fn wsm_kernel_kind_name(kind: WsmKernelKind) -> *const c_char {
    match kind {
        WsmKernelKind::CommonLisp => c"common-lisp".as_ptr(),
        WsmKernelKind::Prolog => c"prolog".as_ptr(),
        WsmKernelKind::Clips => c"clips".as_ptr(),
        WsmKernelKind::Datalog => c"datalog".as_ptr(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    unsafe extern "C" fn ok_start(_: *mut c_void) -> WsmStatus { WsmStatus::Ok }
    unsafe extern "C" fn ok_stop(_: *mut c_void) -> WsmStatus { WsmStatus::Ok }
    unsafe extern "C" fn echo_exchange(
        _: *mut c_void,
        request: WsmKernelRequest,
        response: WsmMutableByteSpan,
        written: *mut usize,
    ) -> WsmStatus {
        if written.is_null() { return WsmStatus::InvalidArgument; }
        if request.payload.len != 0 && request.payload.ptr.is_null() {
            return WsmStatus::InvalidArgument;
        }
        let input = if request.payload.len == 0 {
            &[]
        } else {
            unsafe { core::slice::from_raw_parts(request.payload.ptr, request.payload.len) }
        };
        if response.len < input.len() {
            unsafe { *written = input.len(); }
            return WsmStatus::BufferTooSmall;
        }
        if !input.is_empty() && response.ptr.is_null() { return WsmStatus::InvalidArgument; }
        unsafe {
            core::ptr::copy_nonoverlapping(input.as_ptr(), response.ptr, input.len());
            *written = input.len();
        }
        WsmStatus::Ok
    }
    unsafe extern "C" fn empty_snapshot(
        _: *mut c_void,
        _: WsmMutableByteSpan,
        written: *mut usize,
    ) -> WsmStatus {
        if written.is_null() { return WsmStatus::InvalidArgument; }
        unsafe { *written = 0; }
        WsmStatus::Ok
    }

    fn table(kind: WsmKernelKind) -> WsmKernelVTable {
        WsmKernelVTable {
            abi_version: WSM_KERNEL_ABI_VERSION,
            kernel: kind,
            context: core::ptr::null_mut(),
            start: Some(ok_start),
            exchange: Some(echo_exchange),
            snapshot: Some(empty_snapshot),
            stop: Some(ok_stop),
        }
    }

    #[test]
    fn all_four_kernel_kinds_share_only_the_mechanical_contract() {
        for kind in [
            WsmKernelKind::CommonLisp,
            WsmKernelKind::Prolog,
            WsmKernelKind::Clips,
            WsmKernelKind::Datalog,
        ] {
            assert!(table(kind).is_mechanically_complete());
        }
    }

    #[test]
    fn exchange_carries_semantic_id_as_opaque_u8() {
        let request = WsmKernelRequest {
            semantic_id: 0b0000_0101,
            payload: WsmByteSpan::empty(),
        };
        assert_eq!(request.semantic_id, 0b0000_0101);
        assert_eq!(request.payload.len, 0);
    }

    #[test]
    fn exchange_transports_bytes_without_interpreting_them() {
        let vt = table(WsmKernelKind::Prolog);
        let input = b"[alice,alice]";
        let mut output = [0u8; 32];
        let mut written = 0usize;
        let status = unsafe {
            (vt.exchange.unwrap())(
                vt.context,
                WsmKernelRequest {
                    semantic_id: 0b0000_0011,
                    payload: WsmByteSpan { ptr: input.as_ptr(), len: input.len() },
                },
                WsmMutableByteSpan { ptr: output.as_mut_ptr(), len: output.len() },
                &mut written,
            )
        };
        assert_eq!(status, WsmStatus::Ok);
        assert_eq!(&output[..written], input);
    }
}
