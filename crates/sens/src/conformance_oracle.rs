//! Canonical oracle corpus for conformance testing.
//!
//! Authority: sens#3561 — produce single conformance artifact consumed by
//! CML, GraalVM, FPGA, and external witnesses.
//!
//! Machine-readable evidence of semantic conformance with explicit bounds.
//! Never claim exhaustiveness without declaring the bound that was exhausted.

// Serde is deliberately test-only in this capability-free core.

/// Semantic versioning for oracle schema.
pub const ORACLE_VERSION_MAJOR: u32 = 1;
pub const ORACLE_VERSION_MINOR: u32 = 0;

/// Single canonical observable row for one test case.
///
/// No host object/debug/string representation is semantic authority.
/// Every field is deterministic, stable across substrates, and reproducible.
#[derive(Clone, Debug, Eq, Hash, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct CanonicalObservable {
    /// Unique case identifier, stable independent of host language.
    pub case_id: String,

    /// Authority: language-contract.lisp version or Contract reference.
    pub contract: String,

    /// SENS repository SHA at time of corpus generation.
    pub upstream_sha: String,

    /// Source program digest (SHA-256 hex).
    pub program_digest: String,

    /// Trace of exact-domain identities used (D3:001, D4:0010, etc.).
    pub identity_trace_digest: String,

    /// Result kind: "success", "error", "diverge", "type-error", etc.
    pub result_kind: String,

    /// Result value digest (SHA-256 hex) if success.
    pub result_digest: String,

    /// Error kind if result is error (e.g., "arity-mismatch", "type-error").
    pub error_kind: Option<String>,

    /// Deterministic order digest for observable sequence.
    pub observable_order_digest: String,

    /// Mechanism status: "admitted", "unsupported", "research", "deprecated".
    pub mechanism_status: String,

    /// Expected status per Contract (for negative control validation).
    pub expected_status: String,
}

/// Bounded exhaustive corpus generation metadata.
///
/// Principle: **finite exhaustive evidence is powerful only when its
/// boundary is part of the evidence.**
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct ExhaustiveBound {
    /// Domains included: "D1-D3", "D1-D4", "D1-D7", etc.
    pub domain_set: String,

    /// Maximum AST depth (0 for literals only, 1 for simple forms, etc).
    pub max_ast_depth: u32,

    /// Maximum total nodes in AST.
    pub max_nodes: u32,

    /// Maximum value magnitude for numeric arguments.
    pub argument_value_bound: i64,

    /// Total cases generated (before deduplication).
    pub generated_cases: u32,

    /// Cases after deduplication (actual test suite size).
    pub deduplicated_cases: u32,

    /// Evidence class: "LOCAL-EXHAUSTIVE" or "PROGRAM-BOUNDED-EXHAUSTIVE".
    pub evidence_class: String,

    /// Digest of the bound itself (for change detection).
    pub bound_digest: String,
}

/// Complete conformance corpus artifact.
#[derive(Clone, Debug)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct ConformanceCorpus {
    /// Schema version (major.minor).
    pub version: (u32, u32),

    /// Generation timestamp (ISO 8601).
    pub generated_at: String,

    /// Authority bundle (contract, SENS SHA, etc).
    pub authority: AuthorityInfo,

    /// Bounds on this corpus (what "exhaustive" means).
    pub bounds: ExhaustiveBound,

    /// All canonical observable rows (JSONL or TSV format).
    pub observables: Vec<CanonicalObservable>,

    /// Negative controls: cases that MUST fail in specific ways.
    pub negative_controls: Vec<NegativeControl>,

    /// Statistics for audit trail.
    pub statistics: CorpusStatistics,
}

/// Authority facts for the corpus.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct AuthorityInfo {
    /// Language-contract.lisp version (e.g., "11.8").
    pub contract_version: String,

    /// Contract SHA-256.
    pub contract_sha256: String,

    /// SENS repository commit SHA.
    pub upstream_sha: String,

    /// Domain laws referenced (D1-D9 ratification refs).
    pub ratified_laws: Vec<String>,
}

/// Negative control: a case that must fail in a specific way.
///
/// Used to validate that the oracle correctly rejects wrong-domain,
/// malformed, or research-only identities.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct NegativeControl {
    /// What this negative control tests.
    /// e.g., "wrong-domain-equal-payload", "d8-missing-mechanism",
    /// "d7-non-callable-role", "d6-missing-mechanism"
    pub control_name: String,

    /// Program that should fail.
    pub program_digest: String,

    /// Expected failure kind.
    pub expected_error_kind: String,

    /// Whether the oracle correctly rejected this.
    pub rejection_observed: bool,

    /// Diagnostic message if rejection failed.
    pub diagnostic: Option<String>,
}

/// Corpus statistics and audit trail.
#[derive(Clone, Debug, Eq, PartialEq)]
#[cfg_attr(test, derive(serde::Serialize, serde::Deserialize))]
pub struct CorpusStatistics {
    /// Success cases.
    pub success_count: u32,

    /// Error cases (expected failures).
    pub error_count: u32,

    /// Unsupported mechanism cases.
    pub unsupported_count: u32,

    /// Research (D8) cases.
    pub research_count: u32,

    /// Coverage by domain: D1, D2, D3, etc.
    pub domain_coverage: std::collections::BTreeMap<String, u32>,

    /// Coverage by operation (e.g., D3:001 QUOTE, D4:0010 LAMBDA).
    pub operation_coverage: std::collections::BTreeMap<String, u32>,

    /// Negative controls: passed/failed.
    pub negative_controls_passed: u32,
    pub negative_controls_failed: u32,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn oracle_version_correct() {
        assert_eq!(ORACLE_VERSION_MAJOR, 1);
        assert_eq!(ORACLE_VERSION_MINOR, 0);
    }

    #[test]
    fn observable_serializes_to_json() {
        let observable = CanonicalObservable {
            case_id: "d3-001-quote-empty".to_string(),
            contract: "11.8".to_string(),
            upstream_sha: "abc123".to_string(),
            program_digest: "def456".to_string(),
            identity_trace_digest: "ghi789".to_string(),
            result_kind: "success".to_string(),
            result_digest: "jkl012".to_string(),
            error_kind: None,
            observable_order_digest: "mno345".to_string(),
            mechanism_status: "admitted".to_string(),
            expected_status: "admitted".to_string(),
        };

        let json = serde_json::to_string(&observable).expect("serialize");
        let deserialized: CanonicalObservable =
            serde_json::from_str(&json).expect("deserialize");
        assert_eq!(observable, deserialized);
    }

    #[test]
    fn bounds_declare_exhaustiveness() {
        let bound = ExhaustiveBound {
            domain_set: "D1-D3".to_string(),
            max_ast_depth: 3,
            max_nodes: 100,
            argument_value_bound: 1000,
            generated_cases: 5000,
            deduplicated_cases: 3200,
            evidence_class: "PROGRAM-BOUNDED-EXHAUSTIVE".to_string(),
            bound_digest: "pqr678".to_string(),
        };

        assert_eq!(bound.domain_set, "D1-D3");
        assert!(bound.deduplicated_cases <= bound.generated_cases);
    }

    #[test]
    fn negative_control_tracks_rejection() {
        let control = NegativeControl {
            control_name: "wrong-domain-equal-payload".to_string(),
            program_digest: "abc123".to_string(),
            expected_error_kind: "domain-mismatch".to_string(),
            rejection_observed: true,
            diagnostic: None,
        };

        assert!(control.rejection_observed);
    }
}
