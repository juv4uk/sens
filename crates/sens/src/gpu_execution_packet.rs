//! Compact binary execution packet for GPU substrates.
//!
//! Transport only: semantic meaning and execution-role admission remain owned
//! by SENS. This module defines bytes, handles, dependencies and provenance.

use crate::{
    compiler_execution_role, BinarySourceWord, Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8,
    CompilerExecutionRole, CoreDomainIdentity, DomainIdentity, CoreD8,
};

const MAGIC: [u8; 4] = *b"SGP\x01";
const OUTPUT_MATERIALIZE: u8 = 0;
const OUTPUT_HANDLE: u8 = 1;
const NO_DEPENDENCY: u8 = 0;
const HAS_DEPENDENCY: u8 = 1;
const MAX_INPUT_HANDLES: usize = 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum GpuOutputRequest {
    Materialize,
    HandleSlot(u64),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GpuExecutionPacketV1 {
    pub opcode: CoreDomainIdentity,
    pub input_handles: Vec<u64>,
    pub output: GpuOutputRequest,
    pub dependency: Option<u64>,
    pub provenance: [u8; 32],
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum GpuExecutionPacketError {
    WrongMagic,
    Truncated { offset: usize },
    InvalidWidth { width: usize },
    InvalidPayload { width: usize, payload: u8 },
    UnsupportedOpcode { opcode: CoreDomainIdentity },
    UnsupportedWidth { width: usize },
    NonCanonicalVarint { offset: usize },
    VarintOverflow { offset: usize },
    InputCountTooLarge,
    InvalidOutputTag { tag: u8 },
    InvalidDependencyTag { tag: u8 },
    TrailingBytes { offset: usize },
}

impl std::fmt::Display for GpuExecutionPacketError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::WrongMagic => write!(f, "wrong SENS GPU packet magic/version"),
            Self::Truncated { offset } => write!(f, "truncated SENS GPU packet at byte {offset}"),
            Self::InvalidWidth { width } => write!(f, "invalid exact identity width {width}"),
            Self::InvalidPayload { width, payload } => {
                write!(f, "payload {payload} does not fit exact width {width}")
            }
            Self::UnsupportedOpcode { opcode } => {
                write!(f, "SENS opcode is not admitted for GPU execution: {opcode:?}")
            }
            Self::UnsupportedWidth { width } => {
                write!(f, "exact identity width {width} has no admitted GPU opcode projection")
            }
            Self::NonCanonicalVarint { offset } => {
                write!(f, "non-canonical input-count varint at byte {offset}")
            }
            Self::VarintOverflow { offset } => {
                write!(f, "input-count varint overflows at byte {offset}")
            }
            Self::InputCountTooLarge => write!(f, "input handle count exceeds packet bound"),
            Self::InvalidOutputTag { tag } => write!(f, "invalid GPU output tag {tag}"),
            Self::InvalidDependencyTag { tag } => write!(f, "invalid GPU dependency tag {tag}"),
            Self::TrailingBytes { offset } => write!(f, "unexpected trailing packet bytes at {offset}"),
        }
    }
}

impl std::error::Error for GpuExecutionPacketError {}

impl GpuExecutionPacketV1 {
    /// Construct only after SENS's own compiler-role admission.
    pub fn try_new(
        opcode: CoreDomainIdentity,
        input_handles: Vec<u64>,
        output: GpuOutputRequest,
        dependency: Option<u64>,
        provenance: [u8; 32],
    ) -> Result<Self, GpuExecutionPacketError> {
        if input_handles.len() > MAX_INPUT_HANDLES {
            return Err(GpuExecutionPacketError::InputCountTooLarge);
        }
        if compiler_execution_role(opcode).is_none() {
            return Err(GpuExecutionPacketError::UnsupportedOpcode { opcode });
        }
        Ok(Self { opcode, input_handles, output, dependency, provenance })
    }

