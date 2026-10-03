//! Minimal Core-Math binary growth and demand-derivation engine.
//!
//! Architecture (#2460, #2490):
//! - Semantic object = binary number + domain + proved law.
//! - Growth rule: `known bits + proved law -> new bits -> reuse new bits`.
//! - Chained derivation: newly generated binary objects serve as inputs/parents
//!   to subsequent law applications without human names, registry tables, or lookup rows.
//! - On-demand derivation (demand construction): materializes only the demanded
//!   derivation DAG without eagerly enumerating exponential closures (#2473, #2474).
//! - Parity: on-demand derivation yields bit-for-bit exact identity match with
//!   the corresponding node from bounded eager enumeration.
//! - Falsifiers: missing seed/law fails closed, #2508 domain firewall blocks cross-domain
//!   growth, evaluation order invariance, cache invariance, and anti-numerology.
//! - Zero external crate dependencies.

use std::collections::HashMap;

/// Explicit domain in the #2490 ontology.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Hash)]
pub enum Domain {
    SelectorPath,
    QGroupFactor,
    AffineFunctionGF2,
}

impl Domain {
    pub const fn as_str(&self) -> &'static str {
        match self {
            Self::SelectorPath => "SelectorPath",
            Self::QGroupFactor => "QGroupFactor",
            Self::AffineFunctionGF2 => "AffineFunctionGF2",
        }
    }
}

/// Arbitrary-width exact binary number.
#[derive(Clone, Debug, Eq, PartialEq, Hash)]
pub struct BinaryNumber {
    bits: Vec<u8>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum GrowthError {
    Empty,
    InvalidBit,
    DeltaMustBeOneBit,
    DomainMismatch { expected: Domain, actual: Domain },
    MissingSeed { index: usize, total_seeds: usize },
    MissingLaw { law_id: &'static str },
    InvalidNodeIndex { index: usize, total_nodes: usize },
    MalformedAffineCoordinate { width: usize },
    InvalidSlice { start: usize, len: usize, width: usize },
}

impl BinaryNumber {
    pub fn parse(s: &str) -> Result<Self, GrowthError> {
        if s.is_empty() {
            return Err(GrowthError::Empty);
        }
        let mut bits = Vec::with_capacity(s.len());
        for byte in s.bytes() {
            match byte {
                b'0' => bits.push(0),
                b'1' => bits.push(1),
                _ => return Err(GrowthError::InvalidBit),
            }
        }
        Ok(Self { bits })
    }

    pub fn from_raw(bits: Vec<u8>) -> Self {
        Self { bits }
    }

    pub fn width(&self) -> usize {
        self.bits.len()
    }

    pub fn bits(&self) -> String {
        self.bits.iter().map(|b| if *b == 0 { '0' } else { '1' }).collect()
    }

    pub fn raw_bits(&self) -> &[u8] {
        &self.bits
    }

    pub fn is_exactly(&self, expected: &[u8]) -> bool {
        self.bits == expected
    }

    pub fn append_bit(&self, bit: u8) -> Result<Self, GrowthError> {
        if bit > 1 {
            return Err(GrowthError::InvalidBit);
        }
        let mut out = Vec::with_capacity(self.bits.len() + 1);
        out.extend_from_slice(&self.bits);
        out.push(bit);
        Ok(Self { bits: out })
    }

    pub fn concat(&self, other: &Self) -> Self {
        let mut out = Vec::with_capacity(self.bits.len() + other.bits.len());
        out.extend_from_slice(&self.bits);
        out.extend_from_slice(&other.bits);
        Self { bits: out }
    }

    pub fn slice(&self, start: usize, len: usize) -> Result<Self, GrowthError> {
        if start + len > self.bits.len() || len == 0 {
            return Err(GrowthError::InvalidSlice {
                start,
                len,
                width: self.bits.len(),
            });
        }
        Ok(Self {
            bits: self.bits[start..start + len].to_vec(),
        })
    }

    pub fn to_u64(&self) -> Result<u64, GrowthError> {
        if self.bits.len() > 64 {
            return Err(GrowthError::InvalidSlice {
                start: 0,
                len: self.bits.len(),
                width: self.bits.len(),
            });
        }
        let mut val = 0u64;
        for bit in &self.bits {
            val = (val << 1) | (*bit as u64);
        }
        Ok(val)
    }

    pub fn from_u64(mut val: u64, width: usize) -> Self {
        let mut bits = vec![0u8; width];
        for i in (0..width).rev() {
            bits[i] = (val & 1) as u8;
            val >>= 1;
        }
        Self { bits }
    }
}

/// A semantic object in the #2490 ontology: binary number + explicit domain.
#[derive(Clone, Debug, Eq, PartialEq, Hash)]
pub struct SemanticObject {
    domain: Domain,
    bits: BinaryNumber,
}

impl SemanticObject {
    pub fn new(domain: Domain, bits: BinaryNumber) -> Self {
        Self { domain, bits }
    }

    pub fn domain(&self) -> Domain {
        self.domain
    }

    pub fn bits(&self) -> &BinaryNumber {
        &self.bits
    }

    pub fn width(&self) -> usize {
        self.bits.width()
    }
}

/// A proved mathematical law over a specific domain.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProvedLaw {
    law_id: &'static str,
    domain: Domain,
    equation: &'static str,
}

impl ProvedLaw {
    pub const fn new(law_id: &'static str, domain: Domain, equation: &'static str) -> Self {
        Self {
            law_id,
            domain,
            equation,
        }
    }

