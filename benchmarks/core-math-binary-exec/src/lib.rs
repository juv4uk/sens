//! Minimal Core-Math binary executor.
//!
//! Semantic core: exact-width binary input + declared domain + admitted mathematical law
//! yields exact-width binary output in that domain (#2485, #2490).
//!
//! Key principles:
//! - Semantic object = binary number + domain + proved law.
//! - Same bit transform (e.g. 2*parent + bit) can be shared by the low-level mechanism,
//!   but semantic laws remain strictly domain-scoped (#2508, #2509).
//! - Cross-domain law application fails closed with `DomainMismatch`.
//! - Storage is a mechanism detail; there is no fixed host integer width ceiling.
//! - Zero external crate dependencies; no Lisp, JSON, AST, hash, registry, or cache
//!   required for execution.

#[derive(Clone, Copy, Debug, Eq, PartialEq, Hash)]
pub enum Domain {
    SelectorPath,
    QGroupFactor,
}

impl Domain {
    pub const fn as_str(&self) -> &'static str {
        match self {
            Self::SelectorPath => "SelectorPath",
            Self::QGroupFactor => "QGroupFactor",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Hash)]
pub struct BinaryNumber {
    bits: Vec<u8>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Error {
    Empty,
    InvalidBit,
    DeltaMustBeOneBit,
    UnknownLaw,
    WrongArity,
    DomainMismatch,
}

impl BinaryNumber {
    pub fn parse(bits: &str) -> Result<Self, Error> {
        if bits.is_empty() {
            return Err(Error::Empty);
        }
        let mut out = Vec::with_capacity(bits.len());
        for byte in bits.bytes() {
            match byte {
                b'0' => out.push(0),
                b'1' => out.push(1),
                _ => return Err(Error::InvalidBit),
            }
        }
        Ok(Self { bits: out })
    }

    pub fn from_raw(bits: Vec<u8>) -> Self {
        Self { bits }
    }

    pub fn width(&self) -> usize {
        self.bits.len()
    }

    pub fn bits(&self) -> String {
        self.bits
            .iter()
            .map(|bit| if *bit == 0 { '0' } else { '1' })
            .collect()
    }

    pub fn raw_bits(&self) -> &[u8] {
        &self.bits
    }

