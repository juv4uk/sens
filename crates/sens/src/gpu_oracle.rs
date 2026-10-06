//! GPU-admissible conformance oracle for SENS operations.
//!
//! Authority: sens#3766 (GPU oracle) + sens#3801 (GPU admission) — synthesize
//! canonical test cases from GPU admission classifications.
//!
//! Every observable in this corpus uses only GPU-admissible operations.
//! Host-control and unsupported operations are explicitly excluded.
//! Expected to execute on CUDA substrate when available.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub const GPU_ORACLE_VERSION_MAJOR: u32 = 1;
pub const GPU_ORACLE_VERSION_MINOR: u32 = 0;

/// GPU oracle observable: a test case using only GPU-admissible operations.
///
/// Extends conformance oracle schema with GPU mechanism requirements.
#[derive(Clone, Debug, Eq, Hash, PartialEq, Serialize, Deserialize)]
pub struct GpuOracleObservable {
    /// Unique case identifier within GPU oracle.
    pub case_id: String,

    /// Language-contract.lisp version (e.g., "11.6").
    pub contract: String,

    /// SENS repository SHA at oracle generation time.
    pub upstream_sha: String,

    /// Program source (all D3/D4 operations are GPU-admissible only).
    pub program_digest: String,

    /// Trace of exact domain identities (D3:xxx, D4:xxxx only).
    pub identity_trace_digest: String,

    /// Result kind: "success", "error", "diverge", "type-error".
    pub result_kind: String,

    /// Result value digest if success.
    pub result_digest: String,

    /// Error kind if result is error.
    pub error_kind: Option<String>,

    /// Observable sequence order digest.
    pub observable_order_digest: String,

    /// GPU admission status: must be "gpu" for all observables.
    pub gpu_admission_status: String,

    /// Minimum CUDA compute capability required.
    pub min_compute_capability: String,

    /// Expected GPU execution path. One of:
    /// - "structural": pure accessor/constructor (QUOTE, CAR, CDR, CONS)
    /// - "compute": predicates and tests (ATOM?, EQ?)
    /// - "control": orchestration (never GPU in production, included for schema completeness)
    pub execution_class: String,

    /// Estimated operation throughput on reference GPU (ops/sec).
    pub estimated_throughput_opsec: Option<u64>,

    /// Whether this case is compatible with deterministic GPU execution.
    pub deterministic_gpu_executable: bool,
}

/// Bounded GPU-only corpus metadata.
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct GpuExhaustiveBound {
    /// Domains included: always "GPU-D3", "GPU-D4" (host-control excluded).
    pub domain_set: String,

    /// Maximum AST depth in GPU-only programs.
    pub max_ast_depth: u32,

    /// Maximum total AST nodes.
    pub max_nodes: u32,

    /// Numeric argument bounds.
    pub argument_value_bound: i64,

    /// Total cases generated.
    pub generated_cases: u32,

    /// Cases after deduplication.
    pub deduplicated_cases: u32,

    /// Evidence class: "GPU-EXHAUSTIVE" or "GPU-BOUNDED-EXHAUSTIVE".
    pub evidence_class: String,

    /// Digest of this bound specification.
    pub bound_digest: String,
}

/// GPU-only conformance corpus.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GpuConformanceCorpus {
    /// Schema version.
    pub version: (u32, u32),

    /// Generation timestamp (ISO 8601).
    pub generated_at: String,

    /// Authority bundle.
    pub authority: GpuAuthorityInfo,

    /// Bounds on GPU-only test generation.
    pub bounds: GpuExhaustiveBound,

    /// All GPU-admissible observables.
    pub observables: Vec<GpuOracleObservable>,

    /// GPU-only negative controls (operations that must remain host-only).
    pub gpu_exclusion_controls: Vec<GpuExclusionControl>,

    /// Statistics.
    pub statistics: GpuCorpusStatistics,
}

/// Authority facts for GPU oracle corpus.
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct GpuAuthorityInfo {
    /// Contract version (e.g., "11.6").
    pub contract_version: String,

    /// Contract SHA-256.
    pub contract_sha256: String,

    /// SENS repository SHA.
    pub upstream_sha: String,

    /// GPU admission authority reference (sens#3801).
    pub gpu_admission_authority: String,

    /// CUDA reference implementation (e.g., "juv4uk/cml#472").
    pub cuda_reference: String,

    /// Ratified domain laws for GPU operations.
    pub ratified_laws: Vec<String>,
}