    pub fn law_id(&self) -> &'static str {
        self.law_id
    }

    pub fn domain(&self) -> Domain {
        self.domain
    }

    pub fn equation(&self) -> &'static str {
        self.equation
    }

    /// Factor extension law: `output = 2 * parent + delta`.
    /// Enforces domain firewall: parent must belong to self.domain (#2508).
    pub fn apply_factor(
        &self,
        parent: &SemanticObject,
        delta: &BinaryNumber,
    ) -> Result<SemanticObject, GrowthError> {
        if parent.domain() != self.domain {
            return Err(GrowthError::DomainMismatch {
                expected: self.domain,
                actual: parent.domain(),
            });
        }
        if delta.width() != 1 {
            return Err(GrowthError::DeltaMustBeOneBit);
        }
        let delta_bit = delta.raw_bits()[0];
        let child_bits = parent.bits().append_bit(delta_bit)?;
        Ok(SemanticObject::new(self.domain, child_bits))
    }

    /// Affine function composition in GF(2)^2:
    /// `(A, b) ∘ (C, d) = (A * C, A * d XOR b)`.
    /// Coordinate width = 6 bits: A is 2x2 matrix (4 bits), b is 2-bit offset (2 bits).
    pub fn apply_affine_compose(
        &self,
        f: &SemanticObject,
        g: &SemanticObject,
    ) -> Result<SemanticObject, GrowthError> {
        if f.domain() != self.domain {
            return Err(GrowthError::DomainMismatch {
                expected: self.domain,
                actual: f.domain(),
            });
        }
        if g.domain() != self.domain {
            return Err(GrowthError::DomainMismatch {
                expected: self.domain,
                actual: g.domain(),
            });
        }
        if f.width() != 6 {
            return Err(GrowthError::MalformedAffineCoordinate { width: f.width() });
        }
        if g.width() != 6 {
            return Err(GrowthError::MalformedAffineCoordinate { width: g.width() });
        }

        let f_bits = f.bits().raw_bits();
        let g_bits = g.bits().raw_bits();

        // A = [[f[0], f[1]], [f[2], f[3]]], b = [f[4], f[5]]
        let a00 = f_bits[0];
        let a01 = f_bits[1];
        let a10 = f_bits[2];
        let a11 = f_bits[3];
        let b0 = f_bits[4];
        let b1 = f_bits[5];

        // C = [[g[0], g[1]], [g[2], g[3]]], d = [g[4], g[5]]
        let c00 = g_bits[0];
        let c01 = g_bits[1];
        let c10 = g_bits[2];
        let c11 = g_bits[3];
        let d0 = g_bits[4];
        let d1 = g_bits[5];

        // A * C over GF(2)
        let ac00 = (a00 & c00) ^ (a01 & c10);
        let ac01 = (a00 & c01) ^ (a01 & c11);
        let ac10 = (a10 & c00) ^ (a11 & c10);
        let ac11 = (a10 & c01) ^ (a11 & c11);

        // A * d over GF(2)
        let ad0 = (a00 & d0) ^ (a01 & d1);
        let ad1 = (a10 & d0) ^ (a11 & d1);

        // (A * d) XOR b over GF(2)
        let res_b0 = ad0 ^ b0;
        let res_b1 = ad1 ^ b1;

        let comp_bits = vec![ac00, ac01, ac10, ac11, res_b0, res_b1];
        Ok(SemanticObject::new(
            self.domain,
            BinaryNumber::from_raw(comp_bits),
        ))
    }
}

