//! Independent Common Lisp execution kernel.
//!
//! my-lisp owns semantic identities and laws. This crate owns only process
//! execution against a real Common Lisp implementation and preserves the
//! caller-provided 8-bit semantic identity as opaque provenance.
//!
//! The first witness uses SBCL, but SBCL names/functions are execution
//! witnesses, never semantic authority.

use std::ffi::c_void;
use std::fmt;
use std::path::{Path, PathBuf};
use std::process::Command;

use wsm_kernel_c_abi::{
    WsmKernelKind, WsmKernelRequest, WsmKernelVTable, WsmMutableByteSpan, WsmStatus,
    WSM_KERNEL_ABI_VERSION,
};

/// Opaque my-lisp experimental semantic identity.
///
/// This crate deliberately does not attach meaning to the byte.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct SemanticId(pub u8);

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CommonLispRequest {
    pub semantic_id: SemanticId,
    pub form: String,
}

impl CommonLispRequest {
    pub fn new(semantic_id: u8, form: impl Into<String>) -> Self {
        Self {
            semantic_id: SemanticId(semantic_id),
            form: form.into(),
        }
    }

    fn printable_eval_form(&self) -> String {
        format!(
            "(let ((*print-readably* t)) (write (progn {}) :escape t) (terpri))",
            self.form
        )
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CommonLispResult {
    pub semantic_id: SemanticId,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProcessResult {
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
}

#[derive(Debug)]
pub enum CommonLispKernelError {
    Spawn(std::io::Error),
    ProcessFailed {
        semantic_id: Option<SemanticId>,
        status: Option<i32>,
        stdout: Vec<u8>,
        stderr: Vec<u8>,
    },
}

impl fmt::Display for CommonLispKernelError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Spawn(error) => write!(formatter, "failed to start Common Lisp runtime: {error}"),
            Self::ProcessFailed {
                semantic_id,
                status,
                stderr,
                ..
            } => write!(
                formatter,
                "Common Lisp process failed for semantic id {semantic_id:?} ({status:?}): {}",
                String::from_utf8_lossy(stderr)
            ),
        }
    }
}

impl std::error::Error for CommonLispKernelError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Spawn(error) => Some(error),
            Self::ProcessFailed { .. } => None,
        }
    }
}

#[derive(Clone, Debug)]
pub struct CommonLispKernel {
    executable: PathBuf,
}

impl Default for CommonLispKernel {
    fn default() -> Self {
        Self::new("sbcl")
    }
}

impl CommonLispKernel {
    pub fn new(executable: impl Into<PathBuf>) -> Self {
        Self {
            executable: executable.into(),
        }
    }

    pub fn executable(&self) -> &Path {
        &self.executable
    }

    pub fn version(&self) -> Result<ProcessResult, CommonLispKernelError> {
        let output = Command::new(&self.executable)
            .arg("--version")
            .output()
            .map_err(CommonLispKernelError::Spawn)?;

        if !output.status.success() {
            return Err(CommonLispKernelError::ProcessFailed {
                semantic_id: None,
                status: output.status.code(),
                stdout: output.stdout,
                stderr: output.stderr,
            });
        }

        Ok(ProcessResult {
            stdout: output.stdout,
            stderr: output.stderr,
        })
    }

    pub fn evaluate(
        &self,
        request: &CommonLispRequest,
    ) -> Result<CommonLispResult, CommonLispKernelError> {
        let output = Command::new(&self.executable)
            .arg("--noinform")
            .arg("--disable-debugger")
            .arg("--non-interactive")
            .arg("--eval")
            .arg(request.printable_eval_form())
            .arg("--quit")
            .output()
            .map_err(CommonLispKernelError::Spawn)?;

        if !output.status.success() {
            return Err(CommonLispKernelError::ProcessFailed {
                semantic_id: Some(request.semantic_id),
                status: output.status.code(),
                stdout: output.stdout,
                stderr: output.stderr,
            });
        }

        Ok(CommonLispResult {
            semantic_id: request.semantic_id,
            stdout: output.stdout,
            stderr: output.stderr,
        })
    }
}

#[derive(Debug)]
struct CommonLispAbiContext {
    kernel: CommonLispKernel,
    running: bool,
    last_semantic_id: Option<SemanticId>,
}

/// Owns the stable context behind the semantic-neutral C ABI vtable.
///
/// The vtable transports a semantic ID byte and opaque payload. This adapter
/// does not interpret the ID; it only forwards the byte into CommonLispRequest.
pub struct CommonLispAbiAdapter {
    context: Box<CommonLispAbiContext>,
    vtable: WsmKernelVTable,
}

impl Default for CommonLispAbiAdapter {
    fn default() -> Self {
        Self::new(CommonLispKernel::default())
    }
}

impl CommonLispAbiAdapter {
    pub fn new(kernel: CommonLispKernel) -> Self {
        let mut context = Box::new(CommonLispAbiContext {
            kernel,
            running: false,
            last_semantic_id: None,
        });
        let context_ptr = (&mut *context) as *mut CommonLispAbiContext as *mut c_void;

        let vtable = WsmKernelVTable {
            abi_version: WSM_KERNEL_ABI_VERSION,
            kernel: WsmKernelKind::CommonLisp,
            context: context_ptr,
            start: Some(common_lisp_start),
            exchange: Some(common_lisp_exchange),
            snapshot: Some(common_lisp_snapshot),
            stop: Some(common_lisp_stop),
        };

        Self { context, vtable }
    }

    pub fn vtable(&self) -> WsmKernelVTable {
        self.vtable
    }

    pub fn last_semantic_id(&self) -> Option<SemanticId> {
        self.context.last_semantic_id
    }
}

