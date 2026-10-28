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
        Self {
            ptr: core::ptr::null(),
            len: 0,
        }
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
        Self {
            ptr: core::ptr::null_mut(),
            len: 0,
        }
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
    /// Historical C ABI byte selector, never a current SENS semantic identity.
    /// Current identity requires a domain + exact bits via the Zig/SENS corridor.
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

