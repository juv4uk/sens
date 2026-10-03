//! Independent Common Lisp execution kernel.
//!
//! sens owns semantic identities and laws. This crate owns process execution
//! against a real Common Lisp implementation.
//!
//! Canonical requests carry `CoreDomainIdentity` (domain + exact bits).
//! The stable C ABI v2 still transports one historical byte; that byte is kept
//! behind the explicitly named `LegacyAbiSemanticId` compatibility boundary
//! and is never widened/narrowed into a canonical domain identity.
//!
//! The first witness uses SBCL, but SBCL names/functions are execution
//! witnesses, never semantic authority.

use sens::CoreDomainIdentity;
use std::ffi::c_void;
use std::fmt;
use std::path::{Path, PathBuf};
use std::process::Command;

use wsm_kernel_c_abi::{
    WsmKernelKind, WsmKernelRequest, WsmKernelVTable, WsmMutableByteSpan, WsmStatus,
    WSM_KERNEL_ABI_VERSION,
};

/// Historical exact-eight identity transported by C ABI v2.
///
/// This is compatibility provenance, not canonical SENS identity. In
/// particular there is deliberately no conversion to/from `CoreDomainIdentity`.
#[repr(transparent)]
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct LegacyAbiSemanticId(pub u8);

/// Provenance attached to a failed Common Lisp mechanism invocation.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum CommonLispIdentityContext {
    Canonical(CoreDomainIdentity),
    LegacyAbi(LegacyAbiSemanticId),
}

const LEGACY_SID_ADD: LegacyAbiSemanticId = LegacyAbiSemanticId(0b0000_1100);

fn legacy_semantic_form_for_request(
    semantic_id: LegacyAbiSemanticId,
    payload: &str,
) -> Result<String, ()> {
    if semantic_id != LEGACY_SID_ADD {
        return Ok(payload.to_string());
    }

    let mut parts = payload.split_whitespace();
    let left = parts.next().and_then(|value| value.parse::<i64>().ok()).ok_or(())?;
    let right = parts.next().and_then(|value| value.parse::<i64>().ok()).ok_or(())?;
    if parts.next().is_some() {
        return Err(());
    }

    Ok(format!("(+ {left} {right})"))
}

fn printable_eval_form(form: &str) -> String {
    format!(
        "(let ((*print-readably* t)) (write (progn {form}) :escape t) (terpri))"
    )
}

/// Canonical Common Lisp mechanism request with domain-qualified SENS provenance.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CommonLispRequest {
    pub semantic_identity: CoreDomainIdentity,
    pub form: String,
}

impl CommonLispRequest {
    pub fn new(semantic_identity: CoreDomainIdentity, form: impl Into<String>) -> Self {
        Self {
            semantic_identity,
            form: form.into(),
        }
    }

    fn printable_eval_form(&self) -> String {
        printable_eval_form(&self.form)
    }
}

/// Canonical Common Lisp result preserving the exact domain identity supplied
/// by the caller.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CommonLispResult {
    pub semantic_identity: CoreDomainIdentity,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
}

/// Compatibility-only request for historical ABI v2 byte identities.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LegacyCommonLispRequest {
    pub semantic_id: LegacyAbiSemanticId,
    pub form: String,
}

impl LegacyCommonLispRequest {
    pub fn new(semantic_id: LegacyAbiSemanticId, form: impl Into<String>) -> Self {
        Self {
            semantic_id,
            form: form.into(),
        }
    }

    fn printable_eval_form(&self) -> String {
        printable_eval_form(&self.form)
    }
}

