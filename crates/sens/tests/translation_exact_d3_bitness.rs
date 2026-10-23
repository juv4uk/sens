//! Перевірки механізму exact-width перенесення доменних координат.
//!
//! Мовні закони EQ/ATOM/COND перевіряються Lisp-свідками в
//! tests/semantic/; цей файл не визначає очікувану семантику SENS.

use sens::{
    domain_ladder::DomainCoordinate, pack_domain_coordinates, packed_transport_accounting,
    unpack_domain_coordinates,
};

#[test]
fn всі_2046_координат_д1_д10_зберігають_ширину_і_біти_без_padding() {
    let mut coordinates = Vec::with_capacity(2046);
    let mut widths = Vec::with_capacity(2046);
    let mut semantic_bits = 0usize;

    for width in 1u8..=10u8 {
        let capacity = 1u16 << width;
        for bits in 0..capacity {
            let coordinate = DomainCoordinate::new(width, bits).expect("повна бітова координата");
            assert_eq!(coordinate.width(), width);
            assert_eq!(coordinate.bits(), bits);

            // Координата є парою (ширина,біти), не числовим ID функції.
            if width != 1 && bits < (1u16 << (width - 1)) {
                assert_ne!(
                    coordinate,
                    DomainCoordinate::new(width - 1, bits).unwrap(),
                    "D{width}:{bits:b} не може успадкувати роль D{}",
                    width - 1
                );
            }
            coordinates.push(coordinate);
            widths.push(width);
            semantic_bits += usize::from(width);
        }
        // Граничний payload для Dn завжди заборонений, навіть якщо влізе в u16.
        assert_eq!(DomainCoordinate::new(width, capacity), None);
    }

    assert_eq!(coordinates.len(), 2046);
    assert_eq!(semantic_bits, 18434);

    let packed = pack_domain_coordinates(&coordinates);
    assert_eq!(packed.bit_len(), semantic_bits);
    assert_eq!(packed.byte_len(), 2305); // 18434 біт без міжслівного вирівнювання
    assert_eq!(
        unpack_domain_coordinates(&packed, &widths).as_deref(),
        Some(coordinates.as_slice()),
        "кожен Dn має відновитися з оригінальною шириною"
    );

    // Семантичні біти не підмінюються байтовим доповненням.
    let accounting = packed_transport_accounting(&packed, 0);
    assert_eq!(accounting.semantic_payload_bits, 18434);
    assert_eq!(accounting.tail_unused_bits, 6);
    assert_eq!(accounting.total_wire_bits, 18440);

    // Декодер без повного доказового розкладу ширин мусить відмовити.
    assert!(unpack_domain_coordinates(&packed, &widths[..widths.len() - 1]).is_none());
    let mut invalid = widths.clone();
    invalid[0] = 11;
    assert!(unpack_domain_coordinates(&packed, &invalid).is_none());

    // Усе це лише перенос координат: жодної автоматичної callability D7/D10
    // чи перенесення ролі D8 EQUAL до того самого payload іншої ширини.
    assert_ne!(
        DomainCoordinate::new(8, 0b11110111),
        DomainCoordinate::new(3, 0b101)
    );
}
