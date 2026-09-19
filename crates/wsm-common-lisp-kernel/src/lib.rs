//! Independent Common Lisp execution kernel.
//!
//! my-lisp owns semantic identities and laws. This crate owns only process
//! execution against a real Common Lisp implementation and preserves the
//! caller-provided 8-bit semantic identity as opaque provenance.
//!
//! The first witness uses SBCL, but SBCL names/functions are execution
//! witnesses, never semantic authority.

use std::fmt;
use std::path::{Path, PathBuf};
use std::process::Command;

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
}