/// Compatibility-only result for C ABI v2 / historical exact-eight callers.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LegacyCommonLispResult {
    pub semantic_id: LegacyAbiSemanticId,
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
        identity: Option<CommonLispIdentityContext>,
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
                identity,
                status,
                stderr,
                ..
            } => write!(
                formatter,
                "Common Lisp process failed for identity {identity:?} ({status:?}): {}",
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
                identity: None,
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

    fn run_form(
        &self,
        printable_form: String,
        identity: CommonLispIdentityContext,
    ) -> Result<ProcessResult, CommonLispKernelError> {
        let output = Command::new(&self.executable)
            .arg("--noinform")
            .arg("--disable-debugger")
            .arg("--non-interactive")
            .arg("--eval")
            .arg(printable_form)
            .arg("--quit")
            .output()
            .map_err(CommonLispKernelError::Spawn)?;

        if !output.status.success() {
            return Err(CommonLispKernelError::ProcessFailed {
                identity: Some(identity),
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

    /// Execute a canonical request without interpreting the identity in this
    /// mechanism crate. The same exact domain identity is returned unchanged.
    pub fn evaluate(
        &self,
        request: &CommonLispRequest,
    ) -> Result<CommonLispResult, CommonLispKernelError> {
        let output = self.run_form(
            request.printable_eval_form(),
            CommonLispIdentityContext::Canonical(request.semantic_identity),
        )?;

        Ok(CommonLispResult {
            semantic_identity: request.semantic_identity,
            stdout: output.stdout,
            stderr: output.stderr,
        })
    }

    /// Execute a compatibility-only exact-eight ABI request.
    ///
    /// No canonical domain identity is fabricated from the byte.
    pub fn evaluate_legacy_abi(
        &self,
        request: &LegacyCommonLispRequest,
    ) -> Result<LegacyCommonLispResult, CommonLispKernelError> {
        let output = self.run_form(
            request.printable_eval_form(),
            CommonLispIdentityContext::LegacyAbi(request.semantic_id),
        )?;

        Ok(LegacyCommonLispResult {
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
    last_legacy_semantic_id: Option<LegacyAbiSemanticId>,
}

/// Owns the stable context behind the semantic-neutral C ABI v2.
///
/// The ABI transports one historical byte plus mechanism arguments. This is an
/// explicit compatibility boundary; it never creates a `CoreDomainIdentity`.
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
            last_legacy_semantic_id: None,
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

    pub fn last_legacy_semantic_id(&self) -> Option<LegacyAbiSemanticId> {
        self.context.last_legacy_semantic_id
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
    let Ok(payload_text) = std::str::from_utf8(payload) else {
        return WsmStatus::InvalidArgument;
    };

    let legacy_id = LegacyAbiSemanticId(request.semantic_id);
    let Ok(form) = legacy_semantic_form_for_request(legacy_id, payload_text) else {
        return WsmStatus::InvalidArgument;
    };
    let kernel_request = LegacyCommonLispRequest::new(legacy_id, form);
    let result = match context.kernel.evaluate_legacy_abi(&kernel_request) {
        Ok(result) => result,
        Err(_) => return WsmStatus::KernelFailure,
    };

    if result.semantic_id != legacy_id {
        return WsmStatus::KernelFailure;
    }
    context.last_legacy_semantic_id = Some(result.semantic_id);

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
    use sens::{Bija3, Bit3};

    fn d3_car() -> CoreDomainIdentity {
        CoreDomainIdentity::from(Bija3::from_word(Bit3::new(0b101).unwrap()))
    }

    #[test]
    fn canonical_request_keeps_exact_domain_identity() {
        let request = CommonLispRequest::new(d3_car(), "(car '(left right))");
        assert_eq!(request.semantic_identity, d3_car());
        assert!(request.printable_eval_form().contains("(car '(left right))"));
    }

    #[test]
    fn legacy_add_uses_exact_abi_byte_and_arguments_only() {
        assert_eq!(
            legacy_semantic_form_for_request(LEGACY_SID_ADD, "2 3"),
            Ok("(+ 2 3)".to_string())
        );
        assert!(
            legacy_semantic_form_for_request(LEGACY_SID_ADD, "(- 7 3)").is_err(),
            "operator/form text must not override the legacy + anchor"
        );
        assert_eq!(
            legacy_semantic_form_for_request(
                LegacyAbiSemanticId(0b0000_0101),
                "(car '(left right))"
            ),
            Ok("(car '(left right))".to_string()),
            "raw legacy ABI paths remain explicit compatibility"
        );
    }

    #[test]
    fn missing_runtime_is_a_transport_failure_not_a_semantic_result() {
        let kernel = CommonLispKernel::new("__wsm_common_lisp_that_does_not_exist__");
        let request = CommonLispRequest::new(d3_car(), "(car '(left right))");
        assert!(matches!(
            kernel.evaluate(&request),
            Err(CommonLispKernelError::Spawn(_))
        ));
    }

    #[test]
    fn process_failure_retains_the_exact_domain_identity() {
        let error = CommonLispKernelError::ProcessFailed {
            identity: Some(CommonLispIdentityContext::Canonical(d3_car())),
            status: Some(1),
            stdout: vec![],
            stderr: b"failure".to_vec(),
        };
        assert!(matches!(
            error,
            CommonLispKernelError::ProcessFailed {
                identity: Some(CommonLispIdentityContext::Canonical(identity)),
                ..
            } if identity == d3_car()
        ));
    }

    #[test]
    fn legacy_abi_byte_is_not_a_core_domain_identity() {
        let legacy = CommonLispIdentityContext::LegacyAbi(LegacyAbiSemanticId(0b0000_0101));
        let canonical = CommonLispIdentityContext::Canonical(d3_car());
        assert_ne!(legacy, canonical);
    }

    #[test]
    fn c_abi_add_uses_legacy_byte_and_arguments_only() {
        if std::env::var_os("WSM_COMMON_LISP_INTEGRATION").is_none() {
            return;
        }

        let adapter = CommonLispAbiAdapter::default();
        let vtable = adapter.vtable();
        assert_eq!(
            unsafe { vtable.start.expect("start")(vtable.context) },
            WsmStatus::Ok
        );

        let input = b"2 3";
        let mut output = [0u8; 64];
        let mut written = 0usize;
        let status = unsafe {
            (vtable.exchange.expect("exchange callback"))(
                vtable.context,
                WsmKernelRequest {
                    semantic_id: LEGACY_SID_ADD.0,
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
        assert_eq!(status, WsmStatus::Ok);
        assert_eq!(String::from_utf8_lossy(&output[..written]).trim(), "5");
        assert_eq!(
            adapter.last_legacy_semantic_id(),
            Some(LEGACY_SID_ADD)
        );

        let override_text = b"(- 7 3)";
        written = 0;
        let status = unsafe {
            (vtable.exchange.expect("exchange callback"))(
                vtable.context,
                WsmKernelRequest {
                    semantic_id: LEGACY_SID_ADD.0,
                    payload: wsm_kernel_c_abi::WsmByteSpan {
                        ptr: override_text.as_ptr(),
                        len: override_text.len(),
                    },
                },
                WsmMutableByteSpan {
                    ptr: output.as_mut_ptr(),
                    len: output.len(),
                },
                &mut written,
            )
        };
        assert_eq!(status, WsmStatus::InvalidArgument);
        assert_eq!(written, 0);

        assert_eq!(
            unsafe { vtable.stop.expect("stop")(vtable.context) },
            WsmStatus::Ok
        );
    }

    #[test]
    fn c_abi_adapter_declares_common_lisp_without_canonical_mapping() {
        let adapter = CommonLispAbiAdapter::new(CommonLispKernel::new(
            "__runtime_is_not_started_by_this_test__",
        ));
        let vtable = adapter.vtable();

        assert_eq!(vtable.abi_version, WSM_KERNEL_ABI_VERSION);
        assert_eq!(vtable.kernel, WsmKernelKind::CommonLisp);
        assert!(vtable.is_mechanically_complete());
        assert_eq!(adapter.last_legacy_semantic_id(), None);
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