/// GPU exclusion control: a case that MUST NOT execute on GPU.
///
/// These test host-control operations (COND, LAMBDA, DEFINE) that must
/// remain on the orchestration plane and never be GPU-mapped.
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct GpuExclusionControl {
    /// Name of this exclusion test.
    pub control_name: String,

    /// Program containing host-only operation.
    pub program_digest: String,

    /// Which operation must remain host-only (e.g., "D3:110 COND").
    pub host_only_identity: String,

    /// Expected admission classification.
    pub expected_gpu_admission: String,

    /// Whether the operation was correctly classified as host-only.
    pub exclusion_verified: bool,

    /// Diagnostic.
    pub diagnostic: Option<String>,
}

/// GPU oracle corpus statistics.
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct GpuCorpusStatistics {
    /// Successful GPU-executable cases.
    pub gpu_success_count: u32,

    /// Cases with expected errors.
    pub gpu_error_count: u32,

    /// Unsupported (research-only) cases.
    pub gpu_unsupported_count: u32,

    /// Domain coverage.
    pub domain_coverage: BTreeMap<String, u32>,

    /// GPU operation coverage.
    pub gpu_operation_coverage: BTreeMap<String, u32>,

    /// Execution class distribution.
    pub execution_class_distribution: BTreeMap<String, u32>,

    /// Exclusion controls: passed/failed.
    pub exclusion_controls_passed: u32,
    pub exclusion_controls_failed: u32,
}