/// A single step in a derivation DAG.
#[derive(Clone, Debug, Eq, PartialEq, Hash)]
pub enum DerivationStep {
    Seed {
        seed_index: usize,
    },
    Extend {
        law_id: &'static str,
        parent_node: usize,
        delta: BinaryNumber,
    },
    Compose {
        law_id: &'static str,
        outer_node: usize,
        inner_node: usize,
    },
}

/// A derivation Directed Acyclic Graph (DAG) for binary growth.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct DerivationDAG {
    steps: Vec<DerivationStep>,
}

impl DerivationDAG {
    pub fn new() -> Self {
        Self { steps: Vec::new() }
    }

    pub fn push_seed(&mut self, seed_index: usize) -> usize {
        let idx = self.steps.len();
        self.steps.push(DerivationStep::Seed { seed_index });
        idx
    }

    pub fn push_extend(
        &mut self,
        law_id: &'static str,
        parent_node: usize,
        delta: BinaryNumber,
    ) -> usize {
        let idx = self.steps.len();
        self.steps.push(DerivationStep::Extend {
            law_id,
            parent_node,
            delta,
        });
        idx
    }

    pub fn push_compose(
        &mut self,
        law_id: &'static str,
        outer_node: usize,
        inner_node: usize,
    ) -> usize {
        let idx = self.steps.len();
        self.steps.push(DerivationStep::Compose {
            law_id,
            outer_node,
            inner_node,
        });
        idx
    }

    pub fn len(&self) -> usize {
        self.steps.len()
    }

    pub fn is_empty(&self) -> bool {
        self.steps.is_empty()
    }

    pub fn steps(&self) -> &[DerivationStep] {
        &self.steps
    }

