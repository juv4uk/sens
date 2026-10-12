//! Точнодоменний транспорт кадрів: історичний W8 не стає D8.
//! Незалежні зовнішні свідки для виконуваного ядра.

use sens::{
    decode_binary_program, encode_binary_program, BinaryFrame, BinaryFrameError,
    BinaryNumber, BinarySourceWord, Bit3, Bit8, Bit9, Rational, Text7,
};

fn числове_слово(width: usize) -> BinaryFrame {
    let mut bits = vec![0u8; width];
    bits[width - 1] = 1;
    BinaryFrame::BinaryNumber(
        BinaryNumber::from_numeric_domain_bits(width, &bits)
            .expect("ратифікована точна числова ширина D24+"),
    )
}

#[test]
fn точні_d3_d8_d9_та_d24_d48_не_змішуються_з_історичним_w8() {
    let d3 = BinaryFrame::Domain(
        BinarySourceWord::W3(Bit3::new(0b001).unwrap()).domain_identity(),
    );
    let d8 = BinaryFrame::Domain(
        BinarySourceWord::W8(Bit8::new(0b10101000).unwrap()).domain_identity(),
    );
    let d9 = BinaryFrame::Domain(
        BinarySourceWord::W9(Bit9::new(0b101010000).unwrap()).domain_identity(),
    );
    let frames = vec![
        BinaryFrame::Open,
        d3.clone(),
        BinaryFrame::Space,
        d8.clone(),
        BinaryFrame::Space,
        d9.clone(),
        BinaryFrame::Space,
        числове_слово(24),
        BinaryFrame::Space,
        числове_слово(48),
        BinaryFrame::Close,
    ];
    let encoded = BinaryFrame::encode_exact_domain_program(&frames).unwrap();
    assert_eq!(BinaryFrame::decode_exact_domain_program(&encoded).unwrap(), frames);
    assert_eq!(decode_binary_program(&encoded).unwrap(), frames);

    // Однаковий восьмибітний payload не є дозволом змінити історичну роль.
    let old = BinaryFrame::Function(sens::sens!(10101000));
    assert_ne!(encode_binary_program(&[old]).unwrap(),
               encode_binary_program(&[d8]).unwrap());
    assert_ne!(encode_binary_program(&[d3]).unwrap(),
               encode_binary_program(&[d9]).unwrap());
    assert_ne!(числове_слово(24), числове_слово(48));
}

#[test]
fn старі_виклики_літерали_та_некваліфіковані_числа_блокуються() {
    let old = [
        BinaryFrame::Function(sens::sens!(10101000)),
        BinaryFrame::Number(Rational::from_literal("1", "2").unwrap()),
        BinaryFrame::BinaryNumber(BinaryNumber::parse("1").unwrap()),
    ];
    for frame in old {
        let sequence = [BinaryFrame::Open, frame, BinaryFrame::Close];
        assert!(matches!(
            BinaryFrame::encode_exact_domain_program(&sequence),
            Err(BinaryFrameError::LegacyFrameForbidden { index: 1 })
        ));
        // Старий декодер зберігається лише для читання архівних кадрів.
        let historical_bits = encode_binary_program(&sequence).unwrap();
        assert_eq!(decode_binary_program(&historical_bits).unwrap(), sequence);
        assert!(matches!(
            BinaryFrame::decode_exact_domain_program(&historical_bits),
            Err(BinaryFrameError::LegacyFrameForbidden { index: 1 })
        ));
    }
}

#[test]
fn текст_d7_і_d2_структура_залишаються_безпечними_даними() {
    let frames = vec![
        BinaryFrame::Open,
        BinaryFrame::Text(Text7::from_cells(vec![0, 127]).unwrap()),
        BinaryFrame::Close,
    ];
    let bits = BinaryFrame::encode_exact_domain_program(&frames).unwrap();
    assert_eq!(BinaryFrame::decode_exact_domain_program(&bits).unwrap(), frames);
    assert!(matches!(
        BinaryFrame::encode_exact_domain_program(&[BinaryFrame::Close]),
        Err(BinaryFrameError::UnexpectedClose { index: 0 })
    ));
}
