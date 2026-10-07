//! Integration-test CPU-oracle observation corpus for the D3 operations that sens#3801 lists as
//! GPU-admission candidates (sens#3766, sens#3561).
//!
//! Every fixture records what the CPU reference evaluator actually returns, and
//! the test below re-evaluates each program and compares. This corpus makes NO
//! claim that any operation runs on a GPU: sens#3889 keeps the GPU oracle
//! fail-closed (`BLOCKED-MECHANISM`) until an exact-domain batched/buffer-map
//! law is ratified. The values here are the CPU side of a future
//! "CPU digest == GPU digest" gate, nothing more.

use sens::{eval_program, Session};

/// Constant by design: no fixture in this module is GPU-executable.
pub const GPU_STATUS: &str = "blocked-mechanism";

#[derive(Clone, Copy, Debug, Eq, PartialEq, PartialOrd, Ord)]
pub enum ConformanceTier {
    /// D3 primitives that return a value.
    CoreSemantics = 1,
    /// Named error paths and edge cases of the language contract.
    LanguageContract = 2,
    /// Library-owned derived operations built on the D3 primitives.
    DerivedLibrary = 3,
}

/// What the CPU evaluator must produce for a fixture.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Expected {
    /// Rendered value of a successful evaluation.
    Value(&'static str),
    /// `Debug` name of the `ErrorKind` of a failed evaluation.
    Error(&'static str),
}

#[derive(Clone, Copy, Debug)]
pub struct CpuOracleFixture {
    pub fixture_id: &'static str,
    pub tier: ConformanceTier,
    /// Exact domain identity per contracts/bija3-l1-l5-ratification.lisp, or a
    /// note that the operation is library-derived.
    pub operation: &'static str,
    pub program: &'static str,
    pub expected: Expected,
}

pub const CORPUS: &[CpuOracleFixture] = &[
    CpuOracleFixture {
        fixture_id: "core-001-quote",
        tier: ConformanceTier::CoreSemantics,
        operation: "D3:001 QUOTE",
        program: "(як-є radio)",
        expected: Expected::Value("radio"),
    },
    CpuOracleFixture {
        fixture_id: "core-010-atom-symbol",
        tier: ConformanceTier::CoreSemantics,
        operation: "D3:010 ATOM",
        program: "(атом? 'radio)",
        expected: Expected::Value("1"),
    },
    CpuOracleFixture {
        fixture_id: "core-010-atom-list",
        tier: ConformanceTier::CoreSemantics,
        operation: "D3:010 ATOM",
        program: "(атом? '(1 2))",
        expected: Expected::Value("0"),
    },
    CpuOracleFixture {
        fixture_id: "core-011-cdr",
        tier: ConformanceTier::CoreSemantics,
        operation: "D3:011 CDR",
        program: "(решта '(a b c))",
        expected: Expected::Value("(b c)"),
    },
    CpuOracleFixture {
        fixture_id: "core-100-car",
        tier: ConformanceTier::CoreSemantics,
        operation: "D3:100 CAR",
        program: "(перше '(a b c))",
        expected: Expected::Value("a"),
    },
    CpuOracleFixture {
        fixture_id: "core-101-eq",
        tier: ConformanceTier::CoreSemantics,
        operation: "D3:101 EQ",
        program: "(тотожне? 'a 'a)",
        expected: Expected::Value("1"),
    },
    CpuOracleFixture {
        fixture_id: "core-111-cons",
        tier: ConformanceTier::CoreSemantics,
        operation: "D3:111 CONS",
        program: "(сполучити 'a '(b c))",
        expected: Expected::Value("(a b c)"),
    },
    CpuOracleFixture {
        fixture_id: "contract-010-atom-nil",
        tier: ConformanceTier::LanguageContract,
        operation: "D3:010 ATOM",
        program: "(атом? '())",
        expected: Expected::Value("1"),
    },
    CpuOracleFixture {
        fixture_id: "contract-100-car-non-list",
        tier: ConformanceTier::LanguageContract,
        operation: "D3:100 CAR",
        program: "(перше 5)",
        expected: Expected::Error("Type"),
    },
    CpuOracleFixture {
        fixture_id: "contract-101-eq-pairs",
        tier: ConformanceTier::LanguageContract,
        operation: "D3:101 EQ",
        program: "(тотожне? '(1) '(2))",
        expected: Expected::Error("Type"),
    },
    CpuOracleFixture {
        fixture_id: "derived-reverse",
        tier: ConformanceTier::DerivedLibrary,
        operation: "library-derived (reverse)",
        program: "(зворот '(1 2 3))",
        expected: Expected::Value("(3 2 1)"),
    },
    CpuOracleFixture {
        fixture_id: "derived-map-atom",
        tier: ConformanceTier::DerivedLibrary,
        operation: "library-derived (map)",
        program: "(відобразити (функція (x) (атом? x)) '(1 2 3))",
        expected: Expected::Value("(1 1 1)"),
    },
];

/// Evaluate `program` on the CPU reference evaluator with the language-owned
/// core library preloaded, and render the outcome like [`Expected`].
pub fn observe(program: &str) -> Expected {
    // Leak is intentional and test-sized: `Expected` borrows `'static` text.
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("core library should preload cleanly");
    match eval_program(program, &mut session) {
        Ok(result) => Expected::Value(Box::leak(result.value.to_string().into_boxed_str())),
        Err(error) => Expected::Error(Box::leak(format!("{:?}", error.kind).into_boxed_str())),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_fixture_matches_the_cpu_oracle() {
        for fixture in CORPUS {
            assert_eq!(
                observe(fixture.program),
                fixture.expected,
                "fixture {} ({})",
                fixture.fixture_id,
                fixture.program
            );
        }
    }

    #[test]
    fn fixture_ids_are_unique() {
        let mut ids: Vec<_> = CORPUS.iter().map(|f| f.fixture_id).collect();
        ids.sort_unstable();
        let before = ids.len();
        ids.dedup();
        assert_eq!(before, ids.len());
    }

    #[test]
    fn every_tier_is_populated_and_errors_are_covered() {
        for tier in [
            ConformanceTier::CoreSemantics,
            ConformanceTier::LanguageContract,
            ConformanceTier::DerivedLibrary,
        ] {
            assert!(CORPUS.iter().any(|f| f.tier == tier), "empty tier {tier:?}");
        }
        assert!(CORPUS
            .iter()
            .any(|f| matches!(f.expected, Expected::Error(_))));
    }

    #[test]
    fn corpus_never_claims_gpu_execution() {
        assert_eq!(GPU_STATUS, "blocked-mechanism");
    }
}
