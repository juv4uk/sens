//! Independent SWI-Prolog island.
//!
//! This crate does not implement Prolog semantics in Rust. It launches a real
//! SWI-Prolog process, consults a Prolog program, and asks Prolog itself to
//! enumerate answers. Rust owns only process transport and error reporting.
//!
//! The result is intentionally raw canonical Prolog bytes. Cross-kernel
//! interpretation belongs to an explicit bridge, never to this kernel.

use std::fmt;
use std::path::{Path, PathBuf};
use std::process::Command;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrologQuery {
    pub goal: String,
    pub template: String,
}

impl PrologQuery {
    pub fn new(goal: impl Into<String>, template: impl Into<String>) -> Self {
        Self { goal: goal.into(), template: template.into() }
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

#[derive(Debug)]
pub enum PrologKernelError {
    Spawn(std::io::Error),
    ProcessFailed { status: Option<i32>, stdout: Vec<u8>, stderr: Vec<u8> },
}

impl fmt::Display for PrologKernelError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Spawn(error) => write!(formatter, "failed to start SWI-Prolog: {error}"),
            Self::ProcessFailed { status, stderr, .. } => write!(
                formatter,
                "SWI-Prolog exited unsuccessfully ({status:?}): {}",
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
pub struct PrologKernel { executable: PathBuf }

impl Default for PrologKernel {
    fn default() -> Self { Self::new("swipl") }
}

impl PrologKernel {
    pub fn new(executable: impl Into<PathBuf>) -> Self { Self { executable: executable.into() } }

    pub fn executable(&self) -> &Path { &self.executable }

    pub fn version(&self) -> Result<PrologResult, PrologKernelError> {
        self.run_command(Command::new(&self.executable).arg("--version"))
    }

    pub fn query(
        &self,
        program: impl AsRef<Path>,
        query: &PrologQuery,
    ) -> Result<PrologResult, PrologKernelError> {
        let mut command = Command::new(&self.executable);
        command
            .arg("-q")
            .arg("-f").arg("none")
            .arg("-s").arg(program.as_ref())
            .arg("-g").arg(query.enumeration_goal())
            .arg("-t").arg("halt");
        self.run_command(&mut command)
    }

    fn run_command(&self, command: &mut Command) -> Result<PrologResult, PrologKernelError> {
        let output = command.output().map_err(PrologKernelError::Spawn)?;
        if !output.status.success() {
            return Err(PrologKernelError::ProcessFailed {
                status: output.status.code(),
                stdout: output.stdout,
                stderr: output.stderr,
            });
        }
        Ok(PrologResult { stdout: output.stdout, stderr: output.stderr })
    }
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
}
