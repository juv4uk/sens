//! Minimal Core-Math binary executor experiment.
//!
//! Semantic core: exact-width binary input plus one admitted mathematical law
//! yields exact-width binary output.
//!
//! There is no fixed semantic width ceiling. Storage is a mechanism detail.
//! No Lisp, JSON, AST, hash, registry, cache, human operation name, or proof
//! format is required by this module.

#[derive(Clone, Debug, Eq, PartialEq)]
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

    pub fn width(&self) -> usize {
        self.bits.len()
    }

    pub fn bits(&self) -> String {
        self.bits
            .iter()
            .map(|bit| if *bit == 0 { '0' } else { '1' })
            .collect()
    }

    fn is_exactly(&self, bits: &[u8]) -> bool {
        self.bits == bits
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Law {
    factor: BinaryNumber,
}

impl Law {
    /// The first admitted law is characterized by its mathematical factor
    /// 10₂ = 2, not by an assigned operation ID or human name.
    pub fn new(factor: BinaryNumber) -> Result<Self, Error> {
        if factor.is_exactly(&[1, 0]) {
            Ok(Self { factor })
        } else {
            Err(Error::UnknownLaw)
        }
    }
}

/// Apply the first admitted binary law.
///
/// Mathematical statement:
/// output = 2 * parent + delta
/// output_width = parent_width + 1
///
/// In positional binary arithmetic multiplication by two shifts one place and
/// the one-bit delta fills that new place. The implementation therefore needs
/// no bounded host integer.
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

#[cfg(test)]
mod tests {
    use super::*;

    fn law() -> Law {
        Law::new(BinaryNumber::parse("10").unwrap()).unwrap()
    }

    #[test]
    fn exact_width_and_leading_zeroes_are_preserved() {
        let x = BinaryNumber::parse("001").unwrap();
        let y = apply(&law(), &[x, BinaryNumber::parse("0").unwrap()]).unwrap();
        assert_eq!(y.bits(), "0010");
        assert_eq!(y.width(), 4);
    }

    #[test]
    fn result_is_reusable() {
        let x = BinaryNumber::parse("101").unwrap();
        let y = apply(&law(), &[x, BinaryNumber::parse("0").unwrap()]).unwrap();
        let z = apply(&law(), &[y, BinaryNumber::parse("1").unwrap()]).unwrap();
        assert_eq!(z.bits(), "10101");
    }

    #[test]
    fn width_has_no_host_integer_ceiling() {
        let source = "1".repeat(4096);
        let x = BinaryNumber::parse(&source).unwrap();
        let y = apply(&law(), &[x, BinaryNumber::parse("1").unwrap()]).unwrap();
        assert_eq!(y.width(), 4097);
        assert!(y.bits().ends_with('1'));
    }

    #[test]
    fn malformed_inputs_and_unknown_law_fail_closed() {
        assert_eq!(BinaryNumber::parse(""), Err(Error::Empty));
        assert_eq!(BinaryNumber::parse("10x"), Err(Error::InvalidBit));

        let x = BinaryNumber::parse("101").unwrap();
        assert_eq!(
            apply(&law(), &[x.clone(), BinaryNumber::parse("10").unwrap()]),
            Err(Error::DeltaMustBeOneBit)
        );
        assert_eq!(
            Law::new(BinaryNumber::parse("11").unwrap()),
            Err(Error::UnknownLaw)
        );
        assert_eq!(apply(&law(), &[x]), Err(Error::WrongArity));
    }
}