    pub fn encode(&self) -> Result<Vec<u8>, GpuExecutionPacketError> {
        if self.input_handles.len() > MAX_INPUT_HANDLES {
            return Err(GpuExecutionPacketError::InputCountTooLarge);
        }
        if compiler_execution_role(self.opcode).is_none() {
            return Err(GpuExecutionPacketError::UnsupportedOpcode { opcode: self.opcode });
        }

        let (width, payload) = identity_parts(self.opcode);
        let mut out = Vec::with_capacity(4 + 2 + 10 + self.input_handles.len() * 8 + 1 + 1 + 32);
        out.extend_from_slice(&MAGIC);
        out.push(width as u8);
        out.push(payload);

        encode_varint(self.input_handles.len() as u64, &mut out);
        for handle in &self.input_handles {
            out.extend_from_slice(&handle.to_le_bytes());
        }

        match self.output {
            GpuOutputRequest::Materialize => out.push(OUTPUT_MATERIALIZE),
            GpuOutputRequest::HandleSlot(slot) => {
                out.push(OUTPUT_HANDLE);
                out.extend_from_slice(&slot.to_le_bytes());
            }
        }

        match self.dependency {
            None => out.push(NO_DEPENDENCY),
            Some(id) => {
                out.push(HAS_DEPENDENCY);
                out.extend_from_slice(&id.to_le_bytes());
            }
        }

        out.extend_from_slice(&self.provenance);
        Ok(out)
    }

    pub fn decode(bytes: &[u8]) -> Result<Self, GpuExecutionPacketError> {
        let mut reader = Reader::new(bytes);
        if reader.take_exact(4)? != MAGIC {
            return Err(GpuExecutionPacketError::WrongMagic);
        }

        let width = reader.take_u8()? as usize;
        let payload = reader.take_u8()?;
        let opcode = decode_admitted_opcode(width, payload)?;

        let input_count = reader.read_varint()?;
        if input_count > MAX_INPUT_HANDLES as u64 {
            return Err(GpuExecutionPacketError::InputCountTooLarge);
        }

        let mut input_handles = Vec::with_capacity(input_count as usize);
        for _ in 0..input_count {
            input_handles.push(reader.take_u64_le()?);
        }

        let output = match reader.take_u8()? {
            OUTPUT_MATERIALIZE => GpuOutputRequest::Materialize,
            OUTPUT_HANDLE => GpuOutputRequest::HandleSlot(reader.take_u64_le()?),
            tag => return Err(GpuExecutionPacketError::InvalidOutputTag { tag }),
        };

        let dependency = match reader.take_u8()? {
            NO_DEPENDENCY => None,
            HAS_DEPENDENCY => Some(reader.take_u64_le()?),
            tag => return Err(GpuExecutionPacketError::InvalidDependencyTag { tag }),
        };

        let provenance_bytes = reader.take_exact(32)?;
        let mut provenance = [0u8; 32];
        provenance.copy_from_slice(provenance_bytes);

        if !reader.is_at_end() {
            return Err(GpuExecutionPacketError::TrailingBytes { offset: reader.offset });
        }

        Ok(Self { opcode, input_handles, output, dependency, provenance })
    }

    /// The role is fetched from SENS authority; it is not decoded from a local table.
    pub fn admitted_role(&self) -> CompilerExecutionRole {
        compiler_execution_role(self.opcode)
            .expect("packet constructor/decoder enforces admission")
    }
}

fn identity_parts(opcode: CoreDomainIdentity) -> (usize, u8) {
    (opcode.width(), opcode.packed_bits())
}

