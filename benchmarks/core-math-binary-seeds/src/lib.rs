//! Minimal Core-Math binary seeds and laws necessity tournament.
//!
//! Architecture (#2426, #2490):
//! - "Every binary seed must earn the right to exist."
//! - Remove-one test: A seed or law is independently necessary if and only if
//!   removing it strictly reduces the bounded generated capability set.
//! - Falsifier: If removing a seed or law leaves the same generated behavior,
//!   it is redundant and must be rejected from the minimal basis.
//! - Bounded capability horizon: generation is evaluated up to maximum width
//!   bounds per domain, preventing step-count artifacts.
//! - Constructor schemas and laws are charged as independent facts (#2465).
//! - Domain firewall: Seeds and laws remain strictly domain-scoped (#2508).
//! - Zero external crate dependencies.

use std::collections::BTreeSet;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Hash, PartialOrd, Ord)]
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

#[derive(Clone, Debug, Eq, PartialEq, Hash, PartialOrd, Ord)]
pub struct BinaryNumber {
    bits: Vec<u8>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum SeedError {
    Empty,
    InvalidBit,
    DeltaMustBeOneBit,
    DomainMismatch { expected: Domain, actual: Domain },
    MalformedAffineCoordinate { width: usize },
}

impl BinaryNumber {
    pub fn parse(s: &str) -> Result<Self, SeedError> {
        if s.is_empty() {
            return Err(SeedError::Empty);
        }
        let mut bits = Vec::with_capacity(s.len());
        for byte in s.bytes() {
            match byte {
                b'0' => bits.push(0),
                b'1' => bits.push(1),
                _ => return Err(SeedError::InvalidBit),
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

    pub fn append_bit(&self, bit: u8) -> Result<Self, SeedError> {
        if bit > 1 {
            return Err(SeedError::InvalidBit);
        }
        let mut out = Vec::with_capacity(self.bits.len() + 1);
        out.extend_from_slice(&self.bits);
        out.push(bit);
        Ok(Self { bits: out })
    }
}

/// A semantic object in the #2490 ontology: binary number + explicit domain.
#[derive(Clone, Debug, Eq, PartialEq, Hash, PartialOrd, Ord)]
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

    pub fn canonical_id(&self) -> String {
        format!("{}:{}", self.domain.as_str(), self.bits.bits())
    }
}

/// A candidate seed premise in the minimal basis.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Seed {
    pub id: &'static str,
    pub object: SemanticObject,
    pub description: &'static str,
}

/// Different kinds of proved mathematical laws.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum LawKind {
    /// Extension by a fixed delta bit: output = 2 * parent + delta
    FactorExtension { delta: BinaryNumber },
    /// Affine function composition in GF(2)^2: (A, b) ∘ (C, d) = (A*C, A*d XOR b)
    AffineCompose,
}

/// A proved mathematical law / schema charged as an independent fact.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Law {
    pub id: &'static str,
    pub domain: Domain,
    pub kind: LawKind,
    pub description: &'static str,
}

impl Law {
    pub fn apply(
        &self,
        primary: &SemanticObject,
        secondary: Option<&SemanticObject>,
    ) -> Result<SemanticObject, SeedError> {
        if primary.domain() != self.domain {
            return Err(SeedError::DomainMismatch {
                expected: self.domain,
                actual: primary.domain(),
            });
        }

        match &self.kind {
            LawKind::FactorExtension { delta } => {
                if delta.width() != 1 {
                    return Err(SeedError::DeltaMustBeOneBit);
                }
                let bit = delta.raw_bits()[0];
                let child_bits = primary.bits().append_bit(bit)?;
                Ok(SemanticObject::new(self.domain, child_bits))
            }
            LawKind::AffineCompose => {
                let sec = secondary.ok_or(SeedError::Empty)?;
                if sec.domain() != self.domain {
                    return Err(SeedError::DomainMismatch {
                        expected: self.domain,
                        actual: sec.domain(),
                    });
                }
                if primary.width() != 6 {
                    return Err(SeedError::MalformedAffineCoordinate {
                        width: primary.width(),
                    });
                }
                if sec.width() != 6 {
                    return Err(SeedError::MalformedAffineCoordinate {
                        width: sec.width(),
                    });
                }

                let f = primary.bits().raw_bits();
                let g = sec.bits().raw_bits();

                let a00 = f[0];
                let a01 = f[1];
                let a10 = f[2];
                let a11 = f[3];
                let b0 = f[4];
                let b1 = f[5];

                let c00 = g[0];
                let c01 = g[1];
                let c10 = g[2];
                let c11 = g[3];
                let d0 = g[4];
                let d1 = g[5];

                // A * C over GF(2)
                let ac00 = (a00 & c00) ^ (a01 & c10);
                let ac01 = (a00 & c01) ^ (a01 & c11);
                let ac10 = (a10 & c00) ^ (a11 & c10);
                let ac11 = (a10 & c01) ^ (a11 & c11);

                // A * d over GF(2)
                let ad0 = (a00 & d0) ^ (a01 & d1);
                let ad1 = (a10 & d0) ^ (a11 & d1);

                // (A * d) XOR b
                let res_b0 = ad0 ^ b0;
                let res_b1 = ad1 ^ b1;

                let comp_bits = vec![ac00, ac01, ac10, ac11, res_b0, res_b1];
                Ok(SemanticObject::new(
                    self.domain,
                    BinaryNumber::from_raw(comp_bits),
                ))
            }
        }
    }
}

