//! #2756 / OD-008 — Synthesis of Text7, Shiva-sutras, and W7 dense bitstream packing.
//!
//! Language ceases to be an arbitrary text file of graphics glyphs (ASCII/UTF-8)
//! and becomes binary sound, where every bit has phonological meaning, every 7 bits
//! represent an indivisible atom of living human speech, and sequential speech
//! packs into dense W7 bitstreams with zero interior byte padding.

use sens::{
    encode_text7, render_text7, BinarySourceWord, Bit7, BitPacker,
    Text7, Text7Layout, Text7W7Error, Text7WordError, Value,
};

#[test]
fn text7_speech_atoms_pack_densely_into_w7_stream() {
    // Ukrainian words "код" ("к" + "о" + "д") and Sanskrit "a i u"
    let uk_text = encode_text7("код", Text7Layout::Uk).expect("valid Ukrainian encoding");
    assert_eq!(uk_text.len(), 3);

    // Each atom is exactly 7 bits: 3 cells = 21 bits
    let packed = uk_text.to_packed_w7();
    assert_eq!(packed.bit_len(), 21);
    // 21 bits require 3 bytes (ceiling(21/8) = 3)
    assert_eq!(packed.byte_len(), 3);

    // Unpack from dense W7 stream
    let restored = Text7::from_packed_w7(&packed).expect("exact W7 unpack");
    assert_eq!(restored, uk_text);
    assert_eq!(render_text7(&restored, Text7Layout::Uk).unwrap(), "код");
}

#[test]
fn eight_sound_atoms_pack_into_exactly_seven_bytes() {
    // 8 distinct human speech cells
    // "дз" (0x3e), "дж" (0x3f), "а" (0x5c), "е" (0x5d), "к" (0x00), "т" (0x0f), "п" (0x14), "м" (0x18)
    let cells = vec![0x3e, 0x3f, 0x5c, 0x5d, 0x00, 0x0f, 0x14, 0x18];
    let speech = Text7::from_cells(cells.clone()).expect("valid sound cells");

    let stream = speech.to_packed_w7();
    // 8 atoms * 7 bits = exactly 56 bits = exactly 7 bytes (zero unused trailing bits)
    assert_eq!(stream.bit_len(), 56);
    assert_eq!(stream.byte_len(), 7);

    // No interior byte padding: 56 payload bits occupy 7 bytes
    let decoded = Text7::from_packed_w7(&stream).expect("exact decode");
    assert_eq!(decoded.cells(), &cells[..]);
}

#[test]
fn binary_source_word_w7_preserves_atomic_speech_width() {
    let cells = vec![0x00, 0x11, 0x24]; // k, d, ś/ш
    let text = Text7::from_cells(cells).unwrap();

    let words = text.to_source_words();
    assert_eq!(words.len(), 3);

    for word in &words {
        assert_eq!(word.width(), 7);
        assert!(matches!(word, BinarySourceWord::W7(_)));
    }

    let restored = Text7::from_source_words(&words).unwrap();
    assert_eq!(restored, text);

    // Reject non-7-bit source words
    let invalid = vec![
        BinarySourceWord::W7(Bit7::new(0x00).unwrap()),
        BinarySourceWord::W2(sens::Bit2::new(0b10).unwrap()),
    ];
    let err = Text7::from_source_words(&invalid).unwrap_err();
    assert_eq!(err, Text7WordError::InvalidWordWidth { index: 1, width: 2 });
}

#[test]
fn shiva_sutras_and_text7_share_7bit_space_with_role_separation() {
    // The 14 Shiva-sutras have ordinals 1..14 (0000001..0001110).
    // In Text7, the same 7-bit coordinates represent specific sound cells
    // (e.g., 0x01 is varga.K.voiceless-aspirated 'kh', 0x02 is 'g', etc.)
    // Domain rules guarantee that their semantic identities remain separate.

    let sutra1_bits = 0b0000001u8;
    let sutra1_bit7 = Bit7::new(sutra1_bits).unwrap();
    assert_eq!(sutra1_bit7.packed_bits(), 1);

    // As a Text7 cell, this represents the voiceless aspirated velar stop "kh"
    let sound_cell = Text7::from_cells(vec![sutra1_bits]).unwrap();
    assert_eq!(sound_cell.to_canonical_wire_token(), "#t7:01");

    // Sound coordinates are distinct from Number arithmetic
    let val_sound = Value::Text7(sound_cell);
    let val_nil = Value::Nil;
    assert_ne!(val_sound, val_nil);
    assert!(val_sound.to_canonical_wire_string().starts_with("#t7:"));
}

#[test]
fn unaligned_w7_streams_fail_closed() {
    let mut packer = BitPacker::new();
    // Push 10 bits
    packer.push(Bit7::new(0x15).unwrap());
    packer.push(sens::Bit3::new(0x05).unwrap());
    let invalid_stream = packer.finish();
    assert_eq!(invalid_stream.bit_len(), 10);

    let err = Text7::from_packed_w7(&invalid_stream).unwrap_err();
    assert_eq!(err, Text7W7Error::UnalignedBitLen { bit_len: 10 });
}
