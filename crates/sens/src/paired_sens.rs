//! Тимчасовий .sens reader із достовірною підказкою від парного .lisp.
//!
//! Принцип: файл .sens має ТІЛЬКИ семантичний двійковий payload;
//! розбиття на D1–D9 слова рідер поки що бере з людської проєкції.
//! Ніяких D7-пробілів, ширинних тегів, коментарів чи ASCII 0/1 у .sens.
//!
//! ПЕРЕХІДНЕ ОБМЕЖЕННЯ: наявний parse_binary_source_words розуміє
//! лише *точні видимі двійкові слова* (D1–D9), не довільну українську
//! .lisp поверхню. Її переклад має виконати окремий перевірений
//! мовний adapter, а не вигаданий словник у цьому модулі.

use crate::{
    pack_binary_source_tokens, parse_binary_source_words, parse_canonical_binary,
    semantic_source_bits, unpack_binary_source_words, BinarySourceWord, PackedBitstream,
};

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PairedSensError {
    InvalidLispProjection,
    InvalidLispStructure,
    EmptyProgram,
    InvalidPhysicalFile,
    SidecarMismatch,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PairedSensProof {
    pub word_widths: Vec<usize>,
    pub semantic_bits: usize,
    pub physical_bytes: usize,
    pub physical_bits: usize,
    pub tail_unused_bits: usize,
}

/// Encode only after a syntax check of the exact visible-binary projection.
/// The output is physical bytes, never the ASCII spelling of binary digits.
pub fn sens_bytes_from_binary_lisp(projection: &str) -> Result<Vec<u8>, PairedSensError> {
    let tokens = parse_binary_source_words(projection)
        .map_err(|_| PairedSensError::InvalidLispProjection)?;
    if tokens.is_empty() {
        return Err(PairedSensError::EmptyProgram);
    }
    parse_canonical_binary(projection).map_err(|_| PairedSensError::InvalidLispStructure)?;
    Ok(pack_binary_source_tokens(&tokens).bytes().to_vec())
}

/// The paired .lisp supplies *widths only as a hint*, not asserted identity.
/// Every decoded exact word is compared with its source projection,
/// including the D2 structural words. The packed .sens may not have
/// extra bytes or nonzero bits in the final partial byte.
///
/// This is a pair-dependent verifier, NOT a standalone .sens decoder and
/// NOT an oracle/evaluator parity proof.
pub fn verify_sens_with_binary_lisp(
    projection: &str,
    physical_sens: &[u8],
) -> Result<PairedSensProof, PairedSensError> {
    let tokens = parse_binary_source_words(projection)
        .map_err(|_| PairedSensError::InvalidLispProjection)?;
    if tokens.is_empty() {
        return Err(PairedSensError::EmptyProgram);
    }
    parse_canonical_binary(projection).map_err(|_| PairedSensError::InvalidLispStructure)?;

    let semantic_bits = semantic_source_bits(&tokens);
    let packed = PackedBitstream::from_parts(physical_sens.to_vec(), semantic_bits)
        .ok_or(PairedSensError::InvalidPhysicalFile)?;
    let word_widths: Vec<usize> = tokens.iter().map(|token| token.word.width()).collect();
    let decoded = unpack_binary_source_words(&packed, &word_widths)
        .ok_or(PairedSensError::InvalidPhysicalFile)?;
    let expected: Vec<BinarySourceWord> = tokens.iter().map(|token| token.word).collect();
    if decoded != expected {
        return Err(PairedSensError::SidecarMismatch);
    }

    // Stronger byte-for-byte replay, not just semantic-value equality.
    let regenerated = pack_binary_source_tokens(&tokens);
    if regenerated.bytes() != physical_sens {
        return Err(PairedSensError::SidecarMismatch);
    }

    let physical_bytes = physical_sens.len();
    let physical_bits = physical_bytes * 8;
    Ok(PairedSensProof {
        word_widths,
        semantic_bits,
        physical_bytes,
        physical_bits,
        tail_unused_bits: physical_bits - semantic_bits,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn complete_quote_empty_list_pair_encodes_to_exact_bits() {
        let source = "10 001 00 000 01";
        let actual = sens_bytes_from_binary_lisp(source).unwrap();
        // 12 semantic bits: 100010000001; final physical byte has four zero tail bits.
        assert_eq!(actual, &[0b1000_1000, 0b0001_0000]);
        let proof = verify_sens_with_binary_lisp(source, &actual).unwrap();
        assert_eq!(proof.word_widths, [2, 3, 2, 3, 2]);
        assert_eq!(proof.semantic_bits, 12);
        assert_eq!(proof.physical_bytes, 2);
        assert_eq!(proof.tail_unused_bits, 4);
    }

    #[test]
    fn complete_nested_form_can_have_exact_byte_boundary() {
        let source = "10 001 00 10 000 01 01";
        let actual = sens_bytes_from_binary_lisp(source).unwrap();
        let proof = verify_sens_with_binary_lisp(source, &actual).unwrap();
        assert_eq!(proof.semantic_bits, 16);
        assert_eq!(proof.physical_bits, 16);
        assert_eq!(proof.tail_unused_bits, 0);
    }

    #[test]
    fn ambiguous_payload_only_works_with_its_matching_sidecar() {
        let d1_plus_d2 = "0 00";
        let d3_empty = "000";
        let binary = sens_bytes_from_binary_lisp(d3_empty).unwrap();
        assert_eq!(binary, sens_bytes_from_binary_lisp(d1_plus_d2).unwrap());

        let a = verify_sens_with_binary_lisp(d1_plus_d2, &binary).unwrap();
        let b = verify_sens_with_binary_lisp(d3_empty, &binary).unwrap();
        assert_eq!(a.word_widths, [1, 2]);
        assert_eq!(b.word_widths, [3]);
        // IMPORTANT: this is why .sens without .lisp is not yet autonomous.
    }

    #[test]
    fn changed_payload_bit_is_detected_not_trusted() {
        let source = "10 001 00 000 01";
        let mut physical = sens_bytes_from_binary_lisp(source).unwrap();
        physical[0] ^= 0b0001_0000;
        assert_eq!(
            verify_sens_with_binary_lisp(source, &physical),
            Err(PairedSensError::SidecarMismatch),
        );
    }

    #[test]
    fn wrong_lisp_partner_is_detected() {
        let original = "10 001 00 000 01";
        let different = "10 010 00 000 01";
        let bytes = sens_bytes_from_binary_lisp(original).unwrap();
        assert_eq!(
            verify_sens_with_binary_lisp(different, &bytes),
            Err(PairedSensError::SidecarMismatch)
        );
    }

    #[test]
    fn appended_byte_or_dirty_unused_tail_is_rejected() {
        let source = "10 001 00 000 01";
        let mut bytes = sens_bytes_from_binary_lisp(source).unwrap();
        let mut appended = bytes.clone();
        appended.push(0);
        assert_eq!(
            verify_sens_with_binary_lisp(source, &appended),
            Err(PairedSensError::InvalidPhysicalFile)
        );
        *bytes.last_mut().unwrap() |= 1;
        assert_eq!(
            verify_sens_with_binary_lisp(source, &bytes),
            Err(PairedSensError::InvalidPhysicalFile)
        );
    }

    #[test]
    fn invalid_structure_and_nonbinary_lisp_fail_closed() {
        assert_eq!(
            sens_bytes_from_binary_lisp("10 001"),
            Err(PairedSensError::InvalidLispStructure)
        );
        assert_eq!(
            sens_bytes_from_binary_lisp("(QUOTE ())"),
            Err(PairedSensError::InvalidLispProjection)
        );
        assert_eq!(
            sens_bytes_from_binary_lisp(""),
            Err(PairedSensError::EmptyProgram)
        );
    }

    #[test]
    fn various_surface_whitespace_does_not_change_binary_payload() {
        let canonical = "10 001 00 000 01";
        let projected = "10\n001\n00\n000\n01\n";
        assert_eq!(
            sens_bytes_from_binary_lisp(canonical).unwrap(),
            sens_bytes_from_binary_lisp(projected).unwrap()
        );
        assert_eq!(
            verify_sens_with_binary_lisp(projected,
                &sens_bytes_from_binary_lisp(canonical).unwrap()).unwrap().semantic_bits,
            12
        );
    }
}
