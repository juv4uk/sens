//! Contract 11.6 GPU oracle admission artifact.
//!
//! Authority:
//! - sens#3766: current-domain GPU oracle gate;
//! - sens#3801: GPU admission classification work;
//! - SENS semantic authority point 5964c4dd2378364a5307b143a65438f8609fecd6.
//!
//! Important distinction:
//! GPU-capable mechanisms and CUDA compiler witnesses exist, but there is not yet
//! a ratified current D1-D7 semantic law for the contiguous batched/buffer map
//! workload requested by the CUDA parity lane. Therefore the canonical GPU
//! oracle is fail-closed: it emits zero positive L0 CUDA oracle rows and an
//! explicit BLOCKED-MECHANISM record.
//!
//! Historical flat 8-bit numeric-buffer-map identity 01011001 is compatibility
//! evidence only. It must never be relabelled as a fresh Contract 11.6 exact
//! DomainIdentity.

// Serde is deliberately test-only in this capability-free core.
use std::collections::BTreeMap;

pub const GPU_ORACLE_VERSION_MAJOR: u32 = 2;
pub const GPU_ORACLE_VERSION_MINOR: u32 = 0;

pub const GPU_ORACLE_STATUS_BLOCKED: &str = "BLOCKED-MECHANISM";
pub const CURRENT_CONTRACT_VERSION: &str = "11.6";
pub const CURRENT_CONTRACT_SHA256: &str =
    "9768f683e90cfb56ca95675d1f6ac0e6ede91e21cebe97e20b455cf1b3094791";
pub const CURRENT_SEMANTIC_REVISION: &str =
    "5964c4dd2378364a5307b143a65438f8609fecd6";
pub const FORBIDDEN_LEGACY_NUMERIC_BUFFER_MAP: &str = "01011001";

/// Future positive GPU observable.
///
/// Schema v2 keeps the positive row shape explicit even though the current
/// corpus intentionally contains zero such rows. A future row may be added
/// only after SENS owns a current exact-domain law that semantically defines
/// the batched workload.
#[derive(Clone, Debug, Eq, Hash, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct GpuOracleObservable {
    pub case_id: String,
    pub contract: String,
    pub semantic_revision: String,
    pub program_digest: String,
    pub identity_trace_digest: String,
    pub result_kind: String,
    pub result_digest: String,
    pub error_kind: Option<String>,
    pub observable_order_digest: String,
    pub gpu_admission_status: String,
    pub min_compute_capability: String,
    pub execution_class: String,
    pub deterministic_gpu_executable: bool,
}

/// Explicit finite boundary of the current oracle evidence.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct GpuOracleBound {
    pub domain_set: String,
    pub generated_positive_cases: u32,
    pub deduplicated_positive_cases: u32,
    pub evidence_class: String,
    pub boundary_statement: String,
}

/// Authority facts for the GPU oracle.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct GpuAuthorityInfo {
    pub contract_version: String,
    pub contract_sha256: String,
    pub semantic_revision: String,
    pub oracle_issue: String,
    pub gpu_admission_issue: String,
    pub cuda_reference: String,
    pub ratified_laws: Vec<String>,
}

/// Review of one current semantic-residency domain for the missing batched law.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct GpuCandidateReview {
    pub domain: String,
    pub status: String,
    pub families: Vec<String>,
    pub result: String,
}

/// Machine-readable fail-closed reason for the absent positive oracle row.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct GpuOracleBlock {
    pub status: String,
    pub missing_law: String,
    pub reasons: Vec<String>,
    pub current_candidates_reviewed: Vec<GpuCandidateReview>,
    pub forbidden_legacy_identity: String,
    pub unblock_rule: String,
}

/// Negative control that must remain rejected by the current oracle.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct GpuExclusionControl {
    pub control_name: String,
    pub identity_or_class: String,
    pub expected_status: String,
    pub exclusion_verified: bool,
    pub diagnostic: Option<String>,
}

/// Audit statistics. Zero positive rows is a meaningful result, not missing data.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct GpuCorpusStatistics {
    pub gpu_success_count: u32,
    pub blocked_mechanism_count: u32,
    pub domain_review_coverage: BTreeMap<String, String>,
    pub exclusion_controls_passed: u32,
    pub exclusion_controls_failed: u32,
}

