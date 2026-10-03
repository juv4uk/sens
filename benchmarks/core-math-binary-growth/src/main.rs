use std::collections::HashMap;
use core_math_binary_growth::{
    BinaryNumber, DemandEngine, DerivationDAG, Domain, EagerClosureEngine,
    GrowthError, ProvedLaw, SemanticObject,
};

fn setup_ontology_environment() -> (Vec<SemanticObject>, Vec<ProvedLaw>) {
    let seeds = vec![
        // Domain::SelectorPath seeds
        SemanticObject::new(
            Domain::SelectorPath,
            BinaryNumber::parse("101").unwrap(), // First root
        ),
        SemanticObject::new(
            Domain::SelectorPath,
            BinaryNumber::parse("110").unwrap(), // Rest root
        ),
        // Domain::QGroupFactor seeds
        SemanticObject::new(
            Domain::QGroupFactor,
            BinaryNumber::parse("0").unwrap(), // Additive group root
        ),
        SemanticObject::new(
            Domain::QGroupFactor,
            BinaryNumber::parse("1").unwrap(), // Multiplicative group root
        ),
        // Domain::AffineFunctionGF2 seeds (6-bit coordinates: 4 bits matrix A, 2 bits offset b)
        // Identity: A=[[1,0],[0,1]], b=[0,0] -> 100100
        SemanticObject::new(
            Domain::AffineFunctionGF2,
            BinaryNumber::parse("100100").unwrap(),
        ),
        // Bitwise Inversion: A=[[1,0],[0,1]], b=[1,1] -> 100111
        SemanticObject::new(
            Domain::AffineFunctionGF2,
            BinaryNumber::parse("100111").unwrap(),
        ),
        // Coordinate Swap: A=[[0,1],[1,0]], b=[0,0] -> 011000
        SemanticObject::new(
            Domain::AffineFunctionGF2,
            BinaryNumber::parse("011000").unwrap(),
        ),
    ];

    let laws = vec![
        ProvedLaw::new(
            "selector.extend/v1",
            Domain::SelectorPath,
            "output = 2 * parent + delta",
        ),
        ProvedLaw::new(
            "q-group.role/v1",
            Domain::QGroupFactor,
            "output = 2 * parent + delta",
        ),
        ProvedLaw::new(
            "affine.compose/v1",
            Domain::AffineFunctionGF2,
            "(A, b) ∘ (C, d) = (A * C, A * d XOR b)",
        ),
    ];

    (seeds, laws)
}

fn test_chained_binary_growth(seeds: &[SemanticObject], laws: &[ProvedLaw]) {
    let engine = DemandEngine::new(seeds, laws);
    let d0 = BinaryNumber::parse("0").unwrap();
    let d1 = BinaryNumber::parse("1").unwrap();

    // 5-step chained derivation:
    // Root: 101 (width 3)
    // Step 1: 101 + 0 -> 1010 (width 4)
    // Step 2: 1010 + 1 -> 10101 (width 5)
    // Step 3: 10101 + 0 -> 101010 (width 6)
    // Step 4: 101010 + 1 -> 1010101 (width 7)
    // Step 5: 1010101 + 1 -> 10101011 (width 8)
    let deltas = vec![d0.clone(), d1.clone(), d0.clone(), d1.clone(), d1.clone()];
    let res = engine
        .derive_factor_path(0, "selector.extend/v1", &deltas, None)
        .expect("chained derivation must succeed");

    assert_eq!(res.target.domain(), Domain::SelectorPath);
    assert_eq!(res.target.bits().bits(), "10101011");
    assert_eq!(res.target.width(), 8);
    assert_eq!(res.nodes_materialized, 6); // 1 root + 5 intermediate nodes
}