    pub fn is_exactly(&self, bits: &[u8]) -> bool {
        self.bits == bits
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

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Law {
    domain: Domain,
    factor: BinaryNumber,
    semantic_equation: &'static str,
}

impl Law {
    /// Backwards-compatible constructor defaulting to `Domain::SelectorPath`.
    pub fn new(factor: BinaryNumber) -> Result<Self, Error> {
        Self::new_scoped(
            Domain::SelectorPath,
            factor,
            "extend(selector,b)(x)=selector(project_b(x))",
        )
    }

    /// Construct a domain-scoped law with explicit domain and semantic equation.
    pub fn new_scoped(
        domain: Domain,
        factor: BinaryNumber,
        semantic_equation: &'static str,
    ) -> Result<Self, Error> {
        if factor.is_exactly(&[1, 0]) {
            Ok(Self {
                domain,
                factor,
                semantic_equation,
            })
        } else {
            Err(Error::UnknownLaw)
        }
    }

    pub fn selector_extend() -> Self {
        Self {
            domain: Domain::SelectorPath,
            factor: BinaryNumber { bits: vec![1, 0] },
            semantic_equation: "extend(selector,b)(x)=selector(project_b(x))",
        }
    }

    pub fn q_group_role() -> Self {
        Self {
            domain: Domain::QGroupFactor,
            factor: BinaryNumber { bits: vec![1, 0] },
            semantic_equation: "child=2*family_root+role_bit; inverse_F / quotient_F",
        }
    }

    pub fn domain(&self) -> Domain {
        self.domain
    }

    pub fn factor(&self) -> &BinaryNumber {
        &self.factor
    }

    pub fn semantic_equation(&self) -> &'static str {
        self.semantic_equation
    }
}

/// Apply the binary law mechanism to raw binary numbers.
///
/// Mathematical statement:
/// output = 2 * parent + delta
/// output_width = parent_width + 1
pub fn apply(law: &Law, inputs: &[BinaryNumber]) -> Result<BinaryNumber, Error> {
    if inputs.len() != 2 {
        return Err(Error::WrongArity);
    }
    if !law.factor.is_exactly(&[1, 0]) {
        return Err(Error::UnknownLaw);
    }

    let parent = &inputs[0];
    let delta = &inputs[1];
    if delta.width() != 1 {
        return Err(Error::DeltaMustBeOneBit);
    }

    let mut bits = parent.bits.clone();
    bits.push(delta.bits[0]);
    Ok(BinaryNumber { bits })
}

/// Apply a domain-scoped binary law to a semantic object.
///
/// Under #2490 and #2508:
/// 1. `parent.domain()` must match `law.domain()`; cross-domain application fails with `DomainMismatch`.
/// 2. `delta.width()` must be 1 bit.
/// 3. `law.factor()` must be 10₂.
/// 4. Resulting semantic object inherits the parent's domain with extended bits.
pub fn apply_scoped(law: &Law, parent: &SemanticObject, delta: &BinaryNumber) -> Result<SemanticObject, Error> {
    if parent.domain() != law.domain() {
        return Err(Error::DomainMismatch);
    }
    let raw = apply(law, &[parent.bits().clone(), delta.clone()])?;
    Ok(SemanticObject::new(parent.domain(), raw))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn selector_law() -> Law {
        Law::selector_extend()
    }

    fn q_law() -> Law {
        Law::q_group_role()
    }

    #[test]
    fn exact_width_and_leading_zeroes_are_preserved() {
        let x = SemanticObject::new(Domain::SelectorPath, BinaryNumber::parse("001").unwrap());
        let y = apply_scoped(&selector_law(), &x, &BinaryNumber::parse("0").unwrap()).unwrap();
        assert_eq!(y.bits().bits(), "0010");
        assert_eq!(y.width(), 4);
        assert_eq!(y.domain(), Domain::SelectorPath);
    }

    #[test]
    fn raw_apply_backwards_compatible() {
        let law = Law::new(BinaryNumber::parse("10").unwrap()).unwrap();
        let x = BinaryNumber::parse("001").unwrap();
        let delta = BinaryNumber::parse("0").unwrap();
        let y = apply(&law, &[x, delta]).unwrap();
        assert_eq!(y.bits(), "0010");
    }

    #[test]
    fn result_is_reusable() {
        let x = SemanticObject::new(Domain::SelectorPath, BinaryNumber::parse("101").unwrap());
        let y = apply_scoped(&selector_law(), &x, &BinaryNumber::parse("0").unwrap()).unwrap();
        let z = apply_scoped(&selector_law(), &y, &BinaryNumber::parse("1").unwrap()).unwrap();
        assert_eq!(z.bits().bits(), "10101");
        assert_eq!(z.domain(), Domain::SelectorPath);
    }

    #[test]
    fn width_has_no_host_integer_ceiling() {
        let source = "1".repeat(4096);
        let x = SemanticObject::new(Domain::SelectorPath, BinaryNumber::parse(&source).unwrap());
        let y = apply_scoped(&selector_law(), &x, &BinaryNumber::parse("1").unwrap()).unwrap();
        assert_eq!(y.width(), 4097);
        assert!(y.bits().bits().ends_with('1'));
    }

    #[test]
    fn malformed_inputs_and_unknown_law_fail_closed() {
        assert_eq!(BinaryNumber::parse(""), Err(Error::Empty));
        assert_eq!(BinaryNumber::parse("10x"), Err(Error::InvalidBit));

        let x = SemanticObject::new(Domain::SelectorPath, BinaryNumber::parse("101").unwrap());
        assert_eq!(
            apply_scoped(&selector_law(), &x, &BinaryNumber::parse("10").unwrap()),
            Err(Error::DeltaMustBeOneBit)
        );
        assert_eq!(
            Law::new_scoped(Domain::SelectorPath, BinaryNumber::parse("11").unwrap(), "test"),
            Err(Error::UnknownLaw)
        );
        assert_eq!(
            apply(&selector_law(), &[x.bits().clone()]),
            Err(Error::WrongArity)
        );
    }

    #[test]
    fn domain_firewall_rejects_cross_domain_application() {
        let sel_obj = SemanticObject::new(Domain::SelectorPath, BinaryNumber::parse("101").unwrap());
        let q_obj = SemanticObject::new(Domain::QGroupFactor, BinaryNumber::parse("1").unwrap());
        let delta = BinaryNumber::parse("0").unwrap();

        // Cross-domain execution must fail closed:
        assert_eq!(apply_scoped(&q_law(), &sel_obj, &delta), Err(Error::DomainMismatch));
        assert_eq!(apply_scoped(&selector_law(), &q_obj, &delta), Err(Error::DomainMismatch));

        // Same-domain execution succeeds:
        assert!(apply_scoped(&selector_law(), &sel_obj, &delta).is_ok());
        assert!(apply_scoped(&q_law(), &q_obj, &delta).is_ok());
    }

    #[test]
    fn identical_bit_strings_in_different_domains_remain_distinct() {
        let sel_10 = SemanticObject::new(Domain::SelectorPath, BinaryNumber::parse("10").unwrap());
        let q_10 = SemanticObject::new(Domain::QGroupFactor, BinaryNumber::parse("10").unwrap());

        assert_eq!(sel_10.bits().bits(), q_10.bits().bits());
        assert_ne!(sel_10, q_10);
    }

    #[test]
    fn q_group_factor_two_family_roots_and_four_children() {
        let law = q_law();
        let add_root = SemanticObject::new(Domain::QGroupFactor, BinaryNumber::parse("0").unwrap());
        let mul_root = SemanticObject::new(Domain::QGroupFactor, BinaryNumber::parse("1").unwrap());

        let d0 = BinaryNumber::parse("0").unwrap();
        let d1 = BinaryNumber::parse("1").unwrap();

        let add_inv = apply_scoped(&law, &add_root, &d0).unwrap(); // 00
        let add_quot = apply_scoped(&law, &add_root, &d1).unwrap(); // 01
        let mul_inv = apply_scoped(&law, &mul_root, &d0).unwrap(); // 10
        let mul_quot = apply_scoped(&law, &mul_root, &d1).unwrap(); // 11

        assert_eq!(add_inv.bits().bits(), "00");
        assert_eq!(add_quot.bits().bits(), "01");
        assert_eq!(mul_inv.bits().bits(), "10");
        assert_eq!(mul_quot.bits().bits(), "11");

        assert_eq!(add_inv.domain(), Domain::QGroupFactor);
        assert_eq!(add_quot.domain(), Domain::QGroupFactor);
        assert_eq!(mul_inv.domain(), Domain::QGroupFactor);
        assert_eq!(mul_quot.domain(), Domain::QGroupFactor);
    }
}
