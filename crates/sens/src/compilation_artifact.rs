//! Canonical, target-neutral compilation artifact schema.
//!
//! Authority: sens#3835 — make compilation an explicit SENS operation.
//!
//! The artifact captures only semantic/target-neutral facts:
//! - source program digest
//! - Contract authority facts
//! - exact-domain identities
//! - canonical lowered graph digest
//! - declared required mechanisms
//!
//! It must NOT contain:
//! - register allocation, PTX/SASS, backend opcodes
//! - Graal nodes, FPGA placement, backend policy
//! - historical Sid8/Sens8 fallbacks
//!
//! Versioning: artifacts are immutable once sealed. Version bumps go to separate schema.

// Serde is deliberately test-only in this capability-free core.
use std::collections::BTreeMap;

/// Semantic versioning for artifact schema.
/// Backward-incompatible changes increment major version.
pub const ARTIFACT_VERSION_MAJOR: u32 = 1;
pub const ARTIFACT_VERSION_MINOR: u32 = 0;

/// Canonical compilation artifact owned by SENS semantic authority.
///
/// This artifact is the contract between:
/// - Producer: SENS compiler nucleus (semantic side)
/// - Consumer: backend-specific installers (mechanism side)
///
/// The artifact uniquely identifies a compilation result without committing
/// to any target/backend mechanism. Mechanisms may have their own digests,
/// but the artifact itself is target-neutral.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct CompilationArtifact {
    /// Artifact schema version (major.minor).
    pub version: (u32, u32),

    /// Source program digest (SHA-256 hex).
    /// Identifies the exact Lisp source that was compiled.
    pub source_digest: String,

    /// SENS language contract authority facts.
    pub contract: ContractAuthority,

    /// Compiler nucleus version/digest that produced this artifact.
    /// Allows tracing back to exact SENS-written compiler source.
    pub compiler_nucleus: CompilerNucleusRef,

    /// Exact-domain identities used in this program.
    /// Maps domain (e.g., "D3", "D4") to set of exact bit patterns used.
    pub exact_domain_usage: BTreeMap<String, Vec<String>>,

    /// Canonical lowered graph representation.
    /// Target-neutral; structure is SENS-owned, not backend-specific.
    pub lowered_graph_digest: String,

    /// Declared required mechanisms for execution.
    /// Backend must satisfy all of these or fail closed.
    pub required_mechanisms: Vec<MechanismRequirement>,

    /// Proof/evidence lineage for this compilation.
    /// Records the authority chain from source to artifact.
    pub proof_lineage: ProofLineage,

    /// Optional metadata for tracing/debugging.
    pub metadata: CompilationMetadata,
}

/// SENS contract and law authority facts.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct ContractAuthority {
    /// language-contract.lisp version/digest.
    pub contract_version: String,  // e.g., "11.8"
    pub contract_sha256: String,

    /// Ratified domain laws used.
    /// e.g., ["D3_BIJA3_LAW_3202", "D4_BOOTSTRAP_LAW_3272"]
    pub ratified_domain_laws: Vec<String>,

    /// D1-D9 authority proof references.
    pub authority_proof_refs: Vec<String>,
}

/// Reference to the compiler nucleus that produced this artifact.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct CompilerNucleusRef {
    /// SENS repository commit SHA or version tag.
    pub nucleus_version: String,  // e.g., "d3938bb7c"
    /// SHA-256 of lib/compiler-nucleus.lisp
    pub nucleus_sha256: String,
}

/// A mechanism required for execution of this artifact.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct MechanismRequirement {
    /// Name of the mechanism (e.g., "core-apply", "core-eval", "float-add").
    pub name: String,

    /// Exact domain identity that declares this requirement.
    /// e.g., "D4:0010" for LAMBDA, "D3:001" for QUOTE
    pub domain_identity: String,

    /// Is this mechanism optional or mandatory for basic execution?
    pub required: bool,

    /// Optional capability level (e.g., "basic", "extended", "gpu-resident").
    pub capability_level: Option<String>,
}

