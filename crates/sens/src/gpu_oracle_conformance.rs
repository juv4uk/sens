//! GPU Oracle Conformance Tiers (sens#3766 + sens#3561).
//!
//! Extends gpu_oracle with conformance tier structure:
//! - Tier 1: Core Semantics (GPU-executable D3 primitives)
//! - Tier 2: Language Contract (error handling, edge cases)
//! - Tier 3: GPU Ecosystem (derived operations, optimization targets)
//!
//! Authority: Contract 11.6 + GPU admission (sens#3801) + Conformance (sens#3561)

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// Conformance tier classification.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize, PartialOrd, Ord)]
pub enum ConformanceTier {
    /// Core semantics: D3 GPU primitives only
    Tier1CoreSemantics = 1,
    /// Language contract: error paths, edge cases, type checking
    Tier2LanguageContract = 2,
    /// GPU ecosystem: derived operations, optimization candidates
    Tier3GpuEcosystem = 3,
}

/// GPU Oracle fixture: a test case with conformance tier classification.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GpuOracleFixture {
    /// Unique fixture ID (e.g., "gpu-core-001-quote")
    pub fixture_id: String,

    /// Conformance tier (1, 2, or 3)
    pub tier: ConformanceTier,

    /// D3/D4 operation identity (e.g., "D3:001 QUOTE")
    pub operation: String,

    /// Canonical program (sexpr format)
    pub program: String,

    /// Expected result kind: "success", "error", "diverge"
    pub expected_result: String,

    /// Result digest (SHA-256) if success
    pub result_digest: Option<String>,

    /// Error kind if expected_result is "error"
    pub error_kind: Option<String>,

    /// GPU admission status: "gpu", "host_control", "unsupported"
    pub gpu_status: String,

    /// Execution class: "structural", "compute", "control"
    pub execution_class: String,

    /// Minimum CUDA compute capability required
    pub min_compute_capability: String,

    /// Deterministic GPU executability flag
    pub deterministic_gpu_executable: bool,

    /// Notes or rationale
    pub note: String,
}

/// GPU Conformance Corpus: all fixtures organized by tier.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GpuConformanceCorpus {
    /// Schema version
    pub version: (u32, u32),

    /// Generation timestamp
    pub generated_at: String,

    /// Authority bundle
    pub authority: CorpusAuthority,

    /// Tier 1 fixtures (core D3 primitives)
    pub tier1_core: Vec<GpuOracleFixture>,

    /// Tier 2 fixtures (contract + error paths)
    pub tier2_contract: Vec<GpuOracleFixture>,

    /// Tier 3 fixtures (ecosystem optimizations)
    pub tier3_ecosystem: Vec<GpuOracleFixture>,

    /// Overall statistics
    pub statistics: CorpusStatistics,
}

/// Authority facts
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CorpusAuthority {
    pub contract_version: String,
    pub contract_sha256: String,
    pub conformance_oracle_authority: String,  // sens#3561
    pub gpu_admission_authority: String,       // sens#3801
    pub cuda_reference: String,
    pub ratified_laws: Vec<String>,
}

/// Statistics across all tiers
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CorpusStatistics {
    pub tier1_count: u32,
    pub tier2_count: u32,
    pub tier3_count: u32,
    pub total_fixtures: u32,
    pub gpu_executable_count: u32,
    pub host_control_count: u32,
    pub unsupported_count: u32,
    pub operations_covered: BTreeMap<String, u32>,
}