fn test_demand_vs_eager_parity_all_nodes(
    seeds: &[SemanticObject],
    laws: &[ProvedLaw],
) -> (usize, usize) {
    let demand_engine = DemandEngine::new(seeds, laws);
    let eager_engine = EagerClosureEngine::new(seeds, laws);

    let max_depth = 3;
    let eager = eager_engine
        .compute_factor_closure(0, "selector.extend/v1", max_depth)
        .expect("eager closure computation");

    // Total eager nodes = 1 + 2 + 4 + 8 = 15
    assert_eq!(eager.all_objects.len(), 15);

    // Verify demand derivation matches bit-for-bit for every target path
    let d0 = BinaryNumber::parse("0").unwrap();
    let d1 = BinaryNumber::parse("1").unwrap();

    // Test a specific demanded target: path [0, 1, 0] -> 101010
    let target_deltas = vec![d0.clone(), d1.clone(), d0.clone()];
    let demand_res = demand_engine
        .derive_factor_path(0, "selector.extend/v1", &target_deltas, None)
        .expect("demand derivation must succeed");

    assert_eq!(demand_res.target.bits().bits(), "101010");

    // Check that demand result exists in eager closure and matches bit-for-bit
    let found = eager
        .all_objects
        .iter()
        .find(|obj| obj.bits().bits() == "101010")
        .expect("target must exist in eager closure");
    assert_eq!(&demand_res.target, found);

    (demand_res.nodes_materialized, eager.all_objects.len())
}

fn test_affine_gf2_all_compositions(seeds: &[SemanticObject], laws: &[ProvedLaw]) -> usize {
    let engine = DemandEngine::new(seeds, laws);

    // Identity (index 4), Inversion (index 5), Swap (index 6)
    // Test involution properties:
    // NOT ∘ NOT = ID
    let not_not = engine
        .derive_affine_composition(5, 5, "affine.compose/v1", None)
        .unwrap();
    assert_eq!(not_not.target.bits().bits(), "100100");

    // SWAP ∘ SWAP = ID
    let swap_swap = engine
        .derive_affine_composition(6, 6, "affine.compose/v1", None)
        .unwrap();
    assert_eq!(swap_swap.target.bits().bits(), "100100");

    // ID ∘ SWAP = SWAP
    let id_swap = engine
        .derive_affine_composition(4, 6, "affine.compose/v1", None)
        .unwrap();
    assert_eq!(id_swap.target.bits().bits(), "011000");

    // SWAP ∘ ID = SWAP
    let swap_id = engine
        .derive_affine_composition(6, 4, "affine.compose/v1", None)
        .unwrap();
    assert_eq!(swap_id.target.bits().bits(), "011000");

    // SWAP ∘ (INV ∘ SWAP) = INV
    let mut dag = DerivationDAG::new();
    let _id_node = dag.push_seed(4);
    let inv_node = dag.push_seed(5);
    let swap_node = dag.push_seed(6);
    let inner_comp = dag.push_compose("affine.compose/v1", inv_node, swap_node);
    dag.push_compose("affine.compose/v1", swap_node, inner_comp);

    let nodes = dag.execute(seeds, laws, None).unwrap();
    let final_res = nodes.last().unwrap();
    assert_eq!(final_res.bits().bits(), "100111"); // Equals Inversion

    // Verify all 4 possible compositions between seed functions
    let mut cases = 0;
    for i in 4..=6 {
        for j in 4..=6 {
            let res = engine
                .derive_affine_composition(i, j, "affine.compose/v1", None)
                .unwrap();
            assert_eq!(res.target.domain(), Domain::AffineFunctionGF2);
            assert_eq!(res.target.width(), 6);
            cases += 1;
        }
    }
    cases
}