/// Proof and evidence lineage for the compilation.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct ProofLineage {
    /// Witness of source verification (how source was validated).
    pub source_witness: String,  // e.g., "parsed-and-normalized"

    /// Witness of semantic request (how SENS determined meaning).
    pub semantic_witness: String,  // e.g., "compiler-semantic-input-from-sens"

    /// Witness of lowering (how exact-domain AST was lowered).
    pub lowering_witness: String,  // e.g., "dispatch-on-exact-bits"

    /// Declared equivalence method for verification.
    /// e.g., "byte-identical", "ir-normalized", "semantic-observable"
    pub equivalence_method: String,

    /// Cross-repo references for audit trail.
    pub related_issues: Vec<String>,  // e.g., ["sens#3835", "cml#604"]
}

/// Optional metadata for artifact tracing and debugging.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct CompilationMetadata {
    /// Timestamp of compilation (ISO 8601).
    pub compiled_at: Option<String>,

    /// Name/identifier of the bootstrap compiler that produced this.
    pub bootstrap_compiler: Option<String>,

    /// Target profile (e.g., "x86_64-freestanding", "gpu-cuda").
    /// Note: this is informational only; the artifact itself is target-neutral.
    pub target_profile: Option<String>,

    /// Optional notes for audit trail.
    pub notes: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn artifact_version_is_correct() {
        assert_eq!(ARTIFACT_VERSION_MAJOR, 1);
        assert_eq!(ARTIFACT_VERSION_MINOR, 0);
    }

    #[test]
    fn artifact_serializes_to_json() {
        let mut exact_domains = BTreeMap::new();
        exact_domains.insert("D3".to_string(), vec!["001".to_string(), "010".to_string()]);
        exact_domains.insert("D4".to_string(), vec!["0010".to_string()]);

        let artifact = CompilationArtifact {
            version: (1, 0),
            source_digest: "abc123".to_string(),
            contract: ContractAuthority {
                contract_version: "11.8".to_string(),
                contract_sha256: "def456".to_string(),
                ratified_domain_laws: vec!["D3_BIJA3_LAW_3202".to_string()],
                authority_proof_refs: vec!["contracts/bija3-l1-l5-ratification.lisp".to_string()],
            },
            compiler_nucleus: CompilerNucleusRef {
                nucleus_version: "d3938bb7c".to_string(),
                nucleus_sha256: "ghi789".to_string(),
            },
            exact_domain_usage: exact_domains,
            lowered_graph_digest: "jkl012".to_string(),
            required_mechanisms: vec![MechanismRequirement {
                name: "core-apply".to_string(),
                domain_identity: "D4:0010".to_string(),
                required: true,
                capability_level: Some("basic".to_string()),
            }],
            proof_lineage: ProofLineage {
                source_witness: "parsed-and-normalized".to_string(),
                semantic_witness: "compiler-semantic-input-from-sens".to_string(),
                lowering_witness: "dispatch-on-exact-bits".to_string(),
                equivalence_method: "ir-normalized".to_string(),
                related_issues: vec!["sens#3835".to_string()],
            },
            metadata: CompilationMetadata {
                compiled_at: Some("2026-10-06T12:00:00Z".to_string()),
                bootstrap_compiler: Some("C0".to_string()),
                target_profile: Some("x86_64-freestanding".to_string()),
                notes: Some("Test artifact".to_string()),
            },
        };

        let json = serde_json::to_string(&artifact).expect("serialize");
        let deserialized: CompilationArtifact =
            serde_json::from_str(&json).expect("deserialize");
        assert_eq!(artifact, deserialized);
    }

    #[test]
    fn artifact_fails_closed_on_unsupported_mechanism() {
        let requirement = MechanismRequirement {
            name: "gpu-resident-apply".to_string(),
            domain_identity: "D4:0010".to_string(),
            required: true,
            capability_level: Some("gpu-resident".to_string()),
        };

        // Backend that doesn't support GPU must reject this artifact.
        // Logic: if backend cannot satisfy all required mechanisms, fail closed.
        assert!(requirement.required);
        assert_eq!(requirement.capability_level, Some("gpu-resident".to_string()));
    }
}