/// Domain-specific width/horizon limits to bound capability closure.
#[derive(Clone, Copy, Debug)]
pub struct BoundedHorizon {
    pub max_selector_width: usize,
    pub max_qgroup_width: usize,
    pub max_affine_rounds: usize,
}

impl Default for BoundedHorizon {
    fn default() -> Self {
        Self {
            max_selector_width: 5,
            max_qgroup_width: 2,
            max_affine_rounds: 3,
        }
    }
}

/// A candidate basis under study: set of seeds + set of proved laws.
#[derive(Clone, Debug)]
pub struct Basis {
    pub seeds: Vec<Seed>,
    pub laws: Vec<Law>,
}

impl Basis {
    pub fn new(seeds: Vec<Seed>, laws: Vec<Law>) -> Self {
        Self { seeds, laws }
    }

    pub fn without_seed(&self, seed_id: &str) -> Self {
        Self {
            seeds: self.seeds.iter().filter(|s| s.id != seed_id).cloned().collect(),
            laws: self.laws.clone(),
        }
    }

    pub fn without_law(&self, law_id: &str) -> Self {
        Self {
            seeds: self.seeds.clone(),
            laws: self.laws.iter().filter(|l| l.id != law_id).cloned().collect(),
        }
    }

    /// Evaluates bounded generation across all admitted domains up to the specified horizon.
    /// Returns the set of all generated unique canonical IDs (`Domain:bits`).
    pub fn generate_closure(&self, horizon: BoundedHorizon) -> BTreeSet<String> {
        let mut out = BTreeSet::new();

        // 1. Initial layer: all seed objects within their domain horizon
        let mut current_layer: Vec<SemanticObject> = Vec::new();
        for seed in &self.seeds {
            let max_w = match seed.object.domain() {
                Domain::SelectorPath => horizon.max_selector_width,
                Domain::QGroupFactor => horizon.max_qgroup_width,
                Domain::AffineFunctionGF2 => 6,
            };
            if seed.object.width() <= max_w {
                out.insert(seed.object.canonical_id());
                current_layer.push(seed.object.clone());
            }
        }

        // 2. Factor extension laws iteration bounded by domain width limits
        let mut changed = true;
        while changed {
            changed = false;
            let mut next_layer = Vec::new();
            for obj in &current_layer {
                let max_w = match obj.domain() {
                    Domain::SelectorPath => horizon.max_selector_width,
                    Domain::QGroupFactor => horizon.max_qgroup_width,
                    Domain::AffineFunctionGF2 => 6,
                };
                if obj.width() < max_w {
                    for law in &self.laws {
                        if law.domain == obj.domain() {
                            if let LawKind::FactorExtension { .. } = law.kind {
                                if let Ok(child) = law.apply(obj, None) {
                                    if out.insert(child.canonical_id()) {
                                        next_layer.push(child);
                                        changed = true;
                                    }
                                }
                            }
                        }
                    }
                }
            }
            current_layer = next_layer;
        }

        // 3. Affine function composition closure
        let affine_laws: Vec<&Law> = self
            .laws
            .iter()
            .filter(|l| l.domain == Domain::AffineFunctionGF2 && matches!(l.kind, LawKind::AffineCompose))
            .collect();

        if !affine_laws.is_empty() {
            let mut affine_current: Vec<SemanticObject> = self
                .seeds
                .iter()
                .filter(|s| s.object.domain() == Domain::AffineFunctionGF2)
                .map(|s| s.object.clone())
                .collect();

            let mut affine_changed = true;
            let mut rounds = 0;
            while affine_changed && rounds < horizon.max_affine_rounds {
                affine_changed = false;
                rounds += 1;
                let mut new_affine = Vec::new();
                for i in 0..affine_current.len() {
                    for j in 0..affine_current.len() {
                        let f = &affine_current[i];
                        let g = &affine_current[j];
                        for law in &affine_laws {
                            if let Ok(comp) = law.apply(f, Some(g)) {
                                if out.insert(comp.canonical_id()) {
                                    new_affine.push(comp);
                                    affine_changed = true;
                                }
                            }
                        }
                    }
                }
                affine_current.extend(new_affine);
            }
        }

        out
    }
}