unsafe fn abi_context_mut<'a>(context: *mut c_void) -> Option<&'a mut CommonLispAbiContext> {
    unsafe { (context as *mut CommonLispAbiContext).as_mut() }
}

unsafe extern "C" fn common_lisp_start(context: *mut c_void) -> WsmStatus {
    let Some(context) = (unsafe { abi_context_mut(context) }) else {
        return WsmStatus::InvalidArgument;
    };
    context.running = true;
    WsmStatus::Ok
}

unsafe extern "C" fn common_lisp_stop(context: *mut c_void) -> WsmStatus {
    let Some(context) = (unsafe { abi_context_mut(context) }) else {
        return WsmStatus::InvalidArgument;
    };
    context.running = false;
    WsmStatus::Ok
}

unsafe extern "C" fn common_lisp_snapshot(
    context: *mut c_void,
    _: WsmMutableByteSpan,
    written: *mut usize,
) -> WsmStatus {
    if context.is_null() || written.is_null() {
        return WsmStatus::InvalidArgument;
    }
    unsafe {
        *written = 0;
    }
    WsmStatus::Ok
}

unsafe extern "C" fn common_lisp_exchange(
    context: *mut c_void,
    request: WsmKernelRequest,
    response: WsmMutableByteSpan,
    written: *mut usize,
) -> WsmStatus {
    if written.is_null() {
        return WsmStatus::InvalidArgument;
    }
    unsafe {
        *written = 0;
    }

    let Some(context) = (unsafe { abi_context_mut(context) }) else {
        return WsmStatus::InvalidArgument;
    };
    if !context.running {
        return WsmStatus::NotRunning;
    }
    if request.payload.len != 0 && request.payload.ptr.is_null() {
        return WsmStatus::InvalidArgument;
    }

    let payload = if request.payload.len == 0 {
        &[]
    } else {
        unsafe { std::slice::from_raw_parts(request.payload.ptr, request.payload.len) }
    };
    let Ok(form) = std::str::from_utf8(payload) else {
        return WsmStatus::InvalidArgument;
    };

    let kernel_request = CommonLispRequest::new(request.semantic_id, form);
    let result = match context.kernel.evaluate(&kernel_request) {
        Ok(result) => result,
        Err(_) => return WsmStatus::KernelFailure,
    };

    if result.semantic_id != SemanticId(request.semantic_id) {
        return WsmStatus::KernelFailure;
    }
    context.last_semantic_id = Some(result.semantic_id);

    if response.len < result.stdout.len() {
        unsafe {
            *written = result.stdout.len();
        }
        return WsmStatus::BufferTooSmall;
    }
    if !result.stdout.is_empty() && response.ptr.is_null() {
        return WsmStatus::InvalidArgument;
    }

    if !result.stdout.is_empty() {
        unsafe {
            std::ptr::copy_nonoverlapping(
                result.stdout.as_ptr(),
                response.ptr,
                result.stdout.len(),
            );
        }
    }
    unsafe {
        *written = result.stdout.len();
    }
    WsmStatus::Ok
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn request_keeps_semantic_id_opaque() {
        let request = CommonLispRequest::new(0b0000_0101, "(car '(left right))");
        assert_eq!(request.semantic_id, SemanticId(0b0000_0101));
        assert!(request.printable_eval_form().contains("(car '(left right))"));
    }

    #[test]
    fn missing_runtime_is_a_transport_failure_not_a_semantic_result() {
        let kernel = CommonLispKernel::new("__wsm_common_lisp_that_does_not_exist__");
        let request = CommonLispRequest::new(0b0000_0101, "(car '(left right))");
        assert!(matches!(
            kernel.evaluate(&request),
            Err(CommonLispKernelError::Spawn(_))
        ));
    }

    #[test]
    fn process_failure_retains_the_semantic_id() {
        let error = CommonLispKernelError::ProcessFailed {
            semantic_id: Some(SemanticId(0b0000_0101)),
            status: Some(1),
            stdout: vec![],
            stderr: b"failure".to_vec(),
        };
        assert!(matches!(
            error,
            CommonLispKernelError::ProcessFailed {
                semantic_id: Some(SemanticId(0b0000_0101)),
                ..
            }
        ));
    }

    #[test]
    fn c_abi_adapter_declares_common_lisp_without_semantic_mapping() {
        let adapter = CommonLispAbiAdapter::new(CommonLispKernel::new(
            "__runtime_is_not_started_by_this_test__",
        ));
        let vtable = adapter.vtable();

        assert_eq!(vtable.abi_version, WSM_KERNEL_ABI_VERSION);
        assert_eq!(vtable.kernel, WsmKernelKind::CommonLisp);
        assert!(vtable.is_mechanically_complete());
        assert_eq!(adapter.last_semantic_id(), None);
    }

    #[test]
    fn c_abi_rejects_exchange_before_start() {
        let adapter = CommonLispAbiAdapter::new(CommonLispKernel::new(
            "__runtime_is_not_started_by_this_test__",
        ));
        let vtable = adapter.vtable();
        let input = b"(car '(left right))";
        let mut output = [0u8; 32];
        let mut written = 0usize;

        let status = unsafe {
            (vtable.exchange.expect("exchange callback"))(
                vtable.context,
                WsmKernelRequest {
                    semantic_id: 0b0000_0101,
                    payload: wsm_kernel_c_abi::WsmByteSpan {
                        ptr: input.as_ptr(),
                        len: input.len(),
                    },
                },
                WsmMutableByteSpan {
                    ptr: output.as_mut_ptr(),
                    len: output.len(),
                },
                &mut written,
            )
        };

        assert_eq!(status, WsmStatus::NotRunning);
        assert_eq!(written, 0);
    }
}
