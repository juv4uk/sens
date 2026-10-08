//! Research-only self-identifying SENS file. NOT a ratified wire format.
//! Binary semantics remain unchanged. The six-byte header is outside SENS.
//! Never auto-detect raw codecs: physical 0x8f admits two incompatible decodes.

use crate::{
    decode_binary_delimited_words, decode_ternary_words,
    encode_binary_delimited_words, encode_ternary_words, BinarySourceWord,
};

const MAGIC: [u8; 4] = *b"SENS";
const VERSION: u8 = 1;
const HEADER_BYTES: usize = 6;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ProposedCodec {
    FiveTritsPerByte,
    PrefixBinary,
}

impl ProposedCodec {
    fn id(self) -> u8 {
        match self {
            Self::FiveTritsPerByte => 1,
            Self::PrefixBinary => 2,
        }
    }
    fn from_id(id: u8) -> Option<Self> {
        match id {
            1 => Some(Self::FiveTritsPerByte),
            2 => Some(Self::PrefixBinary),
            _ => None,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ProposedContainerError {
    TooShort,
    NotSensFile,
    UnknownVersion(u8),
    UnknownCodec(u8),
    InvalidPayload,
}

pub fn encode_proposed_sens_container(
    words: &[BinarySourceWord],
    codec: ProposedCodec,
) -> Result<Vec<u8>, ProposedContainerError> {
    let payload = match codec {
        ProposedCodec::FiveTritsPerByte => encode_ternary_words(words)
            .map_err(|_| ProposedContainerError::InvalidPayload)?,
        ProposedCodec::PrefixBinary => encode_binary_delimited_words(words)
            .map_err(|_| ProposedContainerError::InvalidPayload)?,
    };
    let mut bytes = Vec::with_capacity(HEADER_BYTES + payload.len());
    bytes.extend_from_slice(&MAGIC);
    bytes.push(VERSION);
    bytes.push(codec.id());
    bytes.extend_from_slice(&payload);
    Ok(bytes)
}

pub fn decode_proposed_sens_container(
    bytes: &[u8],
) -> Result<(ProposedCodec, Vec<BinarySourceWord>), ProposedContainerError> {
    if bytes.len() < HEADER_BYTES + 1 {
        return Err(ProposedContainerError::TooShort);
    }
    if &bytes[..4] != MAGIC.as_slice() {
        return Err(ProposedContainerError::NotSensFile);
    }
    if bytes[4] != VERSION {
        return Err(ProposedContainerError::UnknownVersion(bytes[4]));
    }
    let codec = ProposedCodec::from_id(bytes[5])
        .ok_or(ProposedContainerError::UnknownCodec(bytes[5]))?;
    let words = match codec {
        ProposedCodec::FiveTritsPerByte => decode_ternary_words(&bytes[HEADER_BYTES..])
            .map_err(|_| ProposedContainerError::InvalidPayload)?,
        ProposedCodec::PrefixBinary => decode_binary_delimited_words(&bytes[HEADER_BYTES..])
            .map_err(|_| ProposedContainerError::InvalidPayload)?,
    };
    Ok((codec, words))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parse_binary_source_words;

    fn words(source: &str) -> Vec<BinarySourceWord> {
        parse_binary_source_words(source).unwrap()
            .into_iter().map(|t| t.word).collect()
    }

    #[test]
    fn suffix_is_not_file_identity_without_magic() {
        assert_eq!(
            decode_proposed_sens_container(&[0x04, 0, 0, 0, 1, 1, 0x8f]),
            Err(ProposedContainerError::NotSensFile)
        );
        assert_eq!(
            decode_proposed_sens_container(&[0x53, 0x45, 0x4e]),
            Err(ProposedContainerError::TooShort)
        );
    }

    #[test]
    fn golden_ten_byte_container_vectors_are_stable() {
        let input = words("10 001 00 000 01");
        let a = encode_proposed_sens_container(&input, ProposedCodec::FiveTritsPerByte).unwrap();
        let b = encode_proposed_sens_container(&input, ProposedCodec::PrefixBinary).unwrap();
        assert_eq!(a, [0x53,0x45,0x4e,0x53,0x01,0x01,0x63,0x89,0x06,0xa1]);
        assert_eq!(b, [0x53,0x45,0x4e,0x53,0x01,0x02,0x99,0x66,0x35,0xe0]);
        assert_eq!(decode_proposed_sens_container(&a).unwrap(),
                   (ProposedCodec::FiveTritsPerByte, input.clone()));
        assert_eq!(decode_proposed_sens_container(&b).unwrap(),
                   (ProposedCodec::PrefixBinary, input));
    }

    #[test]
    fn ambiguous_raw_8f_requires_explicit_codec_selection() {
        let raw = [0x8fu8];
        assert_eq!(decode_ternary_words(&raw).unwrap(), words("1 0"));
        assert_eq!(decode_binary_delimited_words(&raw).unwrap(), words("100"));
        let a = encode_proposed_sens_container(&words("1 0"),
                    ProposedCodec::FiveTritsPerByte).unwrap();
        let b = encode_proposed_sens_container(&words("100"),
                    ProposedCodec::PrefixBinary).unwrap();
        assert_eq!(&a[6..], &raw);
        assert_eq!(&b[6..], &raw);
        assert_ne!(a, b);
        assert_eq!(decode_proposed_sens_container(&a).unwrap().1, words("1 0"));
        assert_eq!(decode_proposed_sens_container(&b).unwrap().1, words("100"));
    }

    #[test]
    fn unknown_version_or_codec_must_fail_closed() {
        let mut a = encode_proposed_sens_container(
            &words("000"), ProposedCodec::FiveTritsPerByte
        ).unwrap();
        a[4] = 99;
        assert_eq!(decode_proposed_sens_container(&a),
                   Err(ProposedContainerError::UnknownVersion(99)));
        a[4] = VERSION;
        a[5] = 99;
        assert_eq!(decode_proposed_sens_container(&a),
                   Err(ProposedContainerError::UnknownCodec(99)));
    }

    #[test]
    fn physical_truncation_and_extra_byte_must_fail_closed() {
        let a = encode_proposed_sens_container(
            &words("10 001 00 000 01"), ProposedCodec::FiveTritsPerByte
        ).unwrap();
        assert_eq!(decode_proposed_sens_container(&a[..a.len()-1]),
                   Err(ProposedContainerError::InvalidPayload));
        let mut additional = a;
        additional.push(0);
        assert_eq!(decode_proposed_sens_container(&additional),
                   Err(ProposedContainerError::InvalidPayload));
    }
}