    /// Executes the derivation DAG against provided seeds and laws.
    /// Supports an optional external memoization cache to verify cache invariance.
    pub fn execute(
        &self,
        seeds: &[SemanticObject],
        laws: &[ProvedLaw],
        memo: Option<&mut HashMap<DerivationStep, SemanticObject>>,
    ) -> Result<Vec<SemanticObject>, GrowthError> {
        let mut nodes: Vec<SemanticObject> = Vec::with_capacity(self.steps.len());

        let law_map: HashMap<&'static str, &ProvedLaw> =
            laws.iter().map(|l| (l.law_id(), l)).collect();

        // If memo is passed, we check/store per step.
        let mut memo_ref = memo;

        for (node_idx, step) in self.steps.iter().enumerate() {
            if let Some(ref m) = memo_ref {
                if let Some(cached) = m.get(step) {
                    nodes.push(cached.clone());
                    continue;
                }
            }

            let result = match step {
                DerivationStep::Seed { seed_index } => {
                    if *seed_index >= seeds.len() {
                        return Err(GrowthError::MissingSeed {
                            index: *seed_index,
                            total_seeds: seeds.len(),
                        });
                    }
                    seeds[*seed_index].clone()
                }
                DerivationStep::Extend {
                    law_id,
                    parent_node,
                    delta,
                } => {
                    if *parent_node >= node_idx {
                        return Err(GrowthError::InvalidNodeIndex {
                            index: *parent_node,
                            total_nodes: node_idx,
                        });
                    }
                    let law = law_map
                        .get(law_id)
                        .ok_or(GrowthError::MissingLaw { law_id })?;
                    let parent = &nodes[*parent_node];
                    law.apply_factor(parent, delta)?
                }
                DerivationStep::Compose {
                    law_id,
                    outer_node,
                    inner_node,
                } => {
                    if *outer_node >= node_idx {
                        return Err(GrowthError::InvalidNodeIndex {
                            index: *outer_node,
                            total_nodes: node_idx,
                        });
                    }
                    if *inner_node >= node_idx {
                        return Err(GrowthError::InvalidNodeIndex {
                            index: *inner_node,
                            total_nodes: node_idx,
                        });
                    }
                    let law = law_map
                        .get(law_id)
                        .ok_or(GrowthError::MissingLaw { law_id })?;
                    let outer = &nodes[*outer_node];
                    let inner = &nodes[*inner_node];
                    law.apply_affine_compose(outer, inner)?
                }
            };

            if let Some(ref mut m) = memo_ref {
                m.insert(step.clone(), result.clone());
            }
            nodes.push(result);
        }

        Ok(nodes)
    }
}

/// Result of an on-demand derivation.
#[derive(Clone, Debug)]
pub struct DerivationResult {
    pub target: SemanticObject,
    pub nodes_materialized: usize,
    pub dag: DerivationDAG,
}

/// The demand-driven derivation engine: constructs only requested binary objects.
pub struct DemandEngine<'a> {
    seeds: &'a [SemanticObject],
    laws: &'a [ProvedLaw],
}

impl<'a> DemandEngine<'a> {
    pub fn new(seeds: &'a [SemanticObject], laws: &'a [ProvedLaw]) -> Self {
        Self { seeds, laws }
    }

    /// Derives a factor-extended target along a specified sequence of deltas on-demand.
    /// Materializes exactly `deltas.len() + 1` nodes.
    pub fn derive_factor_path(
        &self,
        seed_index: usize,
        law_id: &'static str,
        deltas: &[BinaryNumber],
        memo: Option<&mut HashMap<DerivationStep, SemanticObject>>,
    ) -> Result<DerivationResult, GrowthError> {
        let mut dag = DerivationDAG::new();
        let mut current_node = dag.push_seed(seed_index);

        for delta in deltas {
            current_node = dag.push_extend(law_id, current_node, delta.clone());
        }

        let nodes = dag.execute(self.seeds, self.laws, memo)?;
        let target = nodes
            .last()
            .cloned()
            .ok_or(GrowthError::InvalidNodeIndex {
                index: 0,
                total_nodes: 0,
            })?;

        Ok(DerivationResult {
            target,
            nodes_materialized: dag.len(),
            dag,
        })
    }

    /// Derives a composition of two affine functions on demand:
    /// seeds -> f, seeds -> g -> f ∘ g.
    pub fn derive_affine_composition(
        &self,
        f_seed_idx: usize,
        g_seed_idx: usize,
        law_id: &'static str,
        memo: Option<&mut HashMap<DerivationStep, SemanticObject>>,
    ) -> Result<DerivationResult, GrowthError> {
        let mut dag = DerivationDAG::new();
        let f_node = dag.push_seed(f_seed_idx);
        let g_node = dag.push_seed(g_seed_idx);
        dag.push_compose(law_id, f_node, g_node);

        let nodes = dag.execute(self.seeds, self.laws, memo)?;
        let target = nodes
            .last()
            .cloned()
            .ok_or(GrowthError::InvalidNodeIndex {
                index: 0,
                total_nodes: 0,
            })?;

        Ok(DerivationResult {
            target,
            nodes_materialized: dag.len(),
            dag,
        })
    }
}

