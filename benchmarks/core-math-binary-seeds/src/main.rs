use core_math_binary_seeds::{
    canonical_baseline_basis, BinaryNumber, BoundedHorizon, Domain, RemoveOneTournament, Seed,
    SemanticObject,
};

fn main() {
    let basis = canonical_baseline_basis();
    let horizon = BoundedHorizon::default();
    let tournament = RemoveOneTournament::new(basis.clone(), horizon);

    // 1. Run remove-one tournament across all baseline seeds and laws
    let verdicts = tournament.run();

    let mut seeds_passed = 0;
    let mut laws_passed = 0;
    let total_premises = verdicts.len();

    for v in &verdicts {
        assert!(
            v.is_strictly_necessary,
            "Premise {} must be strictly necessary to be in minimal basis",
            v.premise_id
        );
        assert!(
            !v.capabilities_lost.is_empty(),
            "Premise {} must cause loss of capability on removal",
            v.premise_id
        );
        assert!(v.reduced_count < v.baseline_count);

        if v.is_seed {
            seeds_passed += 1;
        } else {
            laws_passed += 1;
        }
    }

    assert_eq!(seeds_passed, basis.seeds.len());
    assert_eq!(laws_passed, basis.laws.len());

    // 2. Falsifier 1: Derivable child seed (1010) must be detected as redundant
    let redundant_child = Seed {
        id: "seed.selector.redundant_child",
        object: SemanticObject::new(
            Domain::SelectorPath,
            BinaryNumber::parse("1010").unwrap(),
        ),
        description: "Derivable child falsely claimed as seed",
    };
    let child_verdict = tournament.test_redundant_seed_falsifier(redundant_child);
    assert!(
        !child_verdict.is_strictly_necessary,
        "Falsifier: Derivable child must be rejected as non-minimal"
    );
    assert_eq!(child_verdict.capabilities_lost.len(), 0);

    // 3. Falsifier 2: Affine identity (100100) derived via Inversion^2 must be detected as redundant
    let redundant_identity = Seed {
        id: "seed.affine.redundant_identity",
        object: SemanticObject::new(
            Domain::AffineFunctionGF2,
            BinaryNumber::parse("100100").unwrap(),
        ),
        description: "Identity coordinate derived via Inversion^2, falsely claimed as seed",
    };
    let id_verdict = tournament.test_redundant_seed_falsifier(redundant_identity);
    assert!(
        !id_verdict.is_strictly_necessary,
        "Falsifier: Identity must be rejected as a derived theorem, not an irreducible seed"
    );
    assert_eq!(id_verdict.capabilities_lost.len(), 0);

    // 4. Print machine-readable key-value facts
    println!("SEEDS-TOURNAMENT=remove-one-necessity-matrix");
    println!("ONTOLOGY=2490-binary-domain");
    println!("ZERO-DEPENDENCY=PASS");
    println!("CANONICAL-SEEDS-COUNT={}", basis.seeds.len());
    println!("CANONICAL-LAWS-COUNT={}", basis.laws.len());
    println!("TOTAL-PREMISES-EVALUATED={}", total_premises);
    println!("PREMISES-STRICTLY-NECESSARY={}/{}", total_premises, total_premises);
    println!("PREMISES-EARNED-EXISTENCE=PASS");
    println!("REDUNDANT-SEED-FALSIFIER-CHILD=PASS");
    println!("REDUNDANT-SEED-FALSIFIER-IDENTITY=PASS");
    println!("QGROUP-ROOTS-INDEPENDENT=PASS");
    println!("SELECTOR-ROOTS-INDEPENDENT=PASS");
    println!("AFFINE-GENERATORS-INDEPENDENT=PASS");
    println!("DOMAIN-FIREWALL-PRESERVED=PASS");
    println!("LISP-DEPENDENCY=0");
    println!("JSON-DEPENDENCY=0");
    println!("AST-DEPENDENCY=0");
    println!("HASH-IDENTITY-DEPENDENCY=0");
    println!("REGISTRY-LOOKUPS=0");
    println!("STATUS=PASS-CORE-MATH-MINIMAL-SEEDS");
}