fn decode_admitted_opcode(
    width: usize,
    payload: u8,
) -> Result<CoreDomainIdentity, GpuExecutionPacketError> {
    let source = match width {
        1 => BinarySourceWord::W1(Bit1::new(payload).ok_or(
            GpuExecutionPacketError::InvalidPayload { width, payload },
        )?),
        2 => BinarySourceWord::W2(Bit2::new(payload).ok_or(
            GpuExecutionPacketError::InvalidPayload { width, payload },
        )?),
        3 => BinarySourceWord::W3(Bit3::new(payload).ok_or(
            GpuExecutionPacketError::InvalidPayload { width, payload },
        )?),
        4 => BinarySourceWord::W4(Bit4::new(payload).ok_or(
            GpuExecutionPacketError::InvalidPayload { width, payload },
        )?),
        5 => BinarySourceWord::W5(Bit5::new(payload).ok_or(
            GpuExecutionPacketError::InvalidPayload { width, payload },
        )?),
        6 => BinarySourceWord::W6(Bit6::new(payload).ok_or(
            GpuExecutionPacketError::InvalidPayload { width, payload },
        )?),
        7 => return Err(GpuExecutionPacketError::UnsupportedWidth { width }),
        8 => BinarySourceWord::W8(Bit8::new(payload).ok_or(
            GpuExecutionPacketError::InvalidPayload { width, payload },
        )?),
        _ => return Err(GpuExecutionPacketError::InvalidWidth { width }),
    };

    let domain = DomainIdentity::from_source_word(source);
    let Some(opcode) = domain.core_operation() else {
        return Err(GpuExecutionPacketError::UnsupportedWidth { width });
    };
    if compiler_execution_role(opcode).is_none() {
        return Err(GpuExecutionPacketError::UnsupportedOpcode { opcode });
    }
    Ok(opcode)
}

fn encode_varint(mut value: u64, out: &mut Vec<u8>) {
    while value >= 0x80 {
        out.push((value as u8 & 0x7f) | 0x80);
        value >>= 7;
    }
    out.push(value as u8);
}

struct Reader<'a> {
    bytes: &'a [u8],
    offset: usize,
}

impl<'a> Reader<'a> {
    fn new(bytes: &'a [u8]) -> Self { Self { bytes, offset: 0 } }

    fn take_u8(&mut self) -> Result<u8, GpuExecutionPacketError> {
        let offset = self.offset;
        let Some(&byte) = self.bytes.get(self.offset) else {
            return Err(GpuExecutionPacketError::Truncated { offset });
        };
        self.offset += 1;
        Ok(byte)
    }

    fn take_u64_le(&mut self) -> Result<u64, GpuExecutionPacketError> {
        let bytes = self.take_exact(8)?;
        Ok(u64::from_le_bytes(bytes.try_into().unwrap()))
    }

    fn take_exact(&mut self, len: usize) -> Result<&'a [u8], GpuExecutionPacketError> {
        let end = self.offset.checked_add(len).ok_or(GpuExecutionPacketError::Truncated { offset: self.offset })?;
        if end > self.bytes.len() {
            return Err(GpuExecutionPacketError::Truncated { offset: self.offset });
        }
        let start = self.offset;
        self.offset = end;
        Ok(&self.bytes[start..end])
    }

    fn read_varint(&mut self) -> Result<u64, GpuExecutionPacketError> {
        let start = self.offset;
        let mut value = 0u64;
        let mut shift = 0u32;
        for index in 0..10 {
            let byte = self.take_u8()?;
            let data = u64::from(byte & 0x7f);
            if shift == 63 && data > 1 {
                return Err(GpuExecutionPacketError::VarintOverflow { offset: start });
            }
            value |= data << shift;
            if byte & 0x80 == 0 {
                if index > 0 && data == 0 {
                    return Err(GpuExecutionPacketError::NonCanonicalVarint { offset: start });
                }
                return Ok(value);
            }
            shift += 7;
        }
        Err(GpuExecutionPacketError::VarintOverflow { offset: start })
    }

