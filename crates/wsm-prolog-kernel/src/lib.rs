//! Independent SWI-Prolog island.
//!
//! This crate does not implement Prolog semantics in Rust. It launches a real
//! SWI-Prolog process, consults a Prolog program, and asks Prolog itself to
//! enumerate answers. Rust owns only process transport, opaque semantic
//! provenance, lifecycle plumbing and error reporting.

use std::ffi::c_void;
use std::fmt;
use std::path::{Path, PathBuf};
use std::process::Command;

use wsm_kernel_c_abi::{
    WsmKernelKind, WsmKernelRequest, WsmKernelVTable, WsmMutableByteSpan, WsmStatus,
    WSM_KERNEL_ABI_VERSION,
};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct SemanticId(pub u8);

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrologQuery {
    pub goal: String,
    pub template: String,
}

impl PrologQuery {
    pub fn new(goal: impl Into<String>, template: impl Into<String>) -> Self {
        Self {
            goal: goal.into(),
            template: template.into(),
        }
    }

    pub fn enumeration_goal(&self) -> String {
        format!(
            "findall({},({}),Answers),write_canonical(Answers),nl",
            self.template, self.goal
        )
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrologResult {
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrologRequest {
    pub semantic_id: SemanticId,
    pub query: PrologQuery,
}

impl PrologRequest {
    pub fn new(semantic_id: u8, query: PrologQuery) -> Self {
        Self {
            semantic_id: SemanticId(semantic_id),
            query,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrologExecutionResult {
    pub semantic_id: SemanticId,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
}

#[derive(Debug)]
pub enum PrologKernelError {
    Spawn(std::io::Error),
    ProcessFailed {
        semantic_id: Option<SemanticId>,
        status: Option<i32>,
        stdout: Vec<u8>,
        stderr: Vec<u8>,
    },
}

impl fmt::Display for PrologKernelError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Spawn(error) => write!(formatter, "failed to start SWI-Prolog: {error}"),
            Self::ProcessFailed {
                semantic_id,
                status,
                stderr,
                ..
            } => write!(
                formatter,
                "SWI-Prolog exited unsuccessfully for semantic id {semantic_id:?} ({status:?}): {}",
                String::from_utf8_lossy(stderr)
            ),
        }
    }
}

impl std::error::Error for PrologKernelError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Spawn(error) => Some(error),
            Self::ProcessFailed { .. } => None,
        }
    }
}

#[derive(Clone, Debug)]
pub struct PrologKernel {
    executable: PathBuf,
}

impl Default for PrologKernel {
    fn default() -> Self {
        Self::new("swipl")
    }
}

impl PrologKernel {
    pub fn new(executable: impl Into<PathBuf>) -> Self {
        Self {
            executable: executable.into(),
        }
    }

    pub fn executable(&self) -> &Path {
        &self.executable
    }

    pub fn version(&self) -> Result<PrologResult, PrologKernelError> {
        self.run_command(Command::new(&self.executable).arg("--version"), None)
    }

    pub fn query(
        &self,
        program: impl AsRef<Path>,
        query: &PrologQuery,
    ) -> Result<PrologResult, PrologKernelError> {
        let mut command = self.command_for_query(program.as_ref(), query);
        self.run_command(&mut command, None)
    }

    pub fn execute(
        &self,
        program: impl AsRef<Path>,
        request: &PrologRequest,
    ) -> Result<PrologExecutionResult, PrologKernelError> {
        let mut command = self.command_for_query(program.as_ref(), &request.query);
        let result = self.run_command(&mut command, Some(request.semantic_id))?;
        Ok(PrologExecutionResult {
            semantic_id: request.semantic_id,
            stdout: result.stdout,
            stderr: result.stderr,
        })
    }

    fn command_for_query(&self, program: &Path, query: &PrologQuery) -> Command {
        let mut command = Command::new(&self.executable);
        command
            .arg("-q")
            .arg("-f")
            .arg("none")
            .arg("-s")
            .arg(program)
            .arg("-g")
            .arg(query.enumeration_goal())
            .arg("-t")
            .arg("halt");
        command
    }

