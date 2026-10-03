//! Minimal Core-Math binary executor experiment.
//!
//! Semantic core: exact-width binary input plus the admitted append law yields
//! exact-width binary output.
//!
//! No Lisp, JSON, AST, hash, registry, cache, human operation name, or proof
//! format is required by this module.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct BinaryNumber {
    value: u128,
    width: u8,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Error {
    Empty,
    InvalidBit,
    WidthOverflow,
    ValueOverflow,
    DeltaMustBeOneBit,
}

impl BinaryNumber {
    pub fn new(value: u128, width: u8) -> Result<Self, Error> {
        if width == 0 {
            return Err(Error::Empty);
        }
        if width > 127 {
            return Err(Error::WidthOverflow);
        }
        if value >= (1u128 << width) {
            return Err(Error::ValueOverflow);
        }
        Ok(Self { value, width })
    }

    pub fn parse(bits: &str) -> Result<Self, Error> {
        if bits.is_empty() {
            return Err(Error::Empty);
        }
        if bits.len() > 127 {
            return Err(Error::WidthOverflow);
        }
        let mut value = 0u128;
        for byte in bits.bytes() {
            value <<= 1;
            match byte {
                b'0' => {}
                b'1' => value |= 1,
                _ => return Err(Error::InvalidBit),
            }
        }
        Self::new(value, bits.len() as u8)
    }

    pub const fn value(self) -> u128 {
        self.value
    }

    pub const fn width(self) -> u8 {
        self.width
    }

    pub fn bits(self) -> String {
        format!("{:0width$b}", self.value, width = self.width as usize)
    }
}

/// Apply the first admitted binary law.
///
/// Mathematical statement:
/// output = 2 * parent + delta
/// output_width = parent_width + 1
///
/// Delta is itself an exact one-bit binary number. The returned object can
/// immediately become parent in another application.
pub fn apply(parent: BinaryNumber, delta: BinaryNumber) -> Result<BinaryNumber, Error> {
    if delta.width != 1 {
        return Err(Error::DeltaMustBeOneBit);
    }
    let width = parent.width.checked_add(1).ok_or(Error::WidthOverflow)?;
    if width > 127 {
        return Err(Error::WidthOverflow);
    }
    let value = parent
        .value
        .checked_mul(2)
        .and_then(|v| v.checked_add(delta.value))
        .ok_or(Error::ValueOverflow)?;
    BinaryNumber::new(value, width)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_width_is_preserved() {
        let x = BinaryNumber::parse("001").unwrap();
        let y = apply(x, BinaryNumber::parse("0").unwrap()).unwrap();
        assert_eq!(y.bits(), "0010");
        assert_eq!(y.width(), 4);
    }

    #[test]
    fn result_is_reusable() {
        let x = BinaryNumber::parse("101").unwrap();
        let y = apply(x, BinaryNumber::parse("0").unwrap()).unwrap();
        let z = apply(y, BinaryNumber::parse("1").unwrap()).unwrap();
        assert_eq!(z.bits(), "10101");
    }

    #[test]
    fn malformed_inputs_fail_closed() {
        assert_eq!(BinaryNumber::parse(""), Err(Error::Empty));
        assert_eq!(BinaryNumber::parse("10x"), Err(Error::InvalidBit));
        let x = BinaryNumber::parse("101").unwrap();
        assert_eq!(
            apply(x, BinaryNumber::parse("10").unwrap()),
            Err(Error::DeltaMustBeOneBit)
        );
    }
}
