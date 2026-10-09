//! Fixed-point C0→C1→C2 cycle orchestration and checkpoint.
//!
//! Authority: sens#3760, sens#3822 — record deterministic compiler
//! generation cycle and prove fixed-point existence.
//!
//! This module coordinates:
//! - C0 (trusted bootstrap) compiles nucleus source → C1
//! - C1 compiles identical source → C2
//! - Compare C1/C2 via declared equivalence method
//! - Record complete lineage with SelfhostLineage schema

// Serde is deliberately test-only in this capability-free core.
use std::collections::BTreeMap;

/// State of one fixed-point cycle run.
#[derive(Clone, Debug)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct FixpointCycleCheckpoint {
    /// Cycle run identifier (timestamp or session ID).
    pub run_id: String,

    /// C0 bootstrap compiler facts.
    pub bootstrap_c0: C0Facts,

    /// C1 generation result (C0 compiling nucleus).
    pub generation_c1: GenerationResult,

    /// C2 generation result (C1 compiling nucleus).
    pub generation_c2: GenerationResult,

    /// Comparison result.
    pub equivalence: EquivalenceCheck,

    /// Complete lineage (from SelfhostLineage schema).
    pub lineage_digest: String,

    /// Cycle status: "in-progress", "completed", "failed", "blocked".
    pub status: String,

    /// Diagnostic details.
    pub diagnostics: BTreeMap<String, String>,
}

/// C0 bootstrap compiler state.
#[derive(Clone, Debug)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct C0Facts {
    /// C0 implementation SHA (CML commit).
    pub implementation_sha: String,

    /// Source program SHA (lib/compiler-nucleus.lisp).
    pub program_sha: String,

    /// Authority SHA (language-contract.lisp).
    pub contract_sha: String,

    /// Target profile (e.g., "x86_64-freestanding").
    pub target_profile: String,

    /// Readiness check: can C0 accept exact-domain input?
    pub accepts_exact_domain: bool,

    /// Readiness check: does C0 produce versioned artifact?
    pub produces_artifact: bool,
}

/// Result of one compiler generation.
#[derive(Clone, Debug)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct GenerationResult {
    /// Generation name ("C1" or "C2").
    pub name: String,

    /// Executable artifact SHA (binary).
    pub artifact_sha: String,

    /// Compilation artifact digest (from CompilationArtifact schema).
    pub compilation_artifact_digest: String,

    /// IR normalized digest (if available).
    pub ir_normalized_digest: Option<String>,

    /// Compilation time (milliseconds).
    pub compilation_time_ms: u64,

    /// Exit status (0 = success).
    pub exit_status: i32,

    /// Error message if failed.
    pub error: Option<String>,
}

/// Equivalence check result.
#[derive(Clone, Debug)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct EquivalenceCheck {
    /// Method used: "byte-identical", "normalized-ir", "semantic+corpus".
    pub method: String,

    /// Do C1 and C2 match by this method?
    pub matches: bool,

    /// If not matching, why.
    pub failure_reason: Option<String>,

    /// Diff digest (if applicable).
    pub diff_digest: Option<String>,

    /// Evidence strength (for results that didn't match).
    pub evidence_strength: Option<String>,
}

impl FixpointCycleCheckpoint {
    /// Create new checkpoint for a cycle run.
    pub fn new(run_id: String, bootstrap: C0Facts) -> Self {
        Self {
            run_id,
            bootstrap_c0: bootstrap,
            generation_c1: GenerationResult {
                name: "C1".to_string(),
                artifact_sha: String::new(),
                compilation_artifact_digest: String::new(),
                ir_normalized_digest: None,
                compilation_time_ms: 0,
                exit_status: -1,
                error: Some("Not yet run".to_string()),
            },
            generation_c2: GenerationResult {
                name: "C2".to_string(),
                artifact_sha: String::new(),
                compilation_artifact_digest: String::new(),
                ir_normalized_digest: None,
                compilation_time_ms: 0,
                exit_status: -1,
                error: Some("Not yet run".to_string()),
            },
            equivalence: EquivalenceCheck {
                method: "byte-identical".to_string(),
                matches: false,
                failure_reason: Some("Not yet compared".to_string()),
                diff_digest: None,
                evidence_strength: None,
            },
            lineage_digest: String::new(),
            status: "in-progress".to_string(),
            diagnostics: BTreeMap::new(),
        }
    }

    /// Mark C1 generation complete.
    pub fn mark_c1_complete(&mut self, result: GenerationResult) {
        self.generation_c1 = result;
        if self.generation_c1.exit_status == 0 {
            self.diagnostics.insert(
                "c1_ready".to_string(),
                "C1 compilation successful".to_string(),
            );
        }
    }

    /// Mark C2 generation complete.
    pub fn mark_c2_complete(&mut self, result: GenerationResult) {
        self.generation_c2 = result;
        if self.generation_c2.exit_status == 0 {
            self.diagnostics.insert(
                "c2_ready".to_string(),
                "C2 compilation successful".to_string(),
            );
        }
    }

    /// Set equivalence result.
    pub fn set_equivalence(&mut self, check: EquivalenceCheck) {
        self.equivalence = check;
        if self.equivalence.matches {
            self.status = "completed".to_string();
            self.diagnostics.insert(
                "fixed_point_proven".to_string(),
                "C1 ≡ C2 by declared equivalence method".to_string(),
            );
        } else {
            self.status = "failed".to_string();
            self.diagnostics.insert(
                "equivalence_mismatch".to_string(),
                format!("C1 ≢ C2: {}", self.equivalence.failure_reason.as_ref()
                    .unwrap_or(&"unknown".to_string())),
            );
        }
    }

    /// Is this cycle ready for C1 generation?
    pub fn ready_for_c1(&self) -> bool {
        self.bootstrap_c0.accepts_exact_domain && self.bootstrap_c0.produces_artifact
    }

    /// Is this cycle ready for equivalence check?
    pub fn ready_for_equivalence(&self) -> bool {
        self.generation_c1.exit_status == 0 && self.generation_c2.exit_status == 0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn checkpoint_starts_in_progress() {
        let bootstrap = C0Facts {
            implementation_sha: "abc123".to_string(),
            program_sha: "def456".to_string(),
            contract_sha: "ghi789".to_string(),
            target_profile: "x86_64-freestanding".to_string(),
            accepts_exact_domain: true,
            produces_artifact: true,
        };

        let checkpoint = FixpointCycleCheckpoint::new("run-001".to_string(), bootstrap);
        assert_eq!(checkpoint.status, "in-progress");
        assert!(checkpoint.ready_for_c1());
    }

    #[test]
    fn equivalence_check_marks_complete() {
        let bootstrap = C0Facts {
            implementation_sha: "abc".to_string(),
            program_sha: "def456".to_string(),
            contract_sha: "ghi".to_string(),
            target_profile: "x86_64".to_string(),
            accepts_exact_domain: true,
            produces_artifact: true,
        };

        let mut checkpoint = FixpointCycleCheckpoint::new("run-001".to_string(), bootstrap);

        let equivalence = EquivalenceCheck {
            method: "byte-identical".to_string(),
            matches: true,
            failure_reason: None,
            diff_digest: None,
            evidence_strength: Some("strongest".to_string()),
        };

        checkpoint.set_equivalence(equivalence);
        assert_eq!(checkpoint.status, "completed");
        assert!(checkpoint.equivalence.matches);
    }
}