/// Verdict of a remove-one test for a single premise (seed or law).
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RemoveOneVerdict {
    pub premise_id: &'static str,
    pub is_seed: bool,
    pub is_strictly_necessary: bool,
    pub baseline_count: usize,
    pub reduced_count: usize,
    pub capabilities_lost: Vec<String>,
}

/// The Remove-One Necessity Tournament runner.
pub struct RemoveOneTournament {
    pub baseline_basis: Basis,
    pub horizon: BoundedHorizon,
}

impl RemoveOneTournament {
    pub fn new(baseline_basis: Basis, horizon: BoundedHorizon) -> Self {
        Self {
            baseline_basis,
            horizon,
        }
    }

    /// Evaluates the remove-one test across every seed and law in the baseline basis.
    pub fn run(&self) -> Vec<RemoveOneVerdict> {
        let baseline_closure = self.baseline_basis.generate_closure(self.horizon);
        let baseline_count = baseline_closure.len();

        let mut verdicts = Vec::new();

        // 1. Remove-one for each seed
        for seed in &self.baseline_basis.seeds {
            let reduced_basis = self.baseline_basis.without_seed(seed.id);
            let reduced_closure = reduced_basis.generate_closure(self.horizon);

            let capabilities_lost: Vec<String> = baseline_closure
                .difference(&reduced_closure)
                .cloned()
                .collect();

            let is_strictly_necessary = !capabilities_lost.is_empty();

            verdicts.push(RemoveOneVerdict {
                premise_id: seed.id,
                is_seed: true,
                is_strictly_necessary,
                baseline_count,
                reduced_count: reduced_closure.len(),
                capabilities_lost,
            });
        }

        // 2. Remove-one for each law
        for law in &self.baseline_basis.laws {
            let reduced_basis = self.baseline_basis.without_law(law.id);
            let reduced_closure = reduced_basis.generate_closure(self.horizon);

            let capabilities_lost: Vec<String> = baseline_closure
                .difference(&reduced_closure)
                .cloned()
                .collect();

            let is_strictly_necessary = !capabilities_lost.is_empty();

            verdicts.push(RemoveOneVerdict {
                premise_id: law.id,
                is_seed: false,
                is_strictly_necessary,
                baseline_count,
                reduced_count: reduced_closure.len(),
                capabilities_lost,
            });
        }

        verdicts
    }

    /// Tests a candidate redundant seed:
    /// Injects `candidate_seed` into the basis and tests whether removing it causes capability loss.
    /// If `candidate_seed` is redundant, removing it loses 0 capabilities.
    pub fn test_redundant_seed_falsifier(&self, candidate_seed: Seed) -> RemoveOneVerdict {
        let mut candidate_seeds = self.baseline_basis.seeds.clone();
        candidate_seeds.push(candidate_seed.clone());
        let candidate_basis = Basis::new(candidate_seeds, self.baseline_basis.laws.clone());

        let candidate_closure = candidate_basis.generate_closure(self.horizon);
        let baseline_closure = self.baseline_basis.generate_closure(self.horizon);

        // Capabilities lost when removing candidate_seed from (baseline + candidate_seed)
        let capabilities_lost: Vec<String> = candidate_closure
            .difference(&baseline_closure)
            .cloned()
            .collect();

        let is_strictly_necessary = !capabilities_lost.is_empty();

        RemoveOneVerdict {
            premise_id: candidate_seed.id,
            is_seed: true,
            is_strictly_necessary,
            baseline_count: candidate_closure.len(),
            reduced_count: baseline_closure.len(),
            capabilities_lost,
        }
    }
}

