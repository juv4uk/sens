//! Self-hosting lineage: C0→C1→C2 deterministic evidence.
//!
//! Authority: sens#3822 — record deterministic compiler generation cycle.
//!
//! This module defines the schema for capturing the complete lineage
//! of the compiler self-hosting cycle: from trusted bootstrap (C0) through
//! first generation (C1) through second generation (C2).
//!
//! The lineage is versioned, machine-readable core data and mechanically verifiable.
//!
//! Serialization belongs to tooling/host adapters so the capability-free core
//! does not acquire a runtime serde dependency.


/// Semantic versioning for lineage schema.
pub const LINEAGE_VERSION_MAJOR: u32 = 1;
pub const LINEAGE_VERSION_MINOR: u32 = 0;

/// Complete C0→C1→C2 self-hosting lineage.
///
/// Records all authority facts and artifact digests needed to verify
/// that a compiler can compile itself. This is the executable proof
/// of fixed-point existence (sens#3760).
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SelfhostLineage {
    /// Schema version (major.minor).
    pub version: (u32, u32),

    /// Timestamp of lineage recording (ISO 8601).
    pub recorded_at: String,

    /// Authority and source digests (immutable across C0→C1→C2).
    pub authority_bundle: AuthorityBundle,

    /// C0 bootstrap compiler facts.
    pub bootstrap_c0: BootstrapCompiler,

    /// C1: C0 compiling current nucleus source.
    pub generation_c1: CompilerGeneration,

    /// C2: C1 compiling the identical source+authority.
    pub generation_c2: CompilerGeneration,

    /// Equivalence result: how C1/C2 match.
    pub equivalence: EquivalenceResult,

    /// Fresh-bootstrap falsification evidence.
    pub fresh_bootstrap_proof: FreshBootstrapProof,

    /// Optional metadata for audit trail.
    pub metadata: LineageMetadata,
}

/// Immutable authority facts shared across all generations.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AuthorityBundle {
    /// SENS source (lib/compiler-nucleus.lisp) SHA-256.
    pub nucleus_source_sha256: String,

    /// Language contract (language-contract.lisp) SHA-256.
    pub language_contract_sha256: String,

    /// Contract version (e.g., "11.8").
    pub contract_version: String,

    /// D3 L1-L5 structural projection digest (SHA-256).
    pub d3_law_projection_sha256: String,

    /// D4 bootstrap projection digest (SHA-256).
    pub d4_law_projection_sha256: String,

    /// Ratified domain laws used (refs only, hashes above).
    pub ratified_laws: Vec<String>,

    /// Canonical exact-domain identities admitted.
    /// e.g., ["D3:001", "D3:010", ..., "D4:0010", "D4:0011"]
    pub admitted_identities: Vec<String>,
}

/// C0: The trusted bootstrap compiler.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BootstrapCompiler {
    /// Name/version of C0 (e.g., "CML-C0-v1.0", "GCC-native-C").
    pub name: String,

    /// Implementation/repository SHA (CML commit).
    pub implementation_sha256: String,

    /// Target ABI profile (e.g., "x86_64-freestanding", "arm64-linux").
    pub target_profile: String,

    /// Toolchain/backend (e.g., "CML-x86", "GCC-native").
    pub backend: String,

    /// Backend toolchain version/SHA (e.g., GCC version, LLVM commit).
    pub toolchain_sha256: String,

    /// Optional notes about C0 (e.g., "human-written bootstrap").
    pub notes: Option<String>,
}

/// One compiler generation (C1 or C2).
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CompilerGeneration {
    /// Name (e.g., "C1", "C2").
    pub name: String,

    /// Producer (e.g., "C0", "C1").
    pub produced_by: String,

    /// Compilation artifact digest (SHA-256).
    pub artifact_digest: String,

    /// Normalized IR/lowering digest (if available, else "unknown").
    pub normalized_ir_digest: String,

    /// Executable binary digest (SHA-256).
    pub executable_digest: String,

    /// Size in bytes (for reference).
    pub executable_size: u64,

    /// Compilation timestamp (ISO 8601).
    pub compiled_at: String,

    /// Target ABI profile (must match C0 for parity).
    pub target_profile: String,

    /// Optional provenance notes (e.g., "compiled with optimizations").
    pub notes: Option<String>,
}

/// Equivalence criterion and result.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EquivalenceResult {
    /// Method used (strongest available).
    /// Options: "byte-identical", "normalized-ir", "semantic+corpus"
    pub method: String,

    /// Does C1 == C2 by this method?
    pub matches: bool,

    /// If not matched, diagnostic category.
    /// e.g., "byte-differs", "ir-differs", "semantic-mismatch", "backend-mismatch"
    pub failure_category: Option<String>,

    /// Detailed message for non-match.
    pub detail: Option<String>,

    /// Normalized IR diff digest (if applicable, else "unknown").
    pub ir_diff_digest: Option<String>,

    /// Semantic corpus parity result (if applicable).
    pub corpus_parity: Option<CorpusParity>,
}

/// Semantic corpus parity for exact-domain operations.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CorpusParity {
    /// Number of test cases in corpus.
    pub test_count: u32,

    /// Number of passing tests.
    pub passing_count: u32,

    /// Canonical observable digest (SHA-256) if all pass.
    pub canonical_observable_digest: Option<String>,

    /// Failures (if any).
    pub failures: Vec<String>,
}