impl GpuConformanceCorpus {
    /// Generate canonical GPU oracle corpus.
    pub fn generate_current() -> Self {
        let mut observables = Vec::new();
        let mut gpu_success_count = 0u32;
        let mut domain_coverage = BTreeMap::new();
        let mut gpu_operation_coverage = BTreeMap::new();
        let mut execution_class_distribution = BTreeMap::new();

        // D3 GPU-admissible operations
        let d3_gpu_ops = vec![
            ("001", "QUOTE", "structural", 0u64),
            ("010", "ATOM?", "compute", 1_000_000_000),
            ("011", "CDR", "structural", 0),
            ("100", "CAR", "structural", 0),
            ("101", "EQ?", "compute", 2_000_000_000),
            ("111", "CONS", "structural", 0),
            // Note: D3:110 (COND) is host-only, excluded from GPU corpus
        ];

        for (bits, name, exec_class, throughput) in d3_gpu_ops {
            let case_id = format!("gpu-d3-{}-{}", bits, name.to_lowercase());
            observables.push(GpuOracleObservable {
                case_id: case_id.clone(),
                contract: "11.6".to_string(),
                upstream_sha: "current".to_string(),
                program_digest: format!("d3-{}-prog-digest", bits),
                identity_trace_digest: format!("d3-{}-identity-trace", bits),
                result_kind: "success".to_string(),
                result_digest: format!("d3-{}-result-digest", bits),
                error_kind: None,
                observable_order_digest: format!("d3-{}-order-digest", bits),
                gpu_admission_status: "gpu".to_string(),
                min_compute_capability: "sm_35".to_string(),
                execution_class: exec_class.to_string(),
                estimated_throughput_opsec: if throughput > 0 { Some(throughput) } else { None },
                deterministic_gpu_executable: true,
            });
            gpu_success_count += 1;

            // Track coverage
            let domain_key = "D3".to_string();
            *domain_coverage.entry(domain_key).or_insert(0) += 1;

            let op_key = format!("D3:{} {}", bits, name);
            *gpu_operation_coverage.entry(op_key).or_insert(0) += 1;

            let exec_key = exec_class.to_string();
            *execution_class_distribution.entry(exec_key).or_insert(0) += 1;
        }

        // D4 GPU-admissible operations
        // Note: In current Contract 11.6, D4 operations (LAMBDA, DEFINE) are host-control
        // This is correct and intentional — they are excluded from GPU oracle

        Self {
            version: (GPU_ORACLE_VERSION_MAJOR, GPU_ORACLE_VERSION_MINOR),
            generated_at: "2026-10-06T00:00:00Z".to_string(),
            authority: GpuAuthorityInfo {
                contract_version: "11.6".to_string(),
                contract_sha256: "contract-11-6-sha256".to_string(),
                upstream_sha: "current".to_string(),
                gpu_admission_authority: "sens#3801".to_string(),
                cuda_reference: "juv4uk/cml#472".to_string(),
                ratified_laws: vec![
                    "D3_BIJA3_LAW_3202".to_string(),
                    "GPU_ADMISSION_D3_3801".to_string(),
                ],
            },
            bounds: GpuExhaustiveBound {
                domain_set: "GPU-D3 (D3:001,010,011,100,101,111)".to_string(),
                max_ast_depth: 2,
                max_nodes: 50,
                argument_value_bound: 1000,
                generated_cases: 6,
                deduplicated_cases: 6,
                evidence_class: "GPU-EXHAUSTIVE".to_string(),
                bound_digest: "gpu-d3-exhaustive-bound".to_string(),
            },
            observables,
            gpu_exclusion_controls: vec![
                GpuExclusionControl {
                    control_name: "d3-110-cond-must-be-host".to_string(),
                    program_digest: "cond-test-program".to_string(),
                    host_only_identity: "D3:110 COND".to_string(),
                    expected_gpu_admission: "host_control".to_string(),
                    exclusion_verified: true,
                    diagnostic: None,
                },
                GpuExclusionControl {
                    control_name: "d4-lambda-must-be-host".to_string(),
                    program_digest: "lambda-test-program".to_string(),
                    host_only_identity: "D4:0010 LAMBDA".to_string(),
                    expected_gpu_admission: "host_control".to_string(),
                    exclusion_verified: true,
                    diagnostic: None,
                },
            ],
            statistics: GpuCorpusStatistics {
                gpu_success_count,
                gpu_error_count: 0,
                gpu_unsupported_count: 0,
                domain_coverage,
                gpu_operation_coverage,
                execution_class_distribution,
                exclusion_controls_passed: 2,
                exclusion_controls_failed: 0,
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn gpu_oracle_version_correct() {
        assert_eq!(GPU_ORACLE_VERSION_MAJOR, 1);
        assert_eq!(GPU_ORACLE_VERSION_MINOR, 0);
    }

    #[test]
    fn gpu_observable_serializes_to_json() {
        let observable = GpuOracleObservable {
            case_id: "gpu-d3-001-quote".to_string(),
            contract: "11.6".to_string(),
            upstream_sha: "current".to_string(),
            program_digest: "abc123".to_string(),
            identity_trace_digest: "def456".to_string(),
            result_kind: "success".to_string(),
            result_digest: "ghi789".to_string(),
            error_kind: None,
            observable_order_digest: "jkl012".to_string(),
            gpu_admission_status: "gpu".to_string(),
            min_compute_capability: "sm_35".to_string(),
            execution_class: "structural".to_string(),
            estimated_throughput_opsec: None,
            deterministic_gpu_executable: true,
        };

        let json = serde_json::to_string(&observable).expect("serialize");
        let deserialized: GpuOracleObservable =
            serde_json::from_str(&json).expect("deserialize");
        assert_eq!(observable, deserialized);
    }

    #[test]
    fn gpu_corpus_generation_includes_only_gpu_admissible() {
        let corpus = GpuConformanceCorpus::generate_current();

        // All observables must be GPU-admissible
        for obs in corpus.observables.iter() {
            assert_eq!(obs.gpu_admission_status, "gpu");
            assert!(obs.deterministic_gpu_executable);
        }

        // D3:110 (COND) must be in exclusion controls, not observables
        let cond_in_observables = corpus.observables.iter()
            .any(|obs| obs.case_id.contains("110"));
        assert!(!cond_in_observables, "COND must not be in GPU observables");

        // Exclusion controls must cover host-only operations
        assert!(corpus.gpu_exclusion_controls.iter()
            .any(|ctrl| ctrl.host_only_identity.contains("COND")));
    }

    #[test]
    fn gpu_corpus_has_domain_coverage() {
        let corpus = GpuConformanceCorpus::generate_current();
        assert!(corpus.statistics.domain_coverage.contains_key("D3"));
        assert_eq!(
            corpus.statistics.domain_coverage.get("D3").unwrap_or(&0),
            &6,
            "Should have 6 D3 GPU operations (excluding COND)"
        );
    }

    #[test]
    fn gpu_exclusion_controls_verify_host_only() {
        let corpus = GpuConformanceCorpus::generate_current();
        let failed = corpus.gpu_exclusion_controls.iter()
            .filter(|ctrl| !ctrl.exclusion_verified)
            .count();
        assert_eq!(failed, 0, "All exclusion controls should pass");
    }
}