/// Constructs the canonical minimal baseline basis under #2490 / #2426.
/// Notice: Identity (100100) is derived via Inversion^2 and Swap^2, so it is
/// NOT an axiomatic seed! Retaining only Inversion and Swap keeps the basis minimal.
pub fn canonical_baseline_basis() -> Basis {
    let seeds = vec![
        // QGroupFactor roots (#2494)
        Seed {
            id: "seed.qgroup.additive_root",
            object: SemanticObject::new(
                Domain::QGroupFactor,
                BinaryNumber::parse("0").unwrap(),
            ),
            description: "Additive family root premise",
        },
        Seed {
            id: "seed.qgroup.multiplicative_root",
            object: SemanticObject::new(
                Domain::QGroupFactor,
                BinaryNumber::parse("1").unwrap(),
            ),
            description: "Multiplicative family root premise",
        },
        // SelectorPath roots (#2485)
        Seed {
            id: "seed.selector.first_root",
            object: SemanticObject::new(
                Domain::SelectorPath,
                BinaryNumber::parse("101").unwrap(),
            ),
            description: "First selector root premise (CAR)",
        },
        Seed {
            id: "seed.selector.rest_root",
            object: SemanticObject::new(
                Domain::SelectorPath,
                BinaryNumber::parse("110").unwrap(),
            ),
            description: "Rest selector root premise (CDR)",
        },
        // AffineFunctionGF2 seeds (#2319)
        // Inversion: A=[[1,0],[0,1]], b=[1,1] -> 100111
        Seed {
            id: "seed.affine.inversion",
            object: SemanticObject::new(
                Domain::AffineFunctionGF2,
                BinaryNumber::parse("100111").unwrap(),
            ),
            description: "Bitwise NOT coordinate (I, [1,1])",
        },
        // Swap: A=[[0,1],[1,0]], b=[0,0] -> 011000
        Seed {
            id: "seed.affine.swap",
            object: SemanticObject::new(
                Domain::AffineFunctionGF2,
                BinaryNumber::parse("011000").unwrap(),
            ),
            description: "Coordinate transposition (Swap, 0)",
        },
    ];

    let laws = vec![
        // QGroupFactor role laws (#2494)
        Law {
            id: "law.qgroup.inverse_role",
            domain: Domain::QGroupFactor,
            kind: LawKind::FactorExtension {
                delta: BinaryNumber::parse("0").unwrap(),
            },
            description: "Inverse role delta 0 (NEG / RECIP)",
        },
        Law {
            id: "law.qgroup.quotient_role",
            domain: Domain::QGroupFactor,
            kind: LawKind::FactorExtension {
                delta: BinaryNumber::parse("1").unwrap(),
            },
            description: "Quotient role delta 1 (SUB / DIV)",
        },
        // SelectorPath extension laws (#2485)
        Law {
            id: "law.selector.extend_zero",
            domain: Domain::SelectorPath,
            kind: LawKind::FactorExtension {
                delta: BinaryNumber::parse("0").unwrap(),
            },
            description: "First projection extension delta 0",
        },
        Law {
            id: "law.selector.extend_one",
            domain: Domain::SelectorPath,
            kind: LawKind::FactorExtension {
                delta: BinaryNumber::parse("1").unwrap(),
            },
            description: "Rest projection extension delta 1",
        },
        // AffineFunctionGF2 composition law (#2319)
        Law {
            id: "law.affine.composition",
            domain: Domain::AffineFunctionGF2,
            kind: LawKind::AffineCompose,
            description: "Affine composition schema (A*C, A*d XOR b)",
        },
    ];

    Basis::new(seeds, laws)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_all_canonical_seeds_and_laws_earn_existence() {
        let basis = canonical_baseline_basis();
        let tournament = RemoveOneTournament::new(basis, BoundedHorizon::default());
        let verdicts = tournament.run();

        // 6 seeds + 5 laws = 11 premises total
        assert_eq!(verdicts.len(), 11);

        // Every single baseline premise MUST be strictly necessary!
        for v in &verdicts {
            assert!(
                v.is_strictly_necessary,
                "Premise {} failed to earn its right to exist!",
                v.premise_id
            );
            assert!(
                !v.capabilities_lost.is_empty(),
                "Premise {} must cause capability loss on removal",
                v.premise_id
            );
            assert!(
                v.reduced_count < v.baseline_count,
                "Premise {} must strictly reduce baseline count",
                v.premise_id
            );
        }
    }

    #[test]
    fn test_falsifier_detects_redundant_derivable_child_seed() {
        let basis = canonical_baseline_basis();
        let tournament = RemoveOneTournament::new(basis, BoundedHorizon::default());

        // Candidate redundant seed: 1010 in SelectorPath.
        // It can already be derived from seed.selector.first_root (101) + law.selector.extend_zero (0).
        let redundant = Seed {
            id: "seed.selector.redundant_child",
            object: SemanticObject::new(
                Domain::SelectorPath,
                BinaryNumber::parse("1010").unwrap(),
            ),
            description: "Derivable child falsely claimed as seed",
        };

        let verdict = tournament.test_redundant_seed_falsifier(redundant);

        // Redundant seed must NOT be necessary (capabilities_lost is empty)
        assert!(
            !verdict.is_strictly_necessary,
            "Derivable child seed must be caught and rejected as non-minimal"
        );
        assert_eq!(verdict.capabilities_lost.len(), 0);
        assert_eq!(verdict.baseline_count, verdict.reduced_count);
    }

    #[test]
    fn test_falsifier_detects_redundant_affine_identity_seed() {
        let basis = canonical_baseline_basis();
        let tournament = RemoveOneTournament::new(basis, BoundedHorizon::default());

        // Candidate redundant seed: Identity 100100.
        // It can already be derived from Inversion ∘ Inversion = 100100 or Swap ∘ Swap = 100100.
        let redundant_identity = Seed {
            id: "seed.affine.redundant_identity",
            object: SemanticObject::new(
                Domain::AffineFunctionGF2,
                BinaryNumber::parse("100100").unwrap(),
            ),
            description: "Identity coordinate derived via Inversion^2, falsely claimed as seed",
        };

        let verdict = tournament.test_redundant_seed_falsifier(redundant_identity);

        // Identity seed must NOT be necessary because Inversion ∘ Inversion already generates it!
        assert!(
            !verdict.is_strictly_necessary,
            "Identity must be caught as a derived theorem, not an irreducible seed"
        );
        assert_eq!(verdict.capabilities_lost.len(), 0);
        assert_eq!(verdict.baseline_count, verdict.reduced_count);
    }

    #[test]
    fn test_qgroup_root_removal_collapses_factors() {
        let basis = canonical_baseline_basis();
        let tournament = RemoveOneTournament::new(basis, BoundedHorizon::default());
        let verdicts = tournament.run();

        // Removing additive root (0) loses NEG (00) and SUB (01)
        let add_verdict = verdicts
            .iter()
            .find(|v| v.premise_id == "seed.qgroup.additive_root")
            .unwrap();
        assert!(add_verdict.capabilities_lost.contains(&"QGroupFactor:00".to_string()));
        assert!(add_verdict.capabilities_lost.contains(&"QGroupFactor:01".to_string()));

        // Removing multiplicative root (1) loses RECIP (10) and DIV (11)
        let mul_verdict = verdicts
            .iter()
            .find(|v| v.premise_id == "seed.qgroup.multiplicative_root")
            .unwrap();
        assert!(mul_verdict.capabilities_lost.contains(&"QGroupFactor:10".to_string()));
        assert!(mul_verdict.capabilities_lost.contains(&"QGroupFactor:11".to_string()));
    }

    #[test]
    fn test_affine_seed_removal_collapses_subgroup() {
        let basis = canonical_baseline_basis();
        let tournament = RemoveOneTournament::new(basis, BoundedHorizon::default());
        let verdicts = tournament.run();

        // Removing Inversion (100111) loses the NOT coordinate and composite transforms
        let inv_verdict = verdicts
            .iter()
            .find(|v| v.premise_id == "seed.affine.inversion")
            .unwrap();
        assert!(inv_verdict.capabilities_lost.contains(&"AffineFunctionGF2:100111".to_string()));

        // Removing Swap (011000) loses coordinate transposition
        let swap_verdict = verdicts
            .iter()
            .find(|v| v.premise_id == "seed.affine.swap")
            .unwrap();
        assert!(swap_verdict.capabilities_lost.contains(&"AffineFunctionGF2:011000".to_string()));
    }
}
