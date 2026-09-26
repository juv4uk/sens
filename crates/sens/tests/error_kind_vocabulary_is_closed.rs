//! Machine-checkable gate for GitHub issue juv4uk/sens#66 (compiler
//! authority boundary): pins the exhaustive set of `ErrorKind` variants a
//! compiler backend is allowed to observe. See
//! docs/COMPILER-AUTHORITY-BOUNDARY.md for the full boundary this test is
//! one piece of.
//!
//! The exhaustive `match` below is the actual enforcement mechanism: adding
//! or removing an `ErrorKind` variant without updating this file is a Rust
//! compile error ("non-exhaustive patterns" / "no variant named ... in this
//! enum"), not a silent pass. This makes "a compiler-facing change quietly
//! grows the observable error vocabulary" something that must touch this
//! file explicitly, in this repo, under this repo's own review — it cannot
//! land as a side effect of unrelated work here or in a consumer repo that
//! merely imports `ErrorKind`.
//!
//! Mekhanizm perevirky dlia issue #66 (mezha vlady kompiliatora): fiksuie
//! vycherpnyi nabir variantiv `ErrorKind`, yaki compiler-backend maie pravo
//! sposterihaty. Divysia docs/COMPILER-AUTHORITY-BOUNDARY.md dlia povnoi
//! mezhi, chastynoiu yakoi ye tsei test.

use sens::ErrorKind;

/// Every variant `ErrorKind` currently has, named exactly once. If a variant
/// is added or removed in `crates/sens/src/error.rs` without updating
/// this list, `name_of` below fails to compile (non-exhaustive match) --
/// verified directly by temporarily adding a `NotCallable` variant and
/// confirming this file then fails to build, not just fails at runtime.
fn name_of(kind: &ErrorKind) -> &'static str {
    match kind {
        ErrorKind::Parse => "Parse",
        ErrorKind::UnknownSymbol => "UnknownSymbol",
        ErrorKind::Arity => "Arity",
        ErrorKind::Type => "Type",
        ErrorKind::InvalidForm => "InvalidForm",
        ErrorKind::UnsatisfiedConditional => "UnsatisfiedConditional",
        ErrorKind::MechanismUnavailable => "MechanismUnavailable",
        ErrorKind::OutOfMemory => "OutOfMemory",
        ErrorKind::NumericOverflow => "NumericOverflow",
        ErrorKind::DivisionByZero => "DivisionByZero",
    }
}

const ADMITTED_ERROR_KINDS: &[&str] = &[
    "Parse",
    "UnknownSymbol",
    "Arity",
    "Type",
    "InvalidForm",
    "UnsatisfiedConditional",
    "MechanismUnavailable",
    "OutOfMemory",
    "NumericOverflow",
    "DivisionByZero",
];

#[test]
fn error_kind_vocabulary_matches_the_pinned_admitted_list() {
    let all_kinds = [
        ErrorKind::Parse,
        ErrorKind::UnknownSymbol,
        ErrorKind::Arity,
        ErrorKind::Type,
        ErrorKind::InvalidForm,
        ErrorKind::UnsatisfiedConditional,
        ErrorKind::MechanismUnavailable,
        ErrorKind::OutOfMemory,
        ErrorKind::NumericOverflow,
        ErrorKind::DivisionByZero,
    ];
    let observed: Vec<&str> = all_kinds.iter().map(name_of).collect();
    assert_eq!(
        observed, ADMITTED_ERROR_KINDS,
        "ErrorKind's variant set drifted from the admitted vocabulary this \
         compiler-authority gate pins (docs/COMPILER-AUTHORITY-BOUNDARY.md). \
         A new variant here must be a deliberate, reviewed decision about \
         what a compiler backend is now allowed to observe -- update this \
         test's ADMITTED_ERROR_KINDS and name_of together, not either alone."
    );
}