    fn is_at_end(&self) -> bool { self.offset == self.bytes.len() }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bija3, Bit3};

    fn d3(raw: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).unwrap()))
    }

    #[test]
    fn admitted_d3_opcode_round_trips_without_name_lookup() {
        let packet = GpuExecutionPacketV1::try_new(
            d3(0b111),
            vec![11, 17],
            GpuOutputRequest::HandleSlot(42),
            Some(9),
            [7u8; 32],
        ).unwrap();

        let encoded = packet.encode().unwrap();
        assert_eq!(&encoded[..6], b"SGP\x01\x03\x07");
        let decoded = GpuExecutionPacketV1::decode(&encoded).unwrap();
        assert_eq!(decoded, packet);
        assert_eq!(decoded.admitted_role(), CompilerExecutionRole::PairConstruct);
    }

    #[test]
    fn non_admitted_current_and_research_widths_fail_closed() {
        assert!(matches!(
            GpuExecutionPacketV1::try_new(
                d3(0b000),
                vec![],
                GpuOutputRequest::Materialize,
                None,
                [0; 32],
            ),
            Err(GpuExecutionPacketError::UnsupportedOpcode { .. })
        ));

        let d8 = CoreDomainIdentity::D8(CoreD8::from_word(Bit8::new(1).unwrap()));
        assert!(matches!(
            GpuExecutionPacketV1::try_new(d8, vec![], GpuOutputRequest::Materialize, None, [0; 32]),
            Err(GpuExecutionPacketError::UnsupportedOpcode { .. })
        ));

        let d7_source = BinarySourceWord::W7(Bit7::new(1).unwrap());
        let d7 = DomainIdentity::from_source_word(d7_source);
        assert!(d7.core_operation().is_none());
    }

    #[test]
    fn malformed_packet_controls_fail_closed() {
        let packet = GpuExecutionPacketV1::try_new(
            d3(0b100),
            vec![],
            GpuOutputRequest::Materialize,
            None,
            [0xAA; 32],
        ).unwrap();
        let encoded = packet.encode().unwrap();

        let mut wrong_magic = encoded.clone();
        wrong_magic[0] = b'X';
        assert_eq!(
            GpuExecutionPacketV1::decode(&wrong_magic),
            Err(GpuExecutionPacketError::WrongMagic)
        );

        let mut truncated = encoded.clone();
        truncated.truncate(truncated.len() - 1);
        assert!(matches!(
            GpuExecutionPacketV1::decode(&truncated),
            Err(GpuExecutionPacketError::Truncated { .. })
        ));

        let mut extra = encoded;
        extra.push(0);
        assert!(matches!(
            GpuExecutionPacketV1::decode(&extra),
            Err(GpuExecutionPacketError::TrailingBytes { .. })
        ));
    }

    #[test]
    fn canonical_varint_and_handle_bound_are_enforced() {
        let packet = GpuExecutionPacketV1::try_new(
            d3(0b111),
            (0..200).map(|n| n as u64).collect(),
            GpuOutputRequest::Materialize,
            None,
            [0; 32],
        ).unwrap();
        assert_eq!(GpuExecutionPacketV1::decode(&packet.encode().unwrap()).unwrap(), packet);

        let too_many = GpuExecutionPacketV1::try_new(
            d3(0b111),
            vec![0; MAX_INPUT_HANDLES + 1],
            GpuOutputRequest::Materialize,
            None,
            [0; 32],
        );
        assert!(matches!(too_many, Err(GpuExecutionPacketError::InputCountTooLarge)));
    }

    #[test]
    fn noncanonical_input_count_varint_fails_closed() {
        let packet = GpuExecutionPacketV1::try_new(
            d3(0b111),
            vec![],
            GpuOutputRequest::Materialize,
            None,
            [0; 32],
        ).unwrap();
        let mut encoded = packet.encode().unwrap();
        // Byte 6 is the zero input-count varint. Expand it to the non-canonical
        // two-byte spelling 0x80 0x00 by inserting one byte.
        assert_eq!(encoded[6], 0);
        encoded[6] = 0x80;
        encoded.insert(7, 0x00);
        assert!(matches!(
            GpuExecutionPacketV1::decode(&encoded),
            Err(GpuExecutionPacketError::NonCanonicalVarint { offset: 6 })
        ));
    }
    #[test]
    fn provenance_is_opaque_transport_not_admission() {
        let a = GpuExecutionPacketV1::try_new(d3(0b111), vec![], GpuOutputRequest::Materialize, None, [1; 32]).unwrap();
        let b = GpuExecutionPacketV1::try_new(d3(0b111), vec![], GpuOutputRequest::Materialize, None, [2; 32]).unwrap();
        assert_eq!(a.opcode, b.opcode);
        assert_ne!(a.provenance, b.provenance);
        assert_eq!(a.admitted_role(), b.admitted_role());
    }
}