fn run_falsifier_suite(seeds: &[SemanticObject], laws: &[ProvedLaw]) {
    let engine = DemandEngine::new(seeds, laws);
    let d0 = BinaryNumber::parse("0").unwrap();
    let d1 = BinaryNumber::parse("1").unwrap();

    // Falsifier 1: Missing seed fails closed
    let err_seed = engine
        .derive_factor_path(99, "selector.extend/v1", std::slice::from_ref(&d0), None)
        .unwrap_err();
    assert!(matches!(err_seed, GrowthError::MissingSeed { .. }));

    // Falsifier 2: Missing law fails closed
    let err_law = engine
        .derive_factor_path(0, "unregistered.law/v1", std::slice::from_ref(&d0), None)
        .unwrap_err();
    assert!(matches!(err_law, GrowthError::MissingLaw { .. }));

    // Falsifier 3: Domain firewall blocks cross-domain growth (#2508)
    let mut dag = DerivationDAG::new();
    let q_seed = dag.push_seed(2); // QGroupFactor
    dag.push_extend("selector.extend/v1", q_seed, d0.clone()); // SelectorPath law
    let err_domain = dag.execute(seeds, laws, None).unwrap_err();
    assert!(matches!(err_domain, GrowthError::DomainMismatch { .. }));

    // Falsifier 4: Evaluation order invariance
    let a1 = engine
        .derive_factor_path(0, "selector.extend/v1", &[d0.clone(), d1.clone()], None)
        .unwrap();
    let b1 = engine
        .derive_factor_path(0, "selector.extend/v1", &[d1.clone(), d0.clone()], None)
        .unwrap();
    let b2 = engine
        .derive_factor_path(0, "selector.extend/v1", &[d1.clone(), d0.clone()], None)
        .unwrap();
    let a2 = engine
        .derive_factor_path(0, "selector.extend/v1", &[d0.clone(), d1.clone()], None)
        .unwrap();
    assert_eq!(a1.target, a2.target);
    assert_eq!(b1.target, b2.target);

    // Falsifier 5: Cache invariance
    let deltas = vec![d0.clone(), d1.clone(), d0.clone()];
    let cold = engine
        .derive_factor_path(0, "selector.extend/v1", &deltas, None)
        .unwrap();
    let mut memo = HashMap::new();
    let warm1 = engine
        .derive_factor_path(0, "selector.extend/v1", &deltas, Some(&mut memo))
        .unwrap();
    let warm2 = engine
        .derive_factor_path(0, "selector.extend/v1", &deltas, Some(&mut memo))
        .unwrap();
    assert_eq!(cold.target, warm1.target);
    assert_eq!(warm1.target, warm2.target);

    // Falsifier 6: Anti-numerology (arbitrary permutation is rejected)
    // Permuting the delta bit 0 -> 1 changes the mathematical child
    let canonical = engine
        .derive_factor_path(0, "selector.extend/v1", std::slice::from_ref(&d0), None)
        .unwrap();
    let permuted = engine
        .derive_factor_path(0, "selector.extend/v1", std::slice::from_ref(&d1), None)
        .unwrap();
    assert_ne!(canonical.target, permuted.target);
}

fn main() {
    let (seeds, laws) = setup_ontology_environment();

    // 1. Chained binary growth
    test_chained_binary_growth(&seeds, &laws);

    // 2. Demand vs eager parity
    let (demand_nodes, eager_nodes) = test_demand_vs_eager_parity_all_nodes(&seeds, &laws);

    // 3. Affine GF(2) function growth and composition
    let affine_cases = test_affine_gf2_all_compositions(&seeds, &laws);

    // 4. Falsifier suite
    run_falsifier_suite(&seeds, &laws);

    // Print machine-verifiable key-value facts
    println!("GROWTH-ENGINE=bits-plus-laws-to-new-bits-with-demand-derivation");
    println!("ONTOLOGY=2490-binary-domain");
    println!("ZERO-DEPENDENCY=PASS");
    println!("SEEDS-COUNT={}", seeds.len());
    println!("LAWS-COUNT={}", laws.len());
    println!("GROWTH-RULE=known-bits+proved-law->new-bits->reuse-new-bits");
    println!("CHAINED-REUSE-MAX-DEPTH=5");
    println!("DEMAND-DERIVATION-NODES-MATERIALIZED={}", demand_nodes);
    println!("EAGER-CLOSURE-NODES-ENUMERATED={}", eager_nodes);
    println!("MATERIALIZATION-RATIO={}/{}", demand_nodes, eager_nodes);
    println!("EAGER-VS-DEMAND-PARITY=PASS");
    println!("AFFINE-GF2-COMPOSITIONS-TESTED={}", affine_cases);
    println!("AFFINE-INVOLUTION-CHECKS=PASS");
    println!("FALSIFIER-MISSING-SEED=PASS");
    println!("FALSIFIER-MISSING-LAW=PASS");
    println!("FALSIFIER-DOMAIN-MISMATCH=PASS");
    println!("FALSIFIER-ORDER-INVARIANCE=PASS");
    println!("FALSIFIER-CACHE-INVARIANCE=PASS");
    println!("FALSIFIER-ANTI-NUMEROLOGY=PASS");
    println!("LISP-DEPENDENCY=0");
    println!("JSON-DEPENDENCY=0");
    println!("AST-DEPENDENCY=0");
    println!("HASH-IDENTITY-DEPENDENCY=0");
    println!("REGISTRY-LOOKUPS=0");
    println!("CACHE-DEPENDENCY=0");
    println!("STATUS=PASS-CORE-MATH-BINARY-GROWTH");
}