impl GpuConformanceCorpus {
    /// Generate canonical GPU conformance corpus with all tiers.
    pub fn generate_canonical() -> Self {
        let mut tier1 = Vec::new();
        let mut tier2 = Vec::new();
        let mut tier3 = Vec::new();

        // ===== TIER 1: CORE SEMANTICS =====
        // D3 GPU-admissible primitives

        tier1.push(GpuOracleFixture {
            fixture_id: "gpu-core-001-quote".to_string(),
            tier: ConformanceTier::Tier1CoreSemantics,
            operation: "D3:001 QUOTE".to_string(),
            program: "(quote radio)".to_string(),
            expected_result: "success".to_string(),
            result_digest: Some("quote-result-sha256".to_string()),
            error_kind: None,
            gpu_status: "gpu".to_string(),
            execution_class: "structural".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "Core primitive: quote immutable data".to_string(),
        });

        tier1.push(GpuOracleFixture {
            fixture_id: "gpu-core-010-atom".to_string(),
            tier: ConformanceTier::Tier1CoreSemantics,
            operation: "D3:010 ATOM?".to_string(),
            program: "(atom? 'radio)".to_string(),
            expected_result: "success".to_string(),
            result_digest: Some("atom-true-sha256".to_string()),
            error_kind: None,
            gpu_status: "gpu".to_string(),
            execution_class: "compute".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "Core predicate: test exact-ness".to_string(),
        });

        tier1.push(GpuOracleFixture {
            fixture_id: "gpu-core-010-atom-list".to_string(),
            tier: ConformanceTier::Tier1CoreSemantics,
            operation: "D3:010 ATOM?".to_string(),
            program: "(atom? '(1 2))".to_string(),
            expected_result: "success".to_string(),
            result_digest: Some("atom-false-sha256".to_string()),
            error_kind: None,
            gpu_status: "gpu".to_string(),
            execution_class: "compute".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "ATOM? on list returns false".to_string(),
        });

        tier1.push(GpuOracleFixture {
            fixture_id: "gpu-core-011-cdr".to_string(),
            tier: ConformanceTier::Tier1CoreSemantics,
            operation: "D3:011 CDR".to_string(),
            program: "(cdr '(a b c))".to_string(),
            expected_result: "success".to_string(),
            result_digest: Some("cdr-result-sha256".to_string()),
            error_kind: None,
            gpu_status: "gpu".to_string(),
            execution_class: "structural".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "Core accessor: rest of list".to_string(),
        });

        tier1.push(GpuOracleFixture {
            fixture_id: "gpu-core-100-car".to_string(),
            tier: ConformanceTier::Tier1CoreSemantics,
            operation: "D3:100 CAR".to_string(),
            program: "(car '(a b c))".to_string(),
            expected_result: "success".to_string(),
            result_digest: Some("car-result-sha256".to_string()),
            error_kind: None,
            gpu_status: "gpu".to_string(),
            execution_class: "structural".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "Core accessor: head of list".to_string(),
        });

        tier1.push(GpuOracleFixture {
            fixture_id: "gpu-core-101-eq".to_string(),
            tier: ConformanceTier::Tier1CoreSemantics,
            operation: "D3:101 EQ?".to_string(),
            program: "(eq? 'a 'a)".to_string(),
            expected_result: "success".to_string(),
            result_digest: Some("eq-true-sha256".to_string()),
            error_kind: None,
            gpu_status: "gpu".to_string(),
            execution_class: "compute".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "Core predicate: exact identity comparison".to_string(),
        });

        tier1.push(GpuOracleFixture {
            fixture_id: "gpu-core-111-cons".to_string(),
            tier: ConformanceTier::Tier1CoreSemantics,
            operation: "D3:111 CONS".to_string(),
            program: "(cons 'a '(b c))".to_string(),
            expected_result: "success".to_string(),
            result_digest: Some("cons-result-sha256".to_string()),
            error_kind: None,
            gpu_status: "gpu".to_string(),
            execution_class: "structural".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "Core constructor: prepend to list".to_string(),
        });

        // ===== TIER 2: LANGUAGE CONTRACT =====
        // Error handling and edge cases

        tier2.push(GpuOracleFixture {
            fixture_id: "gpu-contract-010-atom-nil".to_string(),
            tier: ConformanceTier::Tier2LanguageContract,
            operation: "D3:010 ATOM?".to_string(),
            program: "(atom? '())".to_string(),
            expected_result: "success".to_string(),
            result_digest: Some("atom-nil-true-sha256".to_string()),
            error_kind: None,
            gpu_status: "gpu".to_string(),
            execution_class: "compute".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "NIL is an atom (Contract 11.6)".to_string(),
        });

        tier2.push(GpuOracleFixture {
            fixture_id: "gpu-contract-car-type-error".to_string(),
            tier: ConformanceTier::Tier2LanguageContract,
            operation: "D3:100 CAR".to_string(),
            program: "(car 5)".to_string(),
            expected_result: "error".to_string(),
            result_digest: None,
            error_kind: Some("type-error".to_string()),
            gpu_status: "gpu".to_string(),
            execution_class: "structural".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "CAR on non-list fails".to_string(),
        });

        tier2.push(GpuOracleFixture {
            fixture_id: "gpu-contract-eq-list-error".to_string(),
            tier: ConformanceTier::Tier2LanguageContract,
            operation: "D3:101 EQ?".to_string(),
            program: "(eq? '(1) '(2))".to_string(),
            expected_result: "error".to_string(),
            result_digest: None,
            error_kind: Some("type-error".to_string()),
            gpu_status: "gpu".to_string(),
            execution_class: "compute".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "EQ? rejects pairs (atoms only)".to_string(),
        });

        // ===== TIER 3: GPU ECOSYSTEM =====
        // Derived operations and optimization targets

        tier3.push(GpuOracleFixture {
            fixture_id: "gpu-ecosystem-reverse".to_string(),
            tier: ConformanceTier::Tier3GpuEcosystem,
            operation: "Derived: reverse".to_string(),
            program: "(reverse '(1 2 3))".to_string(),
            expected_result: "success".to_string(),
            result_digest: Some("reverse-result-sha256".to_string()),
            error_kind: None,
            gpu_status: "gpu".to_string(),
            execution_class: "structural".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "Derived from CAR/CDR/CONS".to_string(),
        });

        tier3.push(GpuOracleFixture {
            fixture_id: "gpu-ecosystem-map".to_string(),
            tier: ConformanceTier::Tier3GpuEcosystem,
            operation: "Derived: map (GPU-only operations)".to_string(),
            program: "(map (lambda (x) (atom? x)) '(1 2 3))".to_string(),
            expected_result: "success".to_string(),
            result_digest: Some("map-result-sha256".to_string()),
            error_kind: None,
            gpu_status: "gpu".to_string(),
            execution_class: "compute".to_string(),
            min_compute_capability: "sm_35".to_string(),
            deterministic_gpu_executable: true,
            note: "GPU-optimizable list operation".to_string(),
        });

        // Compute statistics
        let tier1_count = tier1.len() as u32;
        let tier2_count = tier2.len() as u32;
        let tier3_count = tier3.len() as u32;
        let total = tier1_count + tier2_count + tier3_count;

        let mut ops_covered = BTreeMap::new();
        for fixture in tier1.iter().chain(tier2.iter()).chain(tier3.iter()) {
            *ops_covered.entry(fixture.operation.clone()).or_insert(0) += 1;
        }

        Self {
            version: (1, 0),
            generated_at: "2026-10-06T00:00:00Z".to_string(),
            authority: CorpusAuthority {
                contract_version: "11.6".to_string(),
                contract_sha256: "contract-11-6-sha256".to_string(),
                conformance_oracle_authority: "sens#3561".to_string(),
                gpu_admission_authority: "sens#3801".to_string(),
                cuda_reference: "juv4uk/cml#472".to_string(),
                ratified_laws: vec![
                    "D3_BIJA3_LAW_3202".to_string(),
                    "GPU_ADMISSION_D3_3801".to_string(),
                    "CONFORMANCE_TIERS_3561".to_string(),
                ],
            },
            tier1_core: tier1,
            tier2_contract: tier2,
            tier3_ecosystem: tier3,
            statistics: CorpusStatistics {
                tier1_count,
                tier2_count,
                tier3_count,
                total_fixtures: total,
                gpu_executable_count: total,
                host_control_count: 0,
                unsupported_count: 0,
                operations_covered: ops_covered,
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn gpu_conformance_corpus_generates() {
        let corpus = GpuConformanceCorpus::generate_canonical();
        assert_eq!(corpus.version, (1, 0));
        assert!(corpus.tier1_core.len() > 0);
        assert!(corpus.tier2_contract.len() > 0);
        assert!(corpus.tier3_ecosystem.len() > 0);
    }

    #[test]
    fn tier1_has_core_primitives() {
        let corpus = GpuConformanceCorpus::generate_canonical();
        let ops: Vec<_> = corpus.tier1_core.iter().map(|f| &f.operation).collect();
        assert!(ops.iter().any(|op| op.contains("QUOTE")));
        assert!(ops.iter().any(|op| op.contains("CAR")));
        assert!(ops.iter().any(|op| op.contains("CONS")));
    }

    #[test]
    fn tier2_has_error_cases() {
        let corpus = GpuConformanceCorpus::generate_canonical();
        let errors: Vec<_> = corpus
            .tier2_contract
            .iter()
            .filter(|f| f.expected_result == "error")
            .collect();
        assert!(!errors.is_empty());
    }

    #[test]
    fn all_fixtures_gpu_executable() {
        let corpus = GpuConformanceCorpus::generate_canonical();
        let all: Vec<_> = corpus
            .tier1_core
            .iter()
            .chain(corpus.tier2_contract.iter())
            .chain(corpus.tier3_ecosystem.iter())
            .collect();
        assert!(all.iter().all(|f| f.gpu_status == "gpu"));
    }
}
