//! Side-by-side storage for producer-native kernel results.
//!
//! This crate deliberately has no universal result enum and performs no
//! cross-kernel reconstruction. Each field is owned by the kernel that
//! produced it. The artifact only keeps the four domains adjacent so my-lisp
//! can observe/relate them later without replacing their native shapes.

use wsm_clips_kernel::ClipsExecutionResult;
use wsm_common_lisp_kernel::CommonLispResult;
use wsm_datalog_kernel::Database;
use wsm_prolog_kernel::PrologExecutionResult;

/// One observation from each autonomous execution kernel.
///
/// The concrete field types are the boundary: Common Lisp stays a Common Lisp
/// process result, Prolog stays a Prolog execution result, CLIPS stays its
/// working-memory/agenda observation, and Datalog stays its relation database
/// with generations and derivations.
#[derive(Clone, Debug)]
pub struct FourKernelObservation {
    pub common_lisp: CommonLispResult,
    pub prolog: PrologExecutionResult,
    pub clips: ClipsExecutionResult,
    pub datalog: Database,
}

impl FourKernelObservation {
    pub fn new(
        common_lisp: CommonLispResult,
        prolog: PrologExecutionResult,
        clips: ClipsExecutionResult,
        datalog: Database,
    ) -> Self {
        Self {
            common_lisp,
            prolog,
            clips,
            datalog,
        }
    }

    /// Producer identities are structural: each slot has a distinct concrete
    /// type rather than a tag inside one normalized universal value.
    pub const fn producer_names() -> [&'static str; 4] {
        ["common-lisp", "prolog", "clips", "datalog"]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use wsm_clips_kernel::SemanticId as ClipsSemanticId;
    use wsm_common_lisp_kernel::SemanticId as CommonLispSemanticId;
    use wsm_prolog_kernel::SemanticId as PrologSemanticId;

    #[test]
    fn artifact_preserves_four_concrete_producer_types() {
        let observation = FourKernelObservation::new(
            CommonLispResult {
                semantic_id: CommonLispSemanticId(5),
                stdout: b"LEFT\n".to_vec(),
                stderr: Vec::new(),
            },
            PrologExecutionResult {
                semantic_id: PrologSemanticId(3),
                stdout: b"[bob,dave,carol]\n".to_vec(),
                stderr: Vec::new(),
            },
            ClipsExecutionResult::new(Some(ClipsSemanticId(6)), 1, 1, 2),
            Database::new(),
        );

        assert_eq!(FourKernelObservation::producer_names(),
            ["common-lisp", "prolog", "clips", "datalog"]);
        assert_eq!(observation.common_lisp.stdout, b"LEFT\n");
        assert_eq!(observation.prolog.stdout, b"[bob,dave,carol]\n");
        assert_eq!(observation.clips.fired, 1);
        assert_eq!(observation.clips.facts_before, 1);
        assert_eq!(observation.clips.facts_after, 2);
        assert_eq!(observation.datalog.generation_count(), 0);
    }
}