    fn run_command(
        &self,
        command: &mut Command,
        semantic_id: Option<SemanticId>,
    ) -> Result<PrologResult, PrologKernelError> {
        let output = command.output().map_err(PrologKernelError::Spawn)?;
        if !output.status.success() {
            return Err(PrologKernelError::ProcessFailed {
                semantic_id,
                status: output.status.code(),
                stdout: output.stdout,
                stderr: output.stderr,
            });
        }
        Ok(PrologResult {
            stdout: output.stdout,
            stderr: output.stderr,
        })
    }
}

#[derive(Debug)]
struct PrologAbiContext {
    kernel: PrologKernel,
    program: PathBuf,
    template: String,
    running: bool,
    last_semantic_id: Option<SemanticId>,
}

pub struct PrologAbiAdapter {
    context: Box<PrologAbiContext>,
    vtable: WsmKernelVTable,
}

impl PrologAbiAdapter {
    pub fn new(
        kernel: PrologKernel,
        program: impl Into<PathBuf>,
        template: impl Into<String>,
    ) -> Self {
        let mut context = Box::new(PrologAbiContext {
            kernel,
            program: program.into(),
            template: template.into(),
            running: false,
            last_semantic_id: None,
        });
        let context_ptr = (&mut *context) as *mut PrologAbiContext as *mut c_void;

        let vtable = WsmKernelVTable {
            abi_version: WSM_KERNEL_ABI_VERSION,
            kernel: WsmKernelKind::Prolog,
            context: context_ptr,
            start: Some(prolog_start),
            exchange: Some(prolog_exchange),
            snapshot: Some(prolog_snapshot),
            stop: Some(prolog_stop),
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

unsafe fn abi_context_mut<'a>(context: *mut c_void) -> Option<&'a mut PrologAbiContext> {
    unsafe { (context as *mut PrologAbiContext).as_mut() }
}

unsafe extern "C" fn prolog_start(context: *mut c_void) -> WsmStatus {
    let Some(context) = (unsafe { abi_context_mut(context) }) else {
        return WsmStatus::InvalidArgument;
    };
    context.running = true;
    WsmStatus::Ok
}

unsafe extern "C" fn prolog_stop(context: *mut c_void) -> WsmStatus {
    let Some(context) = (unsafe { abi_context_mut(context) }) else {
        return WsmStatus::InvalidArgument;
    };
    context.running = false;
    WsmStatus::Ok
}

unsafe extern "C" fn prolog_snapshot(
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

unsafe extern "C" fn prolog_exchange(
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
    let Ok(goal) = std::str::from_utf8(payload) else {
        return WsmStatus::InvalidArgument;
    };

    let kernel_request = PrologRequest::new(
        request.semantic_id,
        PrologQuery::new(goal, context.template.clone()),
    );
    let result = match context.kernel.execute(&context.program, &kernel_request) {
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
    fn enumeration_goal_is_owned_by_prolog_not_rust_answer_parsing() {
        let query = PrologQuery::new("ancestor(alice, X)", "X");
        assert_eq!(
            query.enumeration_goal(),
            "findall(X,(ancestor(alice, X)),Answers),write_canonical(Answers),nl"
        );
    }

    #[test]
    fn enumeration_goal_keeps_compound_templates_intact() {
        let query = PrologQuery::new("edge(X,Y)", "(X,Y)");
        assert_eq!(
            query.enumeration_goal(),
            "findall((X,Y),(edge(X,Y)),Answers),write_canonical(Answers),nl"
        );
    }

    #[test]
    fn missing_swipl_is_a_named_transport_failure() {
        let kernel = PrologKernel::new("__wsm_swipl_that_does_not_exist__");
        assert!(matches!(kernel.version(), Err(PrologKernelError::Spawn(_))));
    }

    #[test]
    fn abi_adapter_is_mechanically_prolog() {
        let adapter = PrologAbiAdapter::new(
            PrologKernel::new("__runtime_not_used__"),
            "fixture.pl",
            "X",
        );
        let vtable = adapter.vtable();
        assert_eq!(vtable.abi_version, WSM_KERNEL_ABI_VERSION);
        assert_eq!(vtable.kernel, WsmKernelKind::Prolog);
        assert!(vtable.is_mechanically_complete());
        assert_eq!(adapter.last_semantic_id(), None);
    }
}