/// Canonical current GPU oracle corpus.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct GpuConformanceCorpus {
    pub version: (u32, u32),
    pub status: String,
    pub authority: GpuAuthorityInfo,
    pub bounds: GpuOracleBound,
    pub observables: Vec<GpuOracleObservable>,
    pub blocked: GpuOracleBlock,
    pub gpu_exclusion_controls: Vec<GpuExclusionControl>,
    pub statistics: GpuCorpusStatistics,
}

impl GpuConformanceCorpus {
    /// Generate the current Contract 11.6 GPU oracle.
    ///
    /// This is intentionally fail-closed. CUDA availability, a CUDA compiler
    /// backend, or a successful substrate witness does not authorize a semantic
    /// L0 oracle row by itself.
    pub fn generate_current() -> Self {
        let current_candidates_reviewed = vec![
            GpuCandidateReview {
                domain: "D3".to_string(),
                status: "CALLABLE".to_string(),
                families: vec![
                    "QUOTE".to_string(),
                    "ATOM".to_string(),
                    "CDR".to_string(),
                    "CAR".to_string(),
                    "EQ".to_string(),
                    "COND".to_string(),
                    "CONS".to_string(),
                ],
                result: "not a natural contiguous-buffer batch law".to_string(),
            },
            GpuCandidateReview {
                domain: "D4".to_string(),
                status: "CALLABLE".to_string(),
                families: vec![
                    "necessary forms".to_string(),
                    "selector descendants".to_string(),
                ],
                result: "not a natural contiguous-buffer batch law".to_string(),
            },
            GpuCandidateReview {
                domain: "D5".to_string(),
                status: "CALLABLE".to_string(),
                families: vec![
                    "arithmetic".to_string(),
                    "numeric predicates".to_string(),
                    "selector descendants".to_string(),
                ],
                result: "scalar/list-structure mechanisms; no admitted buffer-map law".to_string(),
            },
            GpuCandidateReview {
                domain: "D6".to_string(),
                status: "RATIFIED_WITHOUT_CURRENT_MECHANISM".to_string(),
                families: Vec::new(),
                result: "0/64 executable mechanisms; blocked".to_string(),
            },
            GpuCandidateReview {
                domain: "D7".to_string(),
                status: "CURRENT_RESIDENCY_NO_CALLABLE_PROJECTION".to_string(),
                families: Vec::new(),
                result: "blocked; width alone must not grant callability".to_string(),
            },
        ];

        let blocked = GpuOracleBlock {
            status: GPU_ORACLE_STATUS_BLOCKED.to_string(),
            missing_law: "exact-domain batched/buffer map semantics".to_string(),
            reasons: vec![
                "Current D3-D5 exact-domain operations are scalar/list-structure mechanisms rather than a current-domain NumericBufferMap law.".to_string(),
                "A batch of independent scalar calls is benchmark composition, not semantic authority for buffer mapping.".to_string(),
                "D6 has current semantic residency but no admitted exact-domain runtime mechanism.".to_string(),
                "D7 has current semantic residency but no callable Core-operation projection.".to_string(),
            ],
            current_candidates_reviewed: current_candidates_reviewed.clone(),
            forbidden_legacy_identity: FORBIDDEN_LEGACY_NUMERIC_BUFFER_MAP.to_string(),
            unblock_rule: "SENS must ratify or expose a current exact-domain law that semantically defines the batched/buffer workload and emits a Contract 11.6 L0 ORACLE row with deterministic digests.".to_string(),
        };

        let gpu_exclusion_controls = vec![
            GpuExclusionControl {
                control_name: "legacy-numeric-buffer-map-must-not-be-current-oracle".to_string(),
                identity_or_class: FORBIDDEN_LEGACY_NUMERIC_BUFFER_MAP.to_string(),
                expected_status: "REJECTED-AS-CURRENT-ORACLE".to_string(),
                exclusion_verified: true,
                diagnostic: None,
            },
            GpuExclusionControl {
                control_name: "d6-width-must-not-grant-callability".to_string(),
                identity_or_class: "D6".to_string(),
                expected_status: "BLOCKED-MECHANISM".to_string(),
                exclusion_verified: true,
                diagnostic: None,
            },
            GpuExclusionControl {
                control_name: "d7-width-must-not-grant-callability".to_string(),
                identity_or_class: "D7".to_string(),
                expected_status: "NO-CALLABLE-PROJECTION".to_string(),
                exclusion_verified: true,
                diagnostic: None,
            },
        ];

        let mut domain_review_coverage = BTreeMap::new();
        for review in &current_candidates_reviewed {
            domain_review_coverage.insert(review.domain.clone(), review.status.clone());
        }

        Self {
            version: (GPU_ORACLE_VERSION_MAJOR, GPU_ORACLE_VERSION_MINOR),
            status: GPU_ORACLE_STATUS_BLOCKED.to_string(),
            authority: GpuAuthorityInfo {
                contract_version: CURRENT_CONTRACT_VERSION.to_string(),
                contract_sha256: CURRENT_CONTRACT_SHA256.to_string(),
                semantic_revision: CURRENT_SEMANTIC_REVISION.to_string(),
                oracle_issue: "sens#3766".to_string(),
                gpu_admission_issue: "sens#3801".to_string(),
                cuda_reference: "juv4uk/cml#472".to_string(),
                ratified_laws: vec![
                    "Contract-11.6-current-D1-D7".to_string(),
                    "D6-ratification-#3393".to_string(),
                ],
            },
            bounds: GpuOracleBound {
                domain_set: "current semantic residency D1-D7; candidate review D3-D7".to_string(),
                generated_positive_cases: 0,
                deduplicated_positive_cases: 0,
                evidence_class: GPU_ORACLE_STATUS_BLOCKED.to_string(),
                boundary_statement:
                    "No current exact-domain batched/buffer semantic law is admitted; zero positive CUDA L0 oracle rows."
                        .to_string(),
            },
            observables: Vec::new(),
            blocked,
            gpu_exclusion_controls,
            statistics: GpuCorpusStatistics {
                gpu_success_count: 0,
                blocked_mechanism_count: 1,
                domain_review_coverage,
                exclusion_controls_passed: 3,
                exclusion_controls_failed: 0,
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn gpu_oracle_schema_is_v2_fail_closed() {
        let corpus = GpuConformanceCorpus::generate_current();
        assert_eq!(corpus.version, (2, 0));
        assert_eq!(corpus.status, GPU_ORACLE_STATUS_BLOCKED);
        assert!(corpus.observables.is_empty());
        assert_eq!(corpus.statistics.gpu_success_count, 0);
        assert_eq!(corpus.statistics.blocked_mechanism_count, 1);
    }

    #[test]
    fn gpu_oracle_pins_real_contract_and_semantic_authority() {
        let corpus = GpuConformanceCorpus::generate_current();
        assert_eq!(corpus.authority.contract_version, CURRENT_CONTRACT_VERSION);
        assert_eq!(corpus.authority.contract_sha256, CURRENT_CONTRACT_SHA256);
        assert_eq!(corpus.authority.semantic_revision, CURRENT_SEMANTIC_REVISION);
        assert_eq!(corpus.authority.oracle_issue, "sens#3766");
    }

    #[test]
    fn gpu_oracle_rejects_legacy_numeric_buffer_map_as_current_identity() {
        let corpus = GpuConformanceCorpus::generate_current();
        assert_eq!(
            corpus.blocked.forbidden_legacy_identity,
            FORBIDDEN_LEGACY_NUMERIC_BUFFER_MAP
        );
        assert!(corpus.gpu_exclusion_controls.iter().any(|control| {
            control.identity_or_class == FORBIDDEN_LEGACY_NUMERIC_BUFFER_MAP
                && control.expected_status == "REJECTED-AS-CURRENT-ORACLE"
                && control.exclusion_verified
        }));
    }

    #[test]
    fn gpu_oracle_does_not_promote_scalar_candidates_into_cuda_rows() {
        let corpus = GpuConformanceCorpus::generate_current();
        for domain in ["D3", "D4", "D5", "D6", "D7"] {
            assert!(corpus.statistics.domain_review_coverage.contains_key(domain));
        }
        assert!(corpus.observables.is_empty());
    }

    #[test]
    fn gpu_oracle_serializes_round_trip() {
        let corpus = GpuConformanceCorpus::generate_current();
        let json = serde_json::to_string(&corpus).expect("serialize");
        let decoded: GpuConformanceCorpus = serde_json::from_str(&json).expect("deserialize");
        assert_eq!(decoded, corpus);
    }
}