/// Proof that C0 does not reuse pre-existing C1/C2.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FreshBootstrapProof {
    /// Was a clean build environment used? (e.g., isolated container).
    pub clean_environment: bool,

    /// Verification that C0 does not read/reuse C1 artifact.
    pub no_c1_reuse: bool,

    /// Verification that C0 generates C1 from authority source.
    pub c1_generated_fresh: bool,

    /// Verification that C1 compiles identical source (bit-for-bit check).
    pub c1_input_verified: bool,

    /// Verification that C2 input is identical to C1 input.
    pub c2_input_identical: bool,

    /// Optional evidence: removed/missing artifacts after generation.
    pub removed_artifacts: Vec<String>,

    /// Audit trail notes.
    pub notes: Option<String>,
}

/// Optional metadata.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct LineageMetadata {
    /// Who/what orchestrated this run (e.g., "sens-ci", "manual").
    pub orchestrator: Option<String>,

    /// CI job/commit reference (if applicable).
    pub ci_reference: Option<String>,

    /// Notes for reviewers.
    pub notes: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lineage_version_correct() {
        assert_eq!(LINEAGE_VERSION_MAJOR, 1);
        assert_eq!(LINEAGE_VERSION_MINOR, 0);
    }

    #[test]
    fn lineage_schema_is_plain_core_data_and_preserves_authority() {
        let lineage = SelfhostLineage {
            version: (1, 0),
            recorded_at: "2026-10-06T12:00:00Z".to_string(),
            authority_bundle: AuthorityBundle {
                nucleus_source_sha256: "abc123".to_string(),
                language_contract_sha256: "def456".to_string(),
                contract_version: "11.8".to_string(),
                d3_law_projection_sha256: "ghi789".to_string(),
                d4_law_projection_sha256: "jkl012".to_string(),
                ratified_laws: vec!["D3_BIJA3_LAW_3202".to_string()],
                admitted_identities: vec!["D3:001".to_string(), "D4:0010".to_string()],
            },
            bootstrap_c0: BootstrapCompiler {
                name: "CML-C0-v1.0".to_string(),
                implementation_sha256: "mno345".to_string(),
                target_profile: "x86_64-freestanding".to_string(),
                backend: "CML-x86".to_string(),
                toolchain_sha256: "pqr678".to_string(),
                notes: Some("Bootstrap compiler".to_string()),
            },
            generation_c1: CompilerGeneration {
                name: "C1".to_string(),
                produced_by: "C0".to_string(),
                artifact_digest: "stu901".to_string(),
                normalized_ir_digest: "vwx234".to_string(),
                executable_digest: "yz567".to_string(),
                executable_size: 1024000,
                compiled_at: "2026-10-06T12:10:00Z".to_string(),
                target_profile: "x86_64-freestanding".to_string(),
                notes: Some("First generation".to_string()),
            },
            generation_c2: CompilerGeneration {
                name: "C2".to_string(),
                produced_by: "C1".to_string(),
                artifact_digest: "yz567".to_string(),
                normalized_ir_digest: "vwx234".to_string(),
                executable_digest: "yz567".to_string(),
                executable_size: 1024000,
                compiled_at: "2026-10-06T12:20:00Z".to_string(),
                target_profile: "x86_64-freestanding".to_string(),
                notes: Some("Second generation".to_string()),
            },
            equivalence: EquivalenceResult {
                method: "byte-identical".to_string(),
                matches: true,
                failure_category: None,
                detail: None,
                ir_diff_digest: None,
                corpus_parity: None,
            },
            fresh_bootstrap_proof: FreshBootstrapProof {
                clean_environment: true,
                no_c1_reuse: true,
                c1_generated_fresh: true,
                c1_input_verified: true,
                c2_input_identical: true,
                removed_artifacts: vec![],
                notes: Some("Clean CI environment".to_string()),
            },
            metadata: LineageMetadata {
                orchestrator: Some("sens-ci".to_string()),
                ci_reference: Some("sens#3822".to_string()),
                notes: Some("Fixed-point verification".to_string()),
            },
        };

        assert_eq!(lineage.version, (LINEAGE_VERSION_MAJOR, LINEAGE_VERSION_MINOR));
        assert_eq!(lineage.authority_bundle.contract_version, "11.8");
        assert_eq!(lineage.generation_c1.produced_by, "C0");
        assert_eq!(lineage.generation_c2.produced_by, "C1");
        assert!(lineage.fresh_bootstrap_proof.no_c1_reuse);
        assert!(lineage.fresh_bootstrap_proof.c2_input_identical);
    }

    #[test]
    fn equivalence_failure_records_diagnostic() {
        let failure = EquivalenceResult {
            method: "byte-identical".to_string(),
            matches: false,
            failure_category: Some("backend-mismatch".to_string()),
            detail: Some("C1/C2 binaries differ due to ASLR".to_string()),
            ir_diff_digest: Some("abc123".to_string()),
            corpus_parity: Some(CorpusParity {
                test_count: 1000,
                passing_count: 1000,
                canonical_observable_digest: Some("def456".to_string()),
                failures: vec![],
            }),
        };

        assert!(!failure.matches);
        assert_eq!(failure.failure_category, Some("backend-mismatch".to_string()));
        // Can fall back to corpus parity if byte-identical fails
        assert!(failure.corpus_parity.is_some());
    }
}