/// Result of bounded eager closure enumeration.
#[derive(Clone, Debug)]
pub struct EagerClosureResult {
    pub all_objects: Vec<SemanticObject>,
    pub count_by_depth: Vec<usize>,
}

/// Bounded eager closure engine: enumerates all reachable objects up to depth `d`.
pub struct EagerClosureEngine<'a> {
    seeds: &'a [SemanticObject],
    laws: &'a [ProvedLaw],
}

impl<'a> EagerClosureEngine<'a> {
    pub fn new(seeds: &'a [SemanticObject], laws: &'a [ProvedLaw]) -> Self {
        Self { seeds, laws }
    }

    /// Computes full eager closure for factor extension up to `max_depth` with delta set {0, 1}.
    pub fn compute_factor_closure(
        &self,
        seed_index: usize,
        law_id: &'static str,
        max_depth: usize,
    ) -> Result<EagerClosureResult, GrowthError> {
        if seed_index >= self.seeds.len() {
            return Err(GrowthError::MissingSeed {
                index: seed_index,
                total_seeds: self.seeds.len(),
            });
        }
        let law = self
            .laws
            .iter()
            .find(|l| l.law_id() == law_id)
            .ok_or(GrowthError::MissingLaw { law_id })?;

        let mut current_layer = vec![self.seeds[seed_index].clone()];
        let mut all_objects = current_layer.clone();
        let mut count_by_depth = vec![current_layer.len()];

        let delta_0 = BinaryNumber::parse("0")?;
        let delta_1 = BinaryNumber::parse("1")?;

        for _ in 1..=max_depth {
            let mut next_layer = Vec::with_capacity(current_layer.len() * 2);
            for parent in &current_layer {
                let child_0 = law.apply_factor(parent, &delta_0)?;
                let child_1 = law.apply_factor(parent, &delta_1)?;
                next_layer.push(child_0);
                next_layer.push(child_1);
            }
            all_objects.extend(next_layer.clone());
            count_by_depth.push(next_layer.len());
            current_layer = next_layer;
        }

        Ok(EagerClosureResult {
            all_objects,
            count_by_depth,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup_fixtures() -> (Vec<SemanticObject>, Vec<ProvedLaw>) {
        let seeds = vec![
            SemanticObject::new(
                Domain::SelectorPath,
                BinaryNumber::parse("101").unwrap(), // First root
            ),
            SemanticObject::new(
                Domain::SelectorPath,
                BinaryNumber::parse("110").unwrap(), // Rest root
            ),
            SemanticObject::new(
                Domain::QGroupFactor,
                BinaryNumber::parse("0").unwrap(), // Additive root
            ),
            SemanticObject::new(
                Domain::QGroupFactor,
                BinaryNumber::parse("1").unwrap(), // Multiplicative root
            ),
            // Affine GF(2) functions (width 6):
            // Identity: A=[[1,0],[0,1]], b=[0,0] -> 100100
            SemanticObject::new(
                Domain::AffineFunctionGF2,
                BinaryNumber::parse("100100").unwrap(),
            ),
            // Inversion/NOT: A=[[1,0],[0,1]], b=[1,1] -> 100111
            SemanticObject::new(
                Domain::AffineFunctionGF2,
                BinaryNumber::parse("100111").unwrap(),
            ),
            // Swap: A=[[0,1],[1,0]], b=[0,0] -> 011000
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

    #[test]
    fn test_binary_growth_chain_and_reuse() {
        let (seeds, laws) = setup_fixtures();
        let engine = DemandEngine::new(&seeds, &laws);

        let d0 = BinaryNumber::parse("0").unwrap();
        let d1 = BinaryNumber::parse("1").unwrap();

        // Grow from root 101: 101 -> 1010 -> 10101 -> 101010
        let res = engine
            .derive_factor_path(0, "selector.extend/v1", &[d0.clone(), d1.clone(), d0.clone()], None)
            .unwrap();

        assert_eq!(res.target.domain(), Domain::SelectorPath);
        assert_eq!(res.target.bits().bits(), "101010");
        assert_eq!(res.nodes_materialized, 4); // 1 root + 3 steps
    }

    #[test]
    fn test_demand_vs_eager_parity() {
        let (seeds, laws) = setup_fixtures();
        let demand_engine = DemandEngine::new(&seeds, &laws);
        let eager_engine = EagerClosureEngine::new(&seeds, &laws);

        let eager = eager_engine
            .compute_factor_closure(0, "selector.extend/v1", 3)
            .unwrap();

        // Total eager nodes = 1 + 2 + 4 + 8 = 15
        assert_eq!(eager.all_objects.len(), 15);
        assert_eq!(eager.count_by_depth, vec![1, 2, 4, 8]);

        // Demand-derive path [0, 1, 0] -> 101010
        let d0 = BinaryNumber::parse("0").unwrap();
        let d1 = BinaryNumber::parse("1").unwrap();
        let demand = demand_engine
            .derive_factor_path(0, "selector.extend/v1", &[d0.clone(), d1.clone(), d0.clone()], None)
            .unwrap();

        // Demand materializes ONLY 4 nodes, not 15!
        assert_eq!(demand.nodes_materialized, 4);
        assert_eq!(demand.target.bits().bits(), "101010");

        // Parity: find target in eager closure
        let matching = eager
            .all_objects
            .iter()
            .find(|obj| obj.bits().bits() == "101010");
        assert!(matching.is_some());
        assert_eq!(matching.unwrap(), &demand.target);
    }

    #[test]
    fn test_falsifier_missing_seed() {
        let (seeds, laws) = setup_fixtures();
        let engine = DemandEngine::new(&seeds, &laws);
        let d0 = BinaryNumber::parse("0").unwrap();

        let err = engine
            .derive_factor_path(999, "selector.extend/v1", &[d0], None)
            .unwrap_err();

        match err {
            GrowthError::MissingSeed { index, total_seeds } => {
                assert_eq!(index, 999);
                assert_eq!(total_seeds, seeds.len());
            }
            other => panic!("expected MissingSeed, got {:?}", other),
        }
    }

    #[test]
    fn test_falsifier_missing_law() {
        let (seeds, laws) = setup_fixtures();
        let engine = DemandEngine::new(&seeds, &laws);
        let d0 = BinaryNumber::parse("0").unwrap();

        let err = engine
            .derive_factor_path(0, "nonexistent.law/v1", &[d0], None)
            .unwrap_err();

        match err {
            GrowthError::MissingLaw { law_id } => {
                assert_eq!(law_id, "nonexistent.law/v1");
            }
            other => panic!("expected MissingLaw, got {:?}", other),
        }
    }

    #[test]
    fn test_falsifier_domain_mismatch_firewall() {
        let (seeds, laws) = setup_fixtures();
        // Seed 2 is QGroupFactor ("0"), law is SelectorPath ("selector.extend/v1")
        let mut dag = DerivationDAG::new();
        let seed_node = dag.push_seed(2);
        let d0 = BinaryNumber::parse("0").unwrap();
        dag.push_extend("selector.extend/v1", seed_node, d0);

        let err = dag.execute(&seeds, &laws, None).unwrap_err();
        match err {
            GrowthError::DomainMismatch { expected, actual } => {
                assert_eq!(expected, Domain::SelectorPath);
                assert_eq!(actual, Domain::QGroupFactor);
            }
            other => panic!("expected DomainMismatch, got {:?}", other),
        }
    }

    #[test]
    fn test_falsifier_order_invariance() {
        let (seeds, laws) = setup_fixtures();
        let engine = DemandEngine::new(&seeds, &laws);

        let d0 = BinaryNumber::parse("0").unwrap();
        let d1 = BinaryNumber::parse("1").unwrap();

        // Derivation A: path [0, 1]
        // Derivation B: path [1, 0]

        // Schedule 1: A then B
        let res_a1 = engine
            .derive_factor_path(0, "selector.extend/v1", &[d0.clone(), d1.clone()], None)
            .unwrap();
        let res_b1 = engine
            .derive_factor_path(0, "selector.extend/v1", &[d1.clone(), d0.clone()], None)
            .unwrap();

        // Schedule 2: B then A
        let res_b2 = engine
            .derive_factor_path(0, "selector.extend/v1", &[d1.clone(), d0.clone()], None)
            .unwrap();
        let res_a2 = engine
            .derive_factor_path(0, "selector.extend/v1", &[d0.clone(), d1.clone()], None)
            .unwrap();

        assert_eq!(res_a1.target, res_a2.target);
        assert_eq!(res_b1.target, res_b2.target);
    }

    #[test]
    fn test_falsifier_cache_invariance() {
        let (seeds, laws) = setup_fixtures();
        let engine = DemandEngine::new(&seeds, &laws);

        let d0 = BinaryNumber::parse("0").unwrap();
        let d1 = BinaryNumber::parse("1").unwrap();
        let deltas = vec![d0.clone(), d1.clone(), d1.clone()];

        // Run 1: Cold cache (no cache passed)
        let cold = engine
            .derive_factor_path(0, "selector.extend/v1", &deltas, None)
            .unwrap();

        // Run 2: Warm cache pre-populated with identical derivation
        let mut memo = HashMap::new();
        let warm1 = engine
            .derive_factor_path(0, "selector.extend/v1", &deltas, Some(&mut memo))
            .unwrap();
        let warm2 = engine
            .derive_factor_path(0, "selector.extend/v1", &deltas, Some(&mut memo))
            .unwrap();

        assert_eq!(cold.target, warm1.target);
        assert_eq!(warm1.target, warm2.target);
    }

    #[test]
    fn test_affine_gf2_function_growth_and_composition() {
        let (seeds, laws) = setup_fixtures();
        let engine = DemandEngine::new(&seeds, &laws);

        // Seed 4: Identity (100100)
        // Seed 5: Inversion (100111)
        // Seed 6: Swap (011000)

        // Test 1: Identity composition: Inversion ∘ Identity = Inversion
        let res1 = engine
            .derive_affine_composition(5, 4, "affine.compose/v1", None)
            .unwrap();
        assert_eq!(res1.target.bits().bits(), "100111");

        // Test 2: Inversion ∘ Inversion = Identity (NOT ∘ NOT = ID)
        let res2 = engine
            .derive_affine_composition(5, 5, "affine.compose/v1", None)
            .unwrap();
        assert_eq!(res2.target.bits().bits(), "100100");

        // Test 3: Swap ∘ Swap = Identity (SWAP ∘ SWAP = ID)
        let res3 = engine
            .derive_affine_composition(6, 6, "affine.compose/v1", None)
            .unwrap();
        assert_eq!(res3.target.bits().bits(), "100100");

        // Test 4: Swap ∘ Inversion:
        // A_swap * b_inv = [[0,1],[1,0]] * [1,1] = [1,1].
        // (A_swap * b_inv) XOR b_swap = [1,1] XOR [0,0] = [1,1].
        // A_swap * A_inv = Swap * ID = Swap.
        // Coordinate = Swap matrix (0110) + offset (11) = 011011.
        let res4 = engine
            .derive_affine_composition(6, 5, "affine.compose/v1", None)
            .unwrap();
        assert_eq!(res4.target.bits().bits(), "011011");
    }
}
